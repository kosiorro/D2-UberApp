const updateEnglish = document.documentElement.lang === 'en';
const updateText = (pl, en) => updateEnglish ? en : pl;
async function refreshAppUpdate() {
    try {
        const response = await fetch('/api/updates');
        if (!response.ok) return;
        const data = await response.json();
        document.getElementById('api-onboarding').hidden = data.has_api_key;
        document.getElementById('update-version').textContent = 'v' + data.current;
        const messages = {
            idle: updateText('Możesz sprawdzić dostępność nowej wersji.', 'Check whether a new version is available.'),
            checking: updateText('Sprawdzanie GitHuba…', 'Checking GitHub…'),
            current: updateText('Masz najnowszą wersję.', 'You are up to date.'),
            available: updateText('Dostępna wersja: ', 'Available version: ') + data.latest,
            downloading: updateText('Pobieranie i sprawdzanie paczki…', 'Downloading and verifying the package…'),
            ready: updateText('Aktualizacja gotowa. Zainstaluj ją po zakończeniu skanowania.', 'Update ready. Install after finishing your scans.'),
            installing: updateText('Instalowanie… Aplikacja uruchomi się ponownie.', 'Installing… The app will restart.'),
            check_error: updateText('Nie udało się sprawdzić aktualizacji. Sprawdź internet i spróbuj ponownie.', 'Could not check for updates. Check your connection and retry.'),
            download_error: updateText('Pobieranie lub weryfikacja nie powiodły się. Pliki aplikacji pozostały bez zmian. Sprawdź aktualizacje, aby ponowić.', 'Download or verification failed. App files are unchanged. Check for updates to retry.')
        };
        document.getElementById('update-status').textContent = (messages[data.status] || '') + (!data.supported ? updateText(' Instalacja aktualizacji jest dostępna w wydaniu EXE dla Windows.', ' Installing updates requires the Windows EXE edition.') : '');
        document.getElementById('update-badge').textContent = ['available', 'ready'].includes(data.status) ? '●' : '';
        document.getElementById('update-auto').checked = data.automatic;
        document.getElementById('update-check').disabled = ['checking', 'downloading', 'ready', 'installing'].includes(data.status);
        document.getElementById('update-download').hidden = data.status !== 'available' || !data.supported;
        document.getElementById('update-install').hidden = data.status !== 'ready' || !data.supported;
    } catch (_) { /* Offline status does not interrupt the app. */ }
}
async function updateAction(action, extra = {}) {
    try {
        const response = await fetch('/api/updates', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action, ...extra})});
        if (!response.ok) throw Error();
        await refreshAppUpdate();
    } catch (_) {
        document.getElementById('update-status').textContent = updateText('Operacja nie powiodła się. Spróbuj ponownie.', 'Operation failed. Please try again.');
    }
}
async function openApiSettings() {
    if (typeof settingsOpen === 'function' && window.pywebview) return settingsOpen();
    await fetch('/api/companion/open', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    alert(updateText('W panelu aplikacji kliknij ikonę koła zębatego i wpisz klucz Gemini API.', 'In the app panel, click the gear icon and enter your Gemini API key.'));
}
async function installAppUpdate() {
    if (!window.pywebview) {
        await fetch('/api/companion/open', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
        alert(updateText('Kliknij „Zainstaluj i uruchom ponownie” w panelu aplikacji.', 'Click “Install and restart” in the app panel.'));
        return;
    }
    const result = await window.pywebview.api.install_update();
    if (result?.error) document.getElementById('update-status').textContent = result.error;
}
refreshAppUpdate();
setInterval(refreshAppUpdate, 3000);
