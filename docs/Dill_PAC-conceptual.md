# Extra concepts regarding Dill's paramters & PAC's


## 1. Comprehensive Reference: Photoactive Compound (PAC) & Dill Parameters

### 1.1 What is PAC?
PAC stands for Photoactive Compound. In older generation optical lithography systems—specifically g-line (436 nm) and i-line (365 nm) setups—a standard positive photoresist formulation consists of three primary components:
1.  **Novolac Resin:** The base polymer matrix that provides structural integrity.
2.  **DNQ Sensitizer (The PAC):** The photoactive compound (Diazonaphthoquinone) that reacts to light.
3.  **Solvent:** The liquid carrier that allows the resist to be spin-coated uniformly onto the wafer.

**Mechanism Before and During Exposure**
*   **Initial State:** Before the stepper shutter opens, PAC molecules are uniformly distributed throughout the bulk volume of the resist film.
*   **Optical Filtering:** The PAC naturally absorbs incoming UV photons. This initial absorption behaves like an internal optical filter, controlling exactly how much light intensity can penetrate into the deeper layers of the film.
*   **The Photochemical Reaction:** When a photon strikes a PAC molecule, it deposits its energy, triggering a rapid chemical transformation:
    $$PAC + Photon \rightarrow Product$$
*   **The Core Interfacial Logic:** The resulting photoproduct possesses completely altered chemical properties compared to the original matrix. Exposed regions undergo a structural shift that makes them highly soluble in an alkaline developer solution, whereas the unexposed regions remain stable and difficult to dissolve. This solubility differential is what ultimately enables sub-micron pattern transfer.

---

### 1.2 Understanding the Normalized Concentration Parameter ($M$)
The state of chemical conversion inside the resist at any discrete $(x,y,z)$ spatial coordinate is tracked using the variable $M$.
*   **$M$:** The local PAC concentration at any active location and time step.
*   **$M_0$:** The initial, pristine PAC concentration before exposure begins.

**Normalized PAC Fraction ($m$):**
$$m = \frac{M}{M_0}$$

> **Physical Interpretation Scale:**
> *   $m = 1.0 \rightarrow$ **Zero exposure occurred.** The resist is completely unexposed; no chemical conversion has taken place.
> *   $m = 0.5 \rightarrow$ **Half-bleached state.** Exactly 50% of the local PAC molecules have reacted with incoming photons.
> *   $m = 0.0 \rightarrow$ **Fully bleached state.** All available PAC at this coordinate has been consumed by the exposure dose.

---

### 1.3 The Dill Parameters ($A, B, C$)
The Dill Parameters characterize how a photoresist absorbs light and how fast its internal chemistry changes over time during exposure. The total absorption profile of the resist film at any point is governed by the fundamental Dill equation:

$$\alpha = A \cdot m + B$$

Where $\alpha$ is the total local absorption coefficient and $m$ is the normalized PAC fraction ($M/M_0$).

#### 🔹 Dill Parameter A (Bleachable Absorption)
Parameter A defines the optical absorption caused directly by the PAC molecules themselves.
*   **High $m$ (High PAC Concentration):** Yields high localized absorption ($\alpha \approx A + B$).
*   **Low $m$ (Low PAC Concentration):** Yields low localized absorption ($\alpha \approx B$).
*   **The Bleaching Phenomenon:** As exposure continues, the concentration of PAC ($m$) steadily drops. Consequently, the local absorption coefficient ($\alpha$) decreases. The resist layer dynamically clears up—or bleaches—allowing light to penetrate deeper and deeper down toward the underlying substrate.

#### 🔹 Dill Parameter B (Unbleachable Absorption)
Parameter B defines the baseline background absorption of the resist system.
*   **Material Origins:** It represents the dead-weight absorption coming from the non-photosensitive resin, the polymer backbone, and other background additives.
*   **Static Nature:** Unlike A, parameter B does not alter or decay during the exposure process; it remains completely constant.
*   **The Baseline Limit:** Even if the resist is exposed to intense energy and the PAC is fully consumed ($m=0$), the film is never 100% transparent. Residual absorption equal to B will always remain.

#### 🔹 Dill Parameter C (Reaction Speed Constant)
Parameter C represents the reaction rate constant or exposure sensitivity coefficient.
*   **Physical Function:** It quantifies the chemical efficiency with which incoming photons convert raw PAC into the soluble photoproduct.
*   **Large C Value:** The resist is highly sensitive; PAC disappears rapidly under light.
*   **Small C Value:** The resist is slow-acting; PAC requires a prolonged dose to convert.

**Exposure Kinetics Equation:** The time-dependent decay of PAC concentration is modeled by the first-order differential relationship:

$$\frac{\partial M}{\partial t} = -C \cdot I \cdot M$$

Where $I$ represents the localized optical intensity at that specific depth layer.

---

### 1.4 The Dill Exposure Equation
By integrating the exposure kinetics differential equation over the total exposure time, we arrive at the classic expression used to calculate the spatial profile of the latent image:

$$m = \frac{M}{M_0} = \exp(-C \cdot E)$$

Where $E$ is the total accumulated exposure dose delivered to that coordinate ($E = \text{Intensity} \times \text{Time}$).

> **Analytical Takeaways:**
> *   $\uparrow$ **Higher Dose ($E$):** Results in a heavier exponential decay, meaning more PAC is consumed ($m \rightarrow 0$).
> *   $\downarrow$ **Lower Dose ($E$):** Leaves the exponential decay minimal, meaning more PAC remains intact ($m \rightarrow 1$).

This closed-form solution is the mathematical foundation universally deployed in lithography simulators (such as PROLITH or numerical physics engines) to instantly translate optical aerial images into spatial chemical concentration maps before running thermal post-exposure bake diffusion algorithms.

