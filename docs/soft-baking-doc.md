# 02. Soft-Baking (Pre-Bake) Process Modeling

**Objective:** To define the physical modeling, kinetic equations, and spatial uniformity metrics utilized in the Post-Apply Bake (PAB) module of the digital twin.

---

## 1. Objectives and Process Overview

Baking a photoresist thin film remains one of the most critical, highly coupled, and complex steps in the lithographic process. The post-apply bake (PAB) process, alternatively referred to as a softbake or prebake, involves drying the photoresist immediately following the centrifugal spin-coating phase by driving out volatile casting solvents.

The physical elimination of solvent achieves four critical process engineering outcomes:
* It stabilizes the film thickness.
* It fundamentally alters subsequent post-exposure bake (PEB) and development rates.
* It optimizes resist adhesion to the underlying substrate matrix.
* It reduces film tackiness, mitigating susceptibility to particulate defect contamination.

---

## 2. Governing Textbook Equations

### 2.1 Thermal Decomposition Kinetics
When a positive photoresist is subjected to thermal excitation on a hotplate at temperatures exceeding approximately 70°C to 80°C, its light-sensitive component, the photoactive compound (PAC), undergoes an unintended thermal decomposition into a non-photosensitive product ($M \to \Delta X$).

To quantify the remaining fraction of active sensitizer ($m'=M_0/M_0'$) as a function of processing parameters, we solve the first-order kinetic decay equation:

$$m'=\exp(-K_T\cdot(t_b-t_{wup}))$$

Where:
* $t_b$ represents the total softbake time configured by the operator.
* $t_{wup}$ is the system warm-up lag time required for the silicon substrate to reach thermal equilibrium with the hotplate chuck.
* $K_T$ represents the thermal decomposition rate constant:

$$K_T=A_r\cdot\exp\left(-\frac{E_a}{R\cdot T}\right)$$

### 2.2 Global Solvent Evaporation and Mass Loss
The physical removal of volatile casting solvents—specifically Propylene Glycol Monomethyl Ether Acetate (PGMEA) from a Poly(p-hydroxystyrene) [PHOST] or acrylic-based chemically amplified resist (CAR) matrix—is governed by coupled free-volume diffusion and surface vaporization.

Integrated across a thin film, the average remaining solvent concentration ($C(t)$) over time follows a specialized first-order exponential decay toward a temperature-dependent saturation ceiling ($C_{dry}$):

$$C(t)=C_{dry}+(C_0-C_{dry})\cdot\exp(-K_T\cdot t)$$

Where:
* $C_0$ is the initial solvent volume fraction directly following spin coating (21% volume fraction).
* $C_{dry}$ represents the asymptotic zero-solvent minimum limit trapped by the collapsing polymer free volume (2% volume fraction).

### 2.3 Geometric Volume-to-Thickness Transformation Law
As the solvent volume fraction decreases, the polymer matrix undergoes structural shrinkage along the Z-axis. The final post-bake geometric thickness ($h_{bake}$) is calculated by normalizing the remaining solvent fraction against the initial unbaked boundary conditions:

$$h_{bake}=h_{dry}+(h_{spin}-h_{dry})\cdot\frac{C(t)-C_{dry}}{C_0-C_{dry}}$$

Where:
* $h_{spin}$ is the initial wet thickness as per the spin coater.
* $h_{dry}$ represents the absolute minimum structural thickness floor of the completely dried solids matrix, calculated via the solids packing fraction:

$$h_{dry}=h_{spin}\cdot(1.0-(C_0-C_{dry}))$$

> "Using this solvent diffusion model, one can predict the impact of pre_bake time and temperature on the final resist thickness and the resulting solvent distribution as a function of depth into the resist at the end of the bake. Such modeling provides for a very interesting result. Any combination of initial resist thickness and initial solvent content that produces a certain final resist thickness always results in essentially the same solvent distribution in the resist at the end of the bake." (pg. 208 C. Mack book.)

