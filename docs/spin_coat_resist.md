# 01. Spin Coating Physics and Digital Twin Modeling

**Objective:** To implement a reduced-order empirical model for real-time machine learning (ML) inference and visualization, rather than a computationally heavy fab-grade physics solver. 

**Target Photoresist Thickness:** Bounded between 120 nm and 350 nm, calibrated specifically for DUV 193nm Lithography processes.

---

## 1. Introduction to Spin Coating

Spin coating is one of the most widely used thin-film deposition techniques in semiconductor fabrication. It is commonly used for applying photoresist layers during the photolithography process. In this procedure, a liquid photoresist is dispensed onto the wafer, and the wafer is rotated at a high angular velocity. Due to centrifugal force, the liquid spreads radially outward and gradually forms a thin, uniform film.

The final thickness of this film depends on several coupled process parameters, including:
* Spin speed (RPM)
* Spin time
* Photoresist viscosity
* Solvent evaporation rate
* Acceleration profile
* Wafer temperature
* Ambient humidity
* Fluid density and surface tension

In semiconductor manufacturing, even nanometer-scale variations in photoresist thickness can severely affect lithography quality, line width control, and overall yield.

---

## 2. Physical Stages of the Spin Coating Process

The physical evolution of the spin coating process is categorized into multiple distinct stages:
1. **Dispense Stage:** Photoresist is dropped onto the wafer surface.
2. **Spin-Up Stage:** The wafer accelerates and the fluid begins radial spreading.
3. **Hydrodynamic Thinning:** Centrifugal force dominates and the film thickness rapidly reduces.
4. **Evaporation-Dominated Stage:** The solvent evaporates, causing the viscosity to increase.
5. **Final Stabilization:** The film reaches a near-steady thickness.

---

## 3. Evolution of Spin Coating Physics Models

### 3.1 The Foundational Emslie Model (1958)
One of the earliest theoretical models was proposed by Emslie, Bonner, and Peck in 1958 in their paper, *'Flow of a Viscous Liquid on a Rotating Disk'*. This model established the hydrodynamic basis of spin coating and mathematically described how film thickness decreases over time due to centrifugal force and viscous flow.

The model relied on the following idealized assumptions:
* The fluid is Newtonian.
* The flow is axisymmetric.
* The liquid is incompressible.
* Solvent evaporation is initially negligible.
* The flow remains laminar.

**Core Emslie Relation:**
$$h = \frac{h_0}{\sqrt{1 + \frac{4\rho \omega^2 h_0^2 t}{3\mu}}}$$

where *$h$ is thickness, $rho$ is density, $omega$ is angular velocity, $mu$ is viscosity, and $t$ is spin time.

### 3.2 Limitations of the Original Emslie Model
While foundational, the purely analytical Emslie model became insufficient for production-level process prediction as semiconductor technology advanced. Its primary limitations included:
* It completely ignored solvent evaporation.
* Real photoresists often exhibit non-Newtonian behavior.
* Edge bead effects at the wafer boundary were not modeled.
* Temperature dependence was ignored.
* Airflow and turbulence within the spin bowl were neglected.
* The final stabilized film thickness was not accurately predicted.

Later researchers extended this framework by incorporating solvent evaporation dynamics, empirical spin curves, viscosity evolution, and advanced numerical simulation methods.

---

## 4. Modern Semiconductor Fab Application

Modern fabrication facilities commonly rely on empirical spin curves and rigorous process characterization. 
* Resist vendors provide baseline thickness vs. RPM curves for standard recipes.
* Process engineers validate and recalibrate these recipes experimentally.
* Thickness measurements are typically verified using metrology systems such as ellipsometry, reflectometry, or profilometry.

**Standard Fab Workflow:**
1. Choose the target resist.
2. Collect spin curve data from vendor datasheets or experimental runs.
3. Fit the data to an empirical model.
4. Extract the empirical constant ($K$).

---

## 5. Empirical Relation Used in This Digital Twin

To achieve real-time simulation speeds without solving complex PDEs, this project utilizes a simplified empirical relation:
$$h = K \cdot \text{RPM}^{-n}$$
* $h$ represents the final stabilized thickness.
* $K$ is an empirical fitting parameter derived from datasheet or experimental thickness measurements. It indirectly captures the resist chemistry, viscosity, solvent concentration, and process behavior.
* $n$ is the spin exponent, which is commonly near $0.5$.

**Project-Specific Calibration:**
* A realistic DUV-style target thickness was selected (approximately 200 nm at 3000 RPM).
* Using $n = 0.5$, the parameter $K$ is calculated as $K = h \cdot \text{RPM}^n$.
* This mathematical extraction produced a $K$ value of approximately 11000 for the selected DUV resist process window.

---

## 6. Digital Twin Modeling & Architecture Approach

This project does not attempt to reproduce full, computationally heavy semiconductor fabrication physics. Instead, the objective is to build a real-time interactive process twin that captures the important qualitative behaviors of spin coating. 

The planned system architecture combines:
* Physics-inspired process equations.
* Synthetic process data generation.
* Machine learning surrogate modeling via MLP regression.
* ONNX deployment for cross-platform compatibility.
* Unity-based real-time visualization.
* GPU shader-based wafer rendering.

### 6.1 Simulation Logic & Stability Fixes
* **Thickness Control:** The RPM variable strictly determines the final thickness.
* **Spreading Control:** Time only controls the radial spreading front and the visual progression.
* **Visual Stability:** A simplified phenomenological radial spreading model was introduced, where the spreading front moves outward over time. To improve ML stability and remove visual discontinuities during rendering, a sigmoid transition was used instead of a hard boundary threshold.

---

## 7. Core References
* Emslie, A.G., Bonner, F.T., Peck, L.G. (1958). *Flow of a Viscous Liquid on a Rotating Disk*.
* Meyerhofer, D. (1978). *Characteristics of resist films produced by spinning*.
* Bornside, D.E., Macosko, C.W., Scriven, L.E. *Spin coating of photoresist*.
