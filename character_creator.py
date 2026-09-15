"""Configure the capture service for the guided character scan."""
from flask import jsonify, request, render_template
from capture import capture_service as service
from db import get_character

SLOTS = {
    'weapon1': ('weapon1', 'weapon'), 'shield1': ('shield1', 'shield,weapon'),
    'weapon2': ('weapon2', 'weapon'), 'shield2': ('shield2', 'shield,weapon'),
    'helm': ('head', 'head'), 'amulet': ('amulet', 'amulet'), 'armor': ('armor', 'armor'),
    'gloves': ('gloves', 'gloves'), 'ring1': ('ring1', 'ring'), 'ring2': ('ring2', 'ring'),
    'belt': ('belt', 'belt'), 'boots': ('boots', 'boots'),
    'mhelm': ('merc_head', 'head'), 'marmor': ('merc_armor', 'armor'),
    'mleft': ('merc_weapon', 'weapon'), 'mright': ('merc_offhand', 'shield,weapon'),
}


def register(app):
    @app.get('/character-creator')
    def creator_page():
        return render_template('character-creator.html')

    @app.post('/api/character-creator/open')
    def creator_open():
        if not request.is_json or (request.headers.get('Origin') and request.headers['Origin'] != request.host_url.rstrip('/')):
            return jsonify(error='Niedozwolone żądanie'), 403
        if not app.config.get('COMPANION_AVAILABLE'):
            return jsonify(error='Uruchom Launch_D2_UberApp.bat, aby otworzyć kreator zawsze na wierzchu.'), 503
        from desktop_companion import creator_requested
        creator_requested.set()
        return jsonify(success=True)

    @app.post('/api/character-creator/stage')
    def creator_stage():
        if not request.is_json or (request.headers.get('Origin') and request.headers['Origin'] != request.host_url.rstrip('/')):
            return jsonify(error='Niedozwolone żądanie'), 403
        if service.queue_count or service.processing_lock.locked():
            return jsonify(error='Poczekaj na zakończenie skanu.'), 409
        stage = str(request.get_json().get('stage') or '')
        slot = SLOTS.get(stage.split(':')[-1])
        mode = 'character'
        if stage == 'stats': mode = 'stat_screen'
        elif stage in ('skillsIntro', 'tree:0', 'tree:1', 'tree:2'): mode = 'skill_screen'
        elif stage == 'mercIntro' or stage.startswith('merc:'): mode = 'merc'
        elif stage == 'inventoryScan': mode = 'stash'
        elif stage not in ('charIntro', 'char:swap', 'done') and not stage.startswith('char:'):
            return jsonify(error='Nieznany etap.'), 400
        if stage.startswith(('char:', 'merc:')) and stage != 'char:swap' and not slot:
            return jsonify(error='Nieznany slot.'), 400
        if stage not in ('stats', 'done') and not get_character(service.current_character):
            return jsonify(error='Najpierw zeskanuj statystyki lub wybierz istniejącą postać w panelu.'), 400
        if stage == 'stats' and not getattr(service, 'creator_context', None):
            service.creator_previous = (service.scan_mode, service.current_location, service.is_swap)
        if stage == 'done':
            close_creator()
            return jsonify(success=True)
        service.wizard_active = False
        service.creator_waiting_stage = None
        service.creator_context = dict(stage=stage, slot=slot[0] if slot else '', accepts=slot[1].split(',') if slot else [],
                                       page=int(stage[-1]) + 1 if stage.startswith('tree:') else None)
        service.set_scan_mode(mode)
        service.set_swap(stage in ('char:weapon2', 'char:shield2'))
        if stage == 'inventoryScan': service.current_location = 'Plecak: ' + service.current_character
        elif hasattr(service, 'creator_previous'): service.current_location = service.creator_previous[1]
        if stage == 'skillsIntro': service.skill_scan_pages = []
        service.start()
        return jsonify(success=True)


def close_creator():
    service.creator_context = None
    service.creator_waiting_stage = None
    previous = getattr(service, 'creator_previous', None)
    if previous:
        service.set_scan_mode(previous[0])
        service.current_location = previous[1]
        service.set_swap(previous[2])
        del service.creator_previous