---

## 3. Calibrated System Constants

| Mathematical Symbol | Calibrated Value | Engineering Dimensions | Physical Justification & Academic Source |
| :--- | :--- | :--- | :--- |
| $R$ | $8.31431$ | $\text{J}\cdot\text{mol}^{-1}\cdot\text{K}^{-1}$ | Universal Gas Constant. |
| $E_a$ | $126.8\times 10^3$ | $\text{J}\cdot\text{mol}^{-1}$ | Activation energy. |
| $\ln(A_r)$ | $35.3$ | $\ln(\text{min}^{-1})$ | Pre-exponential frequency factor for positive resist degradation. |
| $E_{evap}$ | $55.0\times 10^3$ | $\text{J/mol}$ | Combined activation energy path of internal bulk diffusion and vaporization enthalpy. |
| $A_{arr}$ | $5.0\times 10^6$ | $\text{s}^{-1}$ | Frequency coefficient matching empirical solvent loss curves for thin films. |
| $C_0$ | $0.21$ | Volume Fraction | Standard initial solvent payload for a wet spin-coated layer. |
| $C_{dry}$ | $0.02$ | Volume Fraction | High-temperature structural trapping limit (2-3%) where free volume collapses. |
| $t_{wup}$ | $17.5$ | seconds | Proximity hotplate thermal conduction warm-up delay. |

---

## 4. Spatial Uniformity Analysis and ML Model Integration

To bridge the 1D neural network output with a high-resolution 2D visual layout for the digital twin, the system runs parallel batch inference over a $512\times 512$ coordinate grid. Thermal non-uniformities across real equipment are accounted for by introducing a radial temperature droop from the hotter center core out to the cooling margins:

$$T_{pixel}(r)=T_{user}-\Delta T_{droop}\cdot r^2$$

Where $r$ represents the normalized radius ($0\le r\le 1$) and $\Delta T_{droop}=1.5^\circ\text{C}$.

Once the neural network evaluates the thickness at every grid pixel, the macro-level process quality is verified by computing the Percent Non-Uniformity ($U$) Metric directly from the final spatial thickness map:

$$U=\frac{h_{max}-h_{min}}{2\cdot h_{avg}}\times 100$$

Where:
* $h_{max}$ is the maximum thickness detected across the grid pixels (occurring at the cooler outer boundaries).
* $h_{min}$ is the minimum thickness detected (occurring at the hotter center).
* $h_{avg}$ is the calculated arithmetic mean height of the entire active wafer surface area.

### 4.1 Evaluated Process Windows (ONNX Direct Mapping)

Below are the documented console outputs from the digital twin evaluating three distinct thermal processing windows on a baseline 200.0 nm wet-spun film:

```text
======================================================================
DIRECT MAP ONNX RUN: Incoming Flat Spin Base = 200.0 nm
======================================================================

▶ PROFILE READOUT: Low Temp / Short Bake (80.0°C for 30.0s)
  - Center Pixel Film Height:        187.23 nm
  - Center Pixel Residual Solvent:   5.99% Vol
  - Calculated Mean Thickness (Avg): 187.98 nm
  - Uniformity Error Metric (U):     0.396%

▶ PROFILE READOUT: Standard Target Window (95.0°C for 40.0s)
  - Center Pixel Film Height:        169.34 nm
  - Center Pixel Residual Solvent:   5.52% Vol
  - Calculated Mean Thickness (Avg): 169.75 nm
  - Uniformity Error Metric (U):     0.244%

▶ PROFILE READOUT: Aggressive / Over-Bake (115.0°C for 90.0s)
  - Center Pixel Film Height:        162.59 nm
  - Center Pixel Residual Solvent:   5.15% Vol
  - Calculated Mean Thickness (Avg): 162.59 nm
  - Uniformity Error Metric (U):     0.003%
