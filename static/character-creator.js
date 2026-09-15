
const charItems=[
  {id:"weapon1",label:"Broń I",name:"Broń – zestaw I",glyph:"│",board:"weapon",set:1},
  {id:"shield1",label:"Tarcza I",name:"Tarcza – zestaw I",glyph:"◈",board:"shield",set:1},
  {id:"swap",label:"Swap W",name:"Przełącz zestaw broni",glyph:"W"},
  {id:"weapon2",label:"Broń II",name:"Broń – zestaw II",glyph:"│",board:"weapon",set:2},
  {id:"shield2",label:"Tarcza II",name:"Tarcza – zestaw II",glyph:"◈",board:"shield",set:2},
  {id:"helm",label:"Hełm",name:"Hełm",glyph:"⌂",board:"helm"},
  {id:"amulet",label:"Amulet",name:"Amulet",glyph:"◇",board:"amulet"},
  {id:"armor",label:"Pancerz",name:"Pancerz",glyph:"▧",board:"armor"},
  {id:"gloves",label:"Rękawice",name:"Rękawice",glyph:"✥",board:"gloves"},
  {id:"ring1",label:"Pierścień L",name:"Pierścień – lewy",glyph:"○",board:"ring1"},
  {id:"belt",label:"Pas",name:"Pas",glyph:"═",board:"belt"},
  {id:"ring2",label:"Pierścień P",name:"Pierścień – prawy",glyph:"○",board:"ring2"},
  {id:"boots",label:"Buty",name:"Buty",glyph:"⌟",board:"boots"}
];

const inventoryItems=[
  {id:"inv1",name:"Przedmiot 1",glyph:"◆",x:0,y:0,w:2,h:3},
  {id:"inv2",name:"Przedmiot 2",glyph:"●",x:2,y:0,w:1,h:1},
  {id:"inv3",name:"Przedmiot 3",glyph:"✦",x:3,y:0,w:2,h:2},
  {id:"inv4",name:"Przedmiot 4",glyph:"▥",x:5,y:0,w:1,h:2},
  {id:"inv5",name:"Przedmiot 5",glyph:"◇",x:6,y:1,w:2,h:1},
  {id:"inv6",name:"Przedmiot 6",glyph:"✚",x:8,y:0,w:2,h:4}
];

const trees=[
  {name:"Drzewko 1",sub:"Drzewko 1"},
  {name:"Drzewko 2",sub:"Drzewko 2"},
  {name:"Drzewko 3",sub:"Drzewko 3"}
];

let index=0;
const skipped=new Set();
const invScanned=new Set();
let inventoryAnimationIndex=0;
let inventoryAnimationTimer=null;

function mercSlots(){
  return [
    {id:"mhelm",name:"Hełm",glyph:"⌂",board:"mHelm"},
    {id:"marmor",name:"Zbroja",glyph:"▧",board:"mArmor"},
    {id:"mleft",name:"Broń / broń 2H",glyph:"│",board:"mLeft"},
    {id:"mright",name:"Tarcza / druga broń",glyph:"◈",board:"mRight"}
  ];
}

function buildStages(){
  return [
    {id:"stats",type:"stats",phase:"stats",title:"Statystyki postaci"},
    {id:"charIntro",type:"charIntro",phase:"character",title:"Ekwipunek postaci – przygotowanie"},
    ...charItems.map(x=>({id:"char:"+x.id,type:"char",phase:"character",title:x.name,item:x})),
    {id:"inventoryScan",type:"inventoryScan",phase:"character",title:"Ekwipunek osobisty – skanowanie"},
    {id:"mercIntro",type:"mercIntro",phase:"merc",title:"Najemnik – wyposażenie"},
    ...mercSlots().map(x=>({id:"merc:"+x.id,type:"mercItem",phase:"merc",title:x.name,item:x})),
    {id:"skillsIntro",type:"skillsIntro",phase:"skills",title:"Umiejętności – przygotowanie"},
    {id:"tree:0",type:"tree",phase:"skills",title:trees[0].name,tree:0},
    {id:"tree:1",type:"tree",phase:"skills",title:trees[1].name,tree:1},
    {id:"tree:2",type:"tree",phase:"skills",title:trees[2].name,tree:2},
    {id:"done",type:"done",phase:"done",title:"Gotowe"}
  ];
}
let stages=buildStages();


