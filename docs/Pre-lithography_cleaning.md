# Pre-Lithography Wafer Preparation (SC-1 & HMDS)

This directory contains the C# logic and physics models for the pre-lithography wafer preparation sequence of the V-FAB Digital Twin. Before photoresist can be successfully applied via spin coating, the substrate must undergo physical cleaning (RCA SC-1) and chemical surface modification (HMDS Vapor Prime).

These modules are implemented natively in Unity C# using closed-form empirical and physical equations, bypassing the need for heavy neural network inference at this specific stage.

---

## 🧪 Stage 1: RCA SC-1 Wet Clean

The Standard Clean 1 (SC-1) bath removes organic particulates and surface-adsorbed molecular films using a 1:1:5 volume ratio mixture of Ammonium Hydroxide ($NH_4OH$), Hydrogen Peroxide ($H_2O_2$), and Deionized Water (APM).

### Physical Mechanism: Undercut Lift-Off
Unlike strong acids that chemically dissolve organics, SC-1 exploits a physical **undercut lift-off** mechanism. The $NH_4OH$ slowly etches the native silicon dioxide ($SiO_2$) surface at approximately 4 Å/min (at 80°C). As this etch front progresses, it travels laterally underneath the base of contamination particles, cutting away their contact area until adhesion fails and the particle disperses into the bath.

### Governing Equations
*   **Etch Depth Accumulation:**
    $$d(t) = r \times t$$
    *(Where $r = 4.0 \text{ Å/min}$ and $t$ is dip time in minutes).*

*   **Removal Fraction:**
    $$R(t) = \min\left(1.0, \frac{d(t)}{d_{ref}}\right) \times 100\%$$
    *(Where $d_{ref} = 40 \text{ Å}$ is the critical undercut depth required for complete particle lift-off).*

---

## ♨️ Stage 2: HMDS Vapor Prime & Dehydration

Following the SC-1 clean, the $SiO_2$ surface is terminated with hydrophilic silicon hydroxyl ($Si–OH$) groups, which inherently prevent photoresist adhesion. The wafer is processed in a vacuum oven flooded with Hexamethyldisilazane (HMDS) vapor.

### Chemical Conversion
The HMDS reacts with surface hydroxyl groups, replacing them with trimethylsilyl groups and releasing ammonia:
$$2(CH_3)_3Si–NH–Si(CH_3)_3 + Si–OH \rightarrow Si–O–Si(CH_3)_3 + NH_3\uparrow$$

This transforms the hydrophilic surface into a hydrophobic one, raising the water contact angle ($\theta$) to allow for spin-coating adhesion.

### Empirical Adhesion Model
To accurately calculate the contact angle output in real-time, an empirical saturating exponential model was fitted to historical Design of Experiments (DOE) data from UT Dallas. 
1. **Flash Adhesion:** Rapid initial reaction starting from the hydrophilic $SiO_2$ surface.
2. **Saturation Limit:** The maximum possible angle bounded by the selected oven temperature.
3. **Exponential Decay:** Simulates time-dependent saturation over the bake duration.

**Adhesion Gate:** To successfully pass this stage and unlock the Spin Coater, the resulting contact angle must satisfy $\theta \ge 65^\circ$.

---

## 💻 Unity Implementation

### `SC1Controller.cs`
*   **Function:** Manages the SC-1 wet bench simulation.
*   **Operation:** Runs a fixed 80°C standard recipe.
*   **Features:** Displays real-time undercut etch depth and particle removal percentages. Utilizes a background time-multiplier to simulate a 10-minute chemical dip smoothly within gameplay constraints.

### `HMDSController.cs`
*   **Function:** Manages the combined Dehydration Bake and HMDS Vapor Prime oven.
*   **Inputs:** Hotplate Temperature (90°C – 160°C) and Prime Time (20s – 300s).
*   **Outputs:** Calculates the predicted surface contact angle in real-time.
*   **Logic:** Enforces the $65^\circ$ adhesion gate. If the user inputs insufficient parameters, the system flags an adhesion failure, requiring the user to recalibrate the recipe before proceeding.
