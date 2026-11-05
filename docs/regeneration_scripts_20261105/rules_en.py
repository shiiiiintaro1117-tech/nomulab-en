"""Duplicate-title disambiguation rules (EN). Deterministic; reads body text only."""
import re, html, datetime

# --- 1. base normalisation -------------------------------------------------
def norm_base(t):
    t = re.sub(r'\bNomu ?[Ll]abo?\s+Wheel\b|\bNomulabo?\s+Wheel\b', 'Nomu Lab Wheel', t)
    t = re.sub(r'(Nomu Lab Wheel) #(\d)', r'\1 No. \2', t)
    return t

# --- 2. component vocabulary -----------------------------------------------
HUB_ALIAS = [  # (canonical, regex)  -- translation variants of the same Japanese name
    ('Evolite', r'(?:Tni\s+)?(?:Evo[- ]?[Ll]ite|Evolight|Ebolite|Evorite|Eyelite|Avolite|EvoLite)'),
    ('Leaf', r'(?:Leaf|Reif|Reaf|Reife)'),
]
STOP = {'The','This','That','These','Those','A','An','Front','Rear','Black','Silver','Red','White',
        'Japanese','H','Its','It','Our','My','Your','Same','New','Old','Original','Both','Each',
        'One','Two','Its','And','With','For','Of','In','On','At','Disc','Wheel','Rim','Thru',
        'Large','Small','Custom','Standard','Stock','Used','Normal','Regular','Center','Centre'}
CHUNK = r"((?:[A-Z0-9][\w\-\.']*[ ]+){0,2}[A-Z0-9][\w\-\.']*)"

def _chunk_before(word, text):
    for m in re.finditer(CHUNK + r'[ ]+' + word + r'\b', text):
        words = m.group(1).split()
        for i in range(len(words)-1, -1, -1):
            if words[i][-1] in '.,' and words[i] not in ('No.',):
                words = words[i+1:]; break
        while words and words[0] in STOP:
            words = words[1:]
        while words and (words[-1] in STOP or re.fullmatch(r'\d+H', words[-1])):
            words = words[:-1]
        if not words: continue
        c = ' '.join(words)
        if re.fullmatch(r'\d+', c): continue
        return c
    return None

def canon_hub(c):
    for canon, rx in HUB_ALIAS:
        if re.fullmatch(rx, c): return canon
    return c

RIM_CODE = r"\b((?:DT\s)?(?:AL|XR|RR|CX|DA|TB|C)-?\d{2,3}[A-Za-z]{0,2}|Crest MK\d|Open Pro|Exalith)\b"

def hub(text):
    c = _chunk_before(r'hubs?', text)
    return canon_hub(c) if c else None

def rim(text):
    c = _chunk_before(r'rims?', text)
    if c and re.search(r'\d', c) or c in ('Open Pro','Exalith'):
        return c
    m = re.search(RIM_CODE, text)
    return m.group(1) if m else (c if c else None)

def holes(text):
    for m in re.finditer(r'(?<![\d.:])(\d{2})\s?(?:H\b|-?holes?\b|-hole\b)', text):
        n = int(m.group(1))
        if 12 <= n <= 48: return f'{n}H'
    return None

NUM = {'zero':'0','one':'1','two':'2','three':'3','four':'4','six':'6','single':'1','double':'2'}
def lacing(text):
    parts = []
    if re.search(r'\b(?:half|semi)[- ]?comp(?:etition|e)?\b', text, re.I): parts.append('half-comp')
    m = re.search(r'(?<![\d:\-])(\d|zero|one|two|three|four|six)[- ]cross\b', text, re.I)
    if m: parts.append(NUM.get(m.group(1).lower(), m.group(1)) + '-cross')
    elif re.search(r'\bradial', text, re.I): parts.append('radial')
    if re.search(r'\bJIS\b', text): parts.append('JIS')
    elif re.search(r'\bItalian (?:lacing|cross|style)', text, re.I): parts.append('Italian')
    return ' '.join(parts) or None

WORK = [  # service keywords, matched in order of first appearance
    ('rim replacement', r'replac\w*[^.\n]{0,30}\brims?\b|\bnew rim\b|\brim (?:swap|replacement)'),
    ('spoke replacement', r'(?:replac|swapp)\w*[^.\n]{0,30}\bspokes?\b|\b(?:bent|broken|snapped) spokes?\b|\bspokes? (?:was|were|got) (?:bent|broken)'),
    ('rebuild', r'\brebuil[td]'),
    ('freehub service', r'\b(?:freebody|free body|freehub|pawls?)\b'),
    ('bearing service', r'\b(?:bearings?|overhaul\w*|cones?)\b'),
    ('crash damage', r'\b(?:crash\w*|accident)\b'),
    ('truing', r'\b(?:runout|truing|trued|wobbl\w*|centering|dish\w*)\b'),
    ('tension check', r'\btension\b'),
]
def work(text, k=2):
    hits = []
    for name, rx in WORK:
        ms = list(re.finditer(rx, text, re.I))
        if ms: hits.append((-len(ms), ms[0].start(), name))
    return [n for *_, n in sorted(hits)[:k]]

def spec_paragraph(text):
    paras = [p for p in re.split(r'\n\s*\n', text) if p.strip()]
    for p in paras:
        if re.search(r'\bhubs?\b', p) or holes(p): return p
    for p in paras:
        if re.search(RIM_CODE, p): return p
    return ''

BUILD = re.compile(r'\b(?:built|build|rebuilt|assembled|laced|replaced|built up)\b|\bNomu Lab Wheel\b', re.I)
GENERIC = re.compile(r'\b(?:comments?|day off|closed|closure|tomorrow|break|business hours|apology|correction|continuing|not found|arrived)\b', re.I)

def kind(base):
    if GENERIC.search(base) and not BUILD.search(base): return 'notice'
    if BUILD.search(base): return 'build'
    return 'service'

def features(base, text):
    k = kind(base)
    if k == 'notice': return k, []
    low = base.lower()
    toks = []
    if k == 'build':
        p = spec_paragraph(text)
        h, r, n, l = hub(p), rim(p), holes(p), lacing(p)
        if h and h.lower() not in low: toks.append(f'{h} hub')
        if r and r.lower() not in low: toks.append(f'{r} rim')
        nl = ' '.join(x for x in (n, l) if x)
        if nl: toks.append(nl)
    else:
        toks = work(text)
    return k, toks

def fmt_date(iso, short=True):
    d = datetime.date.fromisoformat(iso)
    return d.strftime('%b %-d, %Y') if short else d.strftime('%B %-d, %Y')
