(() => {
  const isExport = Boolean(window.SKILL_EXPORT);
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
  panel?.classList.remove('skill-editing');
  edit?.addEventListener('click', () => {
    editing = !editing;
    panel?.classList.toggle('skill-editing', editing);
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
    if (changed) { dirty = true; if (status) status.textContent = en ? 'Unsaved changes' : 'Niezapisane zmiany'; }
    for (const node of nodes) {
      const value = points[node.dataset.skill] || 0, max = Number(node.dataset.max);
      const out = node.querySelector('output');
      if (out) out.textContent = `${value} / ${max}`;
      const calculated = plan.bonuses?.[gearMode]?.[node.dataset.skill] || {value:0, direct:0, sources:[]};
      const overridden = Object.hasOwn(overrides[gearMode] || {}, node.dataset.skill);
      const bonus = {...calculated, value:overridden ? overrides[gearMode][node.dataset.skill] : calculated.value};
      const hardInput = node.querySelector('.skill-hard-input');
      if (hardInput) hardInput.value = value;
      const bonusInput = node.querySelector('.skill-bonus-input');
      if (bonusInput) bonusInput.value = bonus.value;
      const autoBtn = node.querySelector('.skill-auto-bonus');
      if (autoBtn) autoBtn.disabled = !overridden;
      const bonusElement = node.querySelector('.skill-item-bonus');
      if (bonusElement) {
        bonusElement.textContent = bonus.value ? `+${bonus.value}` : '';
        bonusElement.title = overridden ? (en ? 'Manual / scanned bonus' : 'Bonus ręczny / ze skanu') : bonus.sources.join('\n');
      }
      const effective = overridden || value > 0 || bonus.direct > 0 ? value + bonus.value : 0;
      const effLevel = node.querySelector('.skill-effective-level');
      if (effLevel) effLevel.textContent = `${en ? 'Level' : 'Poziom'} ${effective}`;
      let breakdown = node.querySelector('.skill-breakdown');
      const tooltip = node.querySelector('.skill-tooltip');
      if (!breakdown && tooltip) { breakdown = document.createElement('p'); breakdown.className = 'skill-breakdown'; tooltip.append(breakdown); }
      if (breakdown) {
        breakdown.textContent = `${en ? 'Allocated' : 'Wpisane'}: ${value} · ${en ? 'Items' : 'Przedmioty'}: +${bonus.value} · ${en ? 'Effective level' : 'Poziom łączny'}: ${effective}` + (value === 0 && bonus.direct === 0 ? (en ? ' (not learned)' : ' (nieodblokowana)') : '') + (bonus.sources.length ? '\n' + bonus.sources.join('\n') : '');
        if (overridden) breakdown.textContent = `${en ? 'Hard points' : 'Wbite'}: ${value} · ${en ? 'Items (manual / scan)' : 'Z itemów (ręcznie / skan)'}: +${bonus.value} · ${en ? 'Total' : 'Łącznie'}: ${effective}\n${en ? 'Calculated from equipment' : 'Obliczone z ekwipunku'}: +${calculated.value}`;
      }
      node.classList.toggle('allocated', value > 0);
      const btnDec = node.querySelector('[data-delta="-1"]');
      if (btnDec) btnDec.disabled = value === 0;
      const btnInc = node.querySelector('[data-delta="1"]');
      if (btnInc) btnInc.disabled = value === max;
    }
    const totalEl = document.getElementById('skill-total');
    if (totalEl) totalEl.textContent = Object.values(points).reduce((a,b) => a+b, 0);
    const summary = document.getElementById('skill-summary');
    if (summary) {
      const total = Object.values(points).reduce((a,b) => a+b, 0);
      const levelPoints = Math.max(0, (Number(plan.level) || 1) - 1);
      const learned = plan.skills.filter(skill => (points[skill.uid] || 0) > 0).length;
      const levels = nodes.map(node => Number(node.querySelector('.skill-effective-level')?.textContent.match(/\d+/)?.[0]) || 0);
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
    if (save) save.disabled = !dirty;
    const gearLabel = document.getElementById('skill-gear-label');
    if (gearLabel) gearLabel.textContent = en ? `Item bonuses: ${gearMode === 'swap' ? 'weapon swap' : 'main equipment'}` : `Bonusy z przedmiotów: ${gearMode === 'swap' ? 'zestaw zamienny' : 'zestaw główny'}`;
  }
  function playClickSound() {
    try {
      const audio = document.getElementById('sfxGem');
      if (audio) { audio.currentTime = 0; audio.play().catch(() => {}); }
    } catch (_) {}
  }
  if (!isExport) {
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
    document.getElementById('skill-reset')?.addEventListener('click', () => { points = {}; overrides = {}; render(true); });
  } else {
    for (const node of nodes) {
      const hoverEl = node.querySelector('.skill-hover');
      if (hoverEl) {
        hoverEl.setAttribute('role', 'region');
        hoverEl.setAttribute('tabindex', '0');
      }
    }
  }
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
  document.getElementById('skill-market-export')?.addEventListener('click', () => {
    const equipment = [...document.querySelectorAll('.uber-gear-view')].map(group => {
      const items = [...group.querySelectorAll('article[data-item]')].map(element => {
        const item = JSON.parse(element.dataset.item);
        return `${item.name || item.base || ''}\n${(item.stats || []).map(stat => typeof stat === 'string' ? stat : JSON.stringify(stat)).join('\n')}`;
      });
      return `${group.id.replace('gear-', '')}:\n${items.join('\n\n')}`;
    }).join('\n\n');
    const build = {title: `${plan.character} — ${plan.class.name_en}`, class_name: plan.class.slug,
      level: Number(plan.level) || 1, description: equipment.slice(0, 8000),
      skills: plan.skills.filter(skill => Number(points[skill.uid]) > 0).map(skill => ({name:skill.name, points:Number(points[skill.uid])}))};
    const url = URL.createObjectURL(new Blob([JSON.stringify(build, null, 2)], {type:'application/json'}));
    const link = document.createElement('a');
    link.href = url; link.download = `${plan.character.replace(/[^\p{L}\p{N}_-]/gu, '_')}-market-build.json`;
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = en ? 'Upload the JSON file on Market → Builds → Share build.' : 'Wgraj plik JSON w Markecie → Buildy → Udostępnij build.';
  });

  const buildStandaloneHtml = async () => {
    const root = document.querySelector('.uber-character');
    const copy = root.cloneNode(true);
    copy.querySelectorAll('.uber-properties').forEach(details => details.open = false);
    copy.querySelectorAll('script').forEach(script => script.remove());
    copy.querySelectorAll('*').forEach(element => {
      [...element.attributes].filter(attr => attr.name.startsWith('on')).forEach(attr => element.removeAttribute(attr.name));
    });

    // Strip edit UI and controls from DOM clone for read-only view
    copy.querySelectorAll('.skill-edit-values').forEach(el => el.remove());
    copy.querySelectorAll('.skill-counter button, [data-delta]').forEach(el => el.remove());
    copy.querySelectorAll('#skill-edit, #skill-save, #skill-recalculate, #skill-reset, #skill-export, #skill-market-api-export, #skill-status, #buildMarketModal').forEach(el => el.remove());
    copy.querySelectorAll('.uber-sheet button, .uber-sheet .btn-d2').forEach(el => el.remove());
    copy.querySelectorAll('button.uber-item-title').forEach(btn => {
      const span = document.createElement('span');
      span.className = btn.className;
      span.textContent = btn.textContent;
      btn.replaceWith(span);
    });
    copy.querySelectorAll('button.uber-slot').forEach(btn => {
      const div = document.createElement('div');
      div.className = btn.className;
      div.innerHTML = btn.innerHTML;
      [...btn.attributes].forEach(attr => {
        if (!attr.name.startsWith('on') && attr.name !== 'type') {
          div.setAttribute(attr.name, attr.value);
        }
      });
      btn.replaceWith(div);
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

    const equipmentText = [...document.querySelectorAll('.uber-gear-view')].map(group => {
      const items = [...group.querySelectorAll('article[data-item]')].map(element => {
        const item = JSON.parse(element.dataset.item);
        return `${item.name || item.base || ''}\n${(item.stats || []).map(stat => typeof stat === 'string' ? stat : JSON.stringify(stat)).join('\n')}`;
      });
      return `${group.id.replace('gear-', '')}:\n${items.join('\n\n')}`;
    }).join('\n\n');

    const allocatedSkills = plan.skills
      .filter(skill => Number(points[skill.uid]) > 0)
      .map(skill => ({name: skill.name, points: Number(points[skill.uid])}));

    const exportedPlan = {
      ...plan,
      points: {...points},
      overrides,
      gearMode,
      description: equipmentText.slice(0, 8000),
      skills_allocated: allocatedSkills
    };

    const doc = document.implementation.createHTMLDocument(`${plan.character} — build`);
    doc.documentElement.lang = en ? 'en' : 'pl';
    const meta = doc.createElement('meta');
    meta.name = 'viewport'; meta.content = 'width=device-width, initial-scale=1'; doc.head.append(meta);
    const style = doc.createElement('style');
    style.textContent = styles + '\n' +
      'body{margin:0;padding:24px;background:#0c0f0d;color:#d5d0bb} .uber-character{max-width:none}\n' +
      '.skill-counter button, [data-delta], .skill-edit-values, .skill-auto-bonus, #skill-edit, #skill-save, #skill-recalculate, #skill-reset, #skill-export, #skill-market-api-export, #skill-status, #buildMarketModal, .uber-sheet button, .uber-sheet .btn-d2 { display: none !important; }\n' +
      '.skill-counter { justify-content: center !important; text-align: center; }\n' +
      '.skill-counter output { font-weight: 700; color: #ffd27d; font-size: 0.95rem; }\n' +
      '.skill-node { cursor: default !important; }\n' +
      '.skill-hover { cursor: help !important; }\n' +
      '.uber-slot { cursor: default !important; }\n' +
      '.uber-slot[data-item], .uber-charms button[data-item], .uber-properties article[data-item] { cursor: help !important; }\n' +
      '.uber-slot[data-item]:hover { border-color: #ffd27d !important; box-shadow: 0 0 10px rgba(255, 210, 125, 0.4) !important; }\n' +
      '.uber-item-title { cursor: default !important; color: inherit; font-size: inherit; font-weight: inherit; }\n' +
      '.skill-toolbar { display: flex; justify-content: center !important; align-items: center; padding: 12px 0; }\n' +
      '.skill-toolbar strong { font-size: 1.05rem; color: #ffd27d; }\n' +
      '#d2ItemTooltip { position: fixed; z-index: 9999999; pointer-events: none; display: none; background: rgba(8, 8, 10, 0.97); border: 2px solid #5a4b2c; box-shadow: 0 0 0 1px #111, inset 0 0 0 1px #221c11, 0 10px 30px rgba(0,0,0,0.95); padding: 14px 18px; border-radius: 4px; min-width: 260px; max-width: 440px; text-align: center; line-height: 1.45; font-family: "Cinzel", Georgia, serif; box-sizing: border-box; }\n' +
      '.tt-name { font-size: 1.15rem; font-weight: 700; letter-spacing: 1px; margin-bottom: 2px; }\n' +
      '.tt-base { font-size: 0.88rem; color: #dcdcdc; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }\n' +
      '.tt-runes { font-size: 0.95rem; color: #ff8c00; font-weight: 700; letter-spacing: 1px; margin-bottom: 6px; }\n' +
      '.tt-divider { height: 1px; background: linear-gradient(90deg, transparent, #705820, transparent); margin: 6px 0; }\n' +
      '.tt-base-stats { font-size: 0.85rem; color: #dcdcdc; font-family: "Exo 2", "Segoe UI", Tahoma, sans-serif; margin-bottom: 6px; }\n' +
      '.tt-affixes { font-size: 0.88rem; color: #4a8bf5; font-family: "Exo 2", "Segoe UI", Tahoma, sans-serif; font-weight: 600; text-align: center; }\n' +
      '.tt-affix-line { margin: 3px 0; }\n' +
      '.badge-rating { font-size: 0.72rem; padding: 1px 5px; border-radius: 3px; margin-left: 4px; font-weight: 700; display: inline-block; vertical-align: middle; }\n' +
      '.badge-rating.rating-perf { background: #5a3d00; color: #ffd700; border: 1px solid #ffd700; }\n' +
      '.badge-rating.rating-high { background: #1b3d1b; color: #7cfc00; border: 1px solid #7cfc00; }\n' +
      '.badge-rating.rating-mid { background: #1c2a38; color: #87ceeb; border: 1px solid #87ceeb; }\n' +
      '.badge-rating.rating-low { background: #3a2222; color: #ff7f7f; border: 1px solid #ff7f7f; }\n' +
      '.unikalny, .unique, .tt-quality-unikalny, .tt-quality-unique, .quality-unikalny, .quality-unique, .q-unikalny, .q-unique { color: #b89958 !important; }\n' +
      '.zestaw, .set, .tt-quality-zestaw, .tt-quality-set, .quality-zestaw, .quality-set, .q-zestaw, .q-set { color: #00ff00 !important; }\n' +
      '.rzadki, .rare, .tt-quality-rzadki, .tt-quality-rare, .quality-rzadki, .quality-rare, .q-rzadki, .q-rare { color: #ffff66 !important; }\n' +
      '.magiczny, .magic, .tt-quality-magiczny, .tt-quality-magic, .quality-magiczny, .quality-magic, .q-magiczny, .q-magic { color: #4a8bf5 !important; }\n' +
      '.runiczne, .runeword, .tt-quality-runiczne, .tt-quality-runeword, .quality-runiczne, .quality-runeword, .q-runiczne, .q-runeword { color: #ff8c00 !important; }\n' +
      '.rzemioslo, .crafted, .tt-quality-rzemioslo, .tt-quality-crafted, .quality-rzemioslo, .quality-crafted, .q-rzemioslo, .q-crafted { color: #ff8000 !important; }\n' +
      '.normalny, .normal, .superior, .tt-quality-normalny, .tt-quality-normal, .quality-normalny, .quality-normal, .q-normalny, .q-normal { color: #dcdcdc !important; }';
    doc.head.append(style);
    const logoResponse = await fetch('/static/images/uberapp.png');
    if (!logoResponse.ok) throw new Error('Logo export failed');
    const header = doc.createElement('header'); header.className = 'build-export-header';
    const logo = doc.createElement('img'); logo.src = await toDataURL(await logoResponse.blob()); logo.alt = 'D2 UberApp';
    const title = doc.createElement('h1'); title.textContent = `D2 UberApp · ${plan.character}`;
    header.append(logo, title); doc.body.append(header);
    doc.body.append(copy);
    const tooltipEl = doc.createElement('div');
    tooltipEl.id = 'd2ItemTooltip';
    doc.body.append(tooltipEl);
    const data = doc.createElement('script'); data.id = 'skill-plan-data'; data.type = 'application/json';
    data.textContent = JSON.stringify(exportedPlan).replace(/</g, '\\u003c'); doc.body.append(data);
    const runtime = doc.createElement('script');
    runtime.textContent = 'window.SKILL_EXPORT=true;\n' + script.replace(/<\/script/gi, '<\\/script'); doc.body.append(runtime);
    const gearRuntime = doc.createElement('script');
    gearRuntime.textContent = `
document.querySelectorAll('.uber-equipment [role=tab]').forEach(tab=>tab.addEventListener('click',()=>{
  document.querySelectorAll('.uber-equipment [role=tab]').forEach(t=>{
    const active=t===tab;
    t.classList.toggle('active',active);
    t.setAttribute('aria-selected',String(active));
    document.getElementById(t.getAttribute('aria-controls')).hidden=!active;
  });
}));

(function() {
  const tooltip = document.getElementById('d2ItemTooltip');
  if (!tooltip) return;

  function renderTooltip(item) {
    if (!item) return '';
    const q = (item.quality || 'normal').toLowerCase();
    const name = item.display_name || item.name || 'Przedmiot';
    const nameEn = (item.name_en && item.name_en !== item.name) ? ' (' + item.name_en + ')' : '';
    const base = item.base || '';

    let html = '<div class="tt-name quality-' + q + ' q-' + q + '">' + name + nameEn + '</div>';
    if (base) html += '<div class="tt-base">' + base + '</div>';

    if (q === 'runiczne' || q === 'runeword' || (item.rolls_eval && item.rolls_eval.some(r => r.property === 'runes'))) {
      const rf = item.rolls_eval?.find(r => r.property === 'runes')?.roll || '';
      if (rf) html += '<div class="tt-runes">\\'' + rf + '\\'</div>';
    }

    html += '<div class="tt-divider"></div>';

    const baseStats = [];
    if (item.defense) baseStats.push('Obrona: ' + item.defense);
    if (item.damage) baseStats.push('Obrażenia: ' + item.damage);
    if (item.level_req) baseStats.push('Wymagany poziom: ' + item.level_req);
    if (item.req_str) baseStats.push('Wymagana siła: ' + item.req_str);
    if (item.req_dex) baseStats.push('Wymagana zręczność: ' + item.req_dex);

    if (baseStats.length > 0) {
      html += '<div class="tt-base-stats">' + baseStats.join('<br>') + '</div><div class="tt-divider"></div>';
    }

    let stats = item.stats || [];
    if (typeof stats === 'string') {
      try { stats = JSON.parse(stats); } catch(e) { stats = [stats]; }
    }
    let rolls = item.rolls_eval || item.rolls || [];
    if (typeof rolls === 'string') {
      try { rolls = JSON.parse(rolls); } catch(e) { rolls = []; }
    }

    if (Array.isArray(stats) && stats.length > 0) {
      html += '<div class="tt-affixes">';
      stats.forEach(st => {
        const stText = typeof st === 'string' ? st : (st.text || JSON.stringify(st));
        let badge = '';
        if (Array.isArray(rolls)) {
          const matchRoll = rolls.find(r => r && r.property && stText.toLowerCase().includes(r.property.toLowerCase()));
          if (matchRoll && matchRoll.rating) {
            const rat = String(matchRoll.rating).toUpperCase();
            let badgeClass = 'rating-mid';
            if (rat.includes('PERF')) badgeClass = 'rating-perf';
            else if (rat.includes('HIGH')) badgeClass = 'rating-high';
            else if (rat.includes('LOW') || rat.includes('MIN')) badgeClass = 'rating-low';
            badge = '<span class="badge-rating ' + badgeClass + '">' + (matchRoll.actual || matchRoll.roll) + ' [' + matchRoll.min + '-' + matchRoll.max + '] • ' + rat + '</span>';
          }
        }
        html += '<div class="tt-affix-line">' + stText + ' ' + badge + '</div>';
      });
      html += '</div>';
    }

    if (item.sockets && item.sockets > 0) {
      html += '<div style="color:#4a8bf5; font-size:0.85rem; margin-top:4px; font-weight:600;">Gniazda (' + item.sockets + ')</div>';
    }

    return html;
  }

  function positionTooltip(e) {
    let x = e.clientX + 16;
    let y = e.clientY + 16;
    const ttW = tooltip.offsetWidth;
    const ttH = tooltip.offsetHeight;
    if (x + ttW > window.innerWidth - 12) x = e.clientX - ttW - 16;
    if (y + ttH > window.innerHeight - 12) y = window.innerHeight - ttH - 12;
    if (y < 10) y = 10;
    if (x < 10) x = 10;
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
  }

  document.querySelectorAll('[data-item]').forEach(el => {
    el.addEventListener('mouseenter', e => {
      const raw = el.getAttribute('data-item');
      if (raw) {
        try {
          const it = JSON.parse(raw);
          tooltip.innerHTML = renderTooltip(it);
          tooltip.style.display = 'block';
          positionTooltip(e);
        } catch(err) {}
      }
    });
    el.addEventListener('mousemove', e => {
      if (tooltip.style.display === 'block') positionTooltip(e);
    });
    el.addEventListener('mouseleave', () => {
      tooltip.style.display = 'none';
    });
  });
})();
`;
    doc.body.append(gearRuntime);

    const fullHtml = '<!doctype html>\n' + doc.documentElement.outerHTML;
    return { html: fullHtml, exportedPlan, equipmentText, allocatedSkills };
  };

  document.getElementById('skill-export')?.addEventListener('click', async () => {
    const button = document.getElementById('skill-export');
    button.disabled = true;
    try {
      const { html } = await buildStandaloneHtml();
      const blob = new Blob([html], {type:'text/html;charset=utf-8'});
      const url = URL.createObjectURL(blob), link = document.createElement('a');
      link.href = url; link.download = `${plan.character.replace(/[^\p{L}\p{N}_-]/gu, '_')}-build.html`;
      link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = en ? 'Build exported' : 'Build wyeksportowany';
    } catch { status.textContent = en ? 'Export failed. Try again.' : 'Eksport nie powiódł się. Spróbuj ponownie.'; }
    finally { button.disabled = false; }
  });

  const modal = document.getElementById('buildMarketModal');
  const modalClose = document.getElementById('buildMarketModalClose');
  const modalCancel = document.getElementById('buildMarketModalCancel');
  const modalSubmit = document.getElementById('buildMarketModalSubmit');
  const modalResult = document.getElementById('buildMarketModalResult');
  const serverInput = document.getElementById('buildMarketServerUrl');
  const tokenInput = document.getElementById('buildMarketApiToken');
  const userInput = document.getElementById('buildMarketUsername');
  const passInput = document.getElementById('buildMarketPassword');

  const openBuildMarketModal = () => {
    if (!modal) return;
    let savedUrl = localStorage.getItem('d2_market_url') || 'https://market.d2app.xyz';
    if (savedUrl.includes('d2uberappmarket.tw5.org')) {
      savedUrl = 'https://market.d2app.xyz';
      localStorage.setItem('d2_market_url', savedUrl);
    }
    if (serverInput) serverInput.value = savedUrl;
    if (tokenInput) tokenInput.value = localStorage.getItem('d2_market_token') || '';
    if (userInput) userInput.value = localStorage.getItem('d2_market_user') || '';
    if (passInput) passInput.value = '';
    if (modalResult) { modalResult.style.display = 'none'; modalResult.innerHTML = ''; }
    modal.style.display = 'flex';
  };

  const closeBuildMarketModal = () => {
    if (modal) modal.style.display = 'none';
  };

  document.getElementById('skill-market-api-export')?.addEventListener('click', openBuildMarketModal);
  modalClose?.addEventListener('click', closeBuildMarketModal);
  modalCancel?.addEventListener('click', closeBuildMarketModal);

  modalSubmit?.addEventListener('click', async () => {
    const serverUrl = (serverInput?.value || 'https://market.d2app.xyz').trim();
    const apiToken = (tokenInput?.value || '').trim();
    const username = (userInput?.value || '').trim();
    const password = passInput?.value || '';

    if (!serverUrl) {
      if (modalResult) {
        modalResult.style.display = 'block';
        modalResult.style.background = '#381212';
        modalResult.style.color = '#ff9d9d';
        modalResult.style.border = '1px solid #7a2626';
        modalResult.textContent = en ? 'Provide Market Server URL.' : 'Podaj adres serwera marketu.';
      }
      return;
    }

    if (!apiToken && (!username || !password)) {
      if (modalResult) {
        modalResult.style.display = 'block';
        modalResult.style.background = '#381212';
        modalResult.style.color = '#ff9d9d';
        modalResult.style.border = '1px solid #7a2626';
        modalResult.textContent = en ? 'Provide API Token or Username and Password.' : 'Podaj Token API lub Login i Hasło.';
      }
      return;
    }

    localStorage.setItem('d2_market_url', serverUrl);
    if (apiToken) localStorage.setItem('d2_market_token', apiToken);
    if (username) localStorage.setItem('d2_market_user', username);

    modalSubmit.disabled = true;
    if (modalResult) {
      modalResult.style.display = 'block';
      modalResult.style.background = '#1a1e2b';
      modalResult.style.color = '#ffd27d';
      modalResult.style.border = '1px solid #3d4a66';
      modalResult.textContent = en ? 'Generating HTML view and publishing to Market...' : 'Generowanie widoku HTML i publikowanie na markecie...';
    }

    try {
      const { html, equipmentText, allocatedSkills } = await buildStandaloneHtml();
      const res = await fetch('/api/build/online_sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          server_url: serverUrl,
          api_token: apiToken,
          username: username,
          password: password,
          html_content: html,
          title: `${plan.character} — ${plan.class.name_en}`,
          class_name: plan.class.slug,
          level: Number(plan.level) || 1,
          description: equipmentText.slice(0, 8000),
          skills: allocatedSkills
        })
      });

      const data = await res.json();
      if (!res.ok || data.status === 'error') {
        throw new Error(data.error || (en ? 'Publish failed' : 'Błąd publikacji'));
      }

      const buildUrl = (data.server_url || serverUrl).replace(/\/$/, '') + (data.url || `/builds/${data.id}`);
      const linkHtml = `<a href="${buildUrl}" target="_blank" style="color:#ffd27d;text-decoration:underline;font-weight:700;">` +
        (en ? 'View build online →' : 'Otwórz build online na markecie →') + '</a>';

      if (modalResult) {
        modalResult.style.background = '#162e19';
        modalResult.style.color = '#8cf29c';
        modalResult.style.border = '1px solid #2b6e32';
        modalResult.innerHTML = (en ? 'Build published successfully! ' : 'Build został pomyślnie opublikowany! ') + linkHtml;
      }
      status.innerHTML = (en ? 'Build published online: ' : 'Build opublikowany online: ') + linkHtml;
    } catch (err) {
      if (modalResult) {
        modalResult.style.background = '#381212';
        modalResult.style.color = '#ff9d9d';
        modalResult.style.border = '1px solid #7a2626';
        modalResult.textContent = (en ? 'Export failed: ' : 'Błąd eksportu: ') + (err.message || err);
      }
      status.textContent = (en ? 'Export failed: ' : 'Błąd eksportu: ') + (err.message || err);
    } finally {
      modalSubmit.disabled = false;
    }
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
    document.querySelectorAll('[data-delta], .skill-edit-values, #skill-edit, #skill-save, #skill-reset, #skill-export, #skill-market-api-export, #skill-recalculate, #buildMarketModal, .uber-sheet button').forEach(button => button.hidden = true);
    status.textContent = en ? 'Exported build' : 'Wyeksportowany build';
  }
})();
