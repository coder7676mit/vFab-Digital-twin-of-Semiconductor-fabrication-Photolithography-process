# =========================================================
# STEP 1: INSTALL AND IMPORT COMPATIBILITY DEPENDENCIES
# =========================================================
!pip install -q skl2onnx onnxruntime scikit-learn

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

import skl2onnx
from skl2onnx.common.data_types import FloatTensorType

# =========================================================
# STEP 2: DUV-STYLE RESIST MODEL (TIME ONLY FOR SPREADING)
# =========================================================
def generate_cleanroom_data(samples=10000):
    np.random.seed(42)

    # -----------------------------------------------------
    # 1. INPUT PARAMETERS (Strict float32 arrays)
    # -----------------------------------------------------
    rpm = np.random.uniform(1000, 6000, samples).astype(np.float32)
    time = np.random.uniform(0.0, 30.0, samples).astype(np.float32)
    radius = np.random.uniform(0.0, 1.0, samples).astype(np.float32) # 0 = center, 1 = edge

    # -----------------------------------------------------
    # 2. CALIBRATED MODERN DUV RESIST PARAMETERS
    # -----------------------------------------------------
    K = 11000.0   # Calibrated scaling constant for sub-micron DUV window
    n = 0.5       # Spin-curve power exponent preserved (h ∝ RPM^-0.5)

    # -----------------------------------------------------
    # 3. PHENOMENOLOGICAL RADIAL SPREADING FRONT APPROXIMATION
    # -----------------------------------------------------
    # Time exclusively drives the outward wetting front propagation.
    front_velocity = (rpm / 3000.0) * 0.4
    current_front = np.clip(time * front_velocity, 0.0, 1.0)

    # -----------------------------------------------------
    # 4. FIXED RATIONAL THICKNESS PROFILE (Independent of Time Decay)
    # -----------------------------------------------------
    base_thickness = K * (rpm ** (-n))

    # -----------------------------------------------------
    # 5. SMOOTH SIGMOID TRANSITION TO PREVENT HARD DISCONTINUITIES
    # -----------------------------------------------------
    sharpness = 20.0
    covered_out = 1.0 / (1.0 + np.exp(sharpness * (radius - current_front)))
    covered_out = covered_out.astype(np.float32)

    # Map thickness along the spreading front profile
    thickness_out = (base_thickness * covered_out).astype(np.float32)

    # -----------------------------------------------------
    # 6. REFINED PROCESS VARIATION / NOISE (Tighter Fab Control)
    # -----------------------------------------------------
    # Sourced to match standard deviation tolerances in modern DUV tracks
    noise_std = 5.0
    noise = np.random.normal(0.0, noise_std, samples).astype(np.float32)
    thickness_out = np.where(covered_out > 0.05, thickness_out + noise, 0.0).astype(np.float32)

    # -----------------------------------------------------
    # 7. PHYSICAL SAFEGUARD CLAMPING
    # -----------------------------------------------------
    thickness_out = np.clip(thickness_out, 0.0, 1000.0)

    # -----------------------------------------------------
    # 8. BUILD DATASETS
    # -----------------------------------------------------
    X = np.stack([rpm, time, radius], axis=1).astype(np.float32)
    y = np.stack([thickness_out, covered_out], axis=1).astype(np.float32)

    return X, y

# Generate data arrays
X, y = generate_cleanroom_data()


# =========================================================
# STEP 3: TRAIN NEURAL NETWORK REGRESSOR PIPELINE
# =========================================================
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('mlp', MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42))
])

print("Training the DUV Regressor model...")
pipeline.fit(X, y)
print("Model trained successfully!")


# =========================================================
# STEP 4: EXPORT PIPELINE TO COMPATIBLE ONNX (OPSET 15)
# =========================================================
initial_type = [('float_input', FloatTensorType([None, 3]))]
options = {StandardScaler: {'div': 'div'}}

print("Converting model to ONNX format (Opset 15 mode)...")
onnx_model = skl2onnx.convert_sklearn(
    pipeline,
    initial_types=initial_type,
    options=options,
    target_opset=15
)


# =========================================================
# STEP 5: FORCE FLOAT32 SANITIZATION FOR GAME ENGINE PARSER
# =========================================================
float64_nodes_cleaned = 0
for node in onnx_model.graph.initializer:
    if node.data_type == 11:  # TensorProto.DOUBLE
        arr = np.frombuffer(node.raw_data, dtype=np.float64).astype(np.float32)
        node.raw_data = arr.tobytes()
        node.data_type = 1    # TensorProto.FLOAT
        float64_nodes_cleaned += 1

print(f"Sanitization complete. Scrubbed {float64_nodes_cleaned} double-precision constants to Float32.")


# =========================================================
# STEP 6: SAVE FINAL SERIALIZED MODEL ASSET
# =========================================================
output_filename = "PR_Coating_Model.onnx"
with open(output_filename, "wb") as f:
    f.write(onnx_model.SerializeToString())

print(f"Success! Saved calibrated 32-bit DUV model as '{output_filename}'")
