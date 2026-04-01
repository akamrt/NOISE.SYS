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

| | | |
|:---|:---|:---|
| 🖥️ **Marathon Terminal UI** | Custom dark terminal with live 60fps oscilloscope waveform visualizer | |
| 🛡️ **Non-Destructive** | Works on referenced rigs. Original keyframes untouched — noise routed via `plusMinusAverage` node network | |
| ⚡ **Auto-Live Preview** | See noise in the viewport **in real-time** as you drag any slider — no apply button needed | |
| 🎛️ **Multi-Layer Stacking** | Stack multiple noise layers per axis — SINE, SQUARE, TRIANGLE, SAW, PERLIN, RANDOM | |
| 💾 **Preset System** | Save and load favourite camera shakes / vibrations from local JSON preferences | |
| 🍰 **AnimLayer Baking** | One-click bake to an additive Maya Animation Layer — keeps base timeline clean | |
| 🔄 **Full Revert** | Remove all noise and restore original animation instantly | |
| 🎮 **6 Noise Types** | SINE · SQUARE · TRIANGLE · SAW · PERLIN · RANDOM | |

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
# 1. Select the object or camera you want to affect
# 2. The UI auto-detects your TARGET
# 3. Unmute the channels you want to affect (e.g. Tx, Ty, Rz for camera shake)
# 4. Click +LAY to add a noise layer
# 5. Choose Type + adjust Amp / Freq
# 6. Enable [X] AUTO-LIVE for real-time viewport preview
# 7. Click [BAKE TO LAYER] when happy
```

**Quick example — camera shake on `tx`, `ty`, `rz`:**
```python
import noise_sys_terminal as ns
# UI launches automatically — just select your camera and go
```

---

## 🎛️ UI Overview

| Element | Function |
|:---|:---|
| **OSCILLOSCOPE** | Live waveform showing all active noise layers combined |
| **GLOBAL_MODS** | Master amplitude and frequency multiplier for all layers |
| **Tx / Ty / Tz** | Translate X/Y/Z noise channels — unmute to activate |
| **Rx / Ry / Rz** | Rotate X/Y/Z noise channels — unmute to activate |
| **+LAY** | Add a new noise layer to the active channel |
| **[BAKE TO BASE]** | Commit noise directly into base keyframes |
| **[BAKE TO LAYER]** | Commit noise to an additive Maya Animation Layer |
| **[ REVERT_TARGET_SYSTEM ]** | Remove all noise, restore original animation |

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
