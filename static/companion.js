async function switchCompanionLanguage() {
    const currentLang = window.APP_LANG || 'pl';
    const newLang = currentLang === 'pl' ? 'en' : 'pl';
    try {
        await fetch('/api/set_language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lang: newLang })
        });
        window.location.reload();
    } catch (e) {
        toast('Failed to change language: ' + e.message);
    }
}

const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
let state = {}, currentPage = 'items', wizardRequest = null, originalHero = '', toastTimer, currentMode = 'stash', isMini = false;

function toast(message) {
    $('toast').textContent = message;
    $('toast').hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $('toast').hidden = true, 5000);
}

async function nativeCall(method, ...args) {
    try {
        if (!window.pywebview) throw Error(window.APP_LANG === 'en' ? 'Option available in the desktop window.' : 'Opcja dostępna w oknie aplikacji startowej.');
        const result = await window.pywebview.api[method](...args);
        if (result?.error) throw Error(result.error);
        return result;
    } catch (e) {
        toast(e.message);
        return null;
    }
}

async function action(data) {
    try {
        const response = await fetch('/api/companion/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const value = await response.json();
        if (!response.ok) throw Error(value.error);
        await refresh();
        return true;
    } catch (e) {
        toast(e.message);
        return false;
    }
}

function page(tab) {
    currentPage = tab;
    nativeCall('open_web', tab);
}

async function selectHero() {
    if ($('mini-hero-choice') && $('hero-choice')) {
        $('mini-hero-choice').value = $('hero-choice').value;
    }
    await changeSession();
}

async function selectHeroFromMini(el) {
    if ($('hero-choice') && el) {
        $('hero-choice').value = el.value;
    }
    await changeSession();
}

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.mode === mode));
    if ($('swap-option')) $('swap-option').hidden = mode !== 'character';
    changeSession();
}

async function changeSession() {
    return action({
        action: 'session',
        character: $('hero-choice')?.value || '',
        mode: currentMode,
        swap: $('capture-swap')?.checked || false
    });
}

async function appearance() {
    const onTop = !!$('on-top')?.checked;
    const semiTrans = !!$('semi-transparent')?.checked;
    document.body.classList.toggle('semi-transparent', semiTrans);
    await nativeCall('appearance', onTop, semiTrans);
}

async function toggleMiniMode() {
    isMini = !isMini;
    document.body.classList.toggle('mini-mode', isMini);
    await nativeCall('set_mini_mode', isMini);
}

async function wizardStart() {
    if (await action({ action: 'wizard_start' })) {
        wizardRequest = null;
        $('wizard-result').hidden = true;
        $('wizard-submit').disabled = true;
        $('wizard-status').textContent = window.APP_LANG === 'en' ? 'Waiting for screenshot…' : 'Oczekiwanie na zrzut…';
        $('wizard-title').textContent = window.APP_LANG === 'en' ? '1. Scan character stats' : '1. Zeskanuj statystyki';
        $('wizard-dialog').showModal();
    }
}

async function wizardCancel() {
    if (await action({ action: 'wizard_cancel' })) $('wizard-dialog').close();
}

$('wizard-dialog').addEventListener('cancel', event => {
    event.preventDefault();
    wizardCancel();
});

async function wizardConfirm(event) {
    event.preventDefault();
    if (await action({
        action: 'wizard_confirm',
        name: $('wizard-name').value,
        level: $('wizard-level').value,
        add_items: $('wizard-items').checked
    })) {
        $('wizard-dialog').close();
        toast((window.APP_LANG === 'en' ? 'Character saved: ' : 'Zapisano postać: ') + $('wizard-name').value);
    }
}

function getHeroFields() {
    if (window.APP_LANG === 'en') {
        return [
            ['name', 'Name'], ['class_name', 'Class'], ['level', 'Level'],
            ['strength', 'Strength'], ['dexterity', 'Dexterity'], ['vitality', 'Vitality'],
            ['energy', 'Energy'], ['life', 'Life'], ['mana', 'Mana'],
            ['defense', 'Defense'], ['fire_res', 'Fire Res'], ['cold_res', 'Cold Res'],
            ['light_res', 'Light Res'], ['poison_res', 'Poison Res']
        ];
    }
    return [
        ['name', 'Nazwa'], ['class_name', 'Klasa'], ['level', 'Poziom'],
        ['strength', 'Siła'], ['dexterity', 'Zręczność'], ['vitality', 'Żywotność'],
        ['energy', 'Energia'], ['life', 'Życie'], ['mana', 'Mana'],
        ['defense', 'Obrona'], ['fire_res', 'Ogień'], ['cold_res', 'Zimno'],
        ['light_res', 'Błyskawice'], ['poison_res', 'Trucizna']
    ];
}

