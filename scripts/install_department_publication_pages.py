# Create missing department publication pages and route homepages to them.
from html import escape
from html.parser import HTMLParser
from pathlib import Path

DEPARTMENTS = 'applied-botany applied-geology applied-zoology biochemistry biotechnology business-administration chemistry commerce computer-sciences economics education electronics english environmental-science food-technology hindi history-and-archaeology industrial-chemistry journalism-and-mass-communication kannada library-and-information-science mathematics microbiology pharmaceutical-chemistry physical-education physics political-science sanskrit social-work sociology tourism urdu wildlife-management'.split()

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.name='';self.heading=[];self.title=[];self.in_heading=False;self.in_title=False;self.feed_department=''
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='body': self.name=attrs.get('data-department-name','')
        if tag=='h1' and not self.heading: self.in_heading=True
        if tag=='title': self.in_title=True
        if attrs.get('id')=='publication-feed': self.feed_department=attrs.get('data-department','')
    def handle_endtag(self,tag):
        if tag=='h1': self.in_heading=False
        if tag=='title': self.in_title=False
    def handle_data(self,data):
        if self.in_heading:self.heading.append(data)
        if self.in_title:self.title.append(data)
    def department_name(self):
        value=self.name or ''.join(self.heading) or ''.join(self.title).split(' — ')[0]
        return ' '.join(value.split())

TEMPLATE=r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><meta name="description" content="Publications associated with the {name} teaching team and PhD students at Kuvempu University."><title>{name} publications — Kuvempu University</title><link rel="stylesheet" href="../assets/css/style.css"><script defer src="../assets/js/site.js"></script><script defer src="../assets/js/publications.js"></script><script defer src="../assets/js/department-profile-loader.js"></script></head>
<body data-base="../" class="department-publications-page"><a class="skip" href="#main">Skip to content</a><header class="wrap brandrow"><a class="brand" href="../index.html"><span class="brandname">Kuvempu University</span></a><nav aria-label="Department navigation"><a href="{slug}.html">{name} →</a></nav></header><main id="main" class="wrap page-pad"><p class="breadcrumb"><a href="../index.html">Home</a> / <a href="{slug}.html">{name}</a> / Publications</p><div class="page-intro"><p class="eyebrow">{name}</p><h1>Publications</h1><p>Publications associated with our teaching team and PhD students.</p></div><p><a class="btn" href="{slug}.html#people">Meet the teachers →</a> <a class="btn" href="{slug}.html#students">Meet the researchers →</a></p><section class="department-section" id="publications" aria-labelledby="publications-heading"><h2 id="publications-heading">Publications</h2><div id="publication-feed" data-department="{slug}"><p>Loading publications…</p></div><noscript><p>Enable JavaScript to view the publication list, or use the researcher profile links on the <a href="{slug}.html">department page</a>.</p></noscript></section><p><a href="{slug}.html#research">← Return to Research overview</a></p></main><footer><div class="wrap"><p>Copyright: Kuvempu University; Designed by Prof Rakesh Tiwari</p></div></footer></body></html>
"""

def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError('Publication routing changed; stop for review')
    return text.replace(old,new,1)

def main():
    root=Path(__file__).resolve().parents[1]
    directory=root/'departments'
    proposed={}
    for slug in DEPARTMENTS:
        home=directory/(slug+'.html')
        metadata=Metadata();metadata.feed(home.read_text(encoding='utf-8'))
        name=metadata.department_name()
        if not name:raise ValueError('Department name unavailable: '+slug)
        target=directory/(slug+'-publications.html')
        if target.exists():
            existing=Metadata();existing.feed(target.read_text(encoding='utf-8'))
            if existing.feed_department!=slug:raise ValueError('Existing publication page has a different department: '+slug)
        else:
            proposed[target]=TEMPLATE.format(name=escape(name,quote=True),slug=slug)
    path=root/'assets/js/department-research.js'
    text=path.read_text(encoding='utf-8')
    if 'const publicationPageUrl=' not in text:
        text=once(text,"const dedicated=location.pathname.endsWith('-publications.html');","const dedicated=location.pathname.endsWith('-publications.html');const publicationPageUrl=base+'departments/'+id+'-publications.html';")
        text=once(text,"const section=document.getElementById('publications');let feed=existing;","const section=document.getElementById('publications');let feed=dedicated?existing:null;")
        text=once(text,'if(section&&!feed){','if(dedicated&&section&&!feed){')
        text=once(text,"const destination=id==='environmental-science'?base+'departments/environmental-science-publications.html':section?'#publications':null;","const destination=publicationPageUrl;")
        routing="if(section)section.remove();document.querySelectorAll('a[href]').forEach(link=>{try{const url=new URL(link.href,document.baseURI);if(url.origin===location.origin&&url.pathname===location.pathname&&url.hash==='#publications')link.href=publicationPageUrl}catch{}});if(location.hash==='#publications'){location.replace(publicationPageUrl);return}"
        text=once(text,'if(feed)showFeed(feed,id);',routing)
    for target,content in proposed.items():target.write_text(content,encoding='utf-8')
    path.write_text(text,encoding='utf-8')
    print('Created '+str(len(proposed))+' missing publication pages; existing publication pages preserved.')

if __name__=='__main__':main()