function card(kicker,title,desc,icon,inner){
  return `<section class="card"><div class="cardTop"><div class="cardIcon">${icon}</div><div class="cardTitle">
    <div class="kicker">${kicker}</div><h2>${title}</h2><p>${desc}</p></div></div>${inner}</section>`;
}

function setPhase(){
  const order=["stats","character","merc","skills"], current=order.indexOf(stages[index].phase);
  order.forEach((p,i)=>{
    const el=document.getElementById("phase-"+p);
    el.classList.toggle("active",i===current);
    el.classList.toggle("done",current>i || stages[index].phase==="done");
  });
}

function stateById(stageId){
  const pos=stages.findIndex(s=>s.id===stageId);
  if(skipped.has(stageId)) return "skipped";
  if(pos<index) return "done";
  if(pos===index) return "active";
  return "";
}

function charBoard(activeId="",showSwap=false,activeSet=1){
  const defs=[
    ["weapon","Broń",activeId==="weapon1"?"char:weapon1":activeId==="weapon2"?"char:weapon2":""],
    ["shield","Tarcza",activeId==="shield1"?"char:shield1":activeId==="shield2"?"char:shield2":""],
    ["helm","Hełm","char:helm"],["amulet","Amulet","char:amulet"],["armor","Pancerz","char:armor"],
    ["gloves","Rękawice","char:gloves"],["ring1","Pierścień L","char:ring1"],["belt","Pas","char:belt"],["ring2","Pierścień P","char:ring2"],["boots","Buty","char:boots"]
  ];
  const glyph={weapon:"│",shield:"◈",helm:"⌂",amulet:"◇",armor:"▧",gloves:"✥",ring1:"○",belt:"═",ring2:"○",boots:"⌟"};
  return `<div class="eqBoard">
    <div class="setBadge"><span class="${activeSet===1?"on":""}">I</span><span class="${activeSet===2?"on":""}">II</span></div>
    <div class="centerSigil"></div>
    ${defs.map(([cls,name,id])=>{
      let st=id?stateById(id):"";
      const currentItem=charItems.find(x=>x.id===activeId);
      if(currentItem && currentItem.board===cls) st="active";
      return `<div class="eSlot ${cls} ${st}" data-name="${name}"><div class="itemGlyph">${glyph[cls]}</div></div>`;
    }).join("")}
    ${showSwap?`<div class="swapNote"><div class="w">W</div><b>Przełącz zestaw broni</b><small>Po swapie przechodzimy do zestawu II.</small></div>`:""}
  </div>`;
}

function charList(){
  return `<div class="scanList">${charItems.filter(x=>x.id!=="swap").map(x=>{
    const st=stateById("char:"+x.id);
    return `<div class="scanItem ${st}"><span class="mini">${x.glyph}</span><span>${x.label}</span>
      <span class="statusPill">${st==="done"?"✓":st==="skipped"?"POMINIĘTO":st==="active"?"TERAZ":""}</span></div>`;
  }).join("")}</div>`;
}

