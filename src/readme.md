# Litho-Digital-Twin: Semiconductor Photolithography Backend

This repository contains the core physics-informed machine learning pipeline for the simulation of semiconductor lithography processes. It includes the physical modeling engines for spin-coating, soft-baking, DUV photon exposure, and chemically amplified resist (CAR) development, paired with a U-Net surrogate model for real-time inference.

## 1. Project Structure

The repository is modularly organized to separate physical simulation logic from deep learning model training:

* `src/physics_engine.py`: Contains the Hopkins-Abbe diffraction solver, reaction-diffusion PDE solvers for PEB, and the Mack Dissolution model.
* `src/train_unet.py`: The PyTorch training pipeline for the U-Net surrogate models.
* `src/inference_utils.py`: Utilities for ONNX model exporting and Unity-Sentis compatibility.
* `data/samples/`: Contains a small subset of pre-computed tensors for architectural verification.

## 2. Getting Started

Follow these steps to set up the environment and run the simulation pipeline:

### Prerequisites

Ensure you have a Python environment (3.9+) installed, then install the required dependencies:

```bash
pip install -r requirements.txt

```

### Reproducing the Dataset

If you wish to regenerate the full dataset locally using the physical solvers:

```bash
python src/physics_engine.py --output_dir ./data/full_dataset

```

### Training the Surrogate Model

To train the native U-Net architecture, point the script to your data directory:

```bash
# To train on the sample subset
python src/train_unet.py --data_dir ./src/samples

```

# To train on the full research dataset
Download the dataset and extract it into a folder named *aerial_image_dataset*

```bash
python src/train_unet.py --data_dir /path/to/your/aerial_image_dataset

```

## 3. Dataset Access

The complete research dataset, consisting of 500 aerial intensity maps and 500 corresponding post-exposure bake (PEB) polymer maps, is available for academic and research purposes:

**[Download Full Dataset (Google Drive)](https://drive.google.com/drive/u/0/folders/1dLii0UoS4ciBFmqyp0dpmPiz6ZV4djaX)

---

## 4. Academic Acknowledgement

This digital twin architecture was developed as part of research into semiconductor process intelligence. The methodologies implemented, including the Hopkins-Abbe TCC formulation and Mack Dissolution kinetics, adhere to standard industry process characterization benchmarks.

*Frontend Visualization:* The Unity-based dashboard and interactive runtime environment for this backend are hosted in a separate repository [Link to Unity Repo].
