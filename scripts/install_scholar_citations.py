"""Install the approved Scholar snapshot without changing publication-count rules."""
from pathlib import Path

def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError('Renderer changed; stop for review rather than overwrite')
    return text.replace(old,new,1)

root=Path(__file__).resolve().parents[1]
a=root/'assets/js/department-research.js'
b=root/'assets/js/publications.js'
x=a.read_text(encoding='utf-8');y=b.read_text(encoding='utf-8')
original='const get=async id=>aggregate(await load(),id);'
previous="const get=async id=>{const result=aggregate(await load(),id);if(id!=='environmental-science')return result;const module=await import(base+'assets/js/scholar-citations.js');return module.apply(result)};"
corrected="const get=async id=>{const result=aggregate(await load(),id);if(id!=='environmental-science')return result;const module=await import(new URL(base+'assets/js/scholar-citations.js',document.baseURI).href);return module.apply(result)};"
if corrected not in x:
    x=once(x,previous if previous in x else original,corrected)
if "dl.querySelector('div:last-child dt').textContent='Citations ('" not in x:
    x=once(x,'get(id).then(r=>{',"get(id).then(r=>{if(r.citationSource)dl.querySelector('div:last-child dt').textContent='Citations ('+r.citationSource+')';")
if "methodology.href=base+'about-research-metrics.html'" not in x:
    x=once(x,'section.append(details);const link=',"const methodology=el('a','About this website and research metrics →');methodology.href=base+'about-research-metrics.html';details.append(methodology);section.append(details);const link=")
if "metrics.source==='Google Scholar'" not in y:
    y=once(y,'function citationLine(p,metrics){',"""function citationLine(p,metrics){
if(metrics&&metrics.source==='Google Scholar'){const line=el('div',undefined,'hint'),entry=metrics.entriesById&&metrics.entriesById[p.id];line.style.fontSize='.875rem';if(entry){line.append(document.createTextNode('Cited by '+entry.count+' · '),anchor('Google Scholar ↗',entry.source_url),document.createTextNode(' · Automatically matched · Retrieved '+new Date(entry.retrieved_at).toISOString().slice(0,10)))}else line.textContent='Google Scholar count unavailable in this snapshot; not treated as zero.';return line}
""")
a.write_text(x,encoding='utf-8');b.write_text(y,encoding='utf-8')