function inventoryBoard(){
  return `<div class="inventoryFrame scanning">
    <div class="inventoryTitle">EKWIPUNEK OSOBISTY · SKANOWANIE CIĄGŁE</div>
    <div class="inventoryCanvas">
      <div class="inventoryGrid">${Array.from({length:40},()=>`<div class="invCell"></div>`).join("")}</div>
      ${inventoryItems.map((it,i)=>{
        const scanned=invScanned.has(it.id);
        const current=i===inventoryAnimationIndex;
        return `<div class="invItem ${scanned?"scanned":""} ${current?"scanning-now":""}"
          style="
            left:calc(4px + ${it.x} * ((100% - 8px - 18px) / 10 + 2px));
            top:calc(4px + ${it.y} * 38px);
            width:calc(${it.w} * ((100% - 8px - 18px) / 10) + ${(it.w-1)*2}px);
            height:${it.h*36 + (it.h-1)*2}px;
          " title="${it.name}">${scanned?"✓":it.glyph}</div>`;
      }).join("")}
    </div>
    <div class="invLegend">
      <span>niebieski = aktualnie wskazywany</span>
      <span>zielony = zapisany skan F10</span>
    </div>
  </div>`;
}

function inventoryScanPanel(){
  const count=invScanned.size;
  return `<div class="sidePanel">
    <h3>Skanowanie ciągłe</h3>
    <div class="inventoryStatusLive">
      <span class="liveDot"></span>
      <span>Licznik aktualizuje się po zapisaniu skanu</span>
    </div>
    <div class="scanCounter">
      <span>Zapisane zrzuty F10</span>
      <strong>${count}</strong>
    </div>
    <div class="inventoryHint">
      Kreator cały czas pozostaje na tym ekranie. Układ przedmiotów jest poglądowy.
      Najedź w grze na dowolny item i naciskaj F10 tyle razy, ile chcesz.
    </div>
    <button class="finishScanBtn" id="finishInventoryBtn">Zakończ skanowanie ekwipunku →</button>
  </div>`;
}

function mercBoard(activeId=""){
  const slots=mercSlots();
  return `<div class="mercBoard"><div class="mercSilhouette"></div>
    ${slots.map(x=>{
      const st=x.id===activeId?"active":stateById("merc:"+x.id);
      return `<div class="mSlot ${x.board} ${st}" data-name="${x.name}"><div class="itemGlyph">${x.glyph}</div></div>`;
    }).join("")}
    <div class="mercLabel">NAJEMNIK</div>
  </div>`;
}

function mercList(){
  return `<div class="scanList">${mercSlots().map(x=>{
    const st=stateById("merc:"+x.id);
    return `<div class="scanItem ${st}"><span class="mini">${x.glyph}</span><span>${x.name}</span>
      <span class="statusPill">${st==="done"?"✓":st==="skipped"?"POMINIĘTO":st==="active"?"TERAZ":""}</span></div>`;
  }).join("")}</div>`;
}

function statsMock(){
  return `<div class="statsMock"><div class="statCol">
    <div class="stat"><span>Siła</span><b>—</b></div><div class="stat"><span>Zręczność</span><b>—</b></div><div class="stat"><span>Witalność</span><b>—</b></div>
  </div><div class="statCol">
    <div class="stat"><span>Życie</span><b>—</b></div><div class="stat"><span>Mana</span><b>—</b></div><div class="stat"><span>Poziom</span><b>—</b></div>
  </div></div>`;
}

function skillMock(active=-1){
  return `<div class="treeTabs">${trees.map((t,i)=>`<div class="treeCard ${i===active?"active":""}">
    <h4>${t.name}</h4><div class="nodes">${Array.from({length:9},(_,n)=>`<div class="node">${n+1}</div>`).join("")}</div>
  </div>`).join("")}</div>`;
}

function stopInventoryAnimation(){
  if(inventoryAnimationTimer){
    clearInterval(inventoryAnimationTimer);
    inventoryAnimationTimer=null;
  }
}

function startInventoryAnimation(){
  stopInventoryAnimation();
  if(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  inventoryAnimationTimer=setInterval(()=>{
    if(stages[index]?.type!=="inventoryScan"){
      stopInventoryAnimation();
      return;
    }
    inventoryAnimationIndex=(inventoryAnimationIndex+1)%inventoryItems.length;
    const board=document.querySelector(".inventoryFrame");
    if(!board) return;
    board.querySelectorAll(".invItem").forEach((el,i)=>{
      el.classList.toggle("scanning-now",i===inventoryAnimationIndex);
    });
  },900);
}

function renderVisual(){
  stopInventoryAnimation();
  stages=buildStages();
  if(index>=stages.length) index=stages.length-1;
  setPhase();
  const s=stages[index], content=document.getElementById("content");
  document.getElementById("wizardTitle").textContent=s.title;
  document.getElementById("backBtn").disabled=index===0;
  document.getElementById("skipBtn").style.visibility=s.type==="done"?"hidden":"visible";
  const nextBtn=document.getElementById("nextBtn");
  nextBtn.style.visibility=s.type==="inventoryScan"?"hidden":"visible";
  nextBtn.textContent=s.type==="done"?"Od początku ↻":"Dalej →";
  document.getElementById("counter").innerHTML=`Etap <b>${index+1} / ${stages.length}</b>${skipped.has(s.id)?`<div class="skipInfo">ten etap pominięto</div>`:""}`;

  if(s.type==="stats"){
    content.innerHTML=card("Krok 1 · Statystyki","Otwórz panel postaci","Najpierw odczytamy podstawowe statystyki postaci.","C",
      `${statsMock()}<div class="instruction"><strong>W grze naciśnij <b>C</b></strong><p>Panel statystyk powinien być w pełni widoczny.</p></div>
      <div class="keyrow"><div class="key">F10</div><div class="keytext"><b>Wykonaj zrzut ekranu</b><small>Po otwarciu statystyk naciśnij F10.</small></div></div>
      <div class="listen"><span class="dot"></span><b>Nasłuch aktywny</b><span>oczekiwanie na F10…</span></div>`);
  }

  if(s.type==="charIntro"){
    content.innerHTML=card("Krok 2 · Postać","Ekwipunek postaci","Najpierw skanujemy przedmioty założone na postaci.","I",
      `<div class="instruction"><strong>Naciśnij <b>I</b></strong><p>Zestaw I → swap W → zestaw II → wszystkie pozostałe sloty. Dolne sloty są teraz dosunięte do pancerza.</p></div>
      <div class="eqWrap">${charBoard("",false,1)}<div class="sidePanel"><h3>Kolejność</h3>${charList()}</div></div>`);
  }

  if(s.type==="char"){
    if(s.item.id==="swap"){
      content.innerHTML=card("Krok 2 · Postać","Przełącz zestaw broni","Zeskanowaliśmy pierwszy zestaw. Teraz pokaż drugi.","W",
        `<div class="eqWrap">${charBoard("",true,2)}<div class="sidePanel"><h3>Postęp</h3>${charList()}</div></div>
        <div class="keyrow"><div class="key">W</div><div class="keytext"><b>Weapon Swap</b><small>Po przełączeniu kliknij „Dalej”.</small></div></div>`);
    }else{
      content.innerHTML=card("Krok 2 · Postać",`Skanuj: ${s.item.name}`,"Najedź na wskazany przedmiot, pokaż cały tooltip i wykonaj zrzut.",s.item.glyph,
        `<div class="eqWrap">${charBoard(s.item.id,false,s.item.set||2)}<div class="sidePanel"><h3>Postęp</h3>${charList()}</div></div>
        <div class="keyrow"><div class="key">F10</div><div class="keytext"><b>Zrób zrzut tego przedmiotu</b><small>Tooltip powinien być cały widoczny.</small></div></div>
        <div class="listen"><span class="dot"></span><b>Nasłuch aktywny</b><span>oczekiwanie na F10…</span></div>`);
    }
  }

  if(s.type==="inventoryScan"){
    content.innerHTML=card("Krok 2 · Plecak","Skanuj dowolną liczbę przedmiotów","Każdy udany skan aktualizuje licznik. Kreator czeka, aż zakończysz skanowanie.","▦",
      `<div class="instruction"><strong>Zostaw otwarte <b>I</b> i skanuj tyle itemów, ile potrzebujesz</strong><p>Układ plecaka jest poglądowy; licznik pokazuje zapisane skany. W grze najedź na dowolny item, pokaż tooltip i naciśnij F10. Gdy skończysz, kliknij „Zakończ skanowanie ekwipunku”.</p></div>
      <div class="invWrap">${inventoryBoard()}${inventoryScanPanel()}</div>
      <div class="keyrow"><div class="key">F10</div><div class="keytext"><b>Możesz wykonywać wiele zrzutów</b><small>Kreator czeka tutaj aż sam klikniesz „Zakończ skanowanie ekwipunku”.</small></div></div>
      <div class="listen"><span class="dot"></span><b>Nasłuch aktywny</b><span>skanowanie ciągłe…</span></div>`);
    const finish=document.getElementById("finishInventoryBtn");
    if(finish) finish.addEventListener("click",()=>{
      stopInventoryAnimation();
      stages=buildStages();
      go(1);
      window.scrollTo({top:0,behavior:"smooth"});
    });
    // Progress follows saved scans.
  }

  if(s.type==="mercIntro"){
    content.innerHTML=card("Krok 3 · Najemnik","Wyposażenie najemnika","Układ jest teraz taki sam jak u gracza: hełm i zbroja pośrodku oraz dwa sloty po lewej i prawej stronie.","☗",
      `<div class="instruction"><strong>Otwórz panel najemnika</strong><p>Lewy slot służy na broń lub broń dwuręczną. Prawy slot może zawierać tarczę albo drugą broń jednoręczną. Jeżeli najemnik używa broni dwuręcznej i prawy slot jest pusty, po prostu pomiń ten krok.</p></div>
      <div class="eqWrap">${mercBoard("")}<div class="sidePanel"><h3>Sloty najemnika</h3>${mercList()}</div></div>
      <div class="tip">Kolejność: hełm → zbroja → lewa ręka → prawa ręka. Każdy slot możesz pominąć.</div>`);
  }

  if(s.type==="mercItem"){
    content.innerHTML=card("Krok 3 · Najemnik",`Skanuj: ${s.item.name}`,"Najedź na wskazany slot najemnika i wykonaj zrzut z widocznym tooltipem. Prawy slot może być tarczą, drugą bronią lub może być pusty przy broni dwuręcznej.",s.item.glyph,
      `<div class="eqWrap">${mercBoard(s.item.id)}<div class="sidePanel"><h3>Wyposażenie najemnika</h3>${mercList()}</div></div>
      <div class="keyrow"><div class="key">F10</div><div class="keytext"><b>Zrób zrzut tego przedmiotu</b><small>Po zapisaniu kreator przejdzie dalej automatycznie.</small></div></div>
      <div class="listen"><span class="dot"></span><b>Nasłuch aktywny</b><span>oczekiwanie na F10…</span></div>`);
  }

  if(s.type==="skillsIntro"){
    content.innerHTML=card("Krok 4 · Umiejętności","Otwórz ekran umiejętności","Na końcu skanujemy trzy drzewka osobno.","T",
      `${skillMock(-1)}<div class="instruction"><strong>Naciśnij <b>T</b></strong><p>W kolejnych krokach pokaż kolejno każde z trzech drzewek.</p></div>`);
  }

  if(s.type==="tree"){
    content.innerHTML=card("Krok 4 · Umiejętności",trees[s.tree].name,`Otwórz drzewko nr ${s.tree+1} i wykonaj zrzut całego panelu.`,String(s.tree+1),
      `${skillMock(s.tree)}<div class="keyrow"><div class="key">F10</div><div class="keytext"><b>Zeskanuj całe drzewko</b><small>Wszystkie poziomy umiejętności powinny być widoczne.</small></div></div>
      <div class="listen"><span class="dot"></span><b>Nasłuch aktywny</b><span>oczekiwanie na F10…</span></div>`);
  }

  if(s.type==="done"){
    content.innerHTML=`<section class="card doneBox"><div class="doneOrb">✓</div><h2>Kreator zakończony</h2>
      <p>Zakończono wybrane etapy skanowania. Zapisane dane znajdziesz w pełnej aplikacji.</p>
      <div class="instruction"><strong>Pominięte kroki: <b>${skipped.size}</b></strong><p>Możesz wrócić przyciskiem Wstecz i uzupełnić pominięte sloty.</p></div></section>`;
  }
}

