# train_and_export_split.py
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

torch.manual_seed(42)
np.random.seed(42)

# Textbook Physical Parameters from your screenshots
A_arr, E_a, R = 5.0e6, 55000, 8.31431
C_0, C_dry, t_wup = 0.21, 0.02, 17.5

def solve_softbake_kinetics(h_spin, temp_celsius, time_seconds):
    eff_time = max(0.0, time_seconds - t_wup)
    k_T = A_arr * np.exp(-E_a / (R * (temp_celsius + 273.15)))
    c_t = C_dry + (C_0 - C_dry) * np.exp(-k_T * eff_time)
    h_dry = h_spin * (1.0 - (C_0 - C_dry))
    h_bake = h_dry + (h_spin - h_dry) * ((c_t - C_dry) / (C_0 - C_dry))
    return h_bake, c_t

# 1. Generate Data over your new 100nm to 380nm envelope
num_samples = 10000
h_spin_data = np.random.uniform(130.0, 360.0, num_samples)
temp_data = np.random.uniform(80.0, 120.0, num_samples)
time_data = np.random.uniform(10.0, 120.0, num_samples)

h_bake_targets = np.array([solve_softbake_kinetics(h, temp, t)[0] for h, temp, t in zip(h_spin_data, temp_data, time_data)], dtype=np.float32)
c_t_targets = np.array([solve_softbake_kinetics(h, temp, t)[1] for h, temp, t in zip(h_spin_data, temp_data, time_data)], dtype=np.float32)

X_raw = np.column_stack((h_spin_data, temp_data, time_data)).astype(np.float32)

# Extract precise Scales for your Unity Guy
X_mean, X_std = X_raw.mean(axis=0), X_raw.std(axis=0)
h_mean, h_std = h_bake_targets.mean(), h_bake_targets.std()
c_mean, c_std = c_t_targets.mean(), c_t_targets.std()

print("=== COPY THESE EXACT FLOATS INTO SCRIPT 2 & SCRIPT 3 ===")
print(f"INPUT MEANS: float[] means = {{ {X_mean[0]}f, {X_mean[1]}f, {X_mean[2]}f }};")
print(f"INPUT STDS:  float[] stds  = {{ {X_std[0]}f, {X_std[1]}f, {X_std[2]}f }};")
print(f"THICKNESS OUT: Mean = {h_mean}f, Std = {h_std}f")
print(f"SOLVENT OUT:   Mean = {c_mean}f, Std = {c_std}f\n")

X_scaled = (X_raw - X_mean) / X_std
X_tensor = torch.tensor(X_scaled)

# 2. Split-Output Architecture to prevent layout corruption in Unity Sentis
class SplitSoftBakeEngine(nn.Module):
    def __init__(self):
        super(SplitSoftBakeEngine, self).__init__()
        self.shared_base = nn.Sequential(
            nn.Linear(3, 64), nn.ReLU(),
            nn.Linear(64, 64), nn.ReLU()
        )
        self.thick_head = nn.Linear(64, 1)
        self.solvent_head = nn.Linear(64, 1)

    def forward(self, x):
        features = self.shared_base(x)
        # Returns two distinct output streams
        return self.thick_head(features), self.solvent_head(features)

model = SplitSoftBakeEngine()
optimizer = optim.Adam(model.parameters(), lr=0.003)

# Train Loop
dataset = torch.utils.data.TensorDataset(X_tensor, torch.tensor(h_bake_targets), torch.tensor(c_t_targets))
loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)

for epoch in range(35):
    for bx, bh, bc in loader:
        optimizer.zero_grad()
        pred_h, pred_c = model(bx)
        loss = nn.MSELoss()(pred_h.squeeze(), bh) + nn.MSELoss()(pred_c.squeeze(), bc)
        loss.backward()
        optimizer.step()

# 3. Export to ONNX with explicitly isolated named port channels
model.eval()
torch.onnx.export(
    model, torch.randn(1, 3), "lumped_softbake.onnx",
    export_params=True, opset_version=12, do_constant_folding=True,
    input_names=['input_features'],
    output_names=['predicted_thickness', 'predicted_solvent'],
    dynamic_axes={
        'input_features': {0: 'batch_size'},
        'predicted_thickness': {0: 'batch_size'},
        'predicted_solvent': {0: 'batch_size'}
    }
)
print("ONNX Model generation complete!")
