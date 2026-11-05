"""Duplicate-title disambiguation rules (zh-TW). Same structure as rules_en."""
import re, datetime, unicodedata
def nfkc(s): return unicodedata.normalize('NFKC', s)
HUB_ALIAS = [('Evolite', r'(?:Tni\s*)?(?:Evo\s*[-]?\s*(?:[Ll]ite|ライト|[Ll]ight)|Evolight|EvoLite|Ebolite|Evorite)'),
             ('Leaf', r'(?:Leaf|Leef|Reif|Reaf)')]
HUBWORD = r'(?:[（(](?:輪轂|花鼓)(?:品牌)?[）)]|(?:[（(]輪轂品牌[）)])?\s*(?:花鼓|輪轂|鼓心|轂))'
def canon(c):
    for k, rx in HUB_ALIAS:
        if re.fullmatch(rx, c): return k
    return c
def hub(p):
    p = nfkc(p)
    m = re.search(r'([A-Za-z0-9][A-Za-z0-9\-\. ]{0,18}?(?:ライト)?)\s*(?:黑色|銀色|紅色)?' + HUBWORD, p)
    if not m: return None
    c = m.group(1).strip()
    if re.fullmatch(r'\d+[H]?', c): return None
    return canon(c)
RIM = r'((?:DT\s?)?(?:AL|XR|RR|CX|DA|TB|C)-?\d{2,3}[A-Za-z]{0,2}|Crest MK\d|Open Pro|Exalith)'
def rim(p):
    m = re.search(RIM, nfkc(p)); return m.group(1) if m else None
def holes(p):
    for m in re.finditer(r'(?<![\d.:])(\d{2})\s?(?:孔|H\b|H(?=[^A-Za-z]))', nfkc(p)):
        n = int(m.group(1))
        if 12 <= n <= 48: return f'{n}孔'
    return None
def lacing(p):
    p = nfkc(p); parts = []
    if re.search(r'半(?:競賽|競速|Comp|コンペ|Conpe|Camp)', p): parts.append('半競賽')
    if re.search(r'放射|徑向|輻射狀', p): parts.append('放射')
    if 'JIS' in p: parts.append('JIS')
    elif re.search(r'義大利', p): parts.append('義大利式')
    return ' '.join(parts) or None
def spec_paragraph(text):
    paras = [x for x in re.split(r'\n\s*\n', text) if x.strip()]
    for x in paras:
        if re.search(HUBWORD, x) or holes(x): return x
    for x in paras:
        if re.search(RIM, nfkc(x)): return x
    return ''
WORK = [('更換輪圈', r'(?:更換|換)[^。\n]{0,8}(?:輪圈|輪框|框)'),
        ('更換輻條', r'(?:更換|換)[^。\n]{0,8}輻條|輻條[^。\n]{0,6}(?:彎|斷)'),
        ('重組', r'重組|重新組'),
        ('飛輪體保養', r'棘爪|飛輪體|塔基'),
        ('軸承保養', r'軸承|培林|珠碗'),
        ('摔車損傷', r'摔車|落車|事故'),
        ('校正', r'偏擺|校正|擺動|偏心|置中|對中'),
        ('張力檢查', r'張力')]
def work(text, k=2):
    hits = []
    for name, rx in WORK:
        ms = list(re.finditer(rx, text))
        if ms: hits.append((-len(ms), ms[0].start(), name))
    return [n for *_, n in sorted(hits)[:k]]
BUILD = re.compile(r'組裝|組了|組好|組成|重組|更換|換了|編了|輪組\d|號')
NOTICE = re.compile(r'休|留言|評論|營業|公告|道歉|更正|接續|昨天|404|到了')
def kind(base):
    if NOTICE.search(base) and not BUILD.search(base): return 'notice'
    return 'build' if BUILD.search(base) else 'service'
def features(base, text):
    k = kind(base)
    if k == 'notice': return k, []
    low = nfkc(base).lower(); toks = []
    if k == 'build':
        p = spec_paragraph(text)
        h, r, n, l = hub(p), rim(p), holes(p), lacing(p)
        if h and h.lower() not in low: toks.append(f'{h}花鼓')
        if r and r.lower() not in low: toks.append(f'{r}輪圈')
        nl = ' '.join(x for x in (n, l) if x)
        if nl: toks.append(nl)
    else:
        toks = work(text)
    return k, toks
def fmt_date(iso):
    d = datetime.date.fromisoformat(iso); return f'{d.year}年{d.month}月{d.day}日'
