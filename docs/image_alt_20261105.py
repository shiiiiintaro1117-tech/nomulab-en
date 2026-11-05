#!/usr/bin/env python3
"""Replace filename-style alt text in post bodies with short context-based alt.

Usage: fix_alt.py REPO_ROOT [--apply] [--sample N]
"""
import glob, html, os, random, re, sys, json, collections

ROOT = sys.argv[1]
APPLY = '--apply' in sys.argv
SAMPLE = int(sys.argv[sys.argv.index('--sample') + 1]) if '--sample' in sys.argv else 0

FILENAME_ALT = re.compile(r'^[^\s"<>/]+\.(?:jpe?g|png|gif|webp|bmp)$', re.I)
BODY = re.compile(r'(<div class="post-body">)(.*?)(<aside class="post-guides">)', re.S)
# an image, optionally wrapped in its link
IMG = re.compile(r'(?:<a\b[^>]*>\s*)?<img\b[^>]*>(?:\s*</a>)?', re.I)
ALT = re.compile(r'\balt="([^"]*)"')
GAP = re.compile(r'^(?:\s|<br\s*/?>|&nbsp;)*$', re.I)          # only breaks between images
PARA_END = re.compile(r'(?:<br\s*/?>\s*){2,}|</p>|<p\b[^>]*>|</div>|<div\b[^>]*>|<hr\b[^>]*>', re.I)
TAG = re.compile(r'<[^>]+>')
SENT_EN = re.compile(r'(?<=[.!?])\s+')
SENT_ZH = re.compile(r'(?<=[。！？])')

LIMIT = {'en': 100, 'zh': 40}
MIN = {'en': 20, 'zh': 8}
TITLE_RE = re.compile(r'<h1>(.*?)</h1>', re.S)


def to_text(fragment):
    t = TAG.sub(' ', re.sub(r'<br\s*/?>', ' ', fragment, flags=re.I))
    t = html.unescape(t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def first_para(fragment):
    m = PARA_END.search(fragment)
    return fragment[:m.start()] if m else fragment


def last_para(fragment):
    parts = PARA_END.split(fragment)
    for p in reversed(parts):
        if to_text(p):
            return p
    return ''


def shorten(text, lang):
    text = re.sub(r'^[\s↑↓←→⇒⇧▲▼※*]+', '', text)
    sents = [s.strip() for s in (SENT_ZH if lang == 'zh' else SENT_EN).split(text) if s.strip()]
    out = ''
    for s in sents:
        out = (out + (' ' if lang == 'en' and out else '') + s)
        if len(out) >= MIN[lang]:
            break
    if not out:
        out = text
    lim = LIMIT[lang]
    if len(out) > lim:
        cut = out[:lim]
        if lang == 'en' and ' ' in cut:
            cut = cut[:cut.rfind(' ')]
        out = cut.rstrip(' ,;:、，') + '…'
    out = out.rstrip(' ,;:、，')
    return out


def process_body(body, lang, title):
    imgs = list(IMG.finditer(body))
    # group consecutive images separated only by breaks/whitespace
    groups = []
    for m in imgs:
        if groups and GAP.match(body[groups[-1][-1].end():m.start()]):
            groups[-1].append(m)
        else:
            groups.append([m])
    repl = {}
    stats = collections.Counter()
    for gi, g in enumerate(groups):
        targets = [m for m in g if (a := ALT.search(m.group(0))) and FILENAME_ALT.match(a.group(1))]
        if not targets:
            continue
        nxt = imgs.index(g[-1]) + 1
        after_end = imgs[nxt].start() if nxt < len(imgs) else len(body)
        after = to_text(first_para(body[g[-1].end():after_end]))
        prv = imgs.index(g[0]) - 1
        before_start = imgs[prv].end() if prv >= 0 else 0
        before = to_text(last_para(body[before_start:g[0].start()]))
        if after:
            ctx, src = after, 'after'
        elif before:
            ctx, src = before, 'before'
        else:
            ctx, src = title, 'title'
        base = shorten(ctx, lang)
        n = len(g)
        for i, m in enumerate(g):
            if m not in targets:
                continue
            alt = base if n == 1 else (f'{base} ({i+1} of {n})' if lang == 'en' else f'{base}（{i+1}/{n}）')
            repl[m.start()] = (m, alt)
            stats[src] += 1
    out, pos, samples = [], 0, []
    for start in sorted(repl):
        m, alt = repl[start]
        tag = m.group(0)
        old = ALT.search(tag).group(1)
        new_tag = ALT.sub('alt="' + html.escape(alt, quote=True) + '"', tag, count=1)
        out.append(body[pos:m.start()]); out.append(new_tag); pos = m.end()
        samples.append((old, alt))
    out.append(body[pos:])
    return ''.join(out), stats, samples


def main():
    total = collections.Counter(); per_lang = collections.Counter(); files_changed = collections.Counter()
    allsamples = []
    leftovers = 0
    for lang, pat in (('en', 'posts/*.html'), ('zh', 'zh/posts/*.html')):
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            s = open(f, encoding='utf-8').read()
            m = BODY.search(s)
            if not m:
                continue
            t = TITLE_RE.search(s)
            title = to_text(t.group(1)) if t else ''
            nb, st, smp = process_body(m.group(2), lang, title)
            if smp:
                total.update(st); per_lang[lang] += len(smp); files_changed[lang] += 1
                allsamples += [(os.path.relpath(f, ROOT), o, a) for o, a in smp]
                if APPLY:
                    s2 = s[:m.start(2)] + nb + s[m.end(2):]
                    open(f, 'w', encoding='utf-8').write(s2)
    # whole-site check of anything left with a filename alt
    for f in glob.glob(os.path.join(ROOT, '**/*.html'), recursive=True):
        if '/.git/' in f: continue
        for a in ALT.findall(open(f, encoding='utf-8').read()):
            if FILENAME_ALT.match(a): leftovers += 1
    print(json.dumps({'by_source': total, 'images_by_lang': per_lang, 'files_by_lang': files_changed,
                      'filename_alts_remaining_sitewide': leftovers}, ensure_ascii=False))
    if SAMPLE:
        random.seed(1)
        for r in random.sample(allsamples, min(SAMPLE, len(allsamples))):
            print(' | '.join(r))


main()
