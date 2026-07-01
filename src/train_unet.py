import os
import glob
import numpy as np
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# =====================================================================
# 1. FIXED DISK-STREAMING DATASET LAYER
# =====================================================================
class LithoDiskDatasetNCHW(Dataset):
    def __init__(self, base_dir):
        self.base_dir = base_dir
        # Looks for X_input folder inside the directory the user provides
        self.samples = sorted(glob.glob(os.path.join(base_dir, "X_input", "sample_*.npy")))
        if len(self.samples) == 0:
            print(f"⚠️ Warning: No samples found in {os.path.join(base_dir, 'X_input')}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        # Load from the provided base_dir
        x = np.load(os.path.join(self.base_dir, "X_input", f"sample_{idx}.npy"))
        y = np.load(os.path.join(self.base_dir, "Y_normalized_aerial", f"sample_{idx}.npy"))
        return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

# =====================================================================
# 2. THE RESIDUAL NATIVE NCHW U-NET ARCHITECTURE
# =====================================================================

class NativeSentisUNet(nn.Module):
    def __init__(self):
        super().__init__()

        self.enc1 = nn.Sequential(
            nn.Conv2d(4,64,3,padding=1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.1)
        )

        self.pool = nn.MaxPool2d(2)

        self.enc2 = nn.Sequential(
            nn.Conv2d(64,128,3,padding=1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.1)
        )

        self.enc3 = nn.Sequential(
            nn.Conv2d(128,256,3,padding=1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.1)
        )

        self.up2 = nn.ConvTranspose2d(256,128,2,stride=2)

        self.dec2 = nn.Sequential(
            nn.Conv2d(256,128,3,padding=1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.1)
        )

        self.up1 = nn.ConvTranspose2d(128,64,2,stride=2)

        self.dec1 = nn.Sequential(
            nn.Conv2d(128,64,3,padding=1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.1)
        )

        self.final = nn.Conv2d(64,1,1)

    def forward(self,x):

        e1=self.enc1(x)
        p1=self.pool(e1)

        e2=self.enc2(p1)
        p2=self.pool(e2)

        b=self.enc3(p2)

        u2=self.up2(b)
        d2=self.dec2(torch.cat([u2,e2],1))

        u1=self.up1(d2)
        d1=self.dec1(torch.cat([u1,e1],1))

        out=self.final(d1)

        return torch.sigmoid(out)

# =====================================================================
# 3. RUN THE REAL GRADIENT DESCENT TRAINING LOOP
# =====================================================================
if __name__ == "__main__":
    # Add command-line argument parsing
    parser = argparse.ArgumentParser(description="Litho-Digital-Twin Training")
    parser.add_argument("--data_dir", type=str, default="./data/aerial_image_dataset", 
                        help="Path to folder containing X_input and Y_normalized_aerial")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch_size", type=int, default=8)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️ Training on: {device}")

    # Use the argument provided by the user
    dataset = LithoDiskDatasetNCHW(base_dir=args.data_dir)
    train_loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    
    model = NativeSentisUNet().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    criterion_mse = nn.MSELoss()
    criterion_l1 = nn.L1Loss()

    print(f"🏁 Starting training operations on data: {args.data_dir}")
    model.train()
    for epoch in range(args.epochs):
        total_loss = 0.0
        for x_batch, y_batch in train_loader:
            x_batch, y_batch = x_batch.to(device), y_batch.to(device)
            
            optimizer.zero_grad()
            y_pred = model(x_batch)

            if len(y_batch.shape) == 3:
                y_batch = y_batch.unsqueeze(1)

            loss = 0.8 * criterion_mse(y_pred, y_batch) + 0.2 * criterion_l1(y_pred, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        print(f"Epoch [{epoch+1:02d}/{args.epochs}] | Loss: {total_loss/len(train_loader):.6f}")
