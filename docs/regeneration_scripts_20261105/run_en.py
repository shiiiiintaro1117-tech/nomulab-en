import os, json, glob, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from apply_titles import apply, root
from build_en import frozen_titles
from rules_en import fmt_date
en = json.load(open('en.json')); r = json.load(open('en_new.json'))
mapping = {}
frozen = frozen_titles('en')
for f, row in frozen.items():
    spec = ', '.join(t for t in row['extracted_tokens'].split(' | ') if t)
    mapping[f] = dict(new=row['new_title'], desc_prefix=fmt_date(row['date_published'], short=False) + (f" — {spec}. " if spec else ". "))
for f, v in r.items():
    date = fmt_date(en[f]['date'], short=False)
    spec = ', '.join(v['tokens'])
    pre = f"{date}" + (f" — {spec}. " if spec else ". ")
    mapping[f] = dict(new=v['new'], desc_prefix=pre)
files = glob.glob(f'{root}/posts/*.html') + [f'{root}/index.html'] + glob.glob(f'{root}/guides/*.html') + [f'{root}/{x}' for x in ('about.html','glossary.html','tools/build-advisor.html','data/rim-weights.html')]
old, ch = apply('posts', r'(?:/|\.\./)?posts/', 'Nomu Lab Diary', mapping, files, aliases={f: {row['old_title']} for f, row in frozen.items()})
json.dump(old, open('en_old.json','w'), ensure_ascii=False)
print('link files changed', ch)