function editHero() {
    const hero = (state.characters || []).find(x => x.name === $('hero-choice').value);
    if (!hero) return toast(window.APP_LANG === 'en' ? 'Add a hero using the wizard first.' : 'Najpierw dodaj postać kreatorem.');
    originalHero = hero.name;
    const fields = getHeroFields();
    $('edit-fields').innerHTML = fields.map(([key, label]) => `<label>${label}<input id="hero-${key}" value="${esc(hero[key])}" required></label>`).join('');
    $('edit-dialog').showModal();
}

async function saveHero(event) {
    event.preventDefault();
    const data = {};
    const fields = getHeroFields();
    fields.forEach(([key]) => data[key] = $('hero-' + key).value);
    for (const key of ['level', 'strength', 'dexterity', 'vitality', 'energy', 'defense']) {
        data[key] = Number(data[key]);
        if (!Number.isFinite(data[key]) || data[key] < 0) return toast(window.APP_LANG === 'en' ? 'Check numbers in stats.' : 'Sprawdź liczby w statystykach.');
    }
    if (await action({ action: 'edit', original: originalHero, character_data: data })) {
        $('edit-dialog').close();
        toast(window.APP_LANG === 'en' ? 'Character updated!' : 'Zaktualizowano postać!');
    }
}

async function settingsOpen() {
    const data = await nativeCall('settings');
    if (!data) return;
    function setSelectValue(el, val) {
        if (!el) return;
        el.value = val;
        if (el.selectedIndex === -1 && val) {
            for (let opt of el.options) {
                if (opt.value.toLowerCase() === (val || '').toLowerCase()) {
                    el.value = opt.value;
                    return;
                }
            }
            const newOpt = document.createElement('option');
            newOpt.value = val;
            newOpt.textContent = val;
            newOpt.selected = true;
            el.appendChild(newOpt);
        }
    }
    setSelectValue($('set-hotkey'), data.hotkey);
    $('set-model').value = data.model;
    $('set-key').value = '';
    $('set-location').value = data.location;
    $('set-sound').checked = data.sound;
    $('set-autostart').checked = data.autostart;
    $('set-stat-region').value = (data.regions.stat_screen || [0, 0, .58, 1]).join(', ');
    $('set-rune-region').value = (data.regions.runes || [0, 0, .65, .95]).join(', ');
    const mhk = data.mode_hotkeys || {};
    ['stash', 'character', 'merc', 'runes', 'stat_screen'].forEach(m => {
        setSelectValue($('set-mode-hk-' + m), mhk[m] || '');
    });
    $('settings-dialog').showModal();
}

async function saveSettings(event) {
    event.preventDefault();
    const region = id => $(id).value.split(',').map(x => Number(x.trim()));
    const modeHotkeys = {};
    ['stash', 'character', 'merc', 'runes', 'stat_screen'].forEach(m => {
        const el = $('set-mode-hk-' + m);
        if (el) modeHotkeys[m] = el.value || '';
    });
    const data = {
        hotkey: $('set-hotkey').value,
        model: $('set-model').value,
        key: $('set-key').value,
        location: $('set-location').value,
        sound: $('set-sound').checked,
        autostart: $('set-autostart').checked,
        mode_hotkeys: modeHotkeys,
        regions: { stat_screen: region('set-stat-region'), runes: region('set-rune-region') }
    };
    const result = await nativeCall('save_settings', data);
    if (result?.success) {
        $('set-key').value = '';
        $('settings-dialog').close();
        toast(window.APP_LANG === 'en' ? 'Settings saved.' : 'Zapisano ustawienia.');
        await refresh();
    }
}

function formatCompanionStatus(rawStatus, running, hotkey) {
    if (window.APP_LANG !== 'en') return rawStatus || (running ? 'Aktywny' : 'Wstrzymany');
    if (!rawStatus) return running ? 'Active' : 'Paused';
    const hk = hotkey || 'F10';
    if (rawStatus.startsWith('Aktywny')) {
        return `Active (Hotkey: ${hk})`;
    }
    if (rawStatus.startsWith('Zatrzymany') || rawStatus.startsWith('Wstrzymany')) {
        return 'Paused';
    }
    if (rawStatus.startsWith('Uruchamianie')) {
        return 'Starting listener...';
    }
    if (rawStatus.includes('Błąd rejestracji') || rawStatus.includes('skrót zajęty')) {
        return `Hotkey registration error: ${hk} (key busy)`;
    }
    return rawStatus;
}

