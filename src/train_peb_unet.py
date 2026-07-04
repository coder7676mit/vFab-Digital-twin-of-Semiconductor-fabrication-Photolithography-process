import os
import glob
import time
import torch
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
base_dir = "/path/to/your/folder/aerial_image_dataset"
drive_root = base_dir
DRIVE_ROOT = base_dir

x_path = os.path.join(base_dir, "X_input")
y_path = os.path.join(base_dir, "Y_normalized_aerial")

# =====================================================================
# 1. SYNCHRONIZED NCHW DATASET LOADER
# =====================================================================
class StandardLithoDataset(Dataset):
    def __init__(self, drive_root):
        self.x_paths = sorted(
    glob.glob(os.path.join(base_dir, "X_input", "*.npy"))
)

        self.y_paths = sorted(
    glob.glob(os.path.join(base_dir, "Y_normalized_aerial", "*.npy"))
)

    def __len__(self):
        return len(self.x_paths)

    def __getitem__(self, idx):
        x_input = np.load(self.x_paths[idx]).astype(np.float32)
        y_aerial = np.load(self.y_paths[idx]).astype(np.float32)

       # Standardize Target Ordering into clean single-channel NCHW layout: [1, 512, 512]
        if y_aerial.ndim == 2:
            y_aerial = np.expand_dims(y_aerial, axis=0)
        elif y_aerial.ndim == 3 and y_aerial.shape[0] != 1:
            y_aerial = y_aerial[0:1, :, :] # Isolate first channel axis

        # FIXED NCHW SLICING: Extract Channel 1 directly from the first axis index
        # Avoids channel-last ellipsis slicing that was distorting spatial coordinates
        dose_map = x_input[1:2, :, :]  # Yields clean [1, 512, 512] slice

        return torch.tensor(y_aerial), torch.tensor(dose_map)

# =====================================================================
# 2. BALANCED 2D PHYSICS SOLVER
# =====================================================================
DILL_C = 0.055
DX = 3.9
DT = 0.4
STEPS = 150

D_H = 3.0
D_Q = 1.5
Q0 = 0.44
K_N = 1.8
K_AMP = 0.18

alpha_h = D_H * DT / (DX ** 2)
alpha_q = D_Q * DT / (DX ** 2)

def compute_standard_peb_target(intensity_batch, dose_batch):
    if torch.max(dose_batch) <= 1.0:
        dose_mJ = dose_batch * 38.0
    else:
        dose_mJ = dose_batch

    H = 1.0 - torch.exp(-DILL_C * intensity_batch * dose_mJ)
    Q = torch.full_like(H, Q0, device=device)
    M = torch.ones_like(H, device=device)

    for step in range(STEPS):
        H_padded = F.pad(H, (1, 1, 1, 1), mode='circular')
        Q_padded = F.pad(Q, (1, 1, 1, 1), mode='circular')

        lap_h = (H_padded[:,:,2:,1:-1] + H_padded[:,:,:-2,1:-1] + H_padded[:,:,1:-1,2:] + H_padded[:,:,1:-1,:-2] - 4.0 * H)
        lap_q = (Q_padded[:,:,2:,1:-1] + Q_padded[:,:,:-2,1:-1] + Q_padded[:,:,1:-1,2:] + Q_padded[:,:,1:-1,:-2] - 4.0 * Q)

        reaction = K_N * H * Q
        H = torch.clamp(H + alpha_h * lap_h - DT * reaction, 0.0, 2.0)
        Q = torch.clamp(Q + alpha_q * lap_q - DT * reaction, 0.0, 1.0)
        M = torch.clamp(M - DT * K_AMP * H * M, 0.0, 1.0)

    return M

# =====================================================================
# 3. FINE-TUNING ADDITION: EDGE-WEIGHTED LOSS FUNCTION
# =====================================================================
class EdgeWeightedMSELoss(nn.Module):
    def __init__(self, edge_weight=5.0):
        super().__init__()
        self.edge_weight = edge_weight
        self.kernel = torch.tensor([[[[-1, -1, -1],
                                      [-1,  8, -1],
                                      [-1, -1, -1]]]], dtype=torch.float32)

    def forward(self, pred, target):
        kernel = self.kernel.to(pred.device)
        edge_map = F.conv2d(target, kernel, padding=1)
        edge_mask = (torch.abs(edge_map) > 0.1).float()

        weight_matrix = 1.0 + (edge_mask * (self.edge_weight - 1.0))
        squared_errors = (pred - target) ** 2
        return torch.mean(squared_errors * weight_matrix)

# =====================================================================
# 4. SENTIS-COMPATIBLE MULTI-PARAMETER CHEMICAL UNET (2-CHANNEL)
# =====================================================================
# FIXED: Re-added the foundational sub-convolutional layer class block
class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    def forward(self, x): return self.conv(x)

class StandardChemicalUNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.inc = DoubleConv(2, 32) # Handled concurrently
        self.down1 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(32, 64))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(64, 128))
        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.upconv1 = DoubleConv(128, 32)
        self.up2 = nn.ConvTranspose2d(32, 32, 2, stride=2)
        self.upconv2 = DoubleConv(64, 32)
        self.outc = nn.Sequential(nn.Conv2d(32, 1, 1), nn.Sigmoid())

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        out = self.up1(x3)
        out = torch.cat([out, x2], dim=1)
        out = self.upconv1(out)
        out = self.up2(out)
        out = torch.cat([out, x1], dim=1)
        out = self.upconv2(out)
        return self.outc(out)

# =====================================================================
# 5. EXECUTE GRADIENT FINE-TUNING SWEEP
# =====================================================================
if __name__ == "__main__":
    # 1. Initialize the DataLoader inside the main block
    train_loader = DataLoader(StandardLithoDataset(DRIVE_ROOT), batch_size=4, shuffle=True, drop_last=True)

    model_chem = StandardChemicalUNet().to(device)
    optimizer_chem = torch.optim.AdamW(model_chem.parameters(), lr=1e-3, weight_decay=1e-4)

    TOTAL_EPOCHS = 10
    criterion = EdgeWeightedMSELoss(edge_weight=5.0)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer_chem, T_max=TOTAL_EPOCHS, eta_min=1e-5)

    print("🚀 Starting Fine-Tuned 2-Channel Chemical U-Net Training...")
    print("-" * 60)

    for epoch in range(TOTAL_EPOCHS):
        model_chem.train()
        total_loss = 0.0
        for intensity, dose in train_loader:
            intensity, dose = intensity.to(device), dose.to(device)

            with torch.no_grad():
                target_M = compute_standard_peb_target(intensity, dose)

            optimizer_chem.zero_grad()
            chem_input = torch.cat([intensity, dose], dim=1)

            preds = model_chem(chem_input)
            loss = criterion(preds, target_M)
            loss.backward()
            optimizer_chem.step()
            total_loss += loss.item()

        current_lr = optimizer_chem.param_groups[0]['lr']
        scheduler.step()
        print(f"✨ Epoch [{epoch+1:02d}/{TOTAL_EPOCHS:02d}] | LR: {current_lr:.6f} | Loss: {total_loss/len(train_loader):.6f}")
