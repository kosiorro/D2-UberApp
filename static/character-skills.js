(() => {
  const source = document.getElementById('skill-plan-data');
  if (!source) return;
  const plan = JSON.parse(source.textContent);
  let points = {...plan.points}, dirty = false;
  let overrides = JSON.parse(JSON.stringify(plan.overrides || {}));
  const en = document.documentElement.lang === 'en' || window.APP_LANG === 'en';
  const status = document.getElementById('skill-status');
  const save = document.getElementById('skill-save');
  const nodes = [...document.querySelectorAll('[data-skill]')];
  const panel = document.querySelector('.skill-panel');
  const edit = document.getElementById('skill-edit');
  let editing = false;
  panel.classList.remove('skill-editing');
  edit.addEventListener('click', () => {
    editing = !editing;
    panel.classList.toggle('skill-editing', editing);
    edit.setAttribute('aria-expanded', String(editing));
    edit.textContent = editing ? (en ? 'Finish editing' : 'Zakończ edycję') : (en ? 'Edit' : 'Edytuj');
    drawConnections();
  });
  let gearMode = plan.gearMode || 'main';
  document.querySelectorAll('.uber-equipment [role="tab"]').forEach(tab => tab.addEventListener('click', () => {
    if (tab.id === 'tab-main' || tab.id === 'tab-swap') gearMode = tab.id.slice(4);
    render();
  }));
  function drawConnections() {
    document.querySelectorAll('.skill-game-grid').forEach(grid => {
      if (!grid.offsetWidth) return;
      grid.querySelector('svg')?.remove();
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.classList.add('skill-connections');
      svg.setAttribute('aria-hidden', 'true');
      const bounds = grid.getBoundingClientRect();
      svg.setAttribute('viewBox', `0 0 ${bounds.width} ${bounds.height}`);
      plan.skills.forEach(skill => {
        const target = grid.querySelector(`[data-game-id="${skill.game_id}"]`);
        if (!target) return;
        for (const id of skill.prerequisites || []) {
          const source = grid.querySelector(`[data-game-id="${id}"]`);
          if (!source) continue;
          const a = source.getBoundingClientRect(), b = target.getBoundingClientRect();
          const x1 = a.left+a.width/2-bounds.left, y1 = a.bottom-bounds.top;
          const x2 = b.left+b.width/2-bounds.left, y2 = b.top-bounds.top;
          const middle = (y1+y2)/2;
          const path = document.createElementNS(svg.namespaceURI, 'path');
          path.setAttribute('d', `M${x1},${y1} V${middle} H${x2} V${y2} m-4,-5 l4,5 l4,-5`);
          svg.append(path);
        }
      });
      grid.prepend(svg);
    });
  }
  window.addEventListener('resize', drawConnections);
  // Render outside the grid's stacking contexts so adjacent cards cannot cover it.
  const floatingTooltip = document.createElement('div');
  floatingTooltip.className = 'skill-tooltip skill-floating-tooltip';
  floatingTooltip.id = 'skill-floating-description';
  floatingTooltip.setAttribute('role', 'tooltip');
  floatingTooltip.hidden = true;
  document.body.append(floatingTooltip);
  let tooltipOwner = null;
  function hideTooltip() {
    if (tooltipOwner) tooltipOwner.setAttribute('aria-describedby', tooltipOwner.querySelector('.skill-tooltip').id);
    tooltipOwner = null;
    floatingTooltip.hidden = true;
  }
  function showTooltip(hover) {
    hideTooltip();
    tooltipOwner = hover;
    floatingTooltip.replaceChildren(...[...hover.querySelector('.skill-tooltip').childNodes].map(node => node.cloneNode(true)));
    hover.setAttribute('aria-describedby', floatingTooltip.id);
    floatingTooltip.hidden = false;
    const rect = hover.getBoundingClientRect();
    const above = rect.top - floatingTooltip.offsetHeight - 10;
    floatingTooltip.style.left = `${Math.max(12, Math.min(rect.left + rect.width / 2 - floatingTooltip.offsetWidth / 2, innerWidth - floatingTooltip.offsetWidth - 12))}px`;
    floatingTooltip.style.top = `${Math.max(12, Math.min(above >= 12 ? above : rect.bottom + 10, innerHeight - floatingTooltip.offsetHeight - 12))}px`;
  }
  document.querySelectorAll('.skill-hover').forEach(hover => {
    hover.addEventListener('mouseenter', () => showTooltip(hover));
    hover.addEventListener('focus', () => showTooltip(hover));
    hover.addEventListener('mouseleave', hideTooltip);
    hover.addEventListener('blur', hideTooltip);
  });
  window.addEventListener('scroll', hideTooltip, {passive:true, capture:true});
  window.addEventListener('resize', hideTooltip);
  document.addEventListener('keydown', event => { if (event.key === 'Escape') hideTooltip(); });
  const tabs = [...document.querySelectorAll('.skill-tabs [role="tab"]')];
  function selectTree(selected) {
    hideTooltip();
    for (const tab of tabs) {
      const active = tab === selected;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      document.getElementById(tab.getAttribute('aria-controls')).hidden = !active;
    }
    drawConnections();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectTree(tab));
    tab.addEventListener('keydown', event => {
      const next = {ArrowRight:(index+1)%tabs.length, ArrowLeft:(index+tabs.length-1)%tabs.length, Home:0, End:tabs.length-1}[event.key];
      if (next === undefined) return;
      event.preventDefault();
      selectTree(tabs[next]);
      tabs[next].focus();
    });
  });
  function render(changed = false) {
    if (changed) { dirty = true; status.textContent = en ? 'Unsaved changes' : 'Niezapisane zmiany'; }
    for (const node of nodes) {
      const value = points[node.dataset.skill] || 0, max = Number(node.dataset.max);
      node.querySelector('output').textContent = `${value} / ${max}`;
      const calculated = plan.bonuses?.[gearMode]?.[node.dataset.skill] || {value:0, direct:0, sources:[]};
      const overridden = Object.hasOwn(overrides[gearMode] || {}, node.dataset.skill);
      const bonus = {...calculated, value:overridden ? overrides[gearMode][node.dataset.skill] : calculated.value};
      node.querySelector('.skill-hard-input').value = value;
      node.querySelector('.skill-bonus-input').value = bonus.value;
      node.querySelector('.skill-auto-bonus').disabled = !overridden;
      const bonusElement = node.querySelector('.skill-item-bonus');
      bonusElement.textContent = bonus.value ? `+${bonus.value}` : '';
      bonusElement.title = overridden ? (en ? 'Manual / scanned bonus' : 'Bonus ręczny / ze skanu') : bonus.sources.join('\n');
      const effective = overridden || value > 0 || bonus.direct > 0 ? value + bonus.value : 0;
      node.querySelector('.skill-effective-level').textContent = `${en ? 'Level' : 'Poziom'} ${effective}`;
      let breakdown = node.querySelector('.skill-breakdown');
      if (!breakdown) { breakdown = document.createElement('p'); breakdown.className = 'skill-breakdown'; node.querySelector('.skill-tooltip').append(breakdown); }
      breakdown.textContent = `${en ? 'Allocated' : 'Wpisane'}: ${value} · ${en ? 'Items' : 'Przedmioty'}: +${bonus.value} · ${en ? 'Effective level' : 'Poziom łączny'}: ${effective}` + (value === 0 && bonus.direct === 0 ? (en ? ' (not learned)' : ' (nieodblokowana)') : '') + (bonus.sources.length ? '\n' + bonus.sources.join('\n') : '');
      if (overridden) breakdown.textContent = `${en ? 'Hard points' : 'Wbite'}: ${value} · ${en ? 'Items (manual / scan)' : 'Z itemów (ręcznie / skan)'}: +${bonus.value} · ${en ? 'Total' : 'Łącznie'}: ${effective}\n${en ? 'Calculated from equipment' : 'Obliczone z ekwipunku'}: +${calculated.value}`;
      node.classList.toggle('allocated', value > 0);
      node.querySelector('[data-delta="-1"]').disabled = value === 0;
      node.querySelector('[data-delta="1"]').disabled = value === max;
    }
    document.getElementById('skill-total').textContent = Object.values(points).reduce((a,b) => a+b, 0);
    const summary = document.getElementById('skill-summary');
    if (summary) {
      const total = Object.values(points).reduce((a,b) => a+b, 0);
      const levelPoints = Math.max(0, (Number(plan.level) || 1) - 1);
      const learned = plan.skills.filter(skill => (points[skill.uid] || 0) > 0).length;
      const levels = nodes.map(node => Number(node.querySelector('.skill-effective-level').textContent.match(/\d+/)?.[0]) || 0);
      const entries = [
        [en ? 'Allocated points' : 'Rozdane punkty', total],
        [en ? 'Learned skills' : 'Wyuczone umiejętności', learned + ' / ' + plan.skills.length],
        [en ? 'Highest skill level' : 'Najwyższy poziom skilla', Math.max(0, ...levels)],
        [en ? 'Points from level + quests' : 'Punkty z poziomu + questów', levelPoints + ' + 0–12'],
        [en ? 'Remaining (depending on quests)' : 'Pozostałe (zależnie od questów)', Math.max(0, levelPoints-total) + '–' + Math.max(0, levelPoints+12-total)]
      ];
      plan.class.trees.forEach(tree => {
        const sum = plan.skills.filter(skill => skill.tree.page === tree.page).reduce((acc, skill) => acc + (points[skill.uid] || 0), 0);
        entries.push([tree[en ? 'name_en' : 'name_pl'], sum + (en ? ' pts' : ' pkt')]);
      });
      summary.replaceChildren(...entries.map(([label, value]) => {
        const cell = document.createElement('div'), heading = document.createElement('span'), number = document.createElement('strong');
        heading.textContent = label; number.textContent = value; cell.append(heading, number); return cell;
      }));
      if (total > levelPoints + 12) {
        const warning = document.createElement('p'); warning.className = 'skill-budget-warning';
        warning.textContent = en ? 'The plan exceeds the point budget for this level.' : 'Plan przekracza limit punktów dla tego poziomu postaci.';
        summary.append(warning);
      }
    }
    save.disabled = !dirty;
    document.getElementById('skill-gear-label').textContent = en ? `Item bonuses: ${gearMode === 'swap' ? 'weapon swap' : 'main equipment'}` : `Bonusy z przedmiotów: ${gearMode === 'swap' ? 'zestaw zamienny' : 'zestaw główny'}`;
  }
  function playClickSound() {
    try {
      const audio = document.getElementById('sfxGem');
      if (audio) { audio.currentTime = 0; audio.play().catch(() => {}); }
    } catch (_) {}
  }
  for (const node of nodes) {
    node.addEventListener('click', event => {
      if (event.target.closest('.skill-auto-bonus')) {
        delete (overrides[gearMode] || {})[node.dataset.skill];
        render(true);
        return;
      }
      if (event.target.closest('.skill-hard-input, .skill-bonus-input')) return;
      const button = event.target.closest('[data-delta]');
      if (button) {
        points[node.dataset.skill] = Math.max(0, Math.min(Number(node.dataset.max), (points[node.dataset.skill] || 0) + Number(button.dataset.delta)));
        playClickSound();
        render(true);
        return;
      }
      // Kliknięcie w skill przełącza go (włącza / wyłącza)
      const current = points[node.dataset.skill] || 0;
      const max = Number(node.dataset.max) || 20;
      if (current > 0) {
        node.dataset.lastPoints = String(current);
        points[node.dataset.skill] = 0;
      } else {
        const restore = event.shiftKey ? max : (Number(node.dataset.lastPoints) || 1);
        points[node.dataset.skill] = Math.min(max, Math.max(1, restore));
      }
      playClickSound();
      render(true);
    });
    node.addEventListener('contextmenu', event => {
      if (event.target.closest('.skill-hard-input, .skill-bonus-input, .skill-auto-bonus')) return;
      event.preventDefault();
      const current = points[node.dataset.skill] || 0;
      if (current > 0) {
        points[node.dataset.skill] = Math.max(0, current - 1);
        playClickSound();
        render(true);
      }
    });
    const hoverEl = node.querySelector('.skill-hover');
    if (hoverEl) {
      hoverEl.setAttribute('role', 'button');
      hoverEl.setAttribute('tabindex', '0');
      hoverEl.addEventListener('keydown', event => {
        if (event.key === ' ' || event.key === 'Enter') {
          event.preventDefault();
          node.click();
        }
      });
    }
  }
  for (const node of nodes) node.addEventListener('change', event => {
    if (!event.target.matches('.skill-hard-input, .skill-bonus-input')) return;
    const value = Number(event.target.value);
    if (!event.target.value.trim() || !Number.isInteger(value) || !event.target.checkValidity()) { render(); return; }
    if (event.target.matches('.skill-hard-input')) points[node.dataset.skill] = value;
    else (overrides[gearMode] ||= {})[node.dataset.skill] = value;
    render(true);
  });
  document.getElementById('skill-reset').addEventListener('click', () => { points = {}; overrides = {}; render(true); });
  document.getElementById('skill-recalculate')?.addEventListener('click', async event => {
    const button = event.currentTarget; button.disabled = true;
    try {
      const response = await fetch('/api/character/skills?character=' + encodeURIComponent(plan.character));
      const current = await response.json();
      if (!response.ok) throw Error(current.error);
      if (current.class.slug !== plan.class.slug) throw Error(en ? 'Class changed. Reload the page.' : 'Klasa postaci zmieniła się. Odśwież stronę.');
      plan.bonuses = current.bonuses; plan.level = current.level;
      delete overrides[gearMode];
      render(true);
      status.textContent = en ? 'Bonuses recalculated. Save to keep the changes.' : 'Bonusy przeliczone. Zapisz, aby zachować zmiany.';
    } catch (error) { status.textContent = error.message; }
    finally { button.disabled = false; }
  });
  document.getElementById('skill-export').addEventListener('click', async () => {
    const button = document.getElementById('skill-export');
    button.disabled = true;
    try {
      const root = document.querySelector('.uber-character');
      const copy = root.cloneNode(true);
      copy.querySelectorAll('.uber-properties').forEach(details => details.open = false);
      copy.querySelectorAll('script').forEach(script => script.remove());
      copy.querySelectorAll('*').forEach(element => {
        [...element.attributes].filter(attr => attr.name.startsWith('on')).forEach(attr => element.removeAttribute(attr.name));
      });
      const toDataURL = blob => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
      await Promise.all([...copy.querySelectorAll('img')].map(async image => {
        const response = await fetch(image.src);
        if (!response.ok) throw new Error('Image export failed');
        image.src = await toDataURL(await response.blob());
        image.removeAttribute('loading');
      }));
      const styles = [...document.styleSheets].map(sheet => {
        try { return [...sheet.cssRules].map(rule => rule.cssText).join('\n'); }
        catch { return ''; }
      }).join('\n');
      const response = await fetch('/static/character-skills.js');
      if (!response.ok) throw new Error('Script export failed');
      const script = await response.text();
      const exportedPlan = {...plan, points:{...points}, overrides, gearMode};
      const doc = document.implementation.createHTMLDocument(`${plan.character} — build`);
      doc.documentElement.lang = en ? 'en' : 'pl';
      const meta = doc.createElement('meta');
      meta.name = 'viewport'; meta.content = 'width=device-width, initial-scale=1'; doc.head.append(meta);
      const style = doc.createElement('style');
      style.textContent = styles + '\nbody{margin:0;padding:24px;background:#0c0f0d;color:#d5d0bb} .uber-character{max-width:none}';
      doc.head.append(style);
      const logoResponse = await fetch('/static/images/uberapp.png');
      if (!logoResponse.ok) throw new Error('Logo export failed');
      const header = doc.createElement('header'); header.className = 'build-export-header';
      const logo = doc.createElement('img'); logo.src = await toDataURL(await logoResponse.blob()); logo.alt = 'D2 UberApp';
      const title = doc.createElement('h1'); title.textContent = `D2 UberApp · ${plan.character}`;
      header.append(logo, title); doc.body.append(header);
      doc.body.append(copy);
      const data = doc.createElement('script'); data.id = 'skill-plan-data'; data.type = 'application/json';
      data.textContent = JSON.stringify(exportedPlan).replace(/</g, '\\u003c'); doc.body.append(data);
      const runtime = doc.createElement('script');
      runtime.textContent = 'window.SKILL_EXPORT=true;\n' + script.replace(/<\/script/gi, '<\\/script'); doc.body.append(runtime);
      const gearRuntime = doc.createElement('script');
      gearRuntime.textContent = "document.querySelectorAll('.uber-equipment [role=tab]').forEach(tab=>tab.addEventListener('click',()=>{document.querySelectorAll('.uber-equipment [role=tab]').forEach(t=>{const active=t===tab;t.classList.toggle('active',active);t.setAttribute('aria-selected',String(active));document.getElementById(t.getAttribute('aria-controls')).hidden=!active;});}));";
      doc.body.append(gearRuntime);
      const blob = new Blob(['<!doctype html>\n', doc.documentElement.outerHTML], {type:'text/html;charset=utf-8'});
      const url = URL.createObjectURL(blob), link = document.createElement('a');
      link.href = url; link.download = `${plan.character.replace(/[^\p{L}\p{N}_-]/gu, '_')}-build.html`;
      link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = en ? 'Build exported' : 'Build wyeksportowany';
    } catch { status.textContent = en ? 'Export failed. Try again.' : 'Eksport nie powiódł się. Spróbuj ponownie.'; }
    finally { button.disabled = false; }
  });
  save.addEventListener('click', async () => {
    const snapshot = JSON.stringify({points, overrides});
    save.disabled = true;
    status.textContent = en ? 'Saving…' : 'Zapisywanie…';
    try {
      const response = await fetch('/api/character/skills', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({character:plan.character, class_slug:plan.class.slug, ...JSON.parse(snapshot)})});
      if (!response.ok) throw new Error();
      dirty = JSON.stringify({points, overrides}) !== snapshot;
      status.textContent = dirty ? (en ? 'Unsaved changes' : 'Niezapisane zmiany') : (en ? 'Saved' : 'Zapisano');
    } catch { status.textContent = en ? 'Save failed. Try again.' : 'Nie udało się zapisać. Spróbuj ponownie.'; }
    save.disabled = !dirty;
  });
  window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
  render();
  requestAnimationFrame(drawConnections);
  if (window.SKILL_EXPORT) {
    document.querySelectorAll('[data-delta], .skill-edit-values, #skill-edit, #skill-save, #skill-reset, #skill-export, #skill-recalculate, .uber-sheet button').forEach(button => button.hidden = true);
    status.textContent = en ? 'Exported build' : 'Wyeksportowany build';
  }
})();
