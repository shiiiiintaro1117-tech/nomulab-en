import os, json, glob, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from apply_titles import apply, root
from build_en import frozen_titles
from rules_zh import fmt_date
zh = json.load(open('zh.json')); r = json.load(open('zh_new.json'))
mapping = {}
frozen = frozen_titles('zh-TW')
for f, row in frozen.items():
    spec = '、'.join(t for t in row['extracted_tokens'].split(' | ') if t)
    mapping[f] = dict(new=row['new_title'], desc_prefix=fmt_date(row['date_published']) + (f'——{spec}。' if spec else '。'))
for f, v in r.items():
    spec = '、'.join(v['tokens'])
    mapping[f] = dict(new=v['new'], desc_prefix=fmt_date(zh[f]['date']) + (f'——{spec}。' if spec else '。'))
files = glob.glob(f'{root}/zh/posts/*.html') + [f'{root}/zh/index.html']
old, ch = apply('zh/posts', r'(?:/zh/)?posts/', '野村工房日記', mapping, files, aliases={f: {row['old_title']} for f, row in frozen.items()})
json.dump(old, open('zh_old.json','w'), ensure_ascii=False)
print('link files changed', ch)
