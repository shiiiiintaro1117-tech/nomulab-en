import re, html
END = re.compile(r'<aside|<ins class="adsbygoogle"|<div class="affiliate-box"|<nav class="related"|<p class="source-link"')
def body_region(s):
    i = s.index('<div class="post-body">')
    m = END.search(s, i)
    return s[i:m.start() if m else len(s)]
def first_image(s):
    b = body_region(s)
    m = re.search(r'(?:<a href="([^"]+)"[^>]*>\s*)?<img\b[^>]*?\bsrc="([^"]+)"', b)
    if not m: return None
    if m.group(1) and re.search(r'\.(?:jpe?g|png|gif|webp)$', m.group(1), re.I): return m.group(1)
    return m.group(2)

# ---- og:image / twitter:card insertion (step 2 of the 2026-11-05 review) ----
DEFAULT_OG = 'https://nomulabworkshop.com/og-default.png'
def og_block(s, is_post):
    """Return the meta lines to place right after og:site_name."""
    u = first_image(s) if is_post else None
    meta = f'<meta property="og:image" content="{html.escape(u or DEFAULT_OG, quote=True)}">\n'
    if not u:
        meta += '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
    return u or DEFAULT_OG, meta + '<meta name="twitter:card" content="summary_large_image">\n'
