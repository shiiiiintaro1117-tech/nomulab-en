"""Same as build_en.py for zh-TW posts (rules_zh)."""
import os, json, collections, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules_zh import nfkc, features, fmt_date
from build_en import frozen_titles
LANG, SRC, OUT = 'zh-TW', 'zh.json', 'zh_new.json'
def key(t): return nfkc(t).casefold().replace(' ', '')

def main():
    zh = json.load(open(SRC)); frozen = frozen_titles(LANG)
    cur = {k: html.unescape(v['title'].rsplit(' — ', 1)[0]) for k, v in zh.items()}
    base = {k: (frozen[k]['old_title'] if k in frozen else cur[k]) for k in zh}
    grp = collections.defaultdict(list)
    for k, b in base.items(): grp[key(b)].append(k)
    taken = collections.Counter(key(cur[k]) for k in zh if k in frozen or len(grp[key(base[k])]) < 2)
    res = {}
    for g, ks in grp.items():
        if len(ks) < 2: continue
        cand = {}
        for k in [k for k in ks if k not in frozen]:
            kd, toks = features(base[k], zh[k]['body'])
            cand[k] = (kd, toks, base[k] + ('：' + '、'.join(toks) if toks else ''))
        c = collections.Counter(key(t) for *_, t in cand.values())
        out = {}
        for k, (kd, toks, t) in cand.items():
            rule = 'features'
            if not toks or c[key(t)] > 1 or taken[key(t)]:
                t = f"{t}（{fmt_date(zh[k]['date'])}）"; rule = 'features+date' if toks else 'date'
            out[k] = [kd, toks, t, rule]
        c2 = collections.Counter(key(v[2]) for v in out.values())
        for k, v in out.items():
            if c2[key(v[2])] > 1 or taken[key(v[2])]:
                v[2] = v[2][:-1] + f"・第{k[:-5]}篇）"; v[3] += '+entry'
        for k, v in out.items():
            res[k] = dict(group=g, size=len(ks), kind=v[0], tokens=v[1], new=v[2], rule=v[3])
    json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=0)
    print(LANG, 'posts to retitle:', len(res), collections.Counter(v['rule'] for v in res.values()))
if __name__ == '__main__': main()
