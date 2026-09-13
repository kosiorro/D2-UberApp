"""Native control window sharing one capture service with the web application."""
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import config
from preferences import save
from capture import capture_service

show_requested = threading.Event()

def run(app):
    from werkzeug.serving import make_server
    root = tk.Tk()
    root.title('UberApp · aplikacja towarzysząca')
    root.geometry('720x810')
    root.minsize(640, 700)
    root.configure(bg='#10140f')
    try:
        root.iconbitmap(str(config.BASE_DIR / 'static/images/uberapp.ico'))
    except tk.TclError:
        pass
    try:
        server = make_server('127.0.0.1', config.FLASK_PORT, app, threaded=True)
    except (OSError, SystemExit):
        messagebox.showerror('UberApp', 'Port aplikacji jest zajęty. Zamknij poprzednią wersję i uruchom ponownie.', parent=root)
        root.destroy()
        return
    threading.Thread(target=server.serve_forever, daemon=True).start()
    app.config['COMPANION_AVAILABLE'] = True
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background='#10140f', foreground='#d7d8c9', font=('Segoe UI', 10))
    style.configure('TFrame', background='#10140f')
    style.configure('TLabel', background='#10140f')
    style.configure('TButton', background='#303622', foreground='#e8dbb7', padding=(13, 9), borderwidth=1)
    style.map('TButton', background=[('active', '#4b5032')])
    style.configure('TEntry', fieldbackground='#20271b', foreground='#e6e8d8', padding=7)
    style.configure('TCombobox', fieldbackground='#20271b', foreground='#e6e8d8', padding=7)
    style.map('TCombobox', fieldbackground=[('readonly', '#20271b')], foreground=[('readonly', '#e6e8d8')])
    style.configure('TCheckbutton', background='#10140f', foreground='#c9cdbd')
    style.map('TCheckbutton', background=[('active', '#20271b')])
    style.configure('TLabelframe', background='#10140f', bordercolor='#464b36')
    style.configure('TLabelframe.Label', foreground='#cbb078', background='#10140f', font=('Georgia', 12))
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='UberApp', font=('Georgia', 24), foreground='#d0ae71').pack(anchor='w')
    ttk.Label(frame, text='PRZECHWYTYWANIE  /  DIABLO II: RESURRECTED', font=('Segoe UI', 9), foreground='#959d87').pack(anchor='w', pady=(5, 18))
    status = tk.StringVar(value='Gotowy')
    activity = tk.StringVar(value='Naciśnij skrót w grze, gdy widoczny jest opis przedmiotu.')
    counts = tk.StringVar()
    ttk.Label(frame, textvariable=status, foreground='#d6c18d', font=('Georgia', 16)).pack(anchor='w')
    ttk.Label(frame, textvariable=activity, wraplength=650).pack(anchor='w', pady=(7, 3))
    ttk.Label(frame, textvariable=counts, foreground='#959d87').pack(anchor='w', pady=(0, 12))
    buttons = ttk.Frame(frame)
    buttons.pack(fill='x', pady=(0, 16))
    def toggle():
        if capture_service.is_running:
            capture_service.stop()
        else:
            capture_service.start()
    toggle_btn = ttk.Button(buttons, text='Włącz nasłuch', command=toggle)
    toggle_btn.pack(side='left')
    ttk.Button(buttons, text='Otwórz skarbiec ↗', command=lambda: webbrowser.open(f'http://127.0.0.1:{config.FLASK_PORT}')).pack(side='left', padx=8)
    ttk.Button(buttons, text='Minimalizuj', command=root.iconify).pack(side='right')
    box = ttk.LabelFrame(frame, text=' Przechwytywanie i AI ', padding=15)
    box.pack(fill='x')
    box.columnconfigure(1, weight=1)
    variables = {
        'hotkey': tk.StringVar(value=config.HOTKEY_NAME),
        'model': tk.StringVar(value=config.GEMINI_MODEL),
        'key': tk.StringVar(value=config.GEMINI_API_KEY),
        'location': tk.StringVar(value=capture_service.current_location),
        'character': tk.StringVar(value=capture_service.current_character),
        'mode': tk.StringVar(value={'normal':'Skrzynia / runy', 'character':'Ekwipunek postaci', 'stat_screen':'Statystyki postaci'}.get(capture_service.scan_mode, 'Skrzynia / runy')),
    }
    modes = {'Skrzynia / runy':'normal', 'Ekwipunek postaci':'character', 'Statystyki postaci':'stat_screen'}
    fields = [('hotkey','Skrót w grze'),('location','Lokalizacja przedmiotów'),('model','Model Gemini'),('key','Klucz API Gemini')]
    for row, (name, label) in enumerate(fields):
        ttk.Label(box, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=4)
        if name in ('hotkey','mode'):
            choices = [f'F{i}' for i in range(1, 13)] if name == 'hotkey' else list(modes)
            entry = ttk.Combobox(box, textvariable=variables[name], values=choices, state='readonly')
        else:
            entry = ttk.Entry(box, textvariable=variables[name], show='•' if name == 'key' else '')
        entry.grid(row=row, column=1, sticky='ew', pady=4)
    swap = tk.BooleanVar(value=capture_service.is_swap)
    sound = tk.BooleanVar(value=config.SOUND_ENABLED)
    autostart = tk.BooleanVar(value=config.CAPTURE_AUTOSTART)

    ttk.Checkbutton(box, text='Dźwięki przechwytywania', variable=sound).grid(row=7,column=1,sticky='w')
    ttk.Checkbutton(box, text='Włącz nasłuch przy uruchomieniu', variable=autostart).grid(row=8,column=1,sticky='w')
    result = tk.StringVar(value='Zmiany zastosujesz przyciskiem Zapisz. Klucz pozostaje na tym komputerze.')
    def apply():
        if capture_service.queue_count or capture_service.processing_lock.locked():
            result.set('Poczekaj na zakończenie bieżącej analizy, a następnie zapisz ustawienia.')
            return
        key, model = variables['key'].get().strip(), variables['model'].get().strip()
        if not key or not model:
            result.set('Podaj klucz API i identyfikator modelu Gemini.')
            return
        was_running = capture_service.is_running
        capture_service.stop()
        if capture_service.queue_count or capture_service.processing_lock.locked():
            if was_running:
                capture_service.start()
            result.set('Skan właśnie się rozpoczął. Zapisz ustawienia po jego zakończeniu.')
            return
        data = dict(config.COMPANION_SETTINGS, api_key=key, model=model, hotkey=variables['hotkey'].get(), sound=sound.get(), autostart=autostart.get(), location=variables['location'].get().strip(), character=capture_service.current_character, mode=capture_service.scan_mode, swap=capture_service.is_swap)
        try:
            save(data)
            config.COMPANION_SETTINGS = data
            config.GEMINI_API_KEY, config.GEMINI_MODEL = key, model
            config.HOTKEY_NAME = data['hotkey']
            config.HOTKEY_VK = 0x70 + int(data['hotkey'][1:]) - 1
            config.SOUND_ENABLED, config.CAPTURE_AUTOSTART = sound.get(), autostart.get()
            capture_service.set_location(data['location'])
            capture_service.set_character(data['character'])
            capture_service.set_scan_mode(data['mode'])
            capture_service.set_swap(data['swap'])
            result.set('Zapisano. Ustawienia obowiązują od następnego skanu.')
        except Exception as error:
            result.set(f'Nie zapisano ustawień: {error}')
        finally:
            if was_running:
                capture_service.start()
    ttk.Button(box, text='Zapisz ustawienia', command=apply).grid(row=9,column=1,sticky='e',pady=(10,0))
    ttk.Label(frame, textvariable=result, foreground='#a5b197', wraplength=650, font=('Segoe UI',9)).pack(anchor='w',pady=(10,14))
    ttk.Label(frame,text='OSTATNIA AKTYWNOŚĆ',foreground='#cbb078',font=('Segoe UI',9)).pack(anchor='w',pady=(0,7))
    logs = tk.Text(frame, height=5, background='#090e0b', foreground='#bfc8af', font=('Consolas',9), relief='flat', padx=12,pady=10,state='disabled',wrap='word')
    logs.pack(fill='both',expand=True)
    bottom = ttk.Frame(frame)
    bottom.pack(fill='x',pady=(12,0))
    ttk.Label(bottom,text='Zamknięcie okna minimalizuje aplikację.',foreground='#959d87',font=('Segoe UI',9)).pack(side='left')
    def quit_app():
        if capture_service.queue_count or capture_service.processing_lock.locked():
            result.set('Trwa analiza. Zakończ aplikację po jej ukończeniu.')
            return
        capture_service.stop()
        if capture_service.queue_count or capture_service.processing_lock.locked():
            result.set('Skan właśnie się rozpoczął. Poczekaj na wynik przed zamknięciem.')
            return
        app.config['COMPANION_AVAILABLE'] = False
        server.shutdown()
        root.destroy()
    ttk.Button(bottom,text='Zakończ aplikację',command=quit_app).pack(side='right')
    root.protocol('WM_DELETE_WINDOW',root.iconify)
    last_logs = None
    def refresh():
        nonlocal last_logs
        if show_requested.is_set():
            show_requested.clear()
            root.deiconify()
            root.lift()
        status.set(capture_service.last_status)
        activity.set(capture_service.last_activity.get('message',''))
        counts.set(f'Zrzuty: {capture_service.total_captured}   ·   Przetwarzane: {capture_service.queue_count}   ·   {config.HOTKEY_NAME}   ·   {capture_service.current_character if capture_service.scan_mode != "normal" else "Skrzynia"}')
        toggle_btn.configure(text='Wstrzymaj nasłuch' if capture_service.is_running else 'Włącz nasłuch')
        current = '\n'.join(f"{line['time']}  {line['status']}  {line['text']}" for line in capture_service.activity_log)
        if current != last_logs:
            logs.configure(state='normal')
            logs.delete('1.0','end')
            logs.insert('1.0', current or 'Historia pojawi się po pierwszym skanie.')
            logs.configure(state='disabled')
            last_logs = current
        root.after(700,refresh)
    from dashboard import attach
    attach(root, frame, lambda: None, quit_app)
    if config.CAPTURE_AUTOSTART:
        capture_service.start()
    refresh()
    root.mainloop()
