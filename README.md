# D2 UberApp

> Nowoczesny asystent, menedżer skrytki i ekwipunku dla **Diablo II: Resurrected** zasilany przez **Google Gemini AI**.

D2 UberApp to zaawansowana aplikacja desktopowa i webowa, która umożliwia natychmiastowe katalogowanie przedmiotów ze zrzutów ekranu w grze, automatyczną weryfikację widełek statystyk (rolls), zarządzanie ekwipunkiem wielu postaci, kalkulator słów runicznych oraz eksport ofert handlowych.

---

## Główne możliwości

- **Błyskawiczne przechwytywanie w grze (F10)**:
  - Globalny skrót Win32 API przechwytujący aktywny ekran gry bez minimalizowania okna.
  - Automatyczne wycinanie tooltipa i natychmiastowy dźwięk potwierdzenia (SFX).
- **Precyzyjne rozpoznawanie Gemini AI (gemini-3.5-flash-lite)**:
  - Bezbłędne czytanie polskiej i angielskiej czcionki D2R, afiksów, run oraz statystyk.
  - Automatyczne dopasowanie do wbudowanej bazy przedmiotów gry (catalog.sqlite).
  - Obliczanie widełek (min-max rolls) dla zmiennych statystyk unikatów, zestawów i słów runicznych.
- **Zarządzanie skrytką i postaciami**:
  - Filtry według jakości (Unikaty, Zestawy, Słowa runiczne, Rzadkie, Magiczne, Bazy).
  - Wirtualna lalka ekwipunku (Paperdoll) z obsługą slotów broni I oraz II (swap).
  - Ekwipunek najemnika (Mercenary).
  - Skaner ekranu statystyk postaci (F7).
  - Wykrywanie duplikatów i sugerowanie optymalnego ułożenia.
- **Kalkulator Run i Słów Runicznych**:
  - Autentyczna siatka run D2R z podziałem na tiery (Low, Mid, High).
  - Wyliczanie możliwych do złożenia słów na podstawie posiadanych run i baz.
- **Desktop Companion HUD**:
  - Podręczny panel nakładkowy na pulpit z regulacją przezroczystości i trybem Always-on-Top.
  - Przełączanie trybów klawiszami funkcyjnymi (F7 - Statystyki, F8 - Runy, F9 - Skrytka, F11 - Postać, F12 - Najemnik).
- **Menedżer Handlu (Trade Manager)**:
  - Generowanie czytelnych linii do wymian handlowych (Discord, fora, d2jsp).
  - Integracja z rynkiem online.

---

## Wymagania systemowe

- **System operacyjny**: Windows 10 / 11 (64-bit)
- **Python**: 3.10 lub nowszy
- **Klucz Google Gemini API**: Darmowy klucz do pobrania na [Google AI Studio](https://aistudio.google.com/)

---

## Instalacja

1. Sklonuj repozytorium lub pobierz archiwum ZIP:
   `ash
   git clone https://github.com/twoj-profil/d2-uberapp.git
   cd d2-uberapp
   `

2. Utwórz wirtualne środowisko (zalecane) i zainstaluj zależności:
   `ash
   python -m venv venv
   venv\Scriptsctivate
   pip install -r requirements.txt
   `

3. Skonfiguruj klucz API Gemini:
   - Skopiuj plik .env.example jako .env:
     `ash
     copy .env.example .env
     `
   - Otwórz .env i wpisz swój klucz GEMINI_API_KEY.
   - Alternatywnie możesz wprowadzić klucz bezpośrednio w ustawieniach Companion HUD po uruchomieniu aplikacji.

---

## Uruchomienie

### Sposób 1: Skrypt startowy (najprostszy)
Uruchom plik start.bat dwuklikiem. Skrypt automatycznie zwolni port 5005 (jeśli był zajęty) i odpali aplikację.

### Sposób 2: Konsola
`ash
python app.py
`

Po uruchomieniu interfejs dostępny jest pod adresem:
http://127.0.0.1:5005

---

## Domyślne skróty klawiszowe

| Skrót | Działanie |
|---|---|
| **F10** | Przechwyć tooltip przedmiotu / zrzut pod kursorem |
| **F7** | Tryb skanowania ekranu statystyk postaci |
| **F8** | Tryb skanowania zakładki run w skrytce |
| **F9** | Tryb skanowania ogólnego do skrzyni (Stash) |
| **F11** | Tryb przypisywania przedmiotu do aktywnej postaci |
| **F12** | Tryb przypisywania przedmiotu do najemnika |

*Skróty klawiszowe można dostosować w panelu bocznym aplikacji Companion HUD.*

---

## Struktura projektu

`	ext
D2 UberApp/
├── data/
│   ├── catalog.sqlite         # Kanoniczna baza danych przedmiotów D2R
│   ├── armor_bases.json       # Bazy pancerzy
│   ├── item_bases.json        # Bazy broni i akcesoriów
│   ├── trade_catalog_500.json # Katalog wycen i prefiksów handlowych
│   ├── screenshots/           # Zrzuty ekranu (tworzone lokalnie)
│   └── previews/              # Wycięte miniatury (tworzone lokalnie)
├── static/                    # CSS, ikony klas, grafiki run, dźwięki SFX
├── templates/                 # Szablony HTML (Flask/Jinja2)
├── ai_processor.py            # Integracja z Google Gemini SDK
├── app.py                     # Główna aplikacja Flask i trasy HTTP
├── capture.py                 # Moduł przechwytywania ekranu (Win32 API)
├── catalog_matcher.py         # Silnik dopasowywania i weryfikacji rolls
├── companion.py               # Serwis panelu pomocniczego (Companion)
├── config.py                  # Konfiguracja środowiska i ścieżek
├── db.py                      # Warstwa bazy danych SQLite
├── runeword_calc.py           # Silnik kalkulatora słów runicznych
├── requirements.txt           # Zależności Python
├── start.bat                  # Skrypt uruchamiający
└── README.md
`

---

## Licencja

Projekt udostępniany na licencji MIT. Zobacz szczegóły w pliku LICENSE.
