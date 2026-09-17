# Wykrywanie opisów przedmiotów

Detektor w `tooltip_detection.py` działa lokalnie, przed wywołaniem AI.
Tryby Skrzynia, Postać i Najemnik korzystają z tego samego algorytmu.

## Przygotowanie obrazu

1. Szuka tekstu na całym ekranie, również przy krawędziach. Łączy litery
   w linie i grupuje wyśrodkowane linie opisu. Uwzględnia kolory tekstu D2R,
   wygładzanie liter, skalę ekranu oraz przyciemnione tło.
2. Dla zwykłych przedmiotów z białym/szarym tekstem dodatkowo sprawdza ramkę.
   Przedmioty z kolorowymi opisami mogą być wykrywane bez ramki.
3. Zachowuje nazwę, bazę, wymagania, właściwości, gniazda i informacje zestawu.
   Rozszerza wycinek o szary tekst nazwy oraz niewielki margines dla liter.
   Szare podpowiedzi sterowania nie są dołączane jako część opisu.
4. Przy kilku kandydatach używa pozycji kursora zapisanej w momencie zrzutu.
   Jeśli wybór pozostaje niejednoznaczny, prosi o ponowienie skanu bez porównania.
5. Do AI przekazywany jest wyłącznie wynikowy wycinek. Niepowodzenie detekcji
   nie powoduje wysłania całego ekranu. Pełny zrzut nadal jest zapisywany lokalnie.

Rozpoznanie treści i walidacja odpowiedzi AI pozostają osobnym etapem.
Geometria i kolory nie gwarantują poprawnego OCR ani kompletności zasłoniętego
opisu. Nietypowe filtry kolorów, skale interfejsu lub nakładające się okna mogą
wymagać ponowienia skanu.

## Zgłoszenia błędów i odtwarzanie bez AI

Po skanie obok zapisanego obrazu `data/screenshots/d2_….png` powstaje plik
`d2_….json`: wersja detektora, rozdzielczość, pozycja kursora, wybrany i wynikowy
tryb, granice wycinka oraz wynik skanu. Nie zawiera konfiguracji ani klucza API.
Zapis jest lokalny i nie wymaga dodatkowych tokenów. Błąd zapisu diagnostyki
nie przerywa skanowania.

Do zgłoszenia warto dołączyć tę parę plików, wersję aplikacji, język gry,
skalę interfejsu i informację o HDR. Sam komunikat nie pozwala rozstrzygnąć,
czy zawiódł wycinek, czy późniejsze rozpoznanie tekstu. Przed udostępnieniem
zrzutu należy sprawdzić jego zawartość.

Odtworzenie lokalnego wykrywania z katalogu projektu:

```console
python scan_diagnostics.py "data/screenshots/d2_….png"
python scan_diagnostics.py "data/screenshots/d2_….png" --mode character
```

Narzędzie wypisuje kandydatów tooltipu, wynik detekcji siatki i wycinek lub
przyczynę odmowy. Czyta zapisany kursor z pliku JSON. Nie wywołuje AI i nie
zapisuje przedmiotów. Odtwarza samą detekcję, bez ograniczeń kroków kreatora.

Rozpoznanie run wymaga teraz powtarzalnych separatorów siatki i tekstury
wewnątrz komórek; pojedynczy szary rząd ani jednolite tło nie wystarczają.
Testy obejmują angielski opis nad szarym tłem oraz błędne rozpoznanie run
w trybach Skrzynia, Postać i Najemnik. To testy geometrii; poprawność OCR
konkretnego zgłoszenia trzeba zweryfikować na jego oryginalnym zrzucie.

## Testy offline

```console
python -m unittest discover -s tests -v
```

Testy obejmują krawędzie ekranu, opisy bez ramki, szare nazwy, czerwony tekst,
pomijanie podpowiedzi, rozdzielczości 720p/1440p/4K, kilka jednoczesnych opisów
i przekazanie wycinka do ścieżki skanowania. Nie wywołują AI.

Jeśli lokalnie dostępne są źródłowe screenshoty z 15.09.2026 w
`data/screenshots`, dodatkowo sprawdzają 29 opisów przedmiotów i 7 ekranów
bez opisu oraz kompletność znanych przypadków Chwytu Drakuli, Serca Griswolda
i Żalu. Prywatne screenshoty nie są dodawane do repozytorium.
# Automatyczny wybór trybu

Przed odczytem AI aplikacja lokalnie sprawdza obraz. Czytelny tooltip w trybie
run, klejnotów, materiałów lub statystyk przełącza skan na Skrzynię. Rozpoznana
siatka run w trybie przedmiotów przełącza na Runy (obecnie detekcja 1920×1080).
Wybór Postać/Najemnik pozostaje zachowany dla tooltipów, ponieważ opis nie
potwierdza właściciela. Kreatory i skanowanie drzewek zachowują wskazany cel.
Niejednoznaczne obrazy nie powodują przełączenia. Mechanizm nie dodaje promptów
ani wywołań modelu; koszt samego odczytu jest taki jak przy ręcznym wyborze
docelowego trybu.
