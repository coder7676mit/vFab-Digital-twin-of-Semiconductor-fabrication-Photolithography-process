# Process Capability Specifications: Sub-100nm DUV Lithography Digital Twin

This repository details the architecture and deployment of a physics-informed deep learning Digital Twin designed for sub-100nm 193nm Deep Ultraviolet (DUV) immersion lithography. By replacing computationally bottlenecked numerical partial differential equation (PDE) solvers with a synchronized, dual-stage Convolutional U-Net surrogate architecture, this platform achieves rapid spatial profile prediction, post-exposure bake (PEB) chemical kinetic mapping, and volumetric fluidic etching simulation while maintaining sub-nanometer critical dimension (CD) fidelity.

## The Digital Twin Paradigm in Semiconductor Fabrication

In advanced semiconductor high-volume manufacturing (HVM), the photolithographic transfer of sub-wavelength design rules is dominated by highly non-linear optical diffraction and complex photoacid diffusion kinetics. Traditionally, predicting wafer-level topography requires Rigorous Coupled-Wave Analysis (RCWA) and iterative finite element methods to solve Hopkins-Abbe equations and Dill/Mack kinetic models. While highly accurate, these first-principle solvers are computationally prohibitive, creating massive bottlenecks in Design-Technology Co-Optimization (DTCO) and Optical Proximity Correction (OPC) verification cycles.

The deployment of a Lithography Digital Twin fundamentally disrupts this workflow. By abstracting the physical fab environment into a high-fidelity virtual replica, process engineers can execute exhaustive multi-variable process window explorations such as Dose-Focus latitude sweeps and localized defect analysis—without the immense capital expenditure of exposing physical test wafers or the temporal cost of traditional TCAD simulations.

This project demonstrates how deep neural networks can function as highly accurate surrogate models for fundamental lithography physics. By mapping the continuous spatial transfer functions of real optical systems and the contrast thresholds of Chemically Amplified Resists (CAR), the system enables near-instantaneous, predictive wafer metrology. This capability allows for real-time fab floor analytics, dynamic recipe correction, and the rapid prototyping of complex sub-100nm layout geometries (including line-end shortening, proximity spillage, and contact corner-rounding) in a purely computational domain.

---

## 🔬 System Resolution & Pattern Capabilities
* **Target Resolution Nodes:** Sub-100nm critical dimensions (CD), capturing structural limits from $40\text{ nm}$ up to $150\text{ nm}$ feature sizes.
* **Supported Layout Topologies:** 
  * Dense Vertical Gratings (Nominal $93\text{ nm}$ Trench target window)
  * Dense Horizontal Gratings
  * Two-Dimensional Contact Arrays & Dense Vias
  * Isolated Lines & High-Frequency Multi-Feature Custom Layouts (e.g., T-Junctions and line-end shortening configurations)

---

## 🛠️ Step-by-Step Module Specifications & Operating Ranges

### 1. Photoresist Spin Coating Module
Defines the chemical and physical baseline of the raw polymer film stacked onto the silicon substrate.
* **Resist Classification:** Advanced 193nm Chemically Amplified Resist (CAR).
* **Film Thickness Operating Envelope ($z_0$):** Exactly $120.0\text{ nm}$ to $350.0\text{ nm}$ thin-film boundary.
* **Input parameters:** Speed of the spin coater (rpm) and time of spin.
* **Output:** Final thickness of the Photoresist puddle coated.

### 2. Soft Bake (PAB / pre-baking) Module
Establishes structural stability, drives off residual solvent, and pre-activates the matrix before optical exposure.
* **Process Variables:** Standardized thermal baseline tracking.
* **Input:** Raw unbaked thin-film boundary layer.
* **Output:** Stabilized uniform matrix array mapped across a $1996.8\text{ nm} \times 1996.8\text{ nm}$ spatial area ($\Delta x, \Delta y = 3.9\text{ nm}$ per pixel resolution).

### 3. Optical Exposure Module (Stage 1 ML Core)
Simulates sub-wavelength optical diffraction using a fast physics-informed deep learning inference loop.
* **Illumination Wavelength ($\lambda$):** $193.0\text{ nm}$ (Argon Fluoride [ArF] DUV Laser Core).
* **Numerical Aperture ($NA$) Sweep Range:** $0.50$ to $1.35$ (Immersion capability).
* **Partial Coherence Factor ($\sigma$):** Bounded at $0.85$ conventional source limits.
* **Lens Wavefront Defocus Window:** Controlled drift from $-45.0\text{ nm}$ to $+45.0\text{ nm}$.
* **Exposure Energy Dose ($E$) Input:** Bounded range from $22.0\text{ mJ/cm}^2$ to $38.0\text{ mJ/cm}^2$.
* **Input:** Process parameters such as Dose, Defocus, Numerical aperture and the Mask layout to be printed.
* **Output:** Continuous 2D diffractive Aerial Intensity Field map bounded between $[0.0, 1.0]$.

### 4. Post-Exposure Bake (PEB) Module (Stage 2 ML Core)
Models localized photoacid generation, thermal catalytic de-protection, and base quencher neutralization.
* **Input:** 2-Channel stacked tensor merging the predicted Stage 1 Aerial Field and the normalized Exposure Dose track.
* **Output:** 2D Chemical Protection Profile ($M$), mapping the normalized concentration of protected polymer bonds remaining in the resist matrix $[0.0, 1.0]$.

