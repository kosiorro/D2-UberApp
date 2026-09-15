import time
import uuid
from db import (get_character_equipment,get_character,get_item,insert_item,create_or_update_character,
                check_for_duplicate,calculate_file_hash,update_runes,
                touch_character,update_item_full,find_character_equipped_item)
from config import SCREENSHOTS_DIR, PREVIEWS_DIR
from recognition import process_image
from scan_history import begin,finish

def run_capture(service):
    from capture import capture_screen,play_sound
    mode,character,swap,location=service.scan_mode,service.current_character,service.is_swap,service.current_location
    uid=uuid.uuid4().hex
    filename=f"d2_{time.strftime('%Y-%m-%d_%H-%M-%S')}_{uid[:8]}.png"
    target=('Najemnik: ' if mode=='merc' else 'Postać: ')+character if mode in ('character','merc') else (location or 'Skrzynia')
    begin(uid,mode,target,filename)
    service.queue_count=1
    def outcome(state,message,kind='',name='',result_id='',raw=None):
        finish(uid,state,kind,name,result_id,message,raw)
        service.last_activity=dict(state=state,message=message,item_name=name,item_id=result_id,request_id=uid,timestamp=time.time(),queue_count=0)
        service._add_log(message,{'success':'Zapisano','rejected':'Odrzucono','error':'Błąd','review':'Do zatwierdzenia'}.get(state,state))
    try:
        if mode == 'merc' and not get_character(character):
            raise ValueError('Wybierz istniejącą postać przed skanowaniem wyposażenia najemnika.')
        service.last_activity=dict(state='analyzing',message='Wycinam obszar odczytu i sprawdzam zawartość…',request_id=uid,timestamp=time.time())
        screen=capture_screen()
        screen.save(SCREENSHOTS_DIR/filename)
        from capture_regions import crop_for_ai
        crop,bounds=crop_for_ai(screen,mode)
        preview=uid+'.png';crop.save(PREVIEWS_DIR/preview)
        service.total_captured+=1
        result=process_image(PREVIEWS_DIR/preview,mode,uid)
        if result['status']!='success':
            play_sound('error')
            if getattr(service,'wizard_active',False):service.last_stat_scan=dict(status='error',message=result['message'])
            outcome(result['status'],result['message'],raw=result.get('raw'));return
        kind=result['type'];data=result['data']
        if kind=='character':
            data=dict(data,screenshot_filename=filename)
            existing=get_character(data.get('name', ''))
            if existing:
                merged = dict(existing)
                merged.update({k: v for k, v in data.items() if v is not None and v != ''})
                merged['screenshot_filename'] = filename
                saved = create_or_update_character(merged)
                service.current_character = saved['name']
                service.last_stat_scan = dict(status='success', character=saved, data=saved)
                service.wizard_active = False
                outcome('success', 'Zaktualizowano postać: ' + saved['name'], kind, saved['name'], saved['id'], result['raw'])
            elif getattr(service, 'wizard_active', False):
                service.last_stat_scan = dict(status='success', character=data, data=data, request_id=uid)
                outcome('review', 'Odczytano ' + data['name'] + '. Potwierdź postać w kreatorze.', kind, data['name'], raw=result['raw'])
            else:
                saved = create_or_update_character(data)
                service.current_character = saved['name']
                service.last_stat_scan = dict(status='success', character=saved, data=saved)
                outcome('success', 'Zapisano statystyki: ' + saved['name'], kind, saved['name'], saved['id'], result['raw'])
        elif kind in ('gems_stash', 'materials_stash'):
            from stack_stash import save_snapshot, TABS
            tab = kind.removesuffix('_stash')
            save_snapshot(tab, data)
            outcome('success', TABS[tab][0]+': '+str(sum(x['count'] for x in data))+' szt.', kind, TABS[tab][0], raw=result['raw'])
        elif kind=='rune_stash':
            update_runes(data,preview_filename=preview)
            outcome('success','Zapisano zakładkę run: '+str(sum(data.values()))+' szt.',kind,'Zakładka run',raw=result['raw'])
        else:
            slot=data['slot'];char_slot='';char_name='';is_dup=False;dup_of=''
            if mode=='merc':
                if not character:raise ValueError('Wybierz postać przed skanowaniem wyposażenia najemnika.')
                eq=get_character_equipment(character)
                if slot=='head':char_slot='merc_head'
                elif slot=='armor':char_slot='merc_armor'
                elif slot=='shield':char_slot='merc_offhand'
                elif slot=='weapon':
                    char_slot='merc_offhand' if (eq.get('merc_weapon') and not eq.get('merc_offhand')) else 'merc_weapon'
                else:raise ValueError('Przedmiot nie pasuje do wyposażenia najemnika.')
                char_name=character
            elif mode=='character':
                active_char = character or service.current_character
                if not active_char or not get_character(active_char):
                    raise ValueError('Wybierz istniejącą postać przed skanowaniem ekwipunku.')
                character = active_char
                eq=get_character_equipment(character)
                w_slot='weapon2' if swap else 'weapon1'
                s_slot='shield2' if swap else 'shield1'
                if slot=='shield':char_slot=s_slot
                elif slot=='weapon':
                    char_slot=s_slot if (eq.get(w_slot) and not eq.get(s_slot)) else w_slot
                elif slot=='ring':char_slot='ring2' if eq.get('ring1') else 'ring1'
                elif slot=='charm':char_slot='charms'
                elif slot in ('head','armor','gloves','belt','boots','amulet'):char_slot=slot
                else:raise ValueError('Nie znaleziono slotu dla tego przedmiotu. Użyj trybu Skrzynia.')
                char_name=character
            image_hash=calculate_file_hash(PREVIEWS_DIR/preview)
            equipped_item = None
            if mode in ('character', 'merc') and char_name:
                equipped_item = find_character_equipped_item(
                    char_name,
                    name=data.get('name', ''),
                    quality=data.get('quality', ''),
                    stats=data.get('stats'),
                    image_hash=image_hash,
                    slot=char_slot
                )

            if equipped_item and mode in ('character', 'merc'):
                item_id = equipped_item['id']
                update_payload = dict(data,
                    preview_filename=preview,
                    screenshot_filename=filename,
                    image_hash=image_hash,
                    location=target,
                    character_name=char_name,
                    character_slot=char_slot or equipped_item.get('character_slot', '')
                )
                update_item_full(item_id, update_payload)
                touch_character(char_name)
                saved = get_item(item_id)
                if data.get('socket_contents'):
                    from uber_features import trade_details, save_trade_details
                    extra = trade_details(saved)
                    contents = data['socket_contents']
                    extra['socket_contents'] = ', '.join(contents) if isinstance(contents, list) else str(contents)
                    save_trade_details(saved, extra)
                outcome('success', f"Zaktualizowano postać {char_name}: {saved['name']}", kind, saved['name'], saved['id'], result['raw'])
            else:
                if not char_name:
                    is_dup, dup_of, _ = check_for_duplicate(data['name'], data['quality'], data['stats'], image_hash)
                stash_loc = location or 'Skrzynia'
                record = dict(data, id=uid, preview_filename=preview, screenshot_filename=filename, location=target if char_name else stash_loc, notes='', is_duplicate=int(is_dup), duplicate_of=dup_of, image_hash=image_hash, character_name=char_name, character_slot=char_slot)
                insert_item(record)
                if char_name:
                    touch_character(char_name)
                saved = get_item(uid)
                if data.get('socket_contents'):
                    from uber_features import trade_details, save_trade_details
                    extra = trade_details(saved)
                    contents = data['socket_contents']
                    extra['socket_contents'] = ', '.join(contents) if isinstance(contents, list) else str(contents)
                    save_trade_details(saved, extra)
                msg = ('Zapisano możliwy duplikat: ' if is_dup else 'Zapisano: ') + saved['name']
                if char_name:
                    msg = f"Zaktualizowano ekwipunek {char_name}: {saved['name']}"
                outcome('success', msg, kind, saved['name'], saved['id'], result['raw'])
        play_sound('drop')
    except Exception as error:
        play_sound('error')
        if getattr(service,'wizard_active',False):service.last_stat_scan=dict(status='error',message=str(error))
        outcome('error',str(error))
    finally:service.queue_count=0
