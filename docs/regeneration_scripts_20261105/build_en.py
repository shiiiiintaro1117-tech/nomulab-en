"""Compute new headlines for EN posts that share a title.
If docs/duplicate_titles_20261105.csv exists, titles listed there are frozen and
their old_title is used as the grouping key, so newly generated posts that reuse
an old title are disambiguated against them."""
import os, json, collections, sys, html, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules_en import norm_base, features, fmt_date
from apply_titles import root
LANG, SRC, OUT = 'en', 'en.json', 'en_new.json'
def key(t): return t.casefold()

def frozen_titles(lang):
    p = f'{root}/docs/duplicate_titles_20261105.csv'
    if not os.path.exists(p): return {}
    return {f"{r['post_id']}.html": r for r in csv.DictReader(open(p, encoding='utf-8-sig')) if r['lang'] == lang}

def main():
    en = json.load(open(SRC)); frozen = frozen_titles(LANG)
    cur = {k: html.unescape(v['title'].rsplit(' — ', 1)[0]) for k, v in en.items()}
    base = {k: norm_base(frozen[k]['old_title'] if k in frozen else cur[k]) for k in en}
    grp = collections.defaultdict(list)
    for k, b in base.items(): grp[key(b)].append(k)
    taken = collections.Counter(key(cur[k]) for k in en if k in frozen or len(grp[key(base[k])]) < 2)
    res = {}
    for g, ks in grp.items():
        if len(ks) < 2: continue
        todo = [k for k in ks if k not in frozen]
        cand = {}
        for k in todo:
            kd, toks = features(base[k], en[k]['body'])
            cand[k] = (kd, toks, base[k] + (': ' + ', '.join(toks) if toks else ''))
        c = collections.Counter(key(t) for *_, t in cand.values())
        out = {}
        for k, (kd, toks, t) in cand.items():
            rule = 'features'
            if not toks or c[key(t)] > 1 or taken[key(t)]:
                t = f"{t} ({fmt_date(en[k]['date'])})"; rule = 'features+date' if toks else 'date'
            out[k] = [kd, toks, t, rule]
        c2 = collections.Counter(key(v[2]) for v in out.values())
        for k, v in out.items():
            if c2[key(v[2])] > 1 or taken[key(v[2])]:
                v[2] = v[2][:-1] + f", entry {k[:-5]})"; v[3] += '+entry'
        for k, v in out.items():
            res[k] = dict(group=g, size=len(ks), kind=v[0], tokens=v[1], new=v[2], rule=v[3])
    json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=0)
    print(LANG, 'posts to retitle:', len(res), collections.Counter(v['rule'] for v in res.values()))
if __name__ == '__main__': main()
