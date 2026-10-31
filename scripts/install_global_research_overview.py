"""Use one shared Research overview per department homepage; retain paper lists."""
from pathlib import Path
path=Path(__file__).resolve().parents[1]/'assets/js/department-research.js'
text=path.read_text(encoding='utf-8')
if 'kuGlobalResearchOverview' not in text:
    start='const mount=()=>{'
    end='\nlet pending=false;const schedule='
    if text.count(start)!=1 or text.count(end)!=1:
        raise ValueError('Research mounting structure changed; stop for review')
    first=text.index(start);last=text.index(end,first)
    replacement=r"""const mount=()=>{
const existing=document.querySelector('#publication-feed[data-department]');
const id=existing?existing.dataset.department:match[1].replace(/-publications$/,'');
const dedicated=location.pathname.endsWith('-publications.html');
const section=document.getElementById('publications');let feed=existing;
if(section&&!feed){feed=el('div','Loading publications…');feed.id='publication-feed';feed.dataset.department=id;section.querySelectorAll(':scope>p').forEach(p=>{if(p.textContent.trim()==='Publication records will be added here.')p.remove()});section.append(feed)}
if(dedicated){
if(feed){const panels=Array.from(document.querySelectorAll('main [data-ku-research-metrics]')),keep=panels.find(p=>p.dataset.kuPublicationMetrics==='true');panels.forEach(p=>{if(p!==keep)p.remove()});if(!keep)metrics(feed.parentElement,id,true);showFeed(feed,id)}
}else{
const previous=document.getElementById('research'),students=document.getElementById('students'),study=document.getElementById('study');
let overview=document.querySelector('[data-ku-global-research-overview]')||document.querySelector('[data-ku-consolidated-overview]')||document.getElementById('department-publication-overview');
if(!overview&&(previous||students||study||section)){overview=el('section',null,'department-section');overview.append(el('h2','Research overview'))}
if(overview){
if(previous&&previous!==overview)previous.replaceWith(overview);else if(!overview.isConnected){if(study)study.after(overview);else if(students)students.before(overview);else if(section)section.before(overview)}
overview.id='research';overview.dataset.kuGlobalResearchOverview=id;overview.dataset.kuConsolidatedOverview=id;
let heading=overview.querySelector(':scope>h2');if(!heading){heading=el('h2','Research overview');overview.prepend(heading)}else if(heading.textContent!=='Research overview')heading.textContent='Research overview';
const keep=overview.querySelector('[data-ku-research-metrics]');document.querySelectorAll('main [data-ku-research-metrics]').forEach(panel=>{if(panel!==keep)panel.remove()});if(!keep)metrics(overview,id,true);
const destination=id==='environmental-science'?base+'departments/environmental-science-publications.html':section?'#publications':null;
if(destination){let all=overview.querySelector('a[data-ku-overview-publications]')||Array.from(overview.querySelectorAll('a')).find(a=>/^View (all )?publications/.test(a.textContent));if(!all){all=el('a','View all publications →');const paragraph=el('p');paragraph.append(all);overview.append(paragraph)}all.dataset.kuOverviewPublications='true';if(all.getAttribute('href')!==destination)all.href=destination}
}
if(feed)showFeed(feed,id);
}
const intro=document.querySelector('.department-publications-page .page-intro>p:last-child');if(intro&&intro.textContent.includes('our faculty'))intro.textContent=intro.textContent.replace('our faculty','our teaching team and PhD students');
};"""
    text=text[:first]+replacement+text[last:]
    path.write_text(text,encoding='utf-8')
