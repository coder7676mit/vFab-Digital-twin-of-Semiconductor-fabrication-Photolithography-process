# 03. Mask Generation & Optical Aerial Image Formation

**Objective:** To define the physical system configurations, geometric layout generation protocols, and the Hopkins-Abbe Fourier diffraction mathematics utilized in the Stage 1 Optical Machine Learning Surrogate Model.

---

## 1. Physical System Configuration & Light Source Parameters

The digital twin models a 193nm Argon Fluoride (ArF) Immersion Step-and-Scan System, analogous to industrial ASML Twinscan NXT scanner platforms. The physical system constants are strictly bound within the execution script as follows:

*   **Exposure Source Wavelength ($\lambda$):** 193.0 nm (Deep Ultraviolet Excimer Laser).
*   **Grid Spatial Resolution ($\Delta x$):** 3.9 nm per pixel grid increment.
*   **Total Matrix Coordinate Domain:** 512×512 pixels (Res×Res), defining a total real-world layout canvas footprint of:
    Field Width = 512 × 3.9 nm ≈ 2.0 μm
*   **Partial Coherence Factor ($\sigma$):** 0.85, specifying the ratio of the numerical aperture of the illumination system (condenser) to the numerical aperture of the objective lens.
  
### 1.1 The Physical Scanner Architecture

The exposure system inserts a complex projection lens assembly between the photomask and the silicon wafer. DUV light waves stream from the excimer source, passing through specialized illumination fly-eye optics to establish a uniform partially coherent spatial mode. This light passes through the photomask (object plane), where structural patterns diffract the incoming photons into a wide spectrum of spatial frequency angles.

These diffracted fields travel onward to meet the entry pupils of the projection objective lens. In high-performance scanner tracks, this objective assembly contains upwards of 20 to 30 highly polished catadioptric (lens and mirror combination) elements operating in an immersion fluid medium (ultrapure water, $n=1.44$). The objective assembly captures the diffracted wave angles, recombining them at the focal plane via inverse Fourier summation to yield the continuous spatial profile known as the Aerial Image Intensity.

---

## 2. Geometric Mask Layout Construction Theory

Photomasks are built as binary chrome-on-glass plates, where clear quartz glass transmits 100% of the light field (1.0) and opaque chrome completely blocks it (0.0). Features are written into the `mask_2d` matrix using a discrete pixel pitch.

Five distinct industrial geometries are generated across a total distribution profile of 500 total files (5 layouts × 100 random process variations):

*   **Layout 0: Dense Vertical Grating Lines**
    *   Critical Dimension (CD): 24 pixels × 3.9 nm = 93.6 nm open clear space.
    *   Grating Pitch ($P_{grid}$): 32 pixels × 3.9 nm = 124.8 nm dark space between slots.
    *   Spatial Distribution Loop: Generates 7 repetitive clear stripes centered on the array:
        $$x_{start} = 512 - \frac{7 \cdot CD + 6 \cdot P_{grid}}{2} + col \cdot (CD + P_{grid})$$
*   **Layout 1: Dense Horizontal Grating Lines**
    *   Critical Dimension (CD): 93.6 nm open vertical height slots.
    *   Grating Pitch ($P_{grid}$): 124.8 nm opaque spaces.
    *   Spatial Distribution Loop: Tracks 7 horizontal transparent blocks centered vertically on the grid using identical spacing offsets mapped along the row axes.
*   **Layout 2: Symmetric Contact Hole Array**
    *   Critical Dimension (CD): 93.6 nm × 93.6 nm transparent square openings.
    *   Grating Pitch ($P_{grid}$): 124.8 nm spacing separating adjacent elements.
    *   Spatial Distribution Loop: Maps an 8×8 matrix grid (64 total vias) balanced using an aggregate spatial envelope offset:
        $$Offset = 512 - \frac{8 \cdot CD + 7 \cdot P_{grid}}{2}$$
*   **Layout 3: Isolated Single Vertical Line (Gate Track)**
    *   Critical Dimension (CD): 32 pixels × 3.9 nm = 124.8 nm wide isolated vertical clear channel.
    *   Spatial Distribution Loop: Placed precisely at the center column coordinate axis:
        $$x_{start} = \frac{512 - 32}{2} = 240$$
*   **Layout 4: Isolated Single Contact Via Window**
    *   Critical Dimension (CD): 40 pixels × 3.9 nm = 156.0 nm wide isolated square box.
    *   Spatial Distribution Loop: Centered along both 2D axes starting at coordinate index 236.

---

## 3. Hopkins-Abbe Frequency Domain Mathematics Core

To simulate a partially coherent system quickly, the forward model uses the Hopkins-Abbe Transmission Cross Coefficient (TCC) Formulation. This method decomposes the extended light source into a discrete array of mutually incoherent point-source nodes. Each node emits a coherent wave plane that undergoes independent Fourier diffraction routing.

### Step 1: Discrete Frequency Space Transformation

A 2D discrete frequency mesh grid ($f_x, f_y$) is mapped out using the sample pitch resolution ($\Delta x = 3.9$ nm):
$$\Delta f = \frac{1}{Res \cdot \Delta x} = \frac{1}{512 \cdot 3.9 \cdot 10^{-9} \text{ m}} \approx 5.008 \cdot 10^5 \text{ m}^{-1}$$
$$f_{radius} = \sqrt{f_x^2 + f_y^2}$$

### Step 2: The Complex Pupil Operator & Wavefront Aberrations

The objective lens system acts as a low-pass frequency filter, truncating high-angle diffraction orders that escape past its numerical aperture (NA). The finite physical lens boundary is explicitly tracked via the binary circular Pupil Function:

