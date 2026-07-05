# External Benchmark Validation: LithoBench-PDE

## Purpose

The lithography surrogate pipeline (optical U-Net → chemical PEB U-Net → Mack development model) was trained entirely on a synthetic, self-generated dataset. This document records an attempt to validate that pipeline against an independent, external benchmark — [AISDL-SNU/LithoBench-PDE](https://huggingface.co/datasets/AISDL-SNU/LithoBench-PDE) — to check whether performance holds up on data the model never saw during training.

This is reported as a **first-pass sanity check**, not a certified accuracy benchmark. The caveats below are as important as the numbers.

---

## Dataset

- Source: `AISDL-SNU/LithoBench-PDE`, category `Contact_I` (163 total `.pt` files available; sampled 40 with fixed seed 42 for a reproducible subset).
- Each sample contains:
  - `M`: binary mask, `[512, 512]`
  - `E`: complex electromagnetic field, `[2, 2, 512, 512]`
  - `m`: polymer/PAC-related volume
  - `h`, `R`, `T`: additional tensors, each `[25, 512, 512]`, purpose not yet confirmed (see Open Questions)

**Important structural finding:** `E` has two leading dimensions of size 2 on complex data. This is consistent with a **polarization-resolved / vector diffraction simulation**, not the scalar Hopkins-Abbe partial-coherence model used to generate the training data. This is a real physics-model gap, not a bug — see Interpretation below.

The dataset does **not** expose the dose, defocus, or NA values used to generate its ground truth. Where these were required as model inputs, fixed nominal values were substituted (see Methodology).

---

## Methodology

### Stage 1 — Optical (aerial image)
- Model: `NativeSentisUNet`, trained on a synthetic Hopkins-Abbe scalar imaging dataset (4 input channels: mask, dose, defocus, NA; DX = 3.9 nm/pixel).
- Since LithoBench-PDE provides no ground-truth dose/defocus/NA, fixed **pre-normalized** channel values were substituted: `dose=0.7, defocus=0.5, NA=1.0` (in the same normalized convention as training: `dose/38.0`, `defocus/45.0`, `na/1.35`).
- Ground truth: `sum(|E|^2, dim=(0,1))`, per-sample max-normalized to `[0,1]`.
- **Dose substitution is low-risk**: earlier diagnostic work on this same model confirmed the dose channel has no measurable effect on Stage 1 output — consistent with correct physics, since dose has no real role in aerial image formation. NA/defocus substitution is unverified against ground truth and is a genuine open assumption.

### Stage 2 — Chemical (PEB)
- Model: `StandardChemicalUNet`, input = predicted Stage 1 intensity + dose channel.
- Ground truth: `mean(m, dim=0)`.

### Stage 3 — Development (Mack model)
- Applied identical Mack dissolution formula to both predicted and true polymer maps (`R_MAX=120, R_MIN=0.05, N_CONTRAST=5.0, M_TH=0.55`, wash time 15s, initial thickness 175nm), so any divergence at Stage 3 originates from Stage 2's prediction error, not from a different development formula.
- Metrics: RMSE on continuous thickness, IoU on a binarized 10nm threshold slice.

### Metrics reported per stage
- Raw MSE **and** scale-matched MSE (`pred` renormalized by its own max before comparison) — separates genuine spatial-pattern error from normalization-convention mismatch between the training target's fixed-scale convention and the benchmark's per-sample max-normalized ground truth.
- SSIM (structural similarity).
- Pearson correlation.

---

## Results (N = 40, Contact_I)

| Stage | Metric | Value |
|---|---|---|
| 1 — Optical | MSE | 0.00522 ± 0.00130 |
| 1 — Optical | MSE (scale-matched) | 0.00522 ± 0.00130 |
| 1 — Optical | SSIM | 0.545 ± 0.018 |
| 1 — Optical | Correlation | 0.912 |
| 2 — Chemical | MSE | 0.03971 ± 0.00718 |
| 2 — Chemical | MAE | 0.12365 ± 0.01525 |
| 2 — Chemical | SSIM | 0.771 |
| 3 — Development | RMSE | 79.90 ± 6.25 nm |
| 3 — Development | Z-slice IoU (10nm threshold) | 77.47% ± 4.24% |

Result stability was checked: metrics computed on N=2 vs. N=40 were close (SSIM 0.545 in both, correlation 0.910→0.912, IoU improved to 77.5%), indicating the N=40 numbers are not dominated by sampling noise from a small subset.

---

## Interpretation

**Stage 1** shows strong positional correlation (0.912) despite moderate SSIM (0.545). Qualitative inspection (side-by-side visualization) shows predicted intensity blobs align with true blob positions, but the true field shows additional smeared/streak-like structure between features that the prediction does not reproduce. This is consistent with, and likely explained by, the scalar-vs-vector physics-model gap identified above — not necessarily a defocus/dose calibration error in the model itself.

**Stage 2** shows reasonable structural agreement (SSIM 0.771); predicted polymer maps are visually crisper/higher-contrast than the true maps' softer blob edges.

**Stage 3** shows a metric split worth flagging explicitly: IoU (77.5%) suggests the binary printed/not-printed contour is reasonably recovered, but RMSE (79.9nm) is large relative to the 175nm initial thickness range (~46% of full scale). The pixel-value histogram over all 40 samples (`thickness_distribution_check.png`) resolves why:

- Both predicted and true thickness distributions are **strongly bimodal** (most pixels sit near 0nm or near 175nm, not spread across intermediate values). This is expected behavior for a development step, not a model artifact — an initial hypothesis that the *true* distribution was smoothly textured while only the *prediction* was artificially bimodal was checked against this data and does not hold; both are bimodal.
- The two distributions are bimodal to different degrees and shifted relative to each other: **97.6%** of predicted pixels sit at the extremes vs. **91.3%** of true pixels.
- **Confirmed quantitatively**: mean bias (pred − true) = **+39.71 nm**, roughly 23% of the full 175nm thickness range. Fraction fully dissolved: predicted 7.5% vs. true 27.9% (predicted under-counts by nearly 4x). Fraction fully intact: predicted 90.1% vs. true 63.4%.
- True shows a small but visible mid-range shoulder (~140–170nm, partial dissolution) that is nearly absent in the prediction.

**Interpretation:** this is a confirmed, quantified **systematic bias toward under-dissolution** (+39.71nm, ~23% of the thickness range) — the model consistently predicts more resist remains than actually does — rather than a fundamental model-class limitation (e.g. stochastic roughness effects a deterministic Mack model can't capture). That stochastic-effects framing was an initial hypothesis based on a single qualitative image before the full histogram was available; the quantitative data does not support it and it has been removed.

**Root cause — confirmed.** Polymer-level bias (pred − true) = **+0.1093** (normalized units), measured directly across all 40 samples. This is *not* the "small upstream offset amplified by the Mack threshold" scenario originally hypothesized — the polymer-distribution histograms (`polymer_distribution_check.png`) show the actual mechanism:

- **Predicted polymer output is heavily saturated**, with the overwhelming majority of pixels concentrated in a single bin near 0.95–1.0, and almost no density in the 0.2–0.9 range.
- **True polymer values are genuinely continuous**, spread broadly across the full 0.2–1.0 range with meaningful density throughout, not concentrated at the extremes.

This means `StandardChemicalUNet`'s output is close to a binary map where the true chemical process produces a graded field. The Mack formula's nonlinearity near `M_TH=0.55` is faithfully propagating this pre-existing saturation into Stage 3's near-binary thickness distribution — it is not creating the problem, it is transmitting it. The fix belongs in Stage 2, not Stage 3: check the PEB model's final activation function for premature saturation (e.g. a sigmoid pushed into its flat regions), check whether its training target itself was already near-binary (a training-data problem) or genuinely continuous (an architecture/training problem), and check the training loss — MSE alone can allow a model to collapse toward extremes if the training targets are imbalanced toward high values, without a term that penalizes loss of intermediate-value variance.

---

## Honest Limitations

- **N=40 from a single geometry category** (`Contact_I`, `INV_X16`/`INV_X32` cell variants). Not yet tested against `Metal_I`, `Metal_T`, `Contact_T`, or other categories in the same dataset.
- **NA and defocus were assumed, not verified.** LithoBench-PDE does not expose the true simulation conditions; Stage 1 discrepancy cannot be cleanly attributed between "model error" and "wrong assumed process condition."
- **Likely physics-model mismatch at Stage 1**: training data uses a scalar Hopkins-Abbe approximation; `E` field shape suggests a vector/polarization-resolved ground truth. Some Stage 1 error is expected from this alone.
- **Pixel pitch (DX_NM=3.9nm) was assumed, not confirmed** against the benchmark's actual physical mask scale.
- **Stage 3's under-dissolution bias is traced to Stage 2 output saturation**, confirmed via the polymer-level bias measurement (+0.1093) and distribution comparison. The Mack development formula is not the source of the error; it is transmitting a saturation problem already present in the chemical-diffusion model's output. Root cause within Stage 2 itself (activation function, training target distribution, or loss function) has not yet been isolated.
- **The `h`, `R`, `T` tensors in the dataset are unexplained.** Their shape `[25, 512, 512]` and naming overlap with this project's own Mack variables (rate, thickness) raise the possibility that real per-condition process sweep ground truth exists in this dataset and was not used. This should be investigated before treating the "no ground truth available" framing as final.

