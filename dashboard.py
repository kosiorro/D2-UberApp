"""Compact native UberApp dashboard; settings remain in a separate window."""
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import config
from capture import capture_service as svc
from preferences import save
from db import get_character, get_all_characters_detailed
from uber_features import select_character, edit_character, character_report

MODES={'Automatycznie':'normal','Runy':'runes','Statystyki':'stat_screen','Skrzynia':'stash','Postać':'character','Najemnik':'merc'}

def attach(root, settings_frame, refresh_status, quit_app):
    root.title('UberApp');root.geometry('440x580');root.minsize(420,560)
    settings_frame.pack_forget()
    box=ttk.Frame(root,padding=18);box.pack(fill='both',expand=True)
    root.iconbitmap(str(config.BASE_DIR/'static/images/uberapp.ico'))
    top=tk.BooleanVar(value=config.COMPANION_SETTINGS.get('topmost',False))
    alpha=tk.BooleanVar(value=config.COMPANION_SETTINGS.get('transparent',False))
    selected=tk.StringVar(value=select_character(config.COMPANION_SETTINGS.get('character','')))
    svc.current_character=selected.get()
    mode=tk.StringVar(value=next((k for k,v in MODES.items() if v==svc.scan_mode),'Automatycznie'))
    swap=tk.BooleanVar(value=svc.is_swap);off=tk.BooleanVar(value=False)
    photos=[]
    def persist():
        data=dict(config.COMPANION_SETTINGS)
        data.update(api_key=config.GEMINI_API_KEY,model=config.GEMINI_MODEL,hotkey=config.HOTKEY_NAME,sound=config.SOUND_ENABLED,
                    autostart=config.CAPTURE_AUTOSTART,character=svc.current_character,mode=svc.scan_mode,swap=svc.is_swap,
                    location=svc.current_location,topmost=top.get(),transparent=alpha.get())
        save(data);config.COMPANION_SETTINGS=data
    def busy():return svc.queue_count or svc.processing_lock.locked()
    def window_style():
        root.attributes('-topmost',top.get());root.attributes('-alpha',.84 if alpha.get() else 1.0)
        try:persist()
        except Exception as e:messagebox.showerror('UberApp',str(e),parent=root)
    root.attributes('-topmost',top.get());root.attributes('-alpha',.84 if alpha.get() else 1.0)
    brand=ttk.Frame(box);brand.pack(fill='x')
    logo=tk.PhotoImage(file=str(config.BASE_DIR/'static/images/uberapp.png')).subsample(2);photos.append(logo)
    ttk.Label(brand,image=logo).pack(side='left',padx=(0,12))
    title=ttk.Frame(brand);title.pack(side='left')
    ttk.Label(title,text='UberApp',font=('Georgia',26),foreground='#d0ae71').pack(anchor='w')
    ttk.Label(title,text='DIABLO II · TWOJE CENTRUM ŁUPÓW',font=('Segoe UI',8),foreground='#9ba48b').pack(anchor='w')
    state=tk.StringVar();activity=tk.StringVar();meta=tk.StringVar()
    ttk.Label(box,textvariable=state,font=('Georgia',15),foreground='#d0ae71').pack(anchor='w',pady=(18,7))
    ttk.Label(box,textvariable=activity,wraplength=390,font=('Segoe UI',9)).pack(anchor='w',pady=(0,15))
    row=ttk.Frame(box);row.pack(fill='x')
    picker=ttk.Combobox(row,textvariable=selected,state='readonly',width=20);picker.pack(side='left',fill='x',expand=True)
    ttk.Label(box,textvariable=meta,font=('Georgia',11),foreground='#a6b197').pack(anchor='w',pady=(7,15))
    ttk.Label(box,text='CO SKANUJEMY?',font=('Segoe UI',8),foreground='#d0ae71').pack(anchor='w')
    tiles=ttk.Frame(box);tiles.pack(fill='x',pady=5)
    gear=ttk.Frame(box);gear.pack(fill='x',pady=6)
    swap_ctl=ttk.Checkbutton(gear,text='Zestaw II · swap',variable=swap,command=lambda:session())
    off_ctl=ttk.Checkbutton(gear,text='Off-hand / druga broń',variable=off,command=lambda:session())
    def session():
        if busy():
            selected.set(svc.current_character);mode.set(next(k for k,v in MODES.items() if v==svc.scan_mode));swap.set(svc.is_swap);off.set(svc.offhand)
            return
        svc.current_character=selected.get();svc.set_scan_mode(MODES[mode.get()]);svc.set_swap(swap.get() if svc.scan_mode=='character' else False)
        svc.offhand=off.get() if svc.scan_mode in ('character','merc') else False
        swap_ctl.pack_forget();off_ctl.pack_forget()
        if svc.scan_mode=='character':swap_ctl.pack(side='left')
        if svc.scan_mode in ('character','merc'):off_ctl.pack(side='left')
        try:persist()
        except Exception as e:messagebox.showerror('UberApp',str(e),parent=root)
    for i,label in enumerate(MODES):ttk.Radiobutton(tiles,text=label,variable=mode,value=label,command=session).grid(row=i//3,column=i%3,sticky='w',padx=(0,12),pady=5)
    picker.bind('<<ComboboxSelected>>',lambda e:session())
    buttons=ttk.Frame(box);buttons.pack(fill='x',pady=10)
    listen=ttk.Button(buttons,command=lambda:svc.stop() if svc.is_running else svc.start());listen.pack(side='left',fill='x',expand=True)
    ttk.Button(buttons,text='Skarbiec ↗',command=lambda:webbrowser.open(f'http://127.0.0.1:{config.FLASK_PORT}')).pack(side='right',padx=(8,0))
    flags=ttk.Frame(box);flags.pack(fill='x',pady=7)
    ttk.Checkbutton(flags,text='Zawsze na wierzchu',variable=top,command=window_style).pack(side='left')
    ttk.Checkbutton(flags,text='Przezroczystość',variable=alpha,command=window_style).pack(side='right')
    counts=tk.StringVar();ttk.Label(box,textvariable=counts,foreground='#95a18c',font=('Segoe UI',9)).pack(anchor='w',pady=9)
    def popup(title,size):
        win=tk.Toplevel(root);win.title('UberApp · '+title);win.geometry(size);win.configure(bg='#10140f');win.iconbitmap(str(config.BASE_DIR/'static/images/uberapp.ico'));return win
    def editor(original=''):
        data=get_character(original) or {};win=popup('Edytuj postać' if original else 'Dodaj postać','430x430')
        form=ttk.Frame(win,padding=20);form.pack(fill='both',expand=True);form.columnconfigure(1,weight=1);fields={}
        for i,(key,label,default) in enumerate([('name','Nazwa',''),('class_name','Klasa','Paladyn'),('level','Poziom',1),('strength','Siła',0),('dexterity','Zręczność',0),('vitality','Żywotność',0),('energy','Energia',0)]):
            fields[key]=tk.StringVar(value=str(data.get(key,default)));ttk.Label(form,text=label).grid(row=i,column=0,sticky='w',padx=(0,15))
            widget=ttk.Combobox(form,textvariable=fields[key],values=['Paladyn','Czarodziejka','Barbarzyńca','Nekromanta','Amazonka','Druid','Zabójczyni'],state='readonly') if key=='class_name' else ttk.Entry(form,textvariable=fields[key])
            widget.grid(row=i,column=1,sticky='ew',pady=5)
        def commit():
            try:
                if busy():raise ValueError('Poczekaj na zakończenie skanu.')
                values={k:v.get().strip() for k,v in fields.items()}
                for key in ('level','strength','dexterity','vitality','energy'):
                    values[key]=int(values[key])
                    if values[key]<0:raise ValueError('Statystyki nie mogą być ujemne.')
                hero=edit_character(original,values);svc.current_character=hero['name'];selected.set(hero['name']);persist();win.destroy()
            except Exception as e:messagebox.showerror('UberApp',str(e),parent=win)
        ttk.Button(form,text='Zapisz postać',command=commit).grid(row=8,column=1,sticky='e',pady=15)
    def heroes():
        if not selected.get():return editor()
        report=character_report(selected.get());char=report['character'] or {};win=popup(selected.get(),'790x790')
        head=ttk.Frame(win,padding=15);head.pack(fill='x')
        ttk.Label(head,text=f"{selected.get()} · {char.get('class_name','')} · {char.get('level',1)}",font=('Georgia',19),foreground='#d0ae71').pack(side='left')
        ttk.Button(head,text='Edytuj',command=lambda:editor(char.get('name',''))).pack(side='right')
        ttk.Button(head,text='Dodaj',command=editor).pack(side='right',padx=5)
        stats=ttk.Frame(win,padding=(15,0,15,12));stats.pack(fill='x')
        for i,(key,label) in enumerate([('strength','Siła'),('dexterity','Zręczność'),('vitality','Żywotność'),('energy','Energia'),('life','Życie'),('mana','Mana'),('defense','Obrona'),('damage','Obrażenia'),('fire_res','Ogień'),('cold_res','Zimno'),('light_res','Błyskawice'),('poison_res','Trucizna')]):
            cell=ttk.Frame(stats,padding=7,relief='ridge');cell.grid(row=i//4,column=i%4,sticky='ew',padx=2,pady=2);stats.columnconfigure(i%4,weight=1)
            ttk.Label(cell,text=label,foreground='#9ba891',font=('Segoe UI',9)).pack(anchor='w');ttk.Label(cell,text=str(char.get(key) or '—'),font=('Georgia',15),foreground='#d0ae71').pack(anchor='w')
        notebook=ttk.Notebook(win);notebook.pack(fill='both',expand=True,padx=15,pady=(0,15));local_photos=[]
        for key,label in [('main','Zestaw I'),('swap','Zestaw II'),('merc','Najemnik')]:
            page=ttk.Frame(notebook);notebook.add(page,text=label);canvas=tk.Canvas(page,bg='#10140f',highlightthickness=0)
            scroll=ttk.Scrollbar(page,command=canvas.yview);canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
            inner=ttk.Frame(canvas,padding=12);anchor=canvas.create_window(0,0,window=inner,anchor='nw')
            inner.bind('<Configure>',lambda e,c=canvas:c.configure(scrollregion=c.bbox('all')));canvas.bind('<Configure>',lambda e,c=canvas,a=anchor:c.itemconfigure(a,width=e.width))
            group=report['groups'][key]
            ttk.Label(inner,text='SUMA ROZPOZNANYCH BONUSÓW',foreground='#d0ae71').pack(anchor='w',pady=(0,8))
            for total in group['totals']:ttk.Label(inner,text=f"{total['label']}   +{total['value']}{total['unit']}").pack(anchor='w')
            ttk.Label(inner,text='Bonusy z opisów. Bez wyliczania obrażeń końcowych i warunkowych efektów.',wraplength=680,foreground='#95a18c',font=('Segoe UI',9)).pack(anchor='w',pady=12)
            for item in group['items']:
                card=ttk.Frame(inner,padding=10,relief='ridge');card.pack(fill='x',pady=5)
                path=config.BASE_DIR/item.get('image_path','').lstrip('/')
                if path.is_file():
                    try:
                        from PIL import Image,ImageTk
                        image=Image.open(path);image.thumbnail((64,95));photo=ImageTk.PhotoImage(image,master=win);local_photos.append(photo);ttk.Label(card,image=photo).pack(side='left',anchor='n',padx=(0,15))
                    except Exception:pass
                info=ttk.Frame(card);info.pack(side='left',fill='x',expand=True)
                ttk.Label(info,text=item['slot_label']+' · '+item['name'],font=('Georgia',13),foreground='#d0ae71',wraplength=580).pack(anchor='w')
                for line in item.get('stats',[]):ttk.Label(info,text=str(line),wraplength=580,foreground='#96aee5').pack(anchor='w')
            if not group['items']:ttk.Label(inner,text='Brak wyposażenia — wybierz cel skanowania w głównym oknie.').pack(anchor='w')
        win._photos=local_photos
    ttk.Button(row,text='Postać / edycja',command=heroes).pack(side='right',padx=(8,0))
    def open_settings():
        box.pack_forget();settings_frame.pack(fill='both',expand=True);root.geometry('720x850');root.minsize(680,800)
        refresh_status()
    def back():
        settings_frame.pack_forget();box.pack(fill='both',expand=True);root.geometry('440x580');root.minsize(420,560)
    ttk.Button(settings_frame,text='← Wróć do panelu',command=back).pack(side='bottom',pady=8)
    bottom=ttk.Frame(box);bottom.pack(side='bottom',fill='x')
    ttk.Button(bottom,text='Ustawienia / historia',command=open_settings).pack(side='left')
    ttk.Button(bottom,text='Zakończ',command=quit_app).pack(side='right')
    tick=0
    def refresh():
        nonlocal tick
        state.set(svc.last_status);activity.set(svc.last_activity.get('message',''))
        listen.configure(text=f'Ⅱ Wstrzymaj · {config.HOTKEY_NAME}' if svc.is_running else f'▶ Nasłuch · {config.HOTKEY_NAME}')
        counts.set(f'Zrzuty: {svc.total_captured}   ·   W toku: {svc.queue_count}')
        if tick%4==0:
            heroes_data=get_all_characters_detailed();names=[h['name'] for h in heroes_data];picker.configure(values=names)
            if svc.current_character not in names:svc.current_character=select_character('')
            selected.set(svc.current_character);char=next((h for h in heroes_data if h['name']==selected.get()),{})
            if not busy() and config.COMPANION_SETTINGS.get('character') != svc.current_character:
                try:persist()
                except Exception:pass
            meta.set(f"{char.get('class_name','Dodaj pierwszą postać')} · Poz. {char.get('level','—')} · {char.get('equipped_count',0)} itemów")
            mode.set(next((k for k,v in MODES.items() if v==svc.scan_mode),'Automatycznie'))
            swap_ctl.pack_forget();off_ctl.pack_forget()
            if svc.scan_mode=='character':swap_ctl.pack(side='left')
            if svc.scan_mode in ('character','merc'):off_ctl.pack(side='left')
        tick+=1;root.after(800,refresh)
    session();refresh()
