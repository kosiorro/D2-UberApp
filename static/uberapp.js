function uberSetGear(key) {
  document.querySelectorAll('.uber-gear-view').forEach(el => el.hidden = el.id !== 'gear-'+key);
  document.querySelectorAll('.uber-equipment .uber-tabs button').forEach(el => {const active=el.id==='tab-'+key;el.classList.toggle('active',active);el.setAttribute('aria-selected',String(active));});
}
let uberTradeItem = null;
async function uberTradeOptions(id) {
  try {
    const response=await fetch('/api/trade/details/'+encodeURIComponent(id));
    const data=await response.json();if(!response.ok)throw new Error(data.error);
    uberTradeItem=id;
    for(const key of ['item_alias','base_alias','socket_contents','trade_stats'])document.getElementById('uber-'+key).value=data[key]||'';
    
    // Suggestion chip
    const suggEl=document.getElementById('uber-item-suggestion');
    if(suggEl){
      if(data.colloquial_suggestion||data.catalog_shorthand){
        suggEl.hidden=false;
        const labelSugg = window.APP_LANG === 'en' ? 'Suggested catalog shorthand:' : 'Sugerowany skrót katalogu:';
        suggEl.innerHTML=`<div style="font-size:0.8rem;color:#bbb;margin-top:3px;margin-bottom:8px;">${labelSugg} <button type="button" class="btn-d2 btn-stone btn-sm" style="padding:2px 8px;font-size:0.75rem;" onclick="document.getElementById('uber-item_alias').value='${data.colloquial_suggestion}'">${data.colloquial_suggestion}</button> ${data.catalog_shorthand?`<span style="color:#888;">(${data.catalog_shorthand})</span>`:''}</div>`;
      }else{suggEl.hidden=true;suggEl.innerHTML='';}
    }

    // Roll selection checkboxes
    const rollsContainer=document.getElementById('uber-rolls-selection');
    if(rollsContainer){
      if(data.rolls_eval&&data.rolls_eval.length>0){
        rollsContainer.hidden=false;
        const sel=new Set(data.selected_rolls&&data.selected_rolls.length?data.selected_rolls:data.rolls_eval.map(r=>r.property||r.property_pl||r.label));
        const labelChoose = window.APP_LANG === 'en' ? 'Select variables for offer:' : 'Wybierz zmienne do oferty:';
        const labelAll = window.APP_LANG === 'en' ? 'All' : 'Wszystkie';
        const labelNone = window.APP_LANG === 'en' ? 'None' : 'Żadne';
        rollsContainer.innerHTML=`
          <div style="font-size:0.85rem;font-weight:700;color:#ffd27d;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">
            <span>${labelChoose}</span>
            <span style="font-size:0.75rem;">
              <a href="javascript:void(0)" onclick="uberToggleAllRolls(true)" style="color:#d4af37;margin-right:8px;text-decoration:underline;">${labelAll}</a>
              <a href="javascript:void(0)" onclick="uberToggleAllRolls(false)" style="color:#888;text-decoration:underline;">${labelNone}</a>
            </span>
          </div>
          <div style="display:flex;flex-direction:column;gap:5px;max-height:160px;overflow-y:auto;background:rgba(0,0,0,0.35);padding:8px;border-radius:4px;border:1px solid #332a1e;margin-bottom:10px;">
            ${data.rolls_eval.map(r=>{
              const key=r.property||r.property_pl||r.label;
              const checked=sel.has(key)?'checked':'';
              const label=r.shorthand||`${(window.APP_LANG === 'en' && r.property) ? r.property : (r.label||key)}: ${r.actual??r.roll}`;
              return `<label style="display:flex;align-items:center;gap:8px;font-size:0.82rem;color:#ddd;cursor:pointer;">
                <input type="checkbox" class="uber-roll-chk" data-roll-key="${key}" ${checked} style="accent-color:#d4af37;width:15px;height:15px;cursor:pointer;">
                <span><strong>${label}</strong> ${r.min&&r.max&&r.min!==r.max?`<span style="color:#888;">(${r.min}-${r.max})</span>`:''}</span>
              </label>`;
            }).join('')}
          </div>
        `;
      }else{
        rollsContainer.hidden=true;rollsContainer.innerHTML='';
      }
    }

    document.getElementById('uber-trade-options').classList.add('active');
    document.getElementById('uber-item_alias').focus();
  } catch(error){alert(error.message);}
}
function uberToggleAllRolls(checked){
  document.querySelectorAll('.uber-roll-chk').forEach(c=>c.checked=checked);
}
async function uberSaveTradeOptions(event) {
  event.preventDefault();const data={};
  for(const key of ['item_alias','base_alias','socket_contents','trade_stats'])data[key]=document.getElementById('uber-'+key).value;
  const selected_rolls=[];
  document.querySelectorAll('.uber-roll-chk:checked').forEach(chk=>selected_rolls.push(chk.dataset.rollKey));
  data.selected_rolls=selected_rolls;
  try {
    const response=await fetch('/api/trade/details/'+encodeURIComponent(uberTradeItem),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    if(!response.ok)throw new Error(window.APP_LANG === 'en' ? 'Could not save options. Please try again.' : 'Nie zapisano opcji. Spróbuj ponownie.');
    document.getElementById('uber-trade-options').classList.remove('active');
  }catch(error){alert(error.message);}
}
document.addEventListener('keydown',event=>{if(event.key==='Escape')document.getElementById('uber-trade-options')?.classList.remove('active');});
async function openCharacterCreator() {
  try {
    const response = await fetch('/api/character-creator/open', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'});
    const result = await response.json();
    if (!response.ok) throw Error(result.error);
  } catch (error) { alert(error.message); }
}
