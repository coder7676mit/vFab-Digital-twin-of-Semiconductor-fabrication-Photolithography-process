# Unity Setup — SC1 Wet Bench (minimal, fast to build)

## What you are building

One slider → physics runs → wafer dips → particles fade → outputs update → PASS shown.
Machine 2 (HMDS) is a static text card that appears after SC1 completes. No animation needed for Machine 2.

---

## Step 1 — Hierarchy (5 minutes)

```
Scene
├── SC1Controller          ← empty GameObject, attach SC1Controller.cs here
├── Canvas (Screen Space Overlay)
│   ├── DipSlider          ← UI > Slider
│   ├── OutputText         ← UI > TextMeshPro
│   └── StartButton        ← UI > Button
└── SC1_3D
    ├── Bath               ← cube, scale 3×1.5×2, position (0,0,0)
    ├── Liquid             ← plane inside bath, semi-transparent teal material
    ├── Wafer              ← cylinder, scale (1.2, 0.05, 1.2), sits above bath
    └── DirtyParticles     ← Particle System on/near wafer surface
```

---

## Step 2 — Assign in Inspector (2 minutes)

Select SC1Controller. Drag these into the matching slot:

| Slot | Object |
|---|---|
| Dip Slider | DipSlider |
| Output Text | OutputText |
| Start Button | StartButton |
| Wafer | Wafer |
| Dirty Particles | DirtyParticles |

That is all. No other wiring needed.

---

## Step 3 — UI settings

**DipSlider**
- Min: 30 · Max: 900 · Whole Numbers: ON · Default: 600

**OutputText**
- Font size: 18 · Alignment: Left · Width: ~420px
- Enable Rich Text: ON (needed for the green/amber colour tags)
- Place it to the right of the slider

**StartButton**
- Label: "Start SC1 Clean"
- Width: 200px

---

## Step 4 — 3D setup

**Bath (cube)**
- Scale: (3, 1.5, 2)
- Material: grey plastic, opaque

**Liquid (plane)**
- Position: just below the top rim of the bath
- Material: teal, URP/Lit, Surface Type: Transparent, Alpha: 0.55

**Wafer (cylinder)**
- Scale: (1.2, 0.05, 1.2)
- Position: about 1.5 units above the bath top
- Material: silicon grey (#909090), slightly metallic

**DirtyParticles (Particle System)**
- Duration: 999 · Loop: ON · Play On Awake: ON
- Start Lifetime: 999 · Start Speed: 0.02 (tiny drift)
- Start Size: 0.08 · Start Color: dark brown (#3E2000)
- Max Particles: 40
- Shape: Surface, assign Wafer mesh
- The script fades the alpha — you do not need to animate anything

---

## Step 5 — What the user sees

When they press Start:

1. Wafer smoothly lowers into the bath (1.5s animation)
2. OutputText updates every frame — etch depth and removal % climb in real time
3. Particles (contamination) fade out as removal % increases
4. When dip time is reached — wafer lifts back out
5. OutputText shows green CLEAN ✓ message

After 0 extra work — user moves the slider before pressing Start to preview what removal % they will get at any dip time.

---

## Step 6 — Machine 2 static card (5 minutes)

Add one more UI panel to Canvas:

```
Canvas
└── Machine2Card     ← Panel, starts INACTIVE (untick in Inspector)
    └── Machine2Text ← TextMeshPro
```

Text to put in Machine2Text:
```
Machine 2 — Prime Oven

Phase 1:  Dehydration bake     ✓
Phase 2:  HMDS vapor prime     ✓

θ after prime  =  77°
Adhesion gate (>65°)  =  SATISFIED ✓

→ Spin coat machine UNLOCKED
```

To make it appear after SC1 completes, add these 4 lines to SC1Controller.cs
inside the CleanDone() function:

```csharp
// add this field at the top of the class:
public GameObject machine2Card;

// add this inside CleanDone():
if (machine2Card != null)
    StartCoroutine(ShowCard());

IEnumerator ShowCard()
{
    yield return new WaitForSeconds(2f);
    machine2Card.SetActive(true);
}
```

Then drag Machine2Card into the new Inspector slot.

---

## Final checklist before showing

- [ ] Press Play — slider at 600s — press Start — removal hits 100%, CLEAN badge appears
- [ ] Press Play — slider at 60s — removal shows ~10%, amber message appears
- [ ] Particles visibly fade out during the run
- [ ] Wafer dips down and lifts back up
- [ ] Machine 2 card appears 2s after clean completes
- [ ] Resetting: just move the slider — the preview updates instantly

---

## Do not add

- Extra sliders for temperature or concentration (not user inputs for SC1)
- Multiple removal bars or uncertainty bands
- Separate PASS/WARN panel GameObjects (the output text handles this with colour)
- Any ONNX or ML model (not needed — math is 2 lines in the script)
