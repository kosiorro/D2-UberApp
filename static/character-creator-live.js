// The visual layout is supplied by the user; state comes from the capture service.
let creatorState = {}, changingStage = false, ready = false;
let lastRequest = '', lastKey = 0;
const completed = new Set();
const statusLine = document.createElement('p');
statusLine.style.cssText = 'padding:8px 16px;color:#d7ad55;font-size:12px;';
statusLine.setAttribute('role', 'status');
document.querySelector('.wizardHead').append(statusLine);

function isScanStage() {
    const stage = stages[index];
    return ['stats', 'mercItem', 'tree'].includes(stage.type) || (stage.type === 'char' && stage.item.id !== 'swap');
}

function updateControls() {
    const busy = changingStage || creatorState.busy || !ready;
    document.getElementById('nextBtn').disabled = busy || (isScanStage() && !completed.has(stages[index].id));
    document.getElementById('backBtn').disabled = busy || index === 0;
    document.getElementById('skipBtn').disabled = busy;
    const finish = document.getElementById('finishInventoryBtn');
    if (finish) finish.disabled = busy;
}

function render() {
    renderVisual();
    const hotkey = creatorState.hotkey || 'F10';
    const walker = document.createTreeWalker(document.getElementById('content'), NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) walker.currentNode.textContent = walker.currentNode.textContent.replaceAll('F10', hotkey);
    document.querySelectorAll('.listen b').forEach(el => el.textContent = creatorState.running ? 'Nasłuch aktywny' : 'Nasłuch wyłączony');
    if (isScanStage()) document.getElementById('nextBtn').textContent = 'Czekam na skan';
    if (stages[index].type === 'skillsIntro') {
        const instruction = document.querySelector('.instruction p');
        if (instruction) instruction.textContent = 'Przed skanowaniem przełącz w grze na zestaw broni I. Następnie otwórz T i pokaż kolejno każde z trzech drzewek.';
    }
    if (stages[index].type === 'stats' && creatorState.last_stat_scan?.character) {
        const hero = creatorState.last_stat_scan.character;
        const values = ['strength', 'dexterity', 'vitality', 'life', 'mana', 'level'];
        document.querySelectorAll('.stat b').forEach((node, i) => node.textContent = hero[values[i]] ?? '—');
    }
    updateControls();
}

async function configureStage() {
    const response = await fetch('/api/character-creator/stage', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({stage: stages[index].id})
    });
    const result = await response.json();
    if (!response.ok) throw Error(result.error);
    ready = true;
}

async function go(delta, skip = false) {
    if (changingStage || creatorState.busy) return false;
    const previous = index;
    changingStage = true;
    updateControls();
    if (stages[index].type === 'done' && delta > 0) index = 0;
    else index = Math.max(0, Math.min(stages.length - 1, index + delta));
    try {
        await configureStage();
        if (skip) skipped.add(stages[previous].id);
        if (previous === stages.length - 1 && index === 0) {
            skipped.clear(); completed.clear(); invScanned.clear(); inventoryAnimationIndex = 0;
        }
        statusLine.textContent = creatorState.character ? 'Postać: ' + creatorState.character : 'Zeskanuj statystyki postaci.';
        render();
        window.scrollTo({top: 0, behavior: 'smooth'});
        return true;
    } catch (error) {
        index = previous;
        statusLine.textContent = error.message;
        return false;
    } finally { changingStage = false; updateControls(); }
}

document.getElementById('nextBtn').onclick = () => go(1);
document.getElementById('backBtn').onclick = () => go(-1);
document.getElementById('skipBtn').onclick = () => go(1, true);

async function pollCreator() {
    try {
        const response = await fetch('/api/companion/state');
        if (!response.ok) throw Error('Nie można odczytać stanu aplikacji.');
        const state = await response.json();
        const initial = !ready;
        creatorState = state;
        (state.skill_trees || []).forEach((tree, i) => { if (trees[i]) trees[i].name = tree.name_pl; });
        if (initial) {
            lastRequest = state.creator_activity?.request_id || '';
            lastKey = state.creator_key?.timestamp || 0;
            await configureStage();
            render();
        }
        updateControls();
        const activity = state.creator_activity || state.activity || {};
        if (state.busy) statusLine.textContent = state.activity?.message || 'Trwa skanowanie…';
        if (!changingStage && !state.busy && ['success', 'error', 'rejected', 'review'].includes(activity.state) && activity.request_id && activity.request_id !== lastRequest) {
            if (activity.creator_stage === stages[index].id) {
                statusLine.textContent = activity.message || '';
                if (activity.state === 'success') {
                    if (stages[index].type === 'inventoryScan') {
                        invScanned.add(activity.request_id);
                        inventoryAnimationIndex = (inventoryAnimationIndex + 1) % inventoryItems.length;
                        render();
                        lastRequest = activity.request_id;
                    } else if (isScanStage()) {
                        if (stages[index].type === 'tree') {
                            const scanned = new Set(state.skill_scan_pages || []);
                            const missing = [1, 2, 3].find(page => !scanned.has(page));
                            const target = missing ? stages.findIndex(stage => stage.id === 'tree:' + (missing - 1)) : stages.length - 1;
                            if (await go(target - index)) lastRequest = activity.request_id;
                            return;
                        }
                        completed.add(stages[index].id);
                        skipped.delete(stages[index].id);
                        if (await go(1)) lastRequest = activity.request_id;
                    }
                } else lastRequest = activity.request_id;
            } else lastRequest = activity.request_id;
        }
        const key = state.creator_key;
        if (key && key.timestamp !== lastKey) {
            lastKey = key.timestamp;
            const expected = {charIntro: 'I', 'char:swap': 'W', skillsIntro: 'T'}[stages[index].id];
            if (key.stage === stages[index].id && key.key === expected && !state.busy && !changingStage) await go(1);
        }
    } catch (error) { statusLine.textContent = error.message; }
    finally { setTimeout(pollCreator, 400); }
}
render();
pollCreator();
