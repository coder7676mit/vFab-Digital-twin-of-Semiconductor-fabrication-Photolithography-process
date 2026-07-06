# Pre-Processing Machine Learning Models

This directory contains the PyTorch training scripts for the wafer pre-processing stages of the V-FAB Digital Twin. 

Because traditional physics-based partial differential equations (PDEs) for fluid dynamics and thermal solvent diffusion are too computationally expensive for real-time 3D rendering, we utilize deep learning surrogate models. These scripts generate synthetic ground-truth data, train the neural networks, and export the optimized weights for native ingestion into the Unity Sentis engine.

## 📂 File Directory

### 1. `Spin-coatML-train.py`
This script trains a Multi-Layer Perceptron (MLP) regression surrogate to predict the final stabilized photoresist film thickness, bypassing time-dependent hydrodynamic thinning and evaporation physics.
* **Inputs:** Spin Speed (RPM), Spin Time (Seconds)
* **Output:** Final Photoresist Thickness Map (Targeting a DUV window of 120nm to 350nm)
* **Architecture:** MLP
* **Export:** Generates ONNX file for the Unity `SpinController.cs` inference engine.

### 2. `soft-bakeML-train.py`
This script trains a Split Neural Network to map complex solvent diffusion and geometric shrinkage during the Post-Apply Bake (PAB) process. 
* **Inputs:** Initial Photoresist Spin Thickness, Hotplate Bake Temperature, Bake Time
* **Outputs:** 
  1. 2D Spatial Film Height Map (tracking structural shrinkage)
  2. Residual Solvent Volume Fraction
* **Architecture:** Split Neural Network (Shared base with diverging output heads to prevent layout corruption in Unity).
* **Export:** Generates `lumped_softbake.onnx`  for the Unity `HotplateController.cs` inference engine.

## Execution & Export Workflow

To train these models locally and generate the required weights, ensure you have the required dependencies installed (see main repository requirements).

Run the scripts directly via terminal:
```bash
python Spin-coatML-train.py
python soft-bakeML-train.py
```
