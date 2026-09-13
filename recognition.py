import json
import time
from PIL import Image
from google.genai import types
import config
from db import record_api_call
from catalog_matcher import catalog_matcher
from scan_validation import PROMPT, validate, RejectedScan

def process_image(image_path, scan_mode='normal', request_id=''):
    from ai_processor import get_client, detect_item_slot
    started = time.monotonic()
    prompt_tokens = output_tokens = 0
    kind = 'unknown'
    name = ''
    status = 'error'
    message = ''
    data = {}
    try:
        with Image.open(image_path) as original:
            image = original.convert('RGB')

        is_rune_grid = (scan_mode == 'runes') or (460 <= image.width <= 480 and 250 <= image.height <= 275)
        if is_rune_grid:
            from rune_processor import read_rune_stash
            runes_dict, prompt_tokens, output_tokens = read_rune_stash(image, get_client(), config.GEMINI_MODEL)
            active_count = sum(1 for v in runes_dict.values() if v > 0)
            total_runes = sum(runes_dict.values())
            kind = 'rune_stash'
            name = f'Zakladka run ({active_count} typow, {total_runes} szt.)'
            status = 'success'
            message = f'Odczyt zweryfikowany: {name}'
            return dict(
                status='success',
                type='rune_stash',
                data=runes_dict,
                runes=runes_dict,
                raw=runes_dict,
                request_id=request_id
            )

        hint = {'normal':'automatyczny','stat_screen':'wylacznie okno statystyk postaci','runes':'wylacznie cala zakladka run','stash':'wylacznie tooltip przedmiotu','character':'wylacznie tooltip wyposazenia postaci','merc':'wylacznie tooltip wyposazenia najemnika'}.get(scan_mode, 'automatyczny')
        response = get_client().models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[image, PROMPT + '\nWybrany cel: ' + hint],
            config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.0)
        )
        usage = getattr(response, 'usage_metadata', None)
        prompt_tokens = getattr(usage, 'prompt_token_count', 0) or 0
        output_tokens = getattr(usage, 'candidates_token_count', 0) or 0
        data = json.loads(response.text or '{}')
        kind, content = validate(data, scan_mode)

        if kind == 'item':
            name = content['name']
            from scan_validation import normalized
            quality = content.get('quality', '')
            cat = catalog_matcher.find_item(name, None, quality)
            if quality in ('runeword', 'unikalny', 'zestaw'):
                if cat and normalized(name) not in (normalized(cat.get('name', '')), normalized(cat.get('name_en', ''))):
                    raise RejectedScan(f'Niepewna nazwa "{name}" - podobne dopasowanie katalogowe zostalo odrzucone. Zeskanuj nazwe ponownie.')
                if not cat:
                    raise RejectedScan(f'Nie potwierdzono nazwy "{name}" w katalogu. Popraw czytelnosc opisu i ponow skan.')
                if cat and quality == 'runeword':
                    types_allowed = json.loads(cat.get('include_types_json') or '[]')
                    armor_types = {'tors':'armor','shld':'shield','ashd':'shield','head':'shield','helm':'head','phlm':'head','pelt':'head','circ':'head'}
                    allowed = {armor_types.get(t, 'weapon') for t in types_allowed}
                    if allowed and content['slot'] not in allowed:
                        raise RejectedScan('Nazwa slowa runicznego nie zgadza sie z typem widocznej bazy. Ponow skan calego opisu.')
            else:
                # Bazy przedmiotow normalnych, magicznych, rzadkich i rzemielniczych
                # Szukanie bazy w katalogu jesli brak dokladnego dopasowania nazwy
                if cat and normalized(name) not in (normalized(cat.get('name', '')), normalized(cat.get('name_en', ''))):
                    base_candidate = content.get('base') or name
                    base_cat = catalog_matcher.find_item(base_candidate, None, 'normalny')
                    cat = base_cat if base_cat else None
            content['catalog_id'] = cat.get('id') if cat else ''

            content['rolls_eval'] = catalog_matcher.evaluate_item_rolls(cat, content['stats'], content.get('rolls') or {}) if cat else []
            content['requirements'] = {k: content.get(k) for k in ('level_req', 'req_str', 'req_dex')}
            content['slot'] = detect_item_slot(name, content.get('name_en') or '', content.get('base') or '', content['slot'], content['quality'])
        elif kind == 'character':
            name = content['name']
        else:
            name = 'Zakladka run'

        status = 'success'
        message = f'Odczyt zweryfikowany: {name}'
        return dict(
            status='success',
            type=kind,
            data=content,
            runes=content if kind == 'rune_stash' else None,
            character=content if kind == 'character' else None,
            raw=data,
            request_id=request_id
        )
    except RejectedScan as error:
        status = 'rejected'
        message = str(error)
        return dict(status=status, message=message, raw=data, request_id=request_id)
    except Exception as error:
        message = str(error)
        if config.GEMINI_API_KEY:
            message = message.replace(config.GEMINI_API_KEY, '[ukryty klucz]')
        return dict(status='error', message=message, request_id=request_id)
    finally:
        record_api_call(
            endpoint=kind,
            model=config.GEMINI_MODEL,
            prompt_tokens=prompt_tokens,
            candidates_tokens=output_tokens,
            duration_ms=int((time.monotonic() - started) * 1000),
            status=status,
            notes=message[:1500],
            request_id=request_id
        )

def process_character_stat_screen(image_path, request_id=''):
    return process_image(image_path, 'stat_screen', request_id)
