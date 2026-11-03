"""Read news source pages directly; Gemini Search grounding quota is not required."""
import hashlib
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; BakraNews/1.0)"
class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip=0; self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','nav','footer','header','noscript'): self.skip+=1
    def handle_endtag(self, tag):
        if tag in ('script','style','nav','footer','header','noscript'): self.skip=max(0,self.skip-1)
    def handle_data(self, data):
        if not self.skip and data.strip(): self.parts.append(data.strip())

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Language':'hi-IN,hi;q=0.9,en;q=0.8'})
    with urllib.request.urlopen(req,timeout=18) as r:
        if 'html' not in r.headers.get('Content-Type','text/html') and 'xml' not in r.headers.get('Content-Type',''):
            raise ValueError('Not a readable article')
        return r.read(1500000).decode('utf-8','ignore'),r.geturl()

def search(query, n=6):
    url='https://www.bing.com/news/search?' + urllib.parse.urlencode({'q':query,'format':'rss','mkt':'hi-IN','setlang':'hi'})
    raw,_=get(url)
    root=ET.fromstring(raw)
    out=[]
    for item in root.iter('item'):
        link=html.unescape(item.findtext('link') or '')
        parsed=urllib.parse.urlparse(link)
        link=urllib.parse.parse_qs(parsed.query).get('url',[link])[0]
        if urllib.parse.urlparse(link).scheme not in ('https','http'): continue
        out.append({'title':item.findtext('title') or '', 'url':link, 'published':item.findtext('pubDate') or ''})
        if len(out)>=n: break
    return out

def collect(pick, candidates):
    query=pick.get('query') or pick['topic']
    try: rows=search(query)
    except Exception as exc:
        print('Source search unavailable:',type(exc).__name__); rows=[]
    # Keep actual URLs selected from this run's news feed as additional evidence candidates.
    words=set(str(pick['topic']).lower().split())
    ranked=sorted(candidates,key=lambda row:-len(words & set(str(row.get('title','')).lower().split())))
    rows += ranked[:4]
    seen=set(); unique=[]
    for row in rows:
        u=row.get('url','')
        if u and u not in seen:
            seen.add(u);unique.append(row)
    def read(row):
        try:
            raw,url=get(row['url']); parser=Text();parser.feed(raw)
            body=' '.join(parser.parts)
            if len(body)<500 or 'news.google.com' in urllib.parse.urlparse(url).netloc: return None
            host=urllib.parse.urlparse(url).netloc
            return {'id':'s'+hashlib.sha256(url.encode()).hexdigest()[:10], 'name':host,
                    'url':url,'date':row.get('published',''),'title':row.get('title',''),
                    'text':body[:10000]}
        except Exception as exc:
            print('Source page unavailable:',urllib.parse.urlparse(row.get('url','')).netloc,type(exc).__name__)
            return None
    with ThreadPoolExecutor(max_workers=4) as pool:
        got=[r for r in pool.map(read,unique[:8]) if r]
    if not got: raise RuntimeError('No readable source articles; cannot verify this news')
    got.sort(key=lambda row: (0 if row['name'].endswith(('.gov.in','.nic.in','rbi.org.in')) else 1))
    return got[:3]