function formatCompanionMessage(msg) {
    if (!msg) return '';
    if (window.APP_LANG !== 'en') return msg;
    if (msg.startsWith('Gotowy. Oczekiwanie na klawisz')) {
        const hk = state.hotkey || 'F10';
        return `Ready. Waiting for ${hk} in-game...`;
    }
    if (msg.startsWith('Gotowy na kolejny')) {
        return 'Ready for next loot.';
    }
    if (msg.startsWith('Wycinam obszar odczytu')) {
        return 'Cropping scan region and checking content…';
    }
    if (msg.startsWith('Zrzut ekranu wykonany')) {
        return 'Screenshot captured. Analyzing with Gemini…';
    }
    if (msg.startsWith('Zapisano możliwy duplikat: ')) {
        return 'Saved possible duplicate: ' + msg.substring(27);
    }
    if (msg.startsWith('Zapisano: ')) {
        return 'Saved: ' + msg.substring(10);
    }
    if (msg.startsWith('Zapisano statystyki: ')) {
        return 'Saved character stats: ' + msg.substring(21);
    }
    if (msg.startsWith('Zapisano zakładkę run: ')) {
        return 'Saved rune tab: ' + msg.substring(23).replace('szt.', 'pcs');
    }
    if (msg.startsWith('Odczytano ') && msg.includes('Potwierdź postać w kreatorze')) {
        const name = msg.replace('Odczytano ', '').split('.')[0];
        return `Read ${name}. Confirm character in wizard.`;
    }
    if (msg.startsWith('Błąd przechwytywania: ')) {
        return 'Capture error: ' + msg.substring(22);
    }
    if (msg.startsWith('Błąd: ')) {
        return 'Error: ' + msg.substring(6);
    }
    if (msg.startsWith('Obraz nie pasuje do wybranego trybu')) {
        return 'Image does not match the selected scan mode.';
    }
    if (msg.startsWith('Nie rozpoznano nazwy postaci')) {
        return 'Could not recognize character name.';
    }
    if (msg.startsWith('Wybierz istniejącą postać')) {
        return 'Select an existing character before scanning.';
    }
    if (msg.startsWith('Poczekaj na zakończenie')) {
        return 'Wait for previous scan to complete.';
    }
    return msg;
}

