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
if 'department-publication-overview' not in x:
    x=once(x,'else if(feed)feed.before(section);else root.prepend(section)',"else if(feed)feed.before(section);else{const heading=root.querySelector(':scope>h2');if(heading)heading.after(section);else root.prepend(section)}")
    anchor="const intro=document.querySelector('.department-publications-page .page-intro>p:last-child');"
    addition="""if(id==='environmental-science'&&!location.pathname.endsWith('-publications.html')&&!section){const students=document.getElementById('students');if(students){let overview=document.getElementById('department-publication-overview');if(!overview){overview=el('section',null,'department-section');overview.id='department-publication-overview';const all=el('a','View all publications →');all.href=base+'departments/environmental-science-publications.html';const paragraph=el('p');paragraph.append(all);overview.append(el('h2','Publications'),paragraph);students.after(overview)}if(!overview.querySelector('[data-ku-publication-metrics]'))metrics(overview,id,true)}}"""
    x=once(x,anchor,addition+anchor)
old="h.style.cssText='font-size:1.15rem;font-weight:500;line-height:1.4'"
new="h.style.cssText=''"
if old in y:
    y=once(y,old,new)
a.write_text(x,encoding='utf-8');b.write_text(y,encoding='utf-8')
