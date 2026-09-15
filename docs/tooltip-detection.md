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
