# 04. Post Exposure Bake & Development stage

**Objective:** To define the physical chemistry, differential equations, surrogate deep learning models, and dissolution kinetics used to simulate the Post-Exposure Bake (PEB) and development of Chemically Amplified Resists (CAR).

---

## 1. Concepts and Resist Chemistry

**Chemically Amplified Resists (CAR):** During 193nm DUV exposure, photons do not possess sufficient energy to directly cleave the polymer matrix. Instead, the optical energy is absorbed by Photoacid Generator (PAG) compounds, which release acid catalysts into the film without immediately changing its solubility.

**Thermal Chemical Amplification:** The Post-Exposure Bake (PEB) utilizes thermal energy from the hotplate to drive the catalytic reactions. Heat facilitates the spatial diffusion of the generated photoacid, allowing a single acid molecule to catalyze multiple deprotection reactions, thereby amplifying the chemical contrast.

**Polymer Protection Fraction ($M$):** By the end of the baking cycle, the system establishes a final spatial distribution of protected polymer sites, denoted as $M$. This value ranges from 0.0 (fully deprotected and soluble) to 1.0 (fully protected and insoluble).

### Phase I: Exposure & Acid Generation (Dill’s ABC Law)
This photochemical response is governed by a simplified variation of Dill’s A/B/C kinetic parameters. The local concentration of generated photoacid $H_0$ immediately following exposure is given by:

$$H_0(x,y) = 1.0 - \exp(-C \cdot I(x,y) \cdot E)$$

Where:
*   $C$: Dill’s photolysis parameter ($0.042 \text{ cm}^2/\text{mJ}$).
*   $I(x,y)$: Local normalized aerial image optical intensity.
*   $E$: Absolute exposure dose delivered to the field in $\text{mJ/cm}^2$.

### Phase II: Post-Exposure Bake (PEB) Kinetics
During the PEB thermal phase, two competing actions occur simultaneously: thermal acid-catalyzed deprotection of the polymer resin matrix and base quencher neutralization.

**1. Coupled Reaction-Diffusion PDEs**
The spatial-temporal progression of the photoacid $H(x,y,t)$ and base quencher $Q(x,y,t)$ concentrations over the bake duration is captured by two coupled non-linear partial differential equations:

$$\frac{\partial H}{\partial t} = D_H \nabla^2 H - K_N H Q$$
$$\frac{\partial Q}{\partial t} = D_Q \nabla^2 Q - K_N H Q$$

Where $\nabla^2$ is the 2D spatial Laplacian operator. 

**2. Catalytic Resin Deprotection Mechanics**
As the photoacid diffuses horizontally through the matrix, it systematically cleaves the bulky ester protecting groups. The concentration of the remaining protected polymer matrix fraction $M(x,y,t)$ changes according to first-order reaction kinetics:

$$\frac{\partial M}{\partial t} = -K_{AMP} \cdot H(x,y,t) \cdot M(x,y,t)$$

Where $K_{AMP}$ is the amplification kinetic multiplier ($0.22$), determining the rate of catalytic deprotection per unit of available acid.

---

## 2. Numerical Implementation & Solver Stability

<!-- INSERT IMAGE HERE: Explicit Euler Finite-Difference Scheme Flowchart -->
<!-- Example: ![Explicit Euler Solver](../Images/euler_solver.png) -->

The system natively solves these non-linear reaction-diffusion PDEs using an Explicit Forward Euler finite-difference method. The architecture applies a 5-point spatial Laplacian stencil and zero-flux padding at the simulation boundaries to maintain chemical mass conservation.

---

## 3. Deep Physics-Informed U-Net Surrogate Model

To bypass the computational overhead of solving 150 temporal finite-difference iterations per sample, a Physics-Informed U-Net acts as a fast surrogate model. It predicts the final steady-state $M(x,y)$ matrix directly from the intensity and dose inputs in a single forward pass.

<!-- INSERT IMAGE HERE: Deep Physics-Informed U-Net Architecture Diagram -->
<!-- Example: ![U-Net Architecture](../Images/unet_architecture.png) -->

**Optimization and Training Loop:**
The model parameters are optimized by minimizing the Mean Squared Error (MSE) loss function using the Adam optimizer:

