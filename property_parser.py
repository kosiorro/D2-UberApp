import re
import unicodedata

def norm(text):return ''.join(c for c in unicodedata.normalize('NFKD',str(text).lower().replace('ł','l')) if not unicodedata.combining(c))

def extended_bonus(line):
    text=norm(line).strip().rstrip('.')
    match=re.fullmatch(r'\+?(\d+)\s+(?:do\s+)?(.+)',text)
    if match:
        amount=int(match[1]);label=match[2]
        # Class/tree/single-skill bonuses are separate from all-skills and from charges/procs.
        if not any(x in label for x in ('szansa','chance','ladunk','charges','poziomu postaci','per character','trafieni','striking')):
            classes={'paladyn':'Paladyn','paladin':'Paladyn','czarodziejk':'Czarodziejka','sorceress':'Czarodziejka','amazon':'Amazonka','barbar':'Barbarzyńca','nekroman':'Nekromanta','necroman':'Nekromanta','druid':'Druid','zabojczyn':'Zabójczyni','assassin':'Zabójczyni'}
            class_name=next((value for key,value in classes.items() if key in label),'')
            trees=[(r'aur\w* ofensywn\w*|offensive auras','Aury Ofensywne'),(r'aur\w* defensywn\w*|defensive auras','Aury Defensywne'),(r'umiejetnosci walki|combat skills','Umiejętności walki'),(r'zaklec\w* ognia|fire skills','Umiejętności ognia'),(r'zaklec\w* zimna|cold skills','Umiejętności zimna'),(r'zaklec\w* blyskawic|lightning skills','Umiejętności błyskawic'),(r'przywolywan\w*|summoning skills','Przywoływanie'),(r'okrzyk\w*|warcries','Okrzyki'),(r'pulapk\w*|traps','Pułapki')]
            tree=next((name for pattern,name in trees if re.search(pattern,label)),None)
            suffix=' ('+class_name+')' if class_name else ''
            if tree:return 'Drzewko: '+tree+suffix,'',amount
            if class_name and (re.search(r'umiejetnosci (?:paladyn|czarodziej|amazon|barbar|nekroman|druid|zabojczyn)',label) or re.search(r'(paladin|sorceress|amazon|barbarian|necromancer|druid|assassin) skill',label)):
                return 'Umiejętności klasy: '+class_name,'',amount
            if 'umiejetnosci' in label and not 'wszystkich' in label:
                return 'Umiejętność: '+label.replace('umiejetnosci ','',1).strip().capitalize(),'',amount
    extras=[(r'\+?(\d+)\s+(?:do )?przywracania zdrowia','Przywracanie zdrowia',''),
            (r'\+?(\d+)%\s+(?:do )?maksymalnej wartosci punktow many','Maksymalna mana','%'),
            (r'\+?(\d+)\s+(?:do )?promienia swiatla','Promień światła',''),
            (r'\+?(\d+)\s+(?:do )?absorpcji magii','Absorpcja magii',''),
            (r'zmniejsza otrzymywane obrazenia od magii o (\d+) pkt','Redukcja obrażeń od magii',''),
            (r'odnoszone obrazenia fizyczne sa zmniejszone o (\d+)%','Redukcja obrażeń fizycznych','%')]
    for pattern,label,unit in extras:
        match=re.fullmatch(pattern,text)
        if match:return label,unit,float(match[1])
    return None
