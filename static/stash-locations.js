// Shared editor: HTML dialogs also work inside the desktop WebView.
(() => {
    const stylesheet = document.createElement('link');
    stylesheet.rel = 'stylesheet'; stylesheet.href = '/static/stash-locations.css';
    document.head.append(stylesheet);
    let input = document.getElementById('stash-location-input') || document.getElementById('webActiveStash');
    if (!input) return;
    const en = window.APP_LANG === 'en';
    const label = (pl, eng) => en ? eng : pl;
    // Native datalist popups are unreliable in embedded WebViews. Use a select.
    for (const field of [input, document.getElementById('mini-stash-location')].filter(Boolean)) {
        const picker = document.createElement('select');
        picker.id = field.id;
        picker.className = field.className;
        picker.style.cssText = field.style.cssText;
        picker.setAttribute('aria-label', label('Skrzynia / muł', 'Stash / mule'));
        picker.onchange = () => field.id === 'webActiveStash' ? setWebActiveStash(picker.value) : updateStashLocation(picker.value);
        field.replaceWith(picker);
        if (field === input) input = picker;
    }
    let listSignature = '';
    async function loadLocations() {
        try {
            const response = await fetch('/api/companion/state');
            if (!response.ok) return;
            const state = await response.json();
            const names = [...new Set([...state.locations, state.location].filter(Boolean))];
            const signature = JSON.stringify(names);
            for (const picker of [input, document.getElementById('mini-stash-location')].filter(Boolean)) {
                if (signature !== listSignature) {
                    picker.replaceChildren(new Option(label('Skrzynia ogólna', 'General stash'), ''));
                    names.forEach(name => picker.add(new Option(name, name)));
                }
                if (document.activeElement !== picker) picker.value = state.location || '';
            }
            listSignature = signature;
        } catch (e) { console.warn(e.message); }
        finally { setTimeout(loadLocations, 1800); }
    }
    loadLocations().catch(() => {});
    const add = input.parentElement.querySelector('button');
    input.parentElement.style.flexWrap = 'wrap';
    input.style.minWidth = '120px';
    add.onclick = () => openEditor('add');
    for (const [mode, title] of [['rename', label('Edytuj', 'Rename')], ['delete', label('Usuń', 'Delete')]]) {
        const button = add.cloneNode(false);
        button.removeAttribute('onclick');
        button.textContent = title;
        button.title = title;
        button.onclick = () => openEditor(mode);
        input.parentElement.append(button);
    }

    async function openEditor(mode) {
        const dialog = document.createElement('dialog');
        dialog.className = 'stash-editor-dialog';
        dialog.setAttribute('aria-labelledby', 'stash-editor-title');
        const form = document.createElement('form');
        form.onsubmit = event => event.preventDefault();
        const title = document.createElement('h3');
        title.id = 'stash-editor-title';
        title.textContent = mode === 'add' ? label('Dodaj skrzynię / muła', 'Add stash / mule') : mode === 'rename' ? label('Zmień nazwę skrzyni / muła', 'Rename stash / mule') : label('Usuń nazwę skrzyni / muła', 'Delete stash / mule name');
        const select = document.createElement('select');
        const name = document.createElement('input');
        name.placeholder = label('Nazwa skrzyni / muła', 'Stash / mule name');
        name.setAttribute('aria-label', name.placeholder);
        select.setAttribute('aria-label', label('Wybierz skrzynię / muła', 'Select stash / mule'));
        select.hidden = mode === 'add';
        name.hidden = mode === 'delete';
        name.required = mode !== 'delete';
        name.maxLength = 100;
        name.autocomplete = 'off';
        for (const element of [select, name]) element.style.cssText = 'display:block;box-sizing:border-box;width:100%;margin:12px 0;padding:8px;';
        if (select.hidden) select.style.display = 'none';
        if (name.hidden) name.style.display = 'none';
        const note = document.createElement('p');
        note.textContent = mode === 'delete' ? label('Usunięcie nazwy przenosi przedmioty do skrzyni ogólnej. Przedmioty pozostają w bazie.', 'Deleting the name moves items to the general stash. Items stay in the database.') : '';
        const error = document.createElement('p');
        error.className = 'stash-editor-error';
        error.setAttribute('role', 'alert');
        const submit = document.createElement('button');
        submit.textContent = mode === 'delete' ? label('Usuń nazwę', 'Delete name') : label('Zapisz', 'Save');
        submit.type = 'submit';
        const cancel = document.createElement('button');
        cancel.type = 'button';
        cancel.textContent = label('Anuluj', 'Cancel');
        cancel.onclick = () => dialog.close();
        const fields = document.createElement('div');
        fields.className = 'stash-editor-fields';
        const selectionLabel = document.createElement('label');
        selectionLabel.textContent = label('Wybierz skrzynię', 'Select stash');
        selectionLabel.hidden = mode === 'add';
        selectionLabel.append(select);
        const nameLabel = document.createElement('label');
        nameLabel.textContent = label('Nazwa', 'Name');
        nameLabel.hidden = mode === 'delete';
        nameLabel.append(name);
        fields.append(selectionLabel, nameLabel);
        const actions = document.createElement('div');
        actions.className = 'stash-editor-actions';
        submit.className = mode === 'delete' ? 'stash-editor-delete' : 'stash-editor-save';
        actions.append(cancel, submit);
        form.append(title, fields, note, error, actions);
        dialog.append(form);
        document.body.append(dialog);
        const trigger = document.activeElement;
        dialog.addEventListener('close', () => { dialog.remove(); trigger?.focus(); });
        dialog.showModal();
        submit.disabled = true;
        try {
            const response = await fetch('/api/companion/state');
            if (!response.ok) throw Error(label('Nie można pobrać nazw.', 'Could not load names.'));
            const state = await response.json();
            const locations = [...new Set([...state.locations, state.location].filter(Boolean))];
            locations.forEach(location => select.add(new Option(location, location)));
            if (locations.includes(input.value)) select.value = input.value;
            name.value = mode === 'rename' ? select.value : '';
            select.onchange = () => { name.value = select.value; };
            submit.disabled = mode !== 'add' && !locations.length;
            if (mode === 'add' || mode === 'rename') name.focus();
            if (mode !== 'add' && !locations.length) error.textContent = label('Nie ma jeszcze zapisanych skrzyń.', 'No saved stashes yet.');
        } catch (e) { error.textContent = e.message; }
        form.onsubmit = async event => {
            event.preventDefault();
            const value = name.value.trim();
            if (mode !== 'delete' && !value) { name.focus(); return; }
            submit.disabled = true;
            cancel.disabled = true;
            try {
                const response = await fetch('/api/companion/action', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({action: mode === 'add' ? 'set_location' : mode + '_location', original: select.value, location: value})
                });
                const result = await response.json();
                if (!response.ok) throw Error(result.error);
                dialog.close();
                if (document.getElementById('stash-location-input')) { listSignature = ''; await refresh(); }
                else {
                    const url = new URL(window.location.href);
                    if (url.searchParams.get('location') === select.value && mode !== 'add') {
                        if (mode === 'delete') url.searchParams.delete('location');
                        else url.searchParams.set('location', value);
                    }
                    window.location.href = url.toString();
                }
            } catch (e) { error.textContent = e.message; submit.disabled = false; cancel.disabled = false; }
        };
    }
})();