$$L_{MSE} = \frac{1}{W \cdot H} \sum_{i=1}^W \sum_{j=1}^H (\text{Pred}_{i,j} - \text{Target}_{i,j})^2$$

---

## 4. Non-Linear Development Engine (Mack Dissolution Model)

The development phase transforms the chemical profile into physical topography. The model relates the local chemical state of the resist to its vertical etching rate in an alkaline developer solution.

**1. The Kinetic Rate Equations**
The dissolution velocity field $R(M)$ in nanometers per second is calculated using the standard four-parameter Mack equation:

$$R(M) = R_{max} \frac{(a+1)(1-M)^n}{a+(1-M)^n} + R_{min}$$

Where $a$ is derived from the threshold activation $M_{th} = 0.55$ and contrast $n = 5$:

$$a = \frac{n+1}{n-1}(1-M_{th})^n \approx 0.00795$$

**2. Physical Constants and Parameters**
*   $R_{max} = 120.0 \text{ nm/s}$: Maximum dissolution rate of fully un-protected resin.
*   $R_{min} = 0.05 \text{ nm/s}$: Background leakage dissolution rate of completely unexposed resist.
*   $n = 5$: Developer selectivity contrast exponent. 
*   $M_{th} = 0.55$: Threshold activation limit for solubility transition.

**3. Topography Slicing and Binary Mask Generation**
The total thickness of photoresist stripped away during development is calculated by integrating the dissolution rate over the wash time ($t_{wash} = 35\text{s}$):

$$h_{removed}(x,y) = R(M(x,y)) \cdot t_{wash}$$

The final remaining topographical height map is bounded by the substrate floor to prevent negative values:

$$h_{final}(x,y) = \max(H_{initial} - h_{removed}(x,y), 0.0)$$

*(Where H_{initial} is the baseline unexposed resist thickness, typically 175.0 nm).*

To extract clean 2D metrology arrays, this continuous height map is converted into a binary matrix step function using a strict substrate clearing threshold:

$$M_{binary}(x,y) = \begin{cases} 1, & \text{if } h_{final}(x,y) > 0.0 \\ 0, & \text{if } h_{final}(x,y) = 0.0 \end{cases}$$

---

## 5. Automated Data Analysis & Metrology Architecture

<!-- INSERT IMAGE HERE: Integrated Lithography Development & Metrology Methodology Diagram -->
<!-- Example: ![Metrology Pipeline](../Images/metrology_pipeline.png) -->

**1. Critical Dimension (CD) Metrology**
A pixel-counting algorithm analyzes the binary thresholded wafer map, converting continuous runs into line and trench Critical Dimensions by multiplying the lengths by the grid pitch ($3.9 \text{ nm}$).

**2. Surface Quality Metrology**
*   **Line Edge Roughness (LER):** Measures the structural displacement variation of the printed feature edges, computed as $3\sigma_{edge}$:
    $$\text{LER} = 3.0 \cdot \sigma_{edge} \cdot \Delta x$$
*   **Line Width Roughness (LWR):** Measures the variation in total line feature thickness, calculated as $3\sigma_{widths}$:
    $$\text{LWR} = 3.0 \cdot \sigma_{widths}$$

---

## 6. Comprehensive Variable Dictionary

| Symbol | Code Variable | Units | Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| $\Delta x$ | `DX` | nm | 3.9 | Mesh coordinate spatial resolution. |
| $\Delta t$ | `DT` | s | 0.4 | Explicit Euler finite-difference time step. |
| $N$ | `STEPS` | — | 150 | Total discrete PEB integration iterations. |
| $C$ | `DILL_C` | $\text{cm}^2/\text{mJ}$ | 0.055 | Photoacid generation activation constant. |
| $D_H$ | `D_H` | $\text{nm}^2/\text{s}$ | 3.0 | Acid spatial diffusion coefficient. |
| $D_Q$ | `D_Q` | $\text{nm}^2/\text{s}$ | 1.5 | Quencher spatial diffusion coefficient. |
| $Q_0$ | `Q0` | — | 0.44 | Base quencher uniform initialization factor. |
| $K_N$ | `K_N` | $\text{s}^{-1}$ | 1.8 | Neutralization recombination velocity. |
| $K_{AMP}$ | `K_AMP` | $\text{s}^{-1}$ | 0.18 | Catalytic deprotection rate multiplier. |
