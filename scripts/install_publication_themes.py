"""Connect the approved publication overview without changing research metrics."""
from pathlib import Path

def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError('Renderer changed; review before modifying it')
    return text.replace(old,new,1)

root=Path(__file__).resolve().parents[1]
a=root/'assets/js/department-research.js'
b=root/'assets/js/publications.js'
x=a.read_text(encoding='utf-8');y=b.read_text(encoding='utf-8')
if 'publication-themes.js' not in x:
    old='if(!publicationView)section.append(link)'
    new="if(!publicationView)section.append(link);if(publicationView)import(new URL(base+'assets/js/publication-themes.js',document.baseURI).href).then(module=>module.render(section,r)).catch(()=>section.append(el('p','Publication themes are temporarily unavailable.','hint')))"
    x=once(x,old,new)
old="h.style.cssText='font-size:1.15rem;font-weight:500;line-height:1.4'"
new="h.style.cssText=''"
if old in y:
    y=once(y,old,new)
a.write_text(x,encoding='utf-8');b.write_text(y,encoding='utf-8')
