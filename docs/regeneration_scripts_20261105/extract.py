import re,os,json,html,collections
root=os.environ.get('NOMULAB_ROOT','.')
def load(d):
    out={}
    for f in os.listdir(f'{root}/{d}'):
        s=open(f'{root}/{d}/{f}',encoding='utf-8').read()
        t=re.search(r'<title>(.*?)</title>',s,re.S).group(1)
        b=re.search(r'<div class="entrytext">(.*?)</div>\s*</div>',s,re.S) or re.search(r'<div class="post-body">(.*?)</div>',s,re.S)
        b=b.group(1)
        b=re.sub(r'<br\s*/?>','\n',b); b=re.sub(r'<[^>]+>','',b); b=html.unescape(b)
        date=re.search(r'"datePublished": "(.*?)"',s).group(1)
        out[f]=dict(title=t,body=b,date=date)
    return out
if __name__=='__main__':
    for d,n in [('posts','en'),('zh/posts','zh')]:
        json.dump(load(d),open(f'{n}.json','w'),ensure_ascii=False)