### 5. Volumetric Chemical Development Module (Backend Physics Engine)
Executes fluidic etching erosion using a threshold-free dissolution kinetics architecture.
* **Development Fluid Wash Duration ($t_{wash}$):** Scaled sweep from $10.0\text{ s}$ to $80.0\text{ s}$.
* **Mack Model Dissolution Primitives:**
  * Maximum Dissolution Rate ($R_{max}$): $120.0\text{ nm/s}$ (fully exposed polymer limits).
  * Minimum Background Leakage Rate ($R_{min}$): $0.05\text{ nm/s}$ (completely unexposed background).
* **Input:** 2D Chemical Profile ($M$) from Stage 2 U-Net.
* **Output:** Raw analog cross-sectional 2D height map containing true sloped sidewalls and footing metrics.

### 6. Real-Time Volumetric Profile Metrology Engine
Extracts unified dimensional measurements without the artifacts associated with single-plane horizontal slicing.
* **Measurement Rule:** Threshold-Free Volumetric Profile Integration (collapses mass coordinates to isolate true 3D spatial properties).
* **Outputs:** 
  * Integrated Average Line CD (nm)
  * Integrated Average Trench CD (nm)
  * Line Edge Roughness (LER - $3\sigma$)
  * Line Width Roughness (LWR - $3\sigma$)

### 7. Current Limitations

While the dual-stage U-Net surrogate model achieves high fidelity within its calibrated boundaries, the current implementation operates under specific physical assumptions that constrain its deployment in absolute real-world High-Volume Manufacturing (HVM):

* **Scalar vs. Vector Optics:** The Stage 1 optical exposure module relies on the scalar Hopkins approximation. At high Numerical Apertures ($NA > 1.20$), vectorial polarization effects, high-angle interference contrast loss, and 3D thick-mask scattering (EMF effects) become dominant. The current scalar model underestimates these high-NA optical phenomena.
* **Continuum vs. Stochastic Chemistry:** The Post-Exposure Bake (PEB) and Mack dissolution modules utilize deterministic, continuum-level PDEs. They do not simulate the stochastic shot noise of photon arrival, nor the probabilistic molecular diffusion of individual photoacids and quenchers. Consequently, while the model calculates geometric LER/LWR, it cannot predict true molecular-scale stochastic defects (e.g., random micro-bridges or line breaks).
* **Idealized Substrate Planarity:** The thin-film module assumes a perfectly planar, highly absorptive silicon substrate. It currently omits the integration of multi-layer optical stacks, such as Bottom Anti-Reflective Coatings (BARC), hardmasks, or underlying topographical features from previous fabrication steps, which introduce complex thin-film standing wave interference.
* **Simplified Dissolution Trajectory:** The development step applies a direct 1D vertical fluidic etching approximation mapped across a 2D grid. True 3D lateral development trajectories—where solvent penetrates sideways into the resist bulk—are simplified, slightly altering the exact curvature of the resist footing.

---

### 8. Future Work & Path to Industry-Grade HVM

To elevate this digital twin from a high-accuracy research prototype to a fully deployable industrial TCAD surrogate, future development will focus on the following architectural integrations:

#### 1. Vectorial Optical Integration & 3D Mask Effects
Upgrading the optical data generation engine to utilize Rigorous Coupled-Wave Analysis (RCWA) or Finite Difference Time Domain (FDTD) solvers. Training the neural network on vector-diffraction datasets will allow the digital twin to accurately map polarization states, Jones matrix pupil functions, and extreme thick-mask shadowing effects essential for high-NA DUV and EUV transitions.

#### 2. Stochastic Defect Modeling
Transitioning the PEB and dissolution stages from continuum mathematics to mesoscale stochastic simulations (e.g., Kinetic Monte Carlo). By introducing photon shot noise and discrete molecular reaction-diffusion tracking, the network will be able to predict the probability distribution of stochastic print failures, rather than just average geometric profiles.

#### 3. Differentiable Inverse Lithography Technology (ILT)
Utilizing the trained forward-predictive digital twin as a differentiable loss layer within an optimization loop. By backpropagating through the optical and chemical U-Nets, the system can automatically synthesize ideal mask patterns, generating advanced Optical Proximity Correction (OPC) features and Sub-Resolution Assist Features (SRAFs) without relying on heuristic rule-based anchoring.

#### 4. Multi-Layer Topography & Standing Wave Simulation
Expanding the input tensor dimensionality to accept substrate layer definitions ($n, k$ values, and thickness arrays). This will allow the U-Net to learn the depth-dependent interference patterns (standing waves) and simulate depth-of-focus (DOF) loss caused by resist coating variations over non-planar underlying device structures.

---

### 9. Project Creators & Contributors

* **Nagendra Kudva** – *Process physics and Machine Learning model developement*  
  B.Tech in Electronics and Communication Engineering, Manipal Institute of Technology. Designed and implemented the core physics-informed deep learning architecture, the continuous Mack dissolution kinetics engine, and the volumetric metrology pipeline.

* **Danny Joseph** – *Unity 3D modeling & Integration*  
  [Institution Name]. Managed the C# bridging logic and real-time visualization deployment for the Unity-based interactive dashboard.

* **Tarun Kumar Agarwal** – *Project Advisor / Principal Investigator*  
  [Institution Name, e.g., IIT Gandhinagar]. Provided domain expertise, guidance on sub-wavelength optical phenomena, and theoretical validation of the physical models.

---

## License

This project is licensed under the **MIT License**

