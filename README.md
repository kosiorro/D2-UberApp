# D2 UberApp

<div align="center">

**AI-Powered Vault, Companion HUD & Trading Hub for Diablo II: Resurrected**

<br>

<p align="center">
  <a href="#english"><img src="https://img.shields.io/badge/%F0%9F%87%AC%F0%9F%87%A7%20English-Documentation-2563eb?style=for-the-badge" alt="English"></a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="#wersja-polska"><img src="https://img.shields.io/badge/%F0%9F%87%B5%F0%9F%87%B1%20Polski-Dokumentacja-dc2626?style=for-the-badge" alt="Polski"></a>
</p>

<p align="center">
  <a href="#english">
    <img src="https://flagcdn.com/24x18/gb.png" alt="English Flag" width="24" height="18" style="vertical-align: middle;">
    <b> Read in English</b>
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="#wersja-polska">
    <img src="https://flagcdn.com/24x18/pl.png" alt="Polish Flag" width="24" height="18" style="vertical-align: middle;">
    <b> Czytaj po polsku</b>
  </a>
</p>

[![Live Website](https://img.shields.io/badge/Website-kosiorro.github.io%2FD2--UberApp-gold.svg)](https://kosiorro.github.io/D2-UberApp/)
[![Online Market](https://img.shields.io/badge/Online%20Market-d2uberappmarket.tw5.org-purple.svg)](https://d2uberappmarket.tw5.org)
[![Releases](https://img.shields.io/badge/Download-Releases%20(v1.0.0)-brightgreen.svg)](https://github.com/kosiorro/D2-UberApp/releases)
[![Status: Active Beta](https://img.shields.io/badge/Status-Active%20Beta-orange.svg)](#beta-notice)
[![Account Safety](https://img.shields.io/badge/Account%20Safety-100%25%20Safe%20(Screenshots)-brightgreen.svg)](#account-safety-screenshot-based-architecture)
[![Gemini 3.5 Flash Lite](https://img.shields.io/badge/AI-Google%20Gemini%203.5%20Flash%20Lite-blue.svg)](#gemini-api-key-required--free)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Bilingual](https://img.shields.io/badge/Language-English%20%7C%20Polski-lightgrey.svg)](#wersja-polska)

🌐 **[Live Website & Guide](https://kosiorro.github.io/D2-UberApp/)** • ⚖️ **[Community Online Market](https://d2uberappmarket.tw5.org)** • 📦 **[Download Releases](https://github.com/kosiorro/D2-UberApp/releases)**

[English](#english) • [Wersja Polska](#wersja-polska) • [Screenshots](#visual-tour) • [Safety](#anti-ban-safety-screenshot-based-architecture) • [API Setup](#gemini-api-key-required--free) • [Hotkeys](#controls--hotkeys) • [Roadmap](#roadmap--planned-features) • [Installation](#quick-start)

</div>

---

<a name="english"></a>
## English Documentation

> 🇵🇱 *Wolisz język polski? [Przejdź do wersji polskiej ➔](#wersja-polska)*

### Official Links & Services
- 🌐 **Live Website & Interactive Guide**: [https://kosiorro.github.io/D2-UberApp/](https://kosiorro.github.io/D2-UberApp/)
- ⚖️ **Community Trading Hub (Online Market)**: [https://d2uberappmarket.tw5.org](https://d2uberappmarket.tw5.org)
- 📦 **Releases & Pre-built Binaries**: [https://github.com/kosiorro/D2-UberApp/releases](https://github.com/kosiorro/D2-UberApp/releases)
- 💻 **Source Code Repository**: [https://github.com/kosiorro/D2-UberApp](https://github.com/kosiorro/D2-UberApp)

### Beta Notice
> **Active Beta Status**: D2 UberApp is currently in active beta testing. Core features are fully functional, with continuous optimizations, balance tuning, and community feedback integration in progress.

### Account Safety (Screenshot-Based Architecture)
> **100% Account Safety**: D2 UberApp operates in complete isolation from the game process.
>
> - **Screenshot-Only Operation**: The application captures pixels purely via the standard Windows Desktop API (`BitBlt` / Desktop Duplication) upon pressing your hotkey.
> - **Zero Process Memory Reading**: D2 UberApp never inspects, hooks, or scans the memory space of `D2R.exe`.
> - **Zero Code or DLL Injection**: No external DLLs are injected into the game process, and game files remain untouched.
> - From the perspective of Blizzard's anti-cheat systems (Warden), D2 UberApp operates identically to desktop tools such as **OBS Studio**, **Snipping Tool**, or **Discord Screen Share**.

### Gemini API Key (Required & Free)
> **A Google Gemini API key is required for optical character recognition and item evaluation.**
>
> - **100% Free of Charge**: You can obtain an API key for **Google Gemini 3.5 Flash Lite** at [Google AI Studio](https://aistudio.google.com/) with no credit card required.
> - The free tier quota generously supports thousands of scans per month.
> - Set your key in `.env` (`GEMINI_API_KEY="..."`) or directly within the Companion HUD settings window.

---

### Key Features

1. **Zero Alt-Tab In-Game Capture (F10)**:
   - High-speed Win32 hotkey capture of item tooltips directly in Sanctuary.
   - Smart cropping, dual-language OCR, and catalog validation complete in ~1.2s with audio confirmation.

2. **Canonical Variable Roll Rating**:
   - Matches items against an embedded canonical database (`catalog.sqlite`).
   - Computes statistical percentile ratings for variable affixes (e.g. *Enhanced Defense*, *All Resistances*, *Magic Find*): `PERFECT (100%)`, `HIGH`, `MID`, `LOW`.

3. **Hero Equipment & Gear Manager**:
   - Visual equipment view for all 7 character classes.
   - Weapon swap support (Slots I and II), mercenary equipment management, and charms inventory.

4. **11x3 Rune Stash & Runeword Calculator**:
   - Authentic 33-rune grid (El to Zod) with live inventory counts.
   - Real-time crafting calculator identifying assembleable runewords based on owned runes and socketed bases.

5. **Trader's Exchange**:
   - Valuation in high runes and forum currency.
   - Automated shorthand jargon generation (e.g., *Hoto 40*, *Arach 120ED*, *CTA 6/6/4*).
   - Instant export formatted for forums and Discord.

6. **Desktop Companion HUD & Mini Mode**:
   - Lightweight always-on-top overlay with live scan feeds, active hero indicator, and hotkey mode switchers.

---

### Visual Tour

| View | Screenshot | Description |
|:---|:---:|:---|
| **Wanderer's Vault** | [Preview PNG](docs/screenshots/01_web_stash.png) | Main stash grid with responsive quality filters, full-text affix search, and hero filters. |
| **Item Detail Modal** | [Preview PNG](docs/screenshots/02_web_item_modal.png) | In-game tooltip crop, base item properties, and variable roll evaluation. |
| **Hero Equipment** | [Preview PNG](docs/screenshots/03_web_character.png) | Complete character equipment slots, weapon swaps (I/II), mercenary gear, and vitals. |
| **11x3 Rune Stash** | [Preview PNG](docs/screenshots/04_web_runes.png) | Authentic 33-rune stash layout with integrated runeword crafting calculator. |
| **Trader's Exchange** | [Preview PNG](docs/screenshots/05_web_trade.png) | Trade management table with quick pricing, shorthand jargon generator, and export tools. |
| **Companion HUD** | [Preview PNG](docs/screenshots/06_companion_hud.png) | Desktop in-game overlay with live capture status, active mode badges, and scan feed. |

---

### Roadmap & Planned Features

- **Remaining Items Support**: Full parsing and tracking for Uber Tristram keys (Key of Terror, Hate, Destruction), boss organs, essences, and Token of Absolution.
- **Skill Points & Synergy Calculator**: Interactive skill tree calculator, total +skills bonuses aggregation, and damage synergy calculations across equipped gear.
- **Alternative & Local AI Models**: Support for local open-source vision models via Ollama / LM Studio for 100% offline scanning, alongside alternative cloud AI providers.
- **Additional Languages**: Expansion of interface and OCR dictionary to German, French, Spanish, and Asian Diablo communities.
- **Bug Fixes & Continuous Polish**: Ongoing performance optimizations, edge-case crop improvements, and UI responsiveness enhancements.

---

### Controls & Hotkeys

All hotkeys are global and functional while Diablo II: Resurrected is the active foreground window:

| Hotkey | Mode / Action | Target & Outcome |
|:---:|:---|:---|
| **F10** | **Capture Target** | Captures the item tooltip under the cursor and queues it for AI evaluation. |
| **F7** | **Character Stats Mode** | Scans the character attribute screen to update level, attributes, and resistances. |
| **F8** | **Rune Stash Mode** | Scans the stash rune tab to update counts for all 33 runes. |
| **F9** | **Vault Stash Mode** | Sets the destination of subsequent F10 scans to the shared vault. |
| **F11** | **Active Hero Gear Mode** | Directs subsequent F10 scans into the active hero's equipment slots. |
| **F12** | **Mercenary Gear Mode** | Directs subsequent F10 scans into the mercenary equipment tab. |

---

### Quick Start

1. **Clone repository**:
   ```bash
   git clone https://github.com/kosiorro/D2-UberApp.git
   cd D2-UberApp
   ```

2. **Install Python dependencies**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure free Gemini API key**:
   - Copy `.env.example` to `.env`:
     ```bash
     copy .env.example .env
     ```
   - Insert your API key in `.env`:
     ```env
     GEMINI_API_KEY="your_actual_key_here"
     GEMINI_MODEL="gemini-3.5-flash-lite"
     ```

4. **Launch Application**:
   - Double-click `start.bat` or run:
     ```bash
     python app.py
     ```
   - Access the Web Vault at `http://127.0.0.1:5005` or Landing Page at `http://127.0.0.1:5005/landing`.

---

<a name="wersja-polska"></a>
## Wersja Polska (Dokumentacja PL)

> 🇬🇧 *Prefer English? [Switch to English documentation ➔](#english)*

### Oficjalne Linki i Serwisy
- 🌐 **Oficjalna Strona WWW i Przewodnik Online**: [https://kosiorro.github.io/D2-UberApp/](https://kosiorro.github.io/D2-UberApp/)
- ⚖️ **Internetowa Giełda Przedmiotów (Market)**: [https://d2uberappmarket.tw5.org](https://d2uberappmarket.tw5.org)
- 📦 **Pobieranie i Najnowsze Wydania (Releases)**: [https://github.com/kosiorro/D2-UberApp/releases](https://github.com/kosiorro/D2-UberApp/releases)
- 💻 **Repozytorium Kodu Źródłowego**: [https://github.com/kosiorro/D2-UberApp](https://github.com/kosiorro/D2-UberApp)

### Informacja o wersji Beta
> **Aktywna Faza Beta**: D2 UberApp znajduje się w fazie intensywnych testów beta. Główne moduły są w pełni sprawne, a kolejne usprawnienia i funkcje dochodzą na bieżąco.

### Bezpieczeństwo Konta (Architektura Screenshot-Only)
> **100% Bezpieczeństwa Konta — Pełna Izolacja Procesu**:
>
> - **Działanie wyłącznie na screenach**: Program wykonuje zrzut wybranego fragmentu pulpitu przez standardowe Windows API (`BitBlt`), identycznie jak **OBS Studio**, **Narzędzie Wycinanie** czy podgląd ekranu na **Discordzie**.
> - **Zero czytania pamięci gry**: Aplikacja nie skanuje i nie podpina się pod pamięć procesu `D2R.exe`.
> - **Zero wstrzykiwania kodu (DLL Injection)**: Żadne biblioteki ani haki nie są wprowadzane do procesu gry, a pliki D2R pozostają nienaruszone.
> - Dla systemu anty-cheat firmy Blizzard (Warden) aplikacja jest całkowicie pasywna i niewykrywalna.

### Darmowy Klucz Gemini API (Wymagany)
> **Do działania rozpoznawania przedmiotów AI wymagany jest klucz Google Gemini API.**
>
> - **W 100% darmowy**: Klucz do modelu **Google Gemini 3.5 Flash Lite** wygenerujesz bezpłatnie w [Google AI Studio](https://aistudio.google.com/) bez konieczności podawania karty kredytowej.
> - Darmowy pakiet obejmuje wysokie limity zapytań, które z dużym zapasem wystarczają na tysiące skanów w miesiącu.
> - Klucz wystarczy wpisać w pliku `.env` lub bezpośrednio w ustawieniach okna Companion HUD.

---

### Główne Możliwości

1. **Skanowanie w grze bez minimalizowania okna (F10)**:
   - Szybki skrót Win32 API przechwytujący tooltip bezpośrednio podczas rozgrywki.
   - Autokadrowanie, wielojęzyczny OCR oraz weryfikacja w katalogu w ~1.2s z dźwiękiem potwierdzenia.

2. **Weryfikacja i Ocena Widełek (Rolls)**:
   - Porównanie parametrów z kanoniczną bazą `catalog.sqlite`.
   - Procentowa ocena zmiennych cech unikatów, zestawów i runewords: `PERFECT (100%)`, `HIGH`, `MID`, `LOW`.

3. **Ekwipunek Bohatera i Wyposażenie**:
   - Kompletny widok slotów ekwipunku dla wszystkich 7 klas postaci.
   - Obsługa zamiany broni (Slot I oraz II), wyposażenie najemnika oraz inwentarz talizmanów.

4. **Siatka 33 Run (11x3) i Kalkulator Słów Runicznych**:
   - Autentyczny układ od runy El do Zod z licznikami posiadanych sztuk.
   - Kalkulator wskazujący słowa runiczne możliwe do złożenia z posiadanych run i baz.

5. **Trader's Exchange (Giełda Wymian)**:
   - Szybkie przypisywanie cen w runach i walucie forumowej.
   - Generator oficjalnego żargonu handlowego (np. *Hoto 40*, *Arach 120ED*).
   - Eksport gotowych formatowanych list na Discord i fora.

6. **Desktop Companion HUD i Tryb Mini**:
   - Lekkie okno nakładkowe Always-on-Top z podglądem skanów, aktywną postacią i skrótami trybów F7–F12.

---

### Plany Rozwoju (Do Zrobienia)

- **Reszta Przedmiotów (Ubery)**: Obsługa kluczy na Uber Tristram (Key of Terror, Hate, Destruction), organów bossów, esencji oraz Token of Absolution.
- **Przeliczanie Skilli**: Kalkulator drzewek umiejętności, agregacja bonusów `+All Skills` z ekwipunku oraz przeliczanie synergii bojowych.
- **Inne Modele AI i Działanie Lokalnie**: Możliwość uruchomienia lokalnych modeli wizyjnych (np. Ollama / LM Studio) do skanowania 100% offline.
- **Więcej Języków**: Dodanie kolejnych wersji językowych dla społeczności międzynarodowej (niemiecki, francuski, hiszpański, koreański).
- **Poprawki Błędów (Bagi) i Optymalizacje**: Ciągłe ulepszanie kadrowania nietypowych rozdzielczości oraz podnoszenie płynności działania.

---

### Tabela Skrótów Klawiszowych

| Skrót | Tryb / Akcja | Opis Działania |
|:---:|:---|:---|
| **F10** | **Przechwyć cel (Capture)** | Skanuje tooltip pod kursorem i przetwarza go przez Gemini AI. |
| **F7** | **Skan statystyk postaci** | Skanuje otwarte okno atrybutów bohatera i aktualizuje statystyki. |
| **F8** | **Skan zakładki run** | Skanuje skrytkę z runami i aktualizuje liczniki wszystkich 33 run. |
| **F9** | **Tryb skrytki ogólnej** | Przełącza cel zapisu kolejnych skanów F10 na wspólny skarbiec. |
| **F11** | **Tryb aktywnego bohatera** | Przełącza cel zapisu kolejnych skanów F10 na ekwipunek postaci. |
| **F12** | **Tryb najemnika** | Przełącza cel zapisu kolejnych skanów F10 na ekwipunek pomocnika. |

---

### Licencja i Zastrzeżenia

Diablo II: Resurrected jest zarejestrowanym znakiem towarowym Blizzard Entertainment, Inc. Aplikacja D2 UberApp jest projektem fanowskim open-source, niepowiązanym z Blizzard Entertainment. Program działa wyłącznie na zrzutach ekranu Windows API i nie modyfikuje plików gry. Dystrybucja na licencji MIT.
