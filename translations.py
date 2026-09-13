# -*- coding: utf-8 -*-
"""Comprehensive Bilingual translations (Polish & English) for D2 UberApp."""

TRANSLATIONS = {
    'pl': {
        # Brand & Nav
        'brand_name': 'D2 UberApp',
        'brand_subtitle': 'DIIR · TWÓJ SKARBIEC',
        'sub_brand': 'SANCTUARY VAULT · GEMINI AI',
        'companion_btn': 'Aplikacja towarzysząca',
        'companion_title_hint': 'Przechwytywanie, skrót i ustawienia AI',
        'nav_stash': 'SKRZYNIA & MUŁY',
        'nav_character': 'POSTACIE & EKWIPUNEK',
        'nav_runes': 'RUNY & SŁOWA',
        'nav_trade': 'LISTA SPRZEDAŻY',
        'nav_duplicates': 'DUPLIKATY',
        'nav_costs': 'KOSZTY API',

        # Language Switcher
        'lang_pl': 'PL',
        'lang_en': 'EN',
        'lang_switch_title': 'Zmień język / Change language',

        # Header Characters
        'chars_more': '+ Więcej ({count})',
        'chars_more_short': '+ Więcej',
        'chars_all_title': 'Wszystkie postacie',

        # Live scan banner
        'banner_scan_mode': 'TRYB SKANOWANIA EKWIPUNKU POSTACI:',
        'banner_scan_desc': 'Najeżdżaj w grze na kolejne założone przedmioty i klikaj {hotkey}. Itemy automatycznie wskakują na lalkę rynsztunku!',
        'swap_weapon_label': 'SWAP BRONI:',
        'swap_main': 'GŁÓWNY (I)',
        'swap_secondary': 'ZAPASOWY (II)',
        'btn_stop_scan': 'STOP: ZAKOŃCZ SKANOWANIE',

        # Intro Section
        'kicker_collection': 'D2 UberApp / KOLEKCJA',
        'intro_quote': 'Każdy przedmiot ma swoją historię. Tutaj zaczyna się następna.',
        'hero_count_label': 'BOHATEROWIE',
        'intro_title_items': 'Skarbiec wędrowca',
        'intro_title_character': 'Twoi bohaterowie',
        'intro_title_runes': 'Moc zaklęta w runach',
        'intro_title_trade': 'Kantor wędrowca',
        'intro_title_duplicates': 'Porządek w skarbcu',
        'intro_title_costs': 'Historia analiz',
        'intro_title_default': 'Twój skarbiec',

        # Stash View
        'stash_title': 'SKRZYNIA & PRZEDMIOTY MUŁÓW',
        'stash_subtitle': 'Przedmioty w magazynie (założony ekwipunek bohaterów jest w zakładce Postacie)',
        'stash_search_placeholder': 'Szukaj przedmiotu...',
        'stash_all_qualities': 'Wszystkie jakości',
        'stash_all_locations': 'Wszystkie skrzynie / muły',
        'btn_cards': 'KAFELKI',
        'btn_table': 'TABELA',
        'stash_empty': 'Brak przedmiotów spełniających wybrane kryteria.',

        # Qualities
        'quality_unique': 'UNIKAT',
        'quality_unique_opt': 'Unikalne',
        'quality_runeword': 'SŁOWO RUNICZNE',
        'quality_runeword_opt': 'Słowa runiczne',
        'quality_set': 'ZESTAW',
        'quality_set_opt': 'Zestawy',
        'quality_rare': 'RZADKI',
        'quality_rare_opt': 'Rzadkie',
        'quality_magic': 'MAGICZNY',
        'quality_magic_opt': 'Magiczne',
        'quality_crafted': 'RZEMIEŚLNICZY',
        'quality_normal': 'NORMALNY',
        'quality_base': 'Bazy',
        'quality_all': 'Wszystkie',

        # Item Card Stats & Badges
        'chip_defense': 'Obrona: {val}',
        'chip_damage': 'Dmg: {val}',
        'chip_level': 'Lvl: {val}',
        'chip_str': 'Siła: {val}',
        'chip_dex': 'Zręczność: {val}',
        'chip_sockets': 'Gniazda: {val}',
        'label_defense': 'Obrona:',
        'label_damage': 'Obrażenia:',
        'label_req_level': 'Wymagany poziom:',
        'label_req_str': 'Wymagana siła:',
        'label_req_dex': 'Wymagana zręczność:',
        'label_sockets': 'Gniazda:',
        'label_in_trade': 'W sprzedaży',
        'btn_details': 'ZOBACZ WIĘCEJ',
        'btn_trade_pricing': 'WYCENA / HANDEL',
        'badge_in_trade': 'W SPRZEDAŻY',
        'btn_delete': 'Usuń',
        'btn_add_trade': 'Dodaj do sprzedaży',
        'btn_remove_trade': 'Usuń ze sprzedaży',
        'btn_equip': 'Załóż na postać',

        # Stash Table
        'th_table_item': 'PRZEDMIOT',
        'th_table_def_dmg': 'OBRONA / DMG',
        'th_table_reqs': 'WYMAGANIA',
        'th_table_stats': 'STATYSTYKI Z ITEMU',
        'th_table_rolls': 'ZMIENNE ROLLS',
        'th_table_actions': 'AKCJE',

        # Character Sheet (uber-character.html)
        'char_sheet_title': 'POSTAĆ',
        'char_default_name': 'Twój bohater',
        'char_add_prompt': 'Dodaj postać w D2 UberApp',
        'char_level_prefix': 'Poz.',
        'char_exp_label': 'Doświadczenie · {val}',
        'char_no_exp': 'Brak odczytu',
        'attr_strength': 'Siła',
        'attr_dexterity': 'Zręczność',
        'attr_vitality': 'Żywotność',
        'attr_energy': 'Energia',
        'vital_main_skill': 'Umiejętność',
        'vital_damage': 'Obrażenia',
        'vital_defense': 'Obrona',
        'vital_stamina': 'Wytrzymałość',
        'vital_life': 'Życie',
        'vital_mana': 'Mana',
        'res_fire': 'Ogień',
        'res_light': 'Błyskawice',
        'res_cold': 'Zimno',
        'res_poison': 'Trucizna',
        'char_sheet_note': 'Wartości z ostatniego skanu okna postaci. Sumy bonusów wyposażenia pokazujemy osobno.',
        'btn_manage_companion': 'Zarządzaj postacią w D2 UberApp ↗',
        'char_gear_title': 'EKWIPUNEK',
        'gear_tab_main': 'Zestaw I',
        'gear_tab_swap': 'Zestaw II',
        'gear_tab_merc': 'Najemnik',
        'slot_head': 'Hełm',
        'slot_armor': 'Pancerz',
        'slot_weapon': 'Broń',
        'slot_offhand': 'Off-hand',
        'slot_amulet': 'Amulet',
        'slot_gloves': 'Rękawice',
        'slot_boots': 'Buty',
        'slot_belt': 'Pas',
        'slot_ring1': 'Pierścień I',
        'slot_ring2': 'Pierścień II',
        'charms_title': 'TALIZMANY',
        'charms_empty': 'Brak zeskanowanych talizmanów.',
        'gear_bonus_header': '{label} · bonusy wyposażenia',
        'items_count': '{count} przedmiotów',
        'gear_bonus_empty': 'Nie ma jeszcze rozpoznanych bonusów do zsumowania.',
        'gear_unaggregated_title': 'Pozostałe właściwości — bez automatycznego sumowania ({count})',
        'gear_properties_title': 'Wszystkie właściwości · źródła bonusów',
        'item_defense_note': 'Obrona przedmiotu: {val}',
        'item_damage_note': 'Obrażenia przedmiotu: {val}',
        'gear_scan_hint': 'Wybierz w aplikacji towarzyszącej tryb {mode} i zeskanuj wyposażenie.',

        # Runes & Runewords
        'rune_stash_title': 'SKRYTKA RUN (UKŁAD 11 × 3 D2R) & SŁOWA RUNICZNE',
        'rune_stash_sub': 'Twój stan run i automatyczny kalkulator możliwych do ułożenia słów runicznych',
        'all_base_types': 'Wszystkie typy baz',
        'badge_missing_rune': 'BRAK',
        'rw_tab_craftable': 'Możliwe do złożenia ({count})',
        'rw_tab_missing1': 'Brakuje 1 runy ({count})',
        'rw_tab_all': 'Wszystkie słowa ({count})',
        'runes_filter_weapons': 'Bronie',
        'runes_filter_armors': 'Zbroje',
        'runes_filter_shields': 'Tarcze',
        'runes_filter_helms': 'Hełmy',

        # Trade list
        'trade_title': 'LISTA SPRZEDAŻY',
        'trade_sub': 'Zarządzaj ofertami handlowymi, ustalaj ceny (runy, przedmioty, fg) i eksportuj gotowy tekst',
        'btn_sync_market': 'Synchronizuj z D2 Marketplace',
        'btn_export_text': 'Eksportuj do tekstu',
        'btn_add_to_trade': '+ Dodaj przedmioty ze skrytki',
        'trade_empty_note': 'Brak przedmiotów na liście sprzedaży. Dodaj przedmioty ze skrytki!',
        'th_trade_item': 'PRZEDMIOT',
        'th_trade_base': 'JAKOŚĆ / BAZA',
        'th_trade_rolls': 'ZMIENNE STATYSTYKI',
        'th_trade_price': 'CENA',
        'th_trade_notes': 'NOTATKI',
        'th_trade_actions': 'AKCJE',
        'trade_price_default': 'Czekam na ofertę',

        # Duplicates
        'dup_title': 'WYKRYWACZ DUPLIKATÓW',
        'dup_sub': 'Przedmioty o tej samej nazwie lub bazie — porównaj statystyki i wybierz najlepszy roll',
        'dup_empty': 'Brak duplikatów w Twojej skrytce.',
        'dup_repeats': '{count} powtórzeń',
        'dup_btn_separate': 'Rozdziel tę grupę',

        # Costs & API
        'costs_title': 'HISTORIA ANALIZ & KOSZTY API',
        'costs_sub': 'Statystyki zużycia tokenów Gemini Flash Lite i estymowany koszt',
        'costs_total_calls': 'ŁĄCZNIE SKANÓW',
        'costs_total_cost': 'SZACUNKOWY KOSZT',
        'costs_avg_time': 'ŚR. CZAS SKANU',

        # Modals
        'modal_details_title': 'SZCZEGÓŁY PRZEDMIOTU',
        'modal_export_title': 'EKSPORT LISTY HANDLOWEJ',
        'modal_sync_title': 'SYNCHRONIZACJA Z D2 MARKETPLACE',
        'btn_close': 'Zamknij',
        'btn_copy': 'Kopiuj listę',
        'btn_save': 'Zapisz',
        'btn_cancel': 'Anuluj',

        # Companion HUD
        'companion_brand': 'UBERAPP',
        'companion_sub': 'COMPANION HUD',
        'companion_status_title': 'STATUS NASŁUCHU',
        'companion_ready': 'Gotowy na kolejny łup.',
        'companion_listening': 'Nasłuch',
        'companion_paused': 'Pauza',
        'companion_connecting': 'Łączenie…',
        'companion_mode_title': 'TRYB SKANOWANIA',
        'companion_mode_stash': 'Skrzynia',
        'companion_mode_character': 'Postać',
        'companion_mode_merc': 'Najemnik',
        'companion_mode_runes': 'Runy',
        'companion_mode_stats': 'Statystyki',
        'companion_hero_title': 'BIEŻĄCA POSTAĆ',
        'companion_topmost': 'Zawsze na wierzchu (Topmost)',
        'companion_recent_title': 'OSTATNIE SKANY',
        'companion_btn_new_hero': '+ Nowa postać (F10)',
        'companion_btn_edit': 'Edytuj',
        'companion_nav_vault': 'Skrzynia',
        'companion_nav_characters': 'Postacie',
        'companion_nav_runes': 'Runy',
        'companion_nav_trade': 'Handel',
        'companion_nav_settings': 'Ustawienia',
        'companion_wizard_title': '1. Zeskanuj statystyki',
        'companion_wizard_desc': 'Przejdź do gry, otwórz okno statystyk postaci i naciśnij {hotkey}. Wróć tutaj po odczycie.',
        'companion_wizard_waiting': 'Oczekiwanie na zrzut…',
    },
    'en': {
        # Brand & Nav
        'brand_name': 'D2 UberApp',
        'brand_subtitle': 'DIIR · YOUR VAULT',
        'sub_brand': 'SANCTUARY VAULT · GEMINI AI',
        'companion_btn': 'Companion App',
        'companion_title_hint': 'Capture, hotkey and AI settings',
        'nav_stash': 'STASH & MULES',
        'nav_character': 'HEROES & GEAR',
        'nav_runes': 'RUNES & WORDS',
        'nav_trade': 'TRADE LIST',
        'nav_duplicates': 'DUPLICATES',
        'nav_costs': 'API COSTS',

        # Language Switcher
        'lang_pl': 'PL',
        'lang_en': 'EN',
        'lang_switch_title': 'Change language / Zmień język',

        # Header Characters
        'chars_more': '+ More ({count})',
        'chars_more_short': '+ More',
        'chars_all_title': 'All Characters',

        # Live scan banner
        'banner_scan_mode': 'CHARACTER GEAR SCANNING MODE:',
        'banner_scan_desc': 'Hover over equipped items in game and press {hotkey}. Items will automatically land on your character sheet!',
        'swap_weapon_label': 'WEAPON SWAP:',
        'swap_main': 'MAIN (I)',
        'swap_secondary': 'OFF-SET (II)',
        'btn_stop_scan': 'STOP: FINISH SCANNING',

        # Intro Section
        'kicker_collection': 'D2 UberApp / COLLECTION',
        'intro_quote': 'Every item has a story. Here begins the next chapter.',
        'hero_count_label': 'HEROES',
        'intro_title_items': "Wanderer's Vault",
        'intro_title_character': 'Your Heroes',
        'intro_title_runes': 'Power of the Runes',
        'intro_title_trade': "Trader's Exchange",
        'intro_title_duplicates': 'Vault Organization',
        'intro_title_costs': 'Analysis History',
        'intro_title_default': 'Your Vault',

        # Stash View
        'stash_title': 'STASH & MULE VAULT',
        'stash_subtitle': 'Items in inventory storage (equipped hero gear is in the Characters tab)',
        'stash_search_placeholder': 'Search item (e.g. Shako, Ber, Enigma)...',
        'stash_all_qualities': 'All Qualities',
        'stash_all_locations': 'All Stashes / Mules',
        'btn_cards': 'CARDS',
        'btn_table': 'TABLE',
        'stash_empty': 'No items matching your filter criteria.',

        # Qualities
        'quality_unique': 'UNIQUE',
        'quality_unique_opt': 'Uniques',
        'quality_runeword': 'RUNEWORD',
        'quality_runeword_opt': 'Runewords',
        'quality_set': 'SET',
        'quality_set_opt': 'Sets',
        'quality_rare': 'RARE',
        'quality_rare_opt': 'Rare',
        'quality_magic': 'MAGIC',
        'quality_magic_opt': 'Magic',
        'quality_crafted': 'CRAFTED',
        'quality_normal': 'NORMAL',
        'quality_base': 'Bases',
        'quality_all': 'All',

        # Item Card Stats & Badges
        'chip_defense': 'Defense: {val}',
        'chip_damage': 'Dmg: {val}',
        'chip_level': 'Lvl: {val}',
        'chip_str': 'Str: {val}',
        'chip_dex': 'Dex: {val}',
        'chip_sockets': 'Sockets: {val}',
        'label_defense': 'Defense:',
        'label_damage': 'Damage:',
        'label_req_level': 'Required Level:',
        'label_req_str': 'Required Strength:',
        'label_req_dex': 'Required Dexterity:',
        'label_sockets': 'Sockets:',
        'label_in_trade': 'In Trade List',
        'btn_details': 'VIEW DETAILS',
        'btn_trade_pricing': 'LIST FOR TRADE',
        'badge_in_trade': 'IN TRADE',
        'btn_delete': 'Delete',
        'btn_add_trade': 'Add to Trade',
        'btn_remove_trade': 'Remove from Trade',
        'btn_equip': 'Equip on Hero',

        # Stash Table
        'th_table_item': 'ITEM',
        'th_table_def_dmg': 'DEFENSE / DMG',
        'th_table_reqs': 'REQUIREMENTS',
        'th_table_stats': 'ITEM STATS',
        'th_table_rolls': 'VARIABLE ROLLS',
        'th_table_actions': 'ACTIONS',

        # Character Sheet (uber-character.html)
        'char_sheet_title': 'HERO',
        'char_default_name': 'Your Hero',
        'char_add_prompt': 'Add hero in D2 UberApp',
        'char_level_prefix': 'Lvl',
        'char_exp_label': 'Experience · {val}',
        'char_no_exp': 'Not recorded',
        'attr_strength': 'Strength',
        'attr_dexterity': 'Dexterity',
        'attr_vitality': 'Vitality',
        'attr_energy': 'Energy',
        'vital_main_skill': 'Main Skill',
        'vital_damage': 'Damage',
        'vital_defense': 'Defense',
        'vital_stamina': 'Stamina',
        'vital_life': 'Life',
        'vital_mana': 'Mana',
        'res_fire': 'Fire',
        'res_light': 'Lightning',
        'res_cold': 'Cold',
        'res_poison': 'Poison',
        'char_sheet_note': 'Values from latest character sheet scan. Equipment bonus totals are shown separately.',
        'btn_manage_companion': 'Manage character in D2 UberApp ↗',
        'char_gear_title': 'EQUIPMENT',
        'gear_tab_main': 'Weapon Set I',
        'gear_tab_swap': 'Weapon Set II',
        'gear_tab_merc': 'Mercenary',
        'slot_head': 'Helm',
        'slot_armor': 'Armor',
        'slot_weapon': 'Weapon',
        'slot_offhand': 'Off-hand',
        'slot_amulet': 'Amulet',
        'slot_gloves': 'Gloves',
        'slot_boots': 'Boots',
        'slot_belt': 'Belt',
        'slot_ring1': 'Ring I',
        'slot_ring2': 'Ring II',
        'charms_title': 'CHARMS',
        'charms_empty': 'No scanned charms.',
        'gear_bonus_header': '{label} · gear bonuses',
        'items_count': '{count} items',
        'gear_bonus_empty': 'No recognized bonuses to sum yet.',
        'gear_unaggregated_title': 'Remaining properties — unaggregated ({count})',
        'gear_properties_title': 'All properties · bonus sources',
        'item_defense_note': 'Item Defense: {val}',
        'item_damage_note': 'Item Damage: {val}',
        'gear_scan_hint': 'Select {mode} mode in Companion and scan equipped gear.',

        # Runes & Runewords
        'rune_stash_title': 'RUNE STASH (11 × 3 D2R LAYOUT) & RUNEWORDS',
        'rune_stash_sub': 'Your rune inventory and automatic crafting calculator for possible runewords',
        'all_base_types': 'All base types',
        'badge_missing_rune': 'MISSING',
        'rw_tab_craftable': 'Craftable Now ({count})',
        'rw_tab_missing1': 'Missing 1 Rune ({count})',
        'rw_tab_all': 'All Runewords ({count})',
        'runes_filter_weapons': 'Weapons',
        'runes_filter_armors': 'Armors',
        'runes_filter_shields': 'Shields',
        'runes_filter_helms': 'Helms',

        # Trade list
        'trade_title': 'TRADE LIST',
        'trade_sub': 'Manage trade listings, set prices (runes, items, fg) and export formatted trade posts',
        'btn_sync_market': 'Sync with Online Marketplace',
        'btn_export_text': 'Export to Text',
        'btn_add_to_trade': '+ Add Items from Stash',
        'trade_empty_note': 'No items in trade list. Add items from your stash!',
        'th_trade_item': 'ITEM',
        'th_trade_base': 'QUALITY / BASE',
        'th_trade_rolls': 'VARIABLE ROLLS',
        'th_trade_price': 'PRICE',
        'th_trade_notes': 'NOTES',
        'th_trade_actions': 'ACTIONS',
        'trade_price_default': 'Offer',

        # Duplicates
        'dup_title': 'DUPLICATE DETECTOR',
        'dup_sub': 'Items with the same name or base — compare rolls and keep the best',
        'dup_empty': 'No duplicates found in your stash.',
        'dup_repeats': '{count} copies',
        'dup_btn_separate': 'Separate this group',

        # Costs & API
        'costs_title': 'ANALYSIS HISTORY & API COSTS',
        'costs_sub': 'Gemini Flash Lite token usage statistics and estimated cost',
        'costs_total_calls': 'TOTAL SCANS',
        'costs_total_cost': 'ESTIMATED COST',
        'costs_avg_time': 'AVG SCAN TIME',

        # Modals
        'modal_details_title': 'ITEM DETAILS',
        'modal_export_title': 'EXPORT TRADE LIST',
        'modal_sync_title': 'SYNC WITH ONLINE MARKET',
        'btn_close': 'Close',
        'btn_copy': 'Copy List',
        'btn_save': 'Save',
        'btn_cancel': 'Cancel',

        # Companion HUD
        'companion_brand': 'UBERAPP',
        'companion_sub': 'COMPANION HUD',
        'companion_status_title': 'CAPTURE STATUS',
        'companion_ready': 'Ready for next loot.',
        'companion_listening': 'Listening',
        'companion_paused': 'Paused',
        'companion_connecting': 'Connecting…',
        'companion_mode_title': 'CAPTURE MODE',
        'companion_mode_stash': 'Stash',
        'companion_mode_character': 'Character',
        'companion_mode_merc': 'Mercenary',
        'companion_mode_runes': 'Runes',
        'companion_mode_stats': 'Stats',
        'companion_hero_title': 'ACTIVE HERO',
        'companion_topmost': 'Always on top (Topmost)',
        'companion_recent_title': 'RECENT SCANS',
        'companion_btn_new_hero': '+ New Character (F10)',
        'companion_btn_edit': 'Edit',
        'companion_nav_vault': 'Stash',
        'companion_nav_characters': 'Heroes',
        'companion_nav_runes': 'Runes',
        'companion_nav_trade': 'Trade',
        'companion_nav_settings': 'Settings',
        'companion_wizard_title': '1. Scan Character Sheet',
        'companion_wizard_desc': 'Switch to game, open character stats sheet and press {hotkey}. Return here once captured.',
        'companion_wizard_waiting': 'Awaiting capture…',
    }
}

def get_t(lang='pl'):
    if lang not in TRANSLATIONS:
        lang = 'pl'
    current_dict = TRANSLATIONS[lang]
    fallback_dict = TRANSLATIONS['pl']

    def t(key, **kwargs):
        val = current_dict.get(key, fallback_dict.get(key, key))
        if kwargs:
            try:
                return val.format(**kwargs)
            except Exception:
                return val
        return val

    return t

def get_item_title(item, lang='pl'):
    if not item:
        return ''
    if lang == 'en':
        if item.get('name_en') and str(item['name_en']).strip():
            return str(item['name_en']).strip()
    return item.get('display_name') or item.get('name') or item.get('name_en') or 'Przedmiot'

def get_roll_label(r, lang='pl'):
    if not r:
        return ''
    if lang == 'en':
        if r.get('label_en'):
            return r['label_en']
        prop = r.get('property')
        try:
            from catalog_matcher import PROP_NAMES_EN
            if prop and prop in PROP_NAMES_EN:
                return PROP_NAMES_EN[prop]
        except Exception:
            pass
    return r.get('label') or r.get('property_pl') or r.get('property') or ''
