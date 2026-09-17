# 🗣️ NOISE.SYS

<div align="center">

![NOISE.SYS — Jitter Matrix for Maya](https://raw.githubusercontent.com/akamrt/NOISE.SYS/main/assets/banner.png)

**A non-destructive, multi-layered procedural noise generator for Autodesk Maya**

*[Stop keyframing camera shake by hand.]*

<a href="https://github.com/akamrt/NOISE.SYS/raw/main/assets/demo.gif">
  <img src="https://github.com/akamrt/NOISE.SYS/raw/main/assets/demo.gif" width="700" alt="NOISE.SYS — Auto-Live preview" style="max-width:100%; border-radius:8px; border:1px solid #1a1a2e;" />
</a>
*[↑ Auto-Live preview — real-time viewport feedback as you drag sliders]*

<a href="https://github.com/akamrt/NOISE.SYS/raw/main/assets/demo-edits.gif">
  <img src="https://github.com/akamrt/NOISE.SYS/raw/main/assets/demo-edits.gif" width="700" alt="NOISE.SYS — Full walkthrough" style="max-width:100%; border-radius:8px; border:1px solid #1a1a2e;" />
</a>
*[↑ Full walkthrough — oscilloscope, baking & more]*

<a href="https://github.com/akamrt/NOISE.SYS/raw/main/assets/oscilloscope.gif">
  <img src="https://github.com/akamrt/NOISE.SYS/raw/main/assets/oscilloscope.gif" width="700" alt="NOISE.SYS — Live oscilloscope" style="max-width:100%; border-radius:8px; border:1px solid #1a1a2e;" />
</a>
*[↑ Live oscilloscope — real-time waveform visualisation]*

</div>

---

## ✨ Features

| | |
|:---|:---|
| 🖥️ **Marathon Terminal UI** | Custom dark terminal with a live oscilloscope and a 3D pyramid preview |
| 🛡️ **Non-Destructive** | Works on referenced rigs. Original keyframes untouched — noise routed through a `plusMinusAverage` node network |
| ⚡ **Fast Auto-Live Preview** | Noise lives on native animation curves (no expressions), so viewport playback stays fast and cached-playback friendly |
| 🎯 **Multiple Targets, Own Seeds** | Drive any number of objects from one setup — each gets its own seed so nothing moves in lockstep |
| 🎛️ **Multi-Layer Stacking** | Stack multiple noise layers per axis — SINE, SQUARE, TRIANGLE, SAW, PERLIN, RANDOM |
| 🎲 **Repeatable Seeds** | Same seed, same motion, every session. Reroll one target or all of them |
| 🔢 **Type-In Values & Raisable Caps** | Type exact values, or Shift-drag past a slider's end to raise its maximum |
| 🍰 **Bake Exactly What You See** | One click bakes the live result to base keys or an additive Animation Layer, reports the difference from the live view, and removes every helper node |
| 🔺 **3D Preview** | Pyramid with selectable tip axis and pivot, a styled motion trail, orbit / pan / zoom |
| 💾 **Preset System** | Save and load favourite camera shakes / vibrations from local JSON preferences |
| 🔄 **Full Revert** | Remove all noise and restore original animation instantly |

---

## 📦 Compatibility

| Maya Version | Status |
|:------------|:------:|
| Maya 2022 | ✅ |
| Maya 2023 | ✅ |
| Maya 2024 | ✅ |
| Maya 2025 | ✅ |

---

## 🚀 Installation

**No complex setup required.**

1. Download `noise_sys_terminal.py`
2. Open Maya → **Script Editor** (`Windows → General Editors → Script Editor`)
3. Switch to the **Python** tab
4. Open the script, select all, **Middle-Mouse-Drag** to your Maya Shelf
5. Click your new shelf button to launch!

---

## 🎮 Usage

```python
# 1. Select one or more objects (controls, cameras...) and press <<< SET
#    Each target gets its own seed so they move independently
# 2. Unmute the channels you want to affect (e.g. Tx, Ty, Rz for camera shake)
# 3. Add noise layers, choose a type, adjust Amp / Freq / Offset (drag or type values)
# 4. Leave [X] AUTO-LIVE on for real-time viewport preview
# 5. Click [ BAKE_TO_LAYER ] or [ BAKE_TO_BASE ] when happy — it bakes all targets and cleans up
```

---

## 🎛️ UI Overview

| Element | Function |
|:---|:---|
| **TARGETS** | `<<< SET` replaces the list with the selection, `+ ADD` appends, `REROLL ALL` gives every target a new seed. Each row: click the name to select it, edit its seed, `RND` to reroll, `X` to remove |
| **Preview controls** | `BOTH / WAVE / 3D` view, `T- T+` time zoom, `A- A+` height zoom, `1:1` reset, `NORM` fit to view, `PAUSE`, `3D OPT` |
| **OSCILLOSCOPE** | Waveform of all active layers. Wheel: zoom time · Shift+wheel: zoom height · double-click: reset |
| **3D PYRAMID** | Noise applied to a pyramid at the playhead. Left-drag orbit · middle or Shift+left-drag pan · wheel or right-drag zoom · double-click or F reset |
| **3D OPT** | Tip axis (±X/±Y/±Z), pivot (base/center/tip), trail on/off, colour, length in frames, fade, thickness, taper, line style |
| **GLOBAL_MODS** | Master amplitude and frequency multiplier for all layers |
| **Tx / Ty / Tz · Rx / Ry / Rz** | Translate and rotate noise channels — unmute to activate |
| **Sliders** | Drag, or type in the value box. Shift-drag past the end raises the cap; double-click resets it |
| **[ BAKE_TO_BASE ]** | Bake the live result into base keyframes on every target |
| **[ BAKE_TO_LAYER ]** | Bake noise into an additive Animation Layer per target (re-baking replaces it) |
| **REVERT_TARGET_SYSTEM** | Remove all noise from every target, restore original animation |

---

## 📂 File Structure

```
NOISE.SYS/
├── noise_sys_terminal.py       # Main script
├── README.md                   # This file
├── LICENSE                     # MIT License
└── assets/
    ├── demo.gif                # Full walkthrough demo
    ├── demo-edits.gif          # Edit workflow demo
    ├── oscilloscope.gif         # Live oscilloscope animation
    ├── oscilloscope-demo.png   # Oscilloscope UI screenshot
    ├── nondestructive-baking.png
    ├── hero-thumb.png
    ├── banner.png              # X/Twitter banner
    └── gumroad-cover-v4.png
```

---

## 🤝 Contributing

Issues and pull requests welcome.

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

*NOISE.SYS is not affiliated with Autodesk or Bungie. Marathon is a trademark of Bungie.*
