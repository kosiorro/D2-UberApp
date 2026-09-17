## D2 UberApp v1.3.2 — aktualizator i poprawki uruchomienia

- Nowa sekcja **Aktualizacje aplikacji / App updates** w panelu i przeglądarce: sprawdzanie wersji przy starcie, ręczne sprawdzanie, pobieranie i instalacja z ponownym uruchomieniem.
- Aktualizacje pochodzą z GitHub Releases i są weryfikowane sumą SHA-256. Podmiana obsługuje instalację Windows i portable, zachowuje dane użytkownika i wykonuje kopię zastępowanych plików programu na potrzeby wycofania błędu podmiany.
- Po czystej instalacji wyświetlana jest instrukcja podłączenia Gemini API po polsku lub angielsku z linkiem do Google AI Studio. Skan bez klucza nie tworzy błędu w historii i nie wywołuje AI.
- Poprawka regresji v1.3.1: ręczny tryb Runy nie wymaga już dopasowania wszystkich sześciu separatorów siatki. Automatyczne przełączanie zachowuje bardziej restrykcyjne sprawdzanie.
- Każdy build powstaje w osobnym katalogu. Weryfikacja paczki blokuje publikację bazy użytkownika, prywatnych ustawień oraz skanów.
- Ustawienia skrótów można zapisać również przed podłączeniem Gemini API.

### Pobieranie

- **D2UberApp_Setup_v1.3.2.exe** — instalator Windows.
- **D2UberApp_Windows_x64.zip** — wersja portable.

Wersje do v1.3.1 nie mają aktualizatora: v1.3.2 należy zainstalować ręcznie. Kolejne aktualizacje można pobierać z aplikacji. Przycisk „Zainstaluj i uruchom ponownie” jest dostępny w oknie aplikacji Windows po pobraniu paczki; należy wcześniej zakończyć skan i zamknąć kreator postaci.

Istniejąca historia skanów pozostaje zachowana przy aktualizacji. Stare błędy w historii nie oznaczają nowych błędów przy uruchamianiu.
