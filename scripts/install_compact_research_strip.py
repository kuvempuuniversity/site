"""Compact the shared strip and accept explicitly provisional departmental PhD totals."""
from pathlib import Path

def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError('Research renderer changed; stop for review')
    return text.replace(old,new,1)

path=Path(__file__).resolve().parents[1]/'assets/js/department-research.js'
text=path.read_text(encoding='utf-8')
if 'const provisionalPhd=' not in text:
    anchor='const rawPhd=data.phds&&data.phds.departments&&data.phds.departments[departmentId];'
    provision=r"const provisionalPhd=rawPhd&&rawPhd.status==='provisional'&&Number.isSafeInteger(rawPhd.count)&&rawPhd.count>=0&&/^\d{4}-\d{2}-\d{2}$/.test(rawPhd.reported_at||'')&&stamp(rawPhd.reported_at,now)&&new Date(rawPhd.reported_at).toISOString().slice(0,10)===rawPhd.reported_at&&typeof rawPhd.source==='string'&&rawPhd.source.trim();"
    text=once(text,anchor,anchor+'\n'+provision)
    text=once(text,'phds:validPhd?rawPhd.count:null',"phds:(validPhd||provisionalPhd)?rawPhd.count:null,phdStatus:validPhd?'verified':provisionalPhd?'provisional':null")
old="if(r.citationSource)dl.querySelector('div:last-child dt').textContent='Citations ('+r.citationSource+')';"
if old in text:
    text=once(text,old,'')
if 'compact-research-strip.js' not in text:
    old='.then(module=>publicationView?module.render(section,r):module.renderResearch(section,r))'
    new=".then(async module=>{if(publicationView)module.render(section,r);else module.renderResearch(section,r);const compact=await import(new URL(base+'assets/js/compact-research-strip.js',document.baseURI).href);compact.compact(section,r)})"
    text=once(text,old,new)
path.write_text(text,encoding='utf-8')
