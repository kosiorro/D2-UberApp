from flask import request,jsonify,render_template
from capture import capture_service as service
from db import get_all_characters_detailed,get_character,create_or_update_character,get_distinct_locations
from uber_features import edit_character
from scan_history import recent,finish

def register(app):
    def busy():return service.queue_count or service.processing_lock.locked()
    @app.get('/companion')
    def companion_page():return render_template('companion.html')
    @app.get('/api/companion/state')
    def state():
        import config
        return jsonify(
            running=service.is_running,
            status=service.last_status,
            activity=service.last_activity,
            hotkey=config.HOTKEY_NAME,
            mode_hotkeys=getattr(config, 'MODE_HOTKEYS', {}),
            mode=service.scan_mode,
            character=service.current_character,
            swap=service.is_swap,
            characters=get_all_characters_detailed(),
            history=recent(),
            wizard_active=getattr(service,'wizard_active',False),
            wizard=service.last_stat_scan if getattr(service,'wizard_active',False) else None,
            lang=config.COMPANION_SETTINGS.get('lang', 'pl'),
            location=service.current_location,
            locations=get_distinct_locations()
        )
    @app.post('/api/companion/action')
    def action():
        if not request.is_json or (request.headers.get('Origin') and request.headers['Origin']!=request.host_url.rstrip('/')):return jsonify(error='Niedozwolone żądanie'),403
        data=request.get_json();command=data.get('action')
        if busy():return jsonify(error='Poczekaj na zakończenie bieżącego skanu.'),409
        try:
            if command=='toggle':
                service.stop() if service.is_running else service.start()
            elif command=='session':
                name=data.get('character','')
                if name and not get_character(name):raise ValueError('Wybierz istniejącą postać.')
                mode=data.get('mode','stash')
                if mode == 'normal': mode = 'stash'
                if mode not in ('stash','runes','gems','materials','stat_screen','character','merc'):raise ValueError('Nieznany tryb.')
                if 'location' in data:
                    service.current_location = str(data.get('location') or '').strip()
                service.current_character=name;service.set_scan_mode(mode);service.set_swap(bool(data.get('swap')) if mode=='character' else False);service.offhand=False
                from desktop_companion import persist
                persist(location=service.current_location)
            elif command=='set_location':
                service.current_location = str(data.get('location') or '').strip()
                from desktop_companion import persist
                persist(location=service.current_location)
                return jsonify(success=True, location=service.current_location)
            elif command=='wizard_start':
                service.wizard_previous_mode=service.scan_mode;service.wizard_active=True;service.last_stat_scan=None;service.set_scan_mode('stat_screen');service.start()
            elif command=='wizard_cancel':
                pending=service.last_stat_scan or {}
                if pending.get('request_id'):finish(pending['request_id'],'cancelled',message='Anulowano dodawanie postaci.')
                service.wizard_active=False;service.last_stat_scan=None;service.set_scan_mode(getattr(service,'wizard_previous_mode','stash'))
            elif command=='wizard_confirm':
                pending=service.last_stat_scan or {}
                if not service.wizard_active or pending.get('status')!='success':raise ValueError('Najpierw zeskanuj statystyki postaci.')
                candidate=dict(pending['character']);name=str(data.get('name') or candidate['name']).strip()
                candidate['name']=name;candidate['level']=int(data.get('level') or candidate['level'])
                existing=get_character(name) or {};existing.update({k:v for k,v in candidate.items() if v is not None})
                if not name or not 1<=candidate['level']<=99:raise ValueError('Sprawdź nazwę i poziom postaci.')
                saved=create_or_update_character(existing);service.current_character=saved['name'];service.wizard_active=False;service.last_stat_scan=None
                service.set_scan_mode('character' if data.get('add_items') else 'stash');service.is_swap=False;service.offhand=False
                finish(pending['request_id'],'success','character',saved['name'],saved['id'],'Zatwierdzono postać: '+saved['name'],candidate)
                from desktop_companion import persist
                persist()
            elif command=='set_language':
                new_lang = data.get('lang', 'pl')
                from desktop_companion import persist
                persist(lang=new_lang)
                config.COMPANION_SETTINGS['lang'] = new_lang
            elif command=='edit':
                saved=edit_character(data.get('original',''),data.get('character_data') or {});service.current_character=saved['name']
                from desktop_companion import persist
                persist()
            else:raise ValueError('Nieznana czynność.')
            return jsonify(success=True)
        except (ValueError,TypeError,KeyError) as error:return jsonify(error=str(error)),400
