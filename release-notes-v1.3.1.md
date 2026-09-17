## D2 UberApp v1.3.1 — poprawki skanowania ekwipunku

- Automatyczny wybór trybu na podstawie lokalnego wykrywania tooltipu lub siatki run, bez dodatkowych zapytań do AI.
- Poprawka fałszywego komunikatu o zakładce run przy szarym tle i niewykrytym opisie przedmiotu.
- Porównywanie przedmiotów nie jest mylone z zakładką run.
- Zachowanie wyboru Postać/Najemnik dla opisów ekwipunku oraz wskazanego celu w kreatorach.
- Lokalny plik diagnostyczny JSON obok screenshotu: rozdzielczość, kursor, tryb, wycinek i wynik skanu. Ułatwia odtwarzanie zgłoszeń bez AI.
- Testy regresji obejmujące angielski opis ekwipunku na szarym tle.

Automatyczna detekcja siatki run obsługuje obecnie rozdzielczość 1920×1080.
Wydanie nie zawiera jeszcze automatycznego aktualizatora aplikacji.

### Pobieranie

- **D2UberApp_Setup_v1.3.1.exe** — instalator Windows.
- **D2UberApp_Windows_x64.zip** — wersja portable; wypakuj i uruchom `D2UberApp.exe`.

Instalator zachowuje istniejące ustawienia użytkownika. Przed ręczną wymianą wersji portable zachowaj swój katalog `data` i plik `.env`, jeżeli go używasz.