$$P(f_x, f_y) = \begin{cases} 1.0, & \text{if } f_{radius} \le \frac{NA}{\lambda} \\ 0.0, & \text{if } f_{radius} > \frac{NA}{\lambda} \end{cases}$$

The wavefront undergoes phase deformation when the lens moves away from the ideal focal plane. This shift is governed by a quadratic optical Defocus Aberration Function ($W$):
$$W(f_x, f_y) = 0.5 \cdot Defocus \cdot \lambda^2 \cdot f_{radius}^2$$

Combining both parameters yields the Complex Pupil Operator ($H_{pupil}$), which models the low-pass truncation behavior alongside focus blur phase shifts:
$$H_{pupil}(f_x, f_y) = P(f_x, f_y) \cdot \exp\left(j \cdot \frac{2\pi}{\lambda} \cdot W(f_x, f_y)\right)$$

### Step 3: Concept of the Spatial Frequency Cutoff

The maximum spatial frequency that can propagate through the objective optics is bounded by the lens aperture limit:
$$f_{cutoff} = \frac{NA}{\lambda}$$

If the spacing between mask patterns becomes smaller than this cutoff, the diffracted light rays bend at an angle so steep that they shoot wide past the objective lens pupil. The lens blocks these higher frequencies, causing the recombined light waves at the wafer plane to lose contrast and flatten out into a uniform blur.

---

## 4. Partially Coherent Source Discretization & Summation

The extended illumination source is bounded using the partial coherence constraint ($\sigma$), defining an effective maximum illumination spatial frequency:
$$f_{source\_limit} = \frac{\sigma \cdot NA}{\lambda}$$

The code samples this circular source domain using a uniform 2D grid spanning from $-f_{source\_limit}$ to $+f_{source\_limit}$ in 5 discrete steps along each axis.

### Loop Dynamics & Frequency Shifting

For every individual point source node ($s_x, s_y$) that falls within the source circle ($s_x^2 + s_y^2 \le f_{source\_limit}^2$), the system computes a coherent light contribution:

1.  **Fourier Mask Transformation:** The binary spatial mask is transformed into the frequency domain via a Forward 2D Fast Fourier Transform (FFT):
    $$O(f_x, f_y) = \mathcal{F}\{mask\_2d(x, y)\}$$
2.  **Source Angle Tilting:** The point source’s oblique angle of incidence shifts the mask’s diffracted waves in frequency space. This shift is calculated in discrete grid coordinates:
    $$shift_x = \text{round}\left(\frac{s_x}{\Delta f}\right), \quad shift_y = \text{round}\left(\frac{s_y}{\Delta f}\right)$$
    The frequency matrix is shifted around these calculated offsets using circular rotation vector controls (`np.roll`):
    $$O_{shifted}(f_x, f_y) = \text{Roll}(O(f_x, f_y), shift_x, shift_y)$$
3.  **Pupil Filtering & Inverse Reconstruction:** The shifted diffracted wave fields pass through the objective pupil filter. They are then mapped back to spatial coordinates via an Inverse 2D Fast Fourier Transform ($\mathcal{F}^{-1}$):
    $$E_{coherent}(x, y) = \mathcal{F}^{-1}\{O_{shifted}(f_x, f_y) \cdot H_{pupil}(f_x, f_y)\}$$
4.  **Incoherent Square-Law Integration:** Because the point sources are mutually incoherent, their resulting electric field amplitudes cannot create interference patterns with one another. Instead, their individual intensities (the square of the complex field amplitude) sum up over all valid source entries ($N_{nodes}$) to construct the total Aerial Image Intensity ($I_{aerial}$):
    $$I_{aerial}(x, y) = \frac{1}{N_{nodes}} \sum_{n=1}^{N_{nodes}} \left| E_{coherent, n}(x, y) \right|^2$$

---

## 5. Global Constant Radiometric Scaling & Dataset Export

To ensure the downstream Chemical U-Net learns the true physical relationship between low-contrast features and exposure kinetics, the aerial image intensities are processed through a Global Radiometric Scaling Law:
$$I_{normalized}(x, y) = \text{Clip}\left(\frac{I_{aerial}(x, y)}{1.0}, 0.0, 1.0\right)$$

By dividing by a fixed global constant (1.0) instead of normalizing each image individually to its own local maximum, the simulator preserves true optical contrast degradation. If lens defocus or a tight feature pitch reduces the peak intensity value down to 0.35, the value remains at 0.35. This allows the downstream chemical network to accurately capture pattern failures and layout bridging issues.

### NCHW Tensor Packing Matrix Definitions

The data arrays are formatted into standard NCHW tensor configurations for immediate compatibility with deep learning models and Unity’s Sentis ONNX runtime inference worker:

**Input Array Tensor ($X_{input}$) - [Shape: 4 x 512 x 512]**
*   **Channel 0 (Mask Matrix):** Unaltered binary mask geometry (0.0 or 1.0).
*   **Channel 1 (Normalized Exposure Dose):** Uniform scalar layer normalized to the maximum pipeline limit: $\frac{\text{Dose}_{mJ}}{38.0}$.
*   **Channel 2 (Normalized Defocus):** Uniform scalar layer tracking lens displacement: $\frac{\text{Defocus}_{nm}}{45.0}$.
*   **Channel 3 (Normalized Lens Aperture):** Uniform scalar layer tracking light gathering power: $\frac{NA}{1.35}$.

**Target Prediction Array ($Y_{target}$) - [Shape: 1 x 512 x 512]**
*   **Channel 0 (Aerial Field intensity):** Continuous un-stretched physical light field intensity values ($0.0 \le I \le 1.0$).

Both matrices are saved directly to local caching directories as raw NumPy binary files (`.npy`), establishing a robust dataset for model training and verification loops.
