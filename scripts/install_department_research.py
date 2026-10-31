"""Connect the shared cached research collection without changing profile data."""
import hashlib
from pathlib import Path

def blob(text):
    raw=text.encode('utf-8')
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError('Unexpected renderer structure; stop rather than overwrite')
    return text.replace(old,new,1)

root=Path(__file__).resolve().parents[1]
pubpath=root/'assets/js/publications.js'
navpath=root/'assets/js/department-navigation.js'
pub=pubpath.read_text(encoding='utf-8')
nav=navpath.read_text(encoding='utf-8')
if 'async function departmentCollection(' not in pub:
    assert blob(pub)=='49051dfc391a37ed27f6122e7236556e6b8f1729','Publication renderer changed after review'
    helper="""async function departmentCollection(id){
if(!window.KUDepartmentResearch){if(!window.KUDepartmentResearchReady)window.KUDepartmentResearchReady=new Promise((resolve,reject)=>{let script=Array.from(document.scripts).find(s=>s.src&&new URL(s.src,location.href).pathname.endsWith('/assets/js/department-research.js'));if(!script){script=document.createElement('script');script.src=base+'assets/js/department-research.js';script.addEventListener('load',resolve,{once:true});script.addEventListener('error',reject,{once:true});document.head.append(script)}else{script.addEventListener('load',resolve,{once:true});script.addEventListener('error',reject,{once:true})}});await window.KUDepartmentResearchReady}
if(!window.KUDepartmentResearch)throw Error('Department research collection unavailable');return window.KUDepartmentResearch.get(id);
}
"""
    pub=once(pub,'function citationLine(p,metrics){',helper+'function citationLine(p,metrics){')
    old="""const [data,status,metrics]=await load();if(!Array.isArray(data.publications))throw Error('Invalid publication data');
const rows=data.publications.filter(p=>options.facultyId?(p.faculty_ids||[]).includes(options.facultyId):(p.departments||[]).includes(options.departmentId)).sort((a,b)=>(Number(b.year)||0)-(Number(a.year)||0)||clean(a.title).localeCompare(clean(b.title)));"""
    new="""let data,status,metrics,rows,collection;
if(options.departmentId){collection=await departmentCollection(options.departmentId);data=collection.metadata;status=null;metrics=collection.metrics;rows=collection.publications}else{[data,status,metrics]=await load();if(!Array.isArray(data.publications))throw Error('Invalid publication data');rows=data.publications.filter(p=>(p.faculty_ids||[]).includes(options.facultyId)).sort((a,b)=>(Number(b.year)||0)-(Number(a.year)||0)||clean(a.title).localeCompare(clean(b.title)))}"""
    pub=once(pub,old,new)
    pub=once(pub,"async function render(target,options={}){", "async function render(target,options={}){\nif(options.departmentId){if(target.dataset.kuDepartmentPublication===options.departmentId)return;target.dataset.kuDepartmentPublication=options.departmentId;}")
    pub=once(pub,"updateSummary(false);target.replaceChildren(summary);", "updateSummary(false);target.replaceChildren(summary);if(collection)target.append(el('p','Research paper count: '+(collection.paperCount==null?'not yet available':collection.paperCount)+'. Other scholarly outputs remain listed but are excluded from the paper and summary-citation counters.','hint'));")
    pub=once(pub,"const note=statusText(data,status,options.facultyId);", "const note=collection?collection.note:statusText(data,status,options.facultyId);")
    pub=once(pub,"const intro=section.querySelector('p');", "const intro=section.querySelector(':scope>p');")
    pub=once(pub,'associated with department faculty, collected','associated with the teaching team and PhD students, collected')
    pub=once(pub,'types[p.type]||clean(p.type)','clean(p.display_type)||types[p.type]||clean(p.type)')
if "research.src=base+'assets/js/department-research.js'" not in nav:
    assert blob(nav)=='a59f45b9c1aa4d03550d4559e153667799fb43e3','Department navigation changed after review'
    nav=once(nav,'document.head.append(cardsCss);',"document.head.append(cardsCss);\nif(!Array.from(document.scripts).some(s=>s.src&&new URL(s.src,location.href).pathname.endsWith('/assets/js/department-research.js'))){const research=document.createElement('script');research.src=base+'assets/js/department-research.js';document.head.append(research)}")
pubpath.write_text(pub,encoding='utf-8')
navpath.write_text(nav,encoding='utf-8')
print('Connected department metrics and combined publication lists; individual profile rendering preserved.')