---

## 2. Physical and Chemical Foundations of Photoresist Parameters

To model light passing through a photosensitive polymer layer, we must track how its internal optical opacity changes over time during exposure. This behavior is governed by the classic Dill A, B, C Parameters (introduced by Rick Dill and his IBM research team in 1975). These coefficients define the complex, time-dependent absorption coefficient, $\alpha$, of a photoresist film as it interacts with ultraviolet light.

$$\alpha = A \cdot M(z,t) + B$$

Where:
*   $\alpha$ is the total local absorption coefficient ($\mu\text{m}^{-1}$).
*   $A$ is the bleachable absorption coefficient ($\mu\text{m}^{-1}$).
*   $B$ is the unbleachable absorption coefficient ($\mu\text{m}^{-1}$).
*   $M(z,t)$ is the relative concentration of the unexposed photoactive molecule at depth $z$ and exposure time $t$. It is a normalized value bounded strictly between 0.0 and 1.0.

### 2.1 The Exposure Kinetics Differential Framework
The fundamental physics of exposure rely on two coupled differential equations. The first describes how the light wave decays as it travels deeper into the material (the Beer-Lambert Law variation), and the second describes how the chemical compound breaks down as it absorbs photons.

$$\frac{\partial I(z,t)}{\partial z} = -\alpha(z,t) \cdot I(z,t) = -(A \cdot M(z,t) + B) \cdot I(z,t)$$

$$\frac{\partial M(z,t)}{\partial t} = -C \cdot I(z,t) \cdot M(z,t)$$

Where:
*   $I(z,t)$ is the local light intensity ($\text{mW/cm}^2$) at depth $z$ and time $t$.
*   $C$ is the bleaching rate constant ($\text{cm}^2/\text{mJ}$), which measures the optical sensitivity of the photoactive components.

Integrating the rate equation over the exposure time reveals how the concentration of the unexposed molecule decays exponentially based on the total accumulated energy dose ($E = \int I \, dt$):

$$M(z,t) = M_0 \cdot \exp\left(-C \int_0^t I(z,\tau) \, d\tau\right)$$

---

### 2.2 The 193 nm Deep Ultraviolet (DUV) Shift: Why $A \approx 0$
In traditional i-line (365 nm) lithography, photoresists use a Diazonaphthoquinone (DNQ) photoactive compound mixed into a Novolak polymer resin base.
*   **Unexposed State:** The DNQ molecules strongly absorb 365 nm light ($A \gg 0$).
*   **Exposed State:** As photons break down the DNQ molecules, they turn into a transparent byproduct. The material visibly "bleaches" clear, letting light reach deeper down into the film.

However, when the semiconductor industry shifted to 193 nm Argon Fluoride (ArF) DUV lasers to print smaller transistors, this chemical system broke down completely. Novolak resins and DNQ molecules contain aromatic carbon rings that absorb 193 nm light so intensely that the light cannot even penetrate past the top few nanometers of the film.

To solve this, modern 193 nm lithography relies on **Chemically Amplified Resists (CAR)**. These systems use non-aromatic, highly transparent polymers (such as acrylics or cyclic olefins) that let the 193 nm DUV light pass uniformly through the entire thickness of the film.

Because the base polymer and the photoactive compounds are designed to start clear and stay clear during the entire exposure run, there is virtually no dynamic bleaching. This changes the material parameters significantly:

$$A \approx 0.0 \, \mu\text{m}^{-1}$$
$$\alpha \approx B$$

The total absorption is almost entirely driven by the fixed, unbleachable baseline absorption factor, Dill B, which represents the steady, unchanging background opacity of the resin, additives, and acid generators. The spatial light decay simplifies to a constant exponential drop-off:

$$I(z) = I_{surface} \cdot e^{-B \cdot z}$$

---

## 3. Volumetric Process Chain: Atomic & Photon Kinetics

The journey from a flat chemical mask pattern to a solid 3D nanostructure on a silicon wafer involves five distinct chemical and physical states.

`[Spin Coat & Softbake] ──> [DUV Photon Exposure] ──> [Post-Exposure Bake (PEB)] ──> [Development] ──> [Hardbake / Etch]`

### Phase 1: Spin Coating and Softbake (Solvent Evaporation)
The photoresist starts as a liquid polymer dissolved in an organic solvent. It is dropped onto a spinning wafer to form a smooth, uniform thin film (typically 300 nm to 400 nm thick).

The wafer then undergoes a Softbake (Pre-exposure Bake) at $100^\circ\text{C}$ to $110^\circ\text{C}$ for 90 seconds. This step accomplishes two main goals:
1.  It evaporates 90% to 95% of the liquid solvent, stabilizing the film into a solid glass-like state.
2.  It relieves internal mechanical stress in the polymer matrix, preventing the film from peeling or wrinkling.

### Phase 2: DUV Photon Exposure (The Photochemical Acid Generation)
When the 193 nm photons pass through the lens system and enter the Chemically Amplified Resist, they do not interact with a DNQ molecule. Instead, they strike specialized molecules called Photoacid Generators (PAGs).

```text
                  193 nm Photon (hν)
                         │
                         ▼
             [Photoacid Generator (PAG)]
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      Photoacid (H+)          Byproducts
```

### Phase 3: Post-Exposure Bake
Thermal energy drives the Fickian diffusion of the photoacid. A single $H^+$ ion acts as a catalyst, tearing off hydrophobic protecting groups across hundreds of polymer chains (Chemical Amplification) before being neutralized by base quenchers.

### Phase 4: Development $\rightarrow$ Mack Dissolution Engine
An alkaline developer fluid (TMAH) selectively dissolves the deprotected, hydrophilic regions of the resist while leaving the protected, hydrophobic walls completely intact.
