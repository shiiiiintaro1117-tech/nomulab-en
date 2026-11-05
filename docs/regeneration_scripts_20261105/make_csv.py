"""Write docs/duplicate_titles_20261105.csv from the work files of a run on the pre-change site.
Run in the same work directory as run_all.sh, with NOMULAB_ROOT pointing at the updated site."""
import os, json, csv, html, re
root = os.environ.get('NOMULAB_ROOT', '.')
rows = []
for lang, d, pref, base in [('en', 'posts', 'en', 'https://nomulabworkshop.com/posts/'),
                            ('zh-TW', 'zh/posts', 'zh', 'https://nomulabworkshop.com/zh/posts/')]:
    new = json.load(open(f'{pref}_new.json')); old = json.load(open(f'{pref}_old.json')); src = json.load(open(f'{pref}.json'))
    for f, v in new.items():
        s = open(f'{root}/{d}/{f}', encoding='utf-8').read()
        desc = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', s).group(1))
        rows.append([lang, int(f[:-5]), base + f, src[f]['date'], html.unescape(old[f]), v['size'], v['kind'],
                     ' | '.join(v['tokens']), v['rule'], v['new'], desc])
rows.sort(key=lambda r: (r[0], r[1]))
with open(f'{root}/docs/duplicate_titles_20261105.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh)
    w.writerow(['lang', 'post_id', 'url', 'date_published', 'old_title', 'group_size', 'kind',
                'extracted_tokens', 'rule_applied', 'new_title', 'new_description'])
    w.writerows(rows)
print('rows', len(rows))
