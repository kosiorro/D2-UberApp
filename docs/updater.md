# Aktualizator Windows

Sekcja „Aktualizacje aplikacji / App updates” znajduje się w panelu aplikacji
i nad głównym widokiem WWW. Sprawdzanie GitHub Releases odbywa się przy starcie
(można wyłączyć) lub po naciśnięciu przycisku. Sprawdzanie i pobieranie działają
w tle, bez Gemini. Instalację użytkownik uruchamia w oknie desktopowym po
zakończeniu skanowania i zamknięciu kreatora.

Updater pobiera wyłącznie `D2UberApp_Windows_x64.zip` z wydania repozytorium
`kosiorro/D2-UberApp`. Weryfikuje wersję, adres, rozmiar i SHA-256 otrzymany
z GitHub API. Wydania przedpremierowe i starsze są pomijane. Ścieżki w ZIP
są walidowane przed rozpakowaniem. Paczka nie może zastąpić pliku `.env`,
ustawień użytkownika, bazy `stash.sqlite`, screenshotów ani podglądów.

Paczka, plan i kopia zastępowanych plików trafiają do `.updates/update-*`
w katalogu aplikacji. Pomocniczy PowerShell czeka na zakończenie procesu,
podmienia pliki, a w razie błędu podmiany próbuje przywrócić poprzednie.
Po podmianie uruchamia aplikację. Wynik zapisuje w `.updates/last-result.txt`.
Kopia obejmuje pliki programu, nie jest kopią bazy użytkownika. Błąd startu
nowego programu po udanej podmianie nie uruchamia automatycznego rollbacku.
Wymagane są prawa zapisu w katalogu instalacji i działający PowerShell.

# Czyste wydania

`python build_release.py` tworzy nowy katalog pod `dist/release-*`, a jego
ścieżkę zapisuje w `build/release-package.txt`. Nie pakuje zawartości starego
`dist/D2UberApp`. Instalator należy kompilować z `/DPackageDir=...` oraz
`/DReleaseVersion=...` zgodnym z `app_version.py`; workflow robi to automatycznie.
`release_validation.py` blokuje paczkę z danymi użytkownika. Dane już istniejące
u użytkownika nie są usuwane podczas instalacji.