async function refresh() {
    try {
        const response = await fetch('/api/companion/state');
        if (!response.ok) return;
        state = await response.json();
        $('capture-state').textContent = formatCompanionStatus(state.status, state.running, state.hotkey);
        $('capture-message').textContent = formatCompanionMessage(state.activity.message);
        
        // Update toggle button text and icon
        const playIcon = document.querySelector('.toggle-icon-play');
        const pauseIcon = document.querySelector('.toggle-icon-pause');
        if (playIcon && pauseIcon) {
            playIcon.style.display = state.running ? 'none' : 'inline-block';
            pauseIcon.style.display = state.running ? 'inline-block' : 'none';
        }
        if ($('capture-toggle-text')) {
            $('capture-toggle-text').textContent = state.running ? (window.APP_LANG === 'en' ? 'Active' : 'Aktywny') : (window.APP_LANG === 'en' ? 'Paused' : 'Wstrzymany');
        }
        
        const dot = $('status-dot');
        if (dot) dot.className = 'status-dot ' + (state.running ? 'active' : 'inactive');
        document.querySelectorAll('.hotkey').forEach(el => el.textContent = state.hotkey);

        const picker = $('hero-choice'), focused = document.activeElement;
        const miniPicker = $('mini-hero-choice');
        const names = (state.characters || []).map(x => x.name);
        if (picker && picker.dataset.names !== JSON.stringify(names)) {
            picker.innerHTML = state.characters.map(h => `<option value="${esc(h.name)}">${esc(h.name)} · ${esc(h.level)} ${esc(h.class_name)}</option>`).join('');
            picker.dataset.names = JSON.stringify(names);
        }
        if (miniPicker && miniPicker.dataset.names !== JSON.stringify(names)) {
            miniPicker.innerHTML = state.characters.map(h => `<option value="${esc(h.name)}">${esc(h.name)} (${esc(h.class_name)})</option>`).join('');
            miniPicker.dataset.names = JSON.stringify(names);
        }
        if (picker && focused !== picker) picker.value = state.character;
        if (miniPicker && focused !== miniPicker) miniPicker.value = state.character;

        if (state.mode && state.mode !== 'normal') {
            currentMode = state.mode;
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.mode === state.mode));
        }
        if ($('capture-swap')) $('capture-swap').checked = state.swap;
        if ($('swap-option')) $('swap-option').hidden = currentMode !== 'character';

        const mhk = state.mode_hotkeys || {};
        document.querySelectorAll('.mode-hotkey-badge').forEach(badge => {
            const m = badge.dataset.modeKey;
            const k = mhk[m] || '';
            badge.textContent = k;
            badge.style.display = k ? 'inline-block' : 'none';
        });

        const historyEl = $('scan-history');
        if (historyEl) {
            const stateDict = window.APP_LANG === 'en'
                ? { success: 'saved', processing: 'analyzing', rejected: 'rejected', error: 'error', review: 'wizard', cancelled: 'cancelled' }
                : { success: 'zapisano', processing: 'analiza', rejected: 'odrzucono', error: 'błąd', review: 'kreator', cancelled: 'anulowano' };
            historyEl.innerHTML = state.history.slice(0, 8).map(h => {
                let mvHtml = '';
                if (h.market_value) {
                    let mv = String(h.market_value).toUpperCase();
                    let color = '#55eedd';
                    let icon = '$';
                    if (mv.includes('VERY') || mv.includes('BARDZO')) { color = '#ffe680'; icon = '$'; }
                    else if (mv === 'HIGH' || mv === 'WYSOKA') { color = '#ffd27d'; icon = '$'; }
                    else if (mv === 'LOW' || mv === 'NISKA') { color = '#9cb5d9'; icon = '$'; }
                    else if (mv === 'TRASH' || mv.includes('ZNIK')) { color = '#ff5555'; icon = '🗑️'; }
                    mvHtml = `<span style="display: inline-block; margin-left: 6px; padding: 1px 5px; font-size: 10px; font-weight: 700; border-radius: 2px; background: rgba(0,0,0,0.5); border: 1px solid ${color}; color: ${color};">${icon} ${esc(h.market_value)}</span>`;
                }
                return `
                <div class="scan-entry ${esc(h.state)}">
                    <time>${esc(h.created_at)}</time>
                    <span> · ${esc(stateDict[h.state] || h.state)}</span>
                    <strong>${esc(h.name || h.message)}</strong>
                    ${mvHtml}
                    ${h.has_preview ? `<a href="/previews/${encodeURIComponent(h.id)}.png" target="_blank">${window.APP_LANG === 'en' ? 'AI Crop' : 'Wycinek AI'}</a>` : ''}
                </div>
            `;}).join('');
        }

        if (state.wizard_active && state.wizard) {
            if (state.wizard.status === 'error') $('wizard-status').textContent = state.wizard.message;
            if (state.wizard.status === 'success' && state.wizard.request_id !== wizardRequest) {
                wizardRequest = state.wizard.request_id;
                const char = state.wizard.character;
                $('wizard-name').value = char.name;
                $('wizard-level').value = char.level;
                $('wizard-title').textContent = window.APP_LANG === 'en' ? '1. Verify scanned hero' : '1. Sprawdź odczytaną postać';
                $('wizard-status').textContent = window.APP_LANG === 'en' ? 'Data read successfully. Confirm before saving.' : 'Dane odczytane. Potwierdź je przed zapisaniem.';
                $('wizard-result').hidden = false;
                $('wizard-submit').disabled = false;
                const wizFields = window.APP_LANG === 'en'
                    ? [['class_name', 'Class'], ['strength', 'Strength'], ['dexterity', 'Dexterity'], ['vitality', 'Vitality'], ['energy', 'Energy'], ['life', 'Life'], ['mana', 'Mana']]
                    : [['class_name', 'Klasa'], ['strength', 'Siła'], ['dexterity', 'Zręczność'], ['vitality', 'Żywotność'], ['energy', 'Energia'], ['life', 'Życie'], ['mana', 'Mana']];
                $('wizard-summary').innerHTML = wizFields.map(([k, label]) => `<div><small>${label}</small>${esc(char[k])}</div>`).join('');
            }
        }
    } catch (e) {
        $('capture-state').textContent = window.APP_LANG === 'en' ? 'No connection to service' : 'Brak połączenia z serwisem';
    }
}

async function poll() {
    await refresh();
    setTimeout(poll, 1400);
}
poll();

window.addEventListener('pywebviewready', async () => {
    const settings = await nativeCall('settings');
    if (settings) {
        if ($('on-top')) $('on-top').checked = !!settings.topmost;
    }
});

