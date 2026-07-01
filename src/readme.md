# Machine learning surrogate models

This folder contains datasets and .py files to completely train and run the models for aerial image intensity & post development bake (PEB) stage

## 1. Project Structure

The folder ./src is modularly organized to separate physical simulation logic from deep learning model training:

* `src/physics_engine.py`: Contains the Hopkins-Abbe diffraction solver, reaction-diffusion PDE solvers for PEB, and the Mack Dissolution model.
* `src/train_unet.py`: The PyTorch training pipeline for the U-Net surrogate models.
* `src/train_peb_unet.py`: The PyTorch training pipeline for the Stage 2 Chemical U-Net, utilizing a custom edge-weighted loss function for precise latent image metrology.
* `src/samples/`: Contains a small subset of pre-computed tensors for architectural verification.

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
python src/physics_engine.py --output_dir ./link/to/your/folder/aerial_image_dataset

```

### Training the Surrogate Model for 

To train the native U-Net architecture, point the script to your data directory:

```bash
# To train on the sample subset
python src/train_unet.py --data_dir ./src/samples

```

### To train on the full research dataset
Download the dataset and extract it into a folder named *aerial_image_dataset*

```bash
python src/train_unet.py --data_dir /path/to/your/aerial_image_dataset

```

### Training the Surrogate Model for Post-exposure Bake

To train the 2-channel chemical surrogate to predict polymer deprotection based on dose and intensity:

```bash
python src/train_peb_unet.py
```
(Note: Ensure paths inside the script match your local aerial_image_dataset directory).

---

## 3. Dataset Access

The complete research dataset, consisting of 500 aerial intensity maps, is available for academic and research purposes:

[Download Full Dataset (Google Drive)](https://drive.google.com/drive/u/0/folders/1dLii0UoS4ciBFmqyp0dpmPiz6ZV4djaX)

---

## 4. Academic Acknowledgement

This digital twin architecture was developed as part of research into semiconductor process intelligence. The methodologies implemented, including the Hopkins-Abbe TCC formulation and Mack Dissolution kinetics, adhere to standard industry process characterization benchmarks.

*Frontend Visualization:* The Unity-based dashboard and interactive runtime environment for this backend are hosted in a separate repository [Link to Unity Repo](https://dannyjoseph.itch.io/photolithography).
