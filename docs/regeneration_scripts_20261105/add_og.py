"""Insert og:image / twitter:card into every page (idempotent) and "image" into BlogPosting JSON-LD."""
import os, re, glob, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import og_block
root = os.environ.get('NOMULAB_ROOT', '.')
n = 0
for f in glob.glob(f'{root}/**/*.html', recursive=True):
    if '/docs/' in f: continue
    s = open(f, encoding='utf-8').read()
    if 'og:image' in s: continue
    rel = os.path.relpath(f, root)
    is_post = rel.startswith('posts/') or rel.startswith('zh/posts/')
    img, meta = og_block(s, is_post)
    s, k = re.subn(r'(<meta property="og:site_name" content="[^"]*">\n)', lambda m: m.group(1) + meta, s, count=1)
    if not k: print('no og:site_name:', rel); continue
    if is_post:
        s = re.sub(r'("datePublished": "[^"]*", )', lambda m: m.group(1) + '"image": ' + json.dumps(img) + ', ', s, count=1)
    open(f, 'w', encoding='utf-8').write(s); n += 1
print('updated', n)
