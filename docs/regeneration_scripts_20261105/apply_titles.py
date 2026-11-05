"""Apply new headline/description to posts and to every link that shows the old title."""
import re, os, json, html, sys
root = os.environ.get('NOMULAB_ROOT', '.')

def trunc(s, n):
    if len(s) <= n: return s
    head = s[:n-1]
    cut = head.rsplit(' ', 1)[0] if ' ' in head[-30:] else head
    return cut.rstrip(' ,.;:') + '…'

def apply(lang_dir, link_prefix, site, mapping, link_files, aliases=None):
    """mapping: fname -> dict(new=headline, desc_prefix=str)
    aliases: fname -> iterable of older (unescaped) titles whose link labels should also be replaced"""
    aliases = aliases or {}
    old_titles = {}
    for f, m in mapping.items():
        p = f'{root}/{lang_dir}/{f}'
        s = open(p, encoding='utf-8').read()
        old_esc = re.search(r'<title>(.*?) — ' + re.escape(site) + '</title>', s).group(1)
        old_titles[f] = old_esc
        if html.unescape(old_esc) == m['new']:
            continue  # already applied (idempotent re-run)
        new_esc = html.escape(m['new'], quote=True)
        new_json = json.dumps(m['new'], ensure_ascii=False)[1:-1]
        n = 0
        s, k = re.subn(r'<title>.*? — ' + re.escape(site) + '</title>', lambda _: f'<title>{new_esc} — {site}</title>', s, count=1); n += k
        s, k = re.subn(r'(<meta property="og:title" content=")[^"]*(")', lambda x: x.group(1)+new_esc+x.group(2), s, count=1); n += k
        s, k = re.subn(r'("headline": ")(?:[^"\\]|\\.)*(")', lambda x: x.group(1)+new_json+x.group(2), s, count=1); n += k
        s, k = re.subn(r'<h1>' + re.escape(old_esc) + '</h1>', lambda _: f'<h1>{new_esc}</h1>', s, count=1); n += k
        # descriptions
        pre = m['desc_prefix']
        d_old = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', s).group(1))
        d_new = html.escape(trunc(pre + d_old, 160), quote=True)
        s, k = re.subn(r'(<meta name="description" content=")[^"]*(")', lambda x: x.group(1)+d_new+x.group(2), s, count=1); n += k
        s, k = re.subn(r'(<meta property="og:description" content=")[^"]*(")', lambda x: x.group(1)+d_new+x.group(2), s, count=1); n += k
        lm = re.search(r'("description": ")((?:[^"\\]|\\.)*)(", "url")', s)
        ld_old = json.loads('"' + lm.group(2) + '"')
        ld_new = json.dumps(trunc(pre + ld_old, 220), ensure_ascii=False)[1:-1]
        s = s[:lm.start(2)] + ld_new + s[lm.end(2):]; n += 1
        assert n == 7, (f, n)
        open(p, 'w', encoding='utf-8').write(s)
    # links
    changed = 0
    pat = re.compile(r'(<a href="' + link_prefix + r'(\d+\.html)">)([^<]*)(</a>)')
    for lf in link_files:
        s = open(lf, encoding='utf-8').read()
        def rep(x):
            f = x.group(2)
            if f in mapping and (x.group(3) == old_titles[f] or html.unescape(x.group(3)) in aliases.get(f, ())):
                return x.group(1) + html.escape(mapping[f]['new'], quote=True) + x.group(4)
            return x.group(0)
        s2 = pat.sub(rep, s)
        if s2 != s:
            open(lf, 'w', encoding='utf-8').write(s2); changed += 1
    return old_titles, changed
