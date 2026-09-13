# D2 UberApp

<div align="center">

![D2 UberApp Banner](static/images/header.jpg)

**The Ultimate AI-Powered Vault, Companion HUD & Trading Hub for Diablo II: Resurrected**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Diablo II: Resurrected](https://img.shields.io/badge/Diablo%20II-Resurrected-darkred.svg)](https://diablo2.blizzard.com/)
[![Google Gemini AI](https://img.shields.io/badge/AI-Google%20Gemini%202.5%20Flash%20Lite-orange.svg)](https://aistudio.google.com/)
[![Windows 10/11](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Bilingual](https://img.shields.io/badge/Language-English%20%7C%20Polski-yellow.svg)](#bilingual-support--dwuj%C4%99zyczno%C5%9B%C4%87)

[Features](#key-features) • [Screenshots](#visual-tour) • [Quick Start](#quick-start) • [Controls & Hotkeys](#controls--hotkeys) • [Architecture](#architecture) • [Trade & Marketplace](#traders-exchange)

</div>

---

## Overview

**D2 UberApp** is a next-generation desktop companion and web application built specifically for **Diablo II: Resurrected** players and collectors. 

By combining native Windows low-level screen capture hooks with **Google Gemini 2.5 Flash Lite** multimodal vision, D2 UberApp allows you to catalog in-game items, charms, runes, and character stat sheets with a single keystroke without ever leaving Sanctuary or alt-tabbing away.

### Highlights
- ⚡ **Zero Alt-Tab Capture**: Press `F10` in-game over any item tooltip. High-resolution crop, OCR, canonical base identification, and stat evaluation occur in ~1.2s.
- 🎯 **Canonical Roll Evaluator**: Automatically detects variable roll ranges (e.g., *Enhanced Defense*, *All Resistances*, *Magic Find*) and computes ratings from `LOW` to `PERFECT (100%)`.
- 🧙 **Multi-Hero Paperdoll & Mercenary Gear**: Visual inventory management for all 7 classes, weapon swap tracking (Slots I & II), and mercenary gear.
- 🔮 **Authentic 11x3 Rune Stash & Runeword Calculator**: Real-time tracking of owned runes (El through Zod) with instant detection of craftable runewords based on your inventory.
- ⚖️ **Trader's Exchange**: One-click generation of forum-ready trade listings, shorthand notation (`Hoto 40`, `Arach 120ED`), and cloud synchronization with the online marketplace.
- 🌐 **Full Bilingual Support**: One-click toggle between English and Polish across the Web App, Companion HUD, item names, and stat rolls.

---

## Visual Tour

### 1. Wanderer's Vault (Main Stash & Filters)
Browse your collection with responsive grid cards or tabular data, filter by quality, base, ethereal status, or sockets, and search by affixes and hero location.

<div align="center">
  <img src="docs/screenshots/01_web_stash.png" alt="Wanderer's Vault Main Stash" width="900" />
</div>

---

### 2. AI Item Inspector & Variable Rolls Evaluation
Examine full in-game tooltip crops alongside canonical catalog matching and statistical percentile ratings.

<div align="center">
  <img src="docs/screenshots/02_web_item_modal.png" alt="Item Detail Modal & Roll Evaluator" width="800" />
</div>

---

### 3. Hero Paperdoll & Equipment Manager
Equip your characters with authentic visual slots, weapon swaps (I/II), charm inventory, and real-time combat vitals parsed from stat screens.

<div align="center">
  <img src="docs/screenshots/03_web_character.png" alt="Hero Paperdoll & Equipment" width="900" />
</div>

---

### 4. 11x3 Rune Stash & Runeword Crafter
Track your rune wealth in the authentic 33-rune grid and immediately see which high-tier runewords you can craft with your current inventory and bases.

<div align="center">
  <img src="docs/screenshots/04_web_runes.png" alt="Rune Stash and Runeword Calculator" width="900" />
</div>

---

### 5. Trader's Exchange (Trade List & Market Sync)
Curate items for sale, set rune/FG prices, generate Discord/d2jsp formatted text, or publish directly to the Online Marketplace.

<div align="center">
  <img src="docs/screenshots/05_web_trade.png" alt="Trader's Exchange" width="900" />
</div>

---

### 6. Desktop Companion HUD & Mini Mode
A lightweight, always-on-top in-game overlay displaying real-time scan feeds, active character indicators, and hotkey mode switchers.

<div align="center">
  <img src="docs/screenshots/06_companion_hud.png" alt="Desktop Companion HUD" width="600" />
  <br/><br/>
  <img src="docs/screenshots/07_companion_mini.png" alt="Mini HUD Compact Overlay" width="380" />
</div>

---

## Key Features

### 🔍 Multimodal AI Vision Engine
- Powered by `gemini-2.5-flash-lite` with optimized prompts for Diablo II: Resurrected typography and colors.
- Recognizes Unique, Set, Runeword, Rare, Magic, Superior, and Crafted items.
- Extracts base item, defense, damage, level requirements, socket count, and all explicit/implicit affixes.
- Automatically handles dual-language font recognition (Polish / English).

### 📊 Canonical Roll Rating Engine
- Matches parsed items against an internal canonical database (`catalog.sqlite`).
- Identifies variable stats and determines exact percentile rolls:
  - **PERFECT** (100% roll)
  - **HIGH** (75% - 99%)
  - **MID** (40% - 74%)
  - **LOW** (0% - 39%)
- Displays clear ranges: e.g. `Enhanced Defense (ED): 99 [90-120] LOW (30%)`.

### 🛡️ Desktop Companion HUD
- Operates in the background using native Win32 API hooks (`ctypes`).
- Two view modes: **Standard HUD** and compact **Mini HUD**.
- Direct mode switching via hotkeys without switching windows:
  - `F7`: Scan Character Stat Screen
  - `F8`: Scan Rune Tab
  - `F9`: General Vault Scan
  - `F11`: Assign to Active Character Equipment
  - `F12`: Assign to Mercenary
- Audio confirmation (SFX) when items are captured and processed.

### 👯 Duplicate Detector & Asset Optimizer
- Scans your vault for duplicate bases or named items.
- Highlights identical drops side-by-side so you can keep the highest roll and trade or vendor the rest.

### 💰 API Cost & Token Monitor
- Complete transparency: tracks exact prompt tokens, candidate tokens, and calculates API costs per scan.
- Free-tier friendly: Gemini Flash Lite runs smoothly within Google AI Studio's free tier quotas.

---

## Quick Start

### Prerequisites
- **Windows 10 / 11** (64-bit)
- **Python 3.10+**
- **Google Gemini API Key** (Free tier available at [Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/d2-uberapp.git
   cd d2-uberapp
   ```

2. **Create a virtual environment & install dependencies:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure your API Key:**
   - Copy `.env.example` to `.env`:
     ```bash
     copy .env.example .env
     ```
   - Open `.env` and set your key:
     ```env
     GEMINI_API_KEY="your_actual_gemini_api_key_here"
     GEMINI_MODEL="gemini-2.5-flash-lite"
     ```
   *(Note: You can also enter or change your API key directly inside the Companion HUD settings GUI.)*

4. **Launch the Application:**
   - **Method A (Recommended):** Double-click `start.bat`. It will free any hung ports and launch both the Companion HUD and the local web server.
   - **Method B (Terminal):**
     ```bash
     python app.py
     ```
   - Open your browser at: `http://127.0.0.1:5005`

---

## Controls & Hotkeys

All hotkeys are global and function directly while Diablo II: Resurrected is the active foreground window:

| Hotkey | Target / Action | Description |
|:---:|:---|:---|
| **F10** | **Capture Target** | Captures the item tooltip under the cursor and queues it for AI processing |
| **F7** | **Character Stats Mode** | Next scan will parse character level, attributes, resistances, and vitals |
| **F8** | **Rune Stash Mode** | Next scan will parse the 11x3 rune grid |
| **F9** | **Vault Stash Mode** | General scan mode; items are placed into the shared vault |
| **F11** | **Active Hero Gear** | Directs scanned item into the selected hero's equipment slots |
| **F12** | **Mercenary Gear** | Directs scanned item into the active hero's mercenary inventory |

*Hotkeys can be customized at any time in the Companion HUD settings tab.*

---

## Architecture

```
D2 UberApp/
├── data/
│   ├── catalog.sqlite          # Canonical D2R database (uniques, sets, runewords, bases)
│   ├── stash.sqlite            # Local player vault & inventory database
│   ├── armor_bases.json        # Base item metadata (armor, helms, shields)
│   ├── item_bases.json         # Base item metadata (weapons, jewelry, charms)
│   ├── trade_catalog_500.json  # Pricing & shorthand dictionary for trade
│   ├── previews/               # Auto-generated tooltip crop previews
│   └── screenshots/            # Raw in-game captures
├── docs/
│   └── screenshots/            # Documentation & README showcase images
├── static/
│   ├── images/                 # Class portraits, runes, item icons, sound effects
│   ├── uberapp.css             # Main application styling (Sanctuary dark theme)
│   ├── uberapp.js              # Vault, paperdoll, runes, and trading interactions
│   ├── companion.css           # Desktop overlay HUD stylesheet
│   └── companion.js            # Live polling & companion controls
├── templates/
│   ├── index.html              # Main single-page web vault interface
│   └── companion.html          # Web-embedded companion HUD view
├── ai_processor.py             # Google GenAI integration & OCR prompts
├── app.py                      # Flask web server & REST API endpoints
├── capture.py                  # Win32 screen capture & crop engine
├── catalog_matcher.py          # Item identification & variable roll evaluation
├── companion_routes.py         # REST endpoints for Companion HUD synchronization
├── desktop_companion.py        # Native desktop overlay window & hotkey manager
├── preferences.py              # Configuration storage (keys, hotkeys, audio)
├── runeword_calc.py            # Runeword crafting & socket availability calculator
├── translations.py             # Bilingual dictionary (PL/EN) & roll formatters
├── uber_features.py            # Trade generator, character stats & reports
├── requirements.txt            # Python package dependencies
├── start.bat                   # One-click Windows launch script
└── README.md
```

---

## Trader's Exchange

D2 UberApp simplifies item trading across forums, Discord servers, and in-game lobbies:

1. **Quick Pricing:** Tag items with standard rune prices (`Pul`, `Um`, `Mal`, `Ist`, `Vex`, `Ohm`, `Ber`, `Jah`) or custom forum gold (FG) values.
2. **Trade Jargon Generator:** Converts complex item stats into standard community trade shorthand:
   - `Heart of the Oak Flail` → `Hoto 40 @ Pul`
   - `Arachnid Mesh` → `Arach 120ED @ Vex`
   - `Call to Arms Crystal Sword` → `CTA 6/6/4 @ Ber`
3. **BBCode & Discord Export:** Generate clean, formatted item lists with one click, ready to paste into trading threads.
4. **Online Market Sync:** Seamlessly publish listings to the integrated community market server.

---

## Bilingual Support / Dwujęzyczność

D2 UberApp has been built from the ground up to support both international and Polish Diablo communities:
- **English**: Uses official D2R English item names, base terminology, and standard Diablo trade abbreviations.
- **Polski**: Wykorzystuje oficjalne nazewnictwo z polskiej wersji językowej Diablo II: Resurrected (*Korbacz, Pajęcza Szarfa, Skarabeusz, Kamień Jordana*).
- Switch anytime with a single click in the top navigation bar (`PL | EN`).

---

## Contributing & Development

Contributions, bug reports, and suggestions are welcome!
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/NewFeature`)
3. Commit your changes (`git commit -m 'Add NewFeature'`)
4. Push to the branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

---

## Disclaimer

D2 UberApp is an open-source companion tool created by fans for fans. Diablo II: Resurrected is a registered trademark of Blizzard Entertainment, Inc. This application is not affiliated with, maintained, authorized, or endorsed by Blizzard Entertainment. D2 UberApp operates exclusively via standard Windows screenshot APIs and external optical character recognition; it does not read, inject into, or modify game memory or files.

---

## License

Distributed under the **MIT License**. See `LICENSE` for more information.
