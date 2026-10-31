"use strict";
(()=>{
if(globalThis.KUDepartmentResearch)return;
const doi=v=>{const d=String(v||'').trim().replace(/^(?:https?:\/\/(?:dx\.)?doi\.org\/|doi\s*:\s*)/i,'').toLowerCase();return /^10\.\d{4,9}\/\S+$/i.test(d)?d:''};
const norm=v=>String(v||'').normalize('NFKC').toLowerCase().replace(/<[^>]*>/g,' ').replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const rows=(data,key)=>data&&Array.isArray(data[key])?data[key]:[];
const stamp=(v,now)=>Number.isFinite(Date.parse(v))&&Date.parse(v)<=now;
const kind=p=>String(p.type||'').toLowerCase().replace(/[_ ]/g,'-');
const paper=p=>['journal-article','review','review-article','conference-paper'].includes(kind(p))&&!p._typeConflict&&!p._unpublished&&!/unpublished/i.test(p.display_type||p.journal||'')&&!doi(p.doi).startsWith('10.13140/rg.');
function aggregate(data,departmentId,now=Date.now()){
const faculty=rows(data.faculty,'faculty'),students=rows(data.students,'students').filter(s=>s.published===true);
const fmap=new Map(faculty.map(p=>[p.id,p])),smap=new Map(students.map(p=>[p.id,p]));
const members=[...faculty.filter(p=>p.department_id===departmentId).map(p=>({...p,role:'faculty'})),...students.filter(p=>p.department_id===departmentId).map(p=>({...p,role:'students'}))];
const identity=p=>p.email?'email:'+p.email.toLowerCase():p.orcid?'orcid:'+p.orcid:p.role+':'+p.id;
const people=new Map();members.forEach(p=>{const key=identity(p);if(!people.has(key))people.set(key,[]);people.get(key).push(p)});
const orcids=new Set(members.map(p=>p.orcid).filter(Boolean));
const knownOrcids=new Set([...faculty,...students].map(p=>p.orcid).filter(Boolean));
let legacy=0;
const belongs=p=>{let known=false,match=false;const check=(id,map)=>{if(map.has(id)){known=true;if(map.get(id).department_id===departmentId)match=true}};
(p.faculty_ids||[]).forEach(id=>check(id,fmap));(p.student_ids||[]).forEach(id=>check(id,smap));
(p.provenance||[]).forEach(s=>{if(s.faculty_id)check(s.faculty_id,fmap);if(s.student_id)check(s.student_id,smap);if(s.orcid&&knownOrcids.has(s.orcid)){known=true;if(orcids.has(s.orcid))match=true}});
if(known)return match;const fallback=(p.departments||[]).includes(departmentId);if(fallback)legacy++;return fallback};
const incoming=[...rows(data.publications,'publications'),...rows(data.studentPublications,'publications')].filter(belongs);
members.forEach(p=>{rows(p,'publications').forEach(v=>incoming.push({...v,title:v.title,url:v.url||v.link,journal:v.journal||v.venue,authors_display:v.authors_display||v.authors,departments:[departmentId],source_name:v.source_name||'User supplied'}))});
const merged=[],byDoi=new Map(),bySignature=new Map();
for(const original of incoming){if(!original||!String(original.title||'').trim())continue;const p={...original,doi:doi(original.doi),provenance:[...(original.provenance||[])]};
const title=norm(p.title),signature=title.length>=40&&p.year&&p.journal?title+'|'+p.year+'|'+norm(p.journal):'';
let target=p.doi?byDoi.get(p.doi):null;
if(!target&&signature){const candidates=(bySignature.get(signature)||[]).filter(v=>!p.doi||!v.doi);if(candidates.length===1)target=candidates[0]}
if(!target&&p.id)target=merged.find(v=>v.id===p.id&&norm(v.title)===title&&v.year===p.year&&(!v.doi||!p.doi||v.doi===p.doi));
if(target){if(kind(target)&&kind(p)&&kind(target)!==kind(p))target._typeConflict=true;
if(/unpublished/i.test(p.display_type||p.journal||'')||p.doi.startsWith('10.13140/rg.'))target._unpublished=true;
for(const key of ['doi','journal','url','authors_display','type','display_type'])if(!target[key]&&p[key])target[key]=p[key];
for(const key of ['faculty_ids','student_ids','departments'])target[key]=[...new Set([...(target[key]||[]),...(p[key]||[])])];
const provenance=new Map([...target.provenance,...p.provenance].map(v=>[JSON.stringify(v),v]));target.provenance=[...provenance.values()];
}else{target=p;merged.push(target);if(signature){if(!bySignature.has(signature))bySignature.set(signature,[]);bySignature.get(signature).push(target)}}
if(target.doi)byDoi.set(target.doi,target);
}
merged.sort((a,b)=>(Number(b.year)||0)-(Number(a.year)||0)||String(a.title).localeCompare(String(b.title)));
const entries=Object.create(null);
for(const metrics of [data.citations,data.studentCitations])for(const [key,value] of Object.entries(metrics&&metrics.entries||{})){
const d=doi(key);if(!d||!value||value.doi!==d||value.source!=='OpenAlex'||!Number.isSafeInteger(value.count)||value.count<0||!/^https:\/\/openalex\.org\/W\d+$/.test(value.source_url||'')||!stamp(value.retrieved_at,now))continue;
if(!entries[d]||Date.parse(value.retrieved_at)>Date.parse(entries[d].retrieved_at))entries[d]=value;
}
const papers=merged.filter(paper),matched=papers.map(p=>entries[p.doi]).filter(Boolean);
const fetched=new Set(),publicationDates=[];
for(const [key,records] of people)for(const p of records){const statuses=p.role==='faculty'?data.status&&data.status.faculty:data.studentStatus&&data.studentStatus.students;const status=statuses&&statuses[p.id];if(status&&stamp(status.last_success,now)){fetched.add(key);publicationDates.push(status.last_success)}}
merged.forEach(p=>(p.provenance||[]).forEach(s=>{if(stamp(s.retrieved_at,now))publicationDates.push(s.retrieved_at)}));
const publicationAvailable=!!(data.publications&&Array.isArray(data.publications.publications)||data.studentPublications&&Array.isArray(data.studentPublications.publications));
const missingDatasets=(!data.publications||!Array.isArray(data.publications.publications)?1:0)+(!data.studentPublications||!Array.isArray(data.studentPublications.publications)?1:0);
const rawPhd=data.phds&&data.phds.departments&&data.phds.departments[departmentId];
const validPhd=rawPhd&&Number.isSafeInteger(rawPhd.count)&&rawPhd.count>=0&&/^\d{4}-\d{2}-\d{2}$/.test(rawPhd.verified_through||'')&&stamp(rawPhd.verified_through,now)&&new Date(rawPhd.verified_through).toISOString().slice(0,10)===rawPhd.verified_through&&typeof rawPhd.source==='string'&&rawPhd.source.trim();
const citationDates=matched.map(v=>v.retrieved_at).sort((a,b)=>Date.parse(a)-Date.parse(b));publicationDates.sort((a,b)=>Date.parse(a)-Date.parse(b));
const count=publicationAvailable&&(merged.length||fetched.size)?papers.length:null;
const note='Teaching-team and PhD-student records, deduplicated across both lists. '+(count===null?'Paper count not yet available. ':count+' source-classified research papers among '+merged.length+' listed outputs. ')+matched.length+' of '+papers.length+' papers have valid OpenAlex citation counts. '+fetched.size+' of '+people.size+' listed researchers have a successful retrieval recorded. '+(missingDatasets?'One or more publication datasets are unavailable. ':'')+(legacy?legacy+' records retain legacy department tags pending profile matching. ':'')+(matched.some(v=>v.status!=='success')?'Some citation values are retained from earlier successful checks. ':'')+'Coverage may be incomplete; records can predate the researcher’s time at Kuvempu University.';
return {publications:merged,papers,paperCount:count,citations:matched.length?matched.reduce((sum,v)=>sum+v.count,0):null,citationCoverage:matched.length,phds:validPhd?rawPhd.count:null,phdDate:validPhd?rawPhd.verified_through:null,citationDates,publicationDates,metrics:{entries},note,metadata:{coverage:'Combined teaching-team and PhD-student records.',automatic_refresh:false}};
}
let loading;
async function load(){if(!loading)loading=(async()=>{const base=typeof document==='undefined'?'../':document.body.dataset.base||'../';const files={faculty:'faculty.json',students:'research-students.json',publications:'publications.json',studentPublications:'student-publications.json',citations:'citation-metrics.json',studentCitations:'student-citation-metrics.json',status:'publication-sync-status.json',studentStatus:'student-publication-sync-status.json',phds:'department-phds.json'};const pairs=await Promise.all(Object.entries(files).map(async([key,file])=>{try{const r=await fetch(base+'data/'+file);if(!r.ok)throw Error(file);return [key,await r.json()]}catch{return [key,null]}}));const data=Object.fromEntries(pairs);if(!data.faculty||!Array.isArray(data.faculty.faculty)||!data.students||!Array.isArray(data.students.students))throw Error('Researcher directory unavailable');return data})();return loading}
const get=async id=>aggregate(await load(),id);
globalThis.KUDepartmentResearch={get,aggregate,doi,paper};
if(typeof document==='undefined')return;
const base=document.body.dataset.base||'../';
const css=document.createElement('link');css.rel='stylesheet';css.href=base+'assets/css/department-research.css';document.head.append(css);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=String(text);if(cls)n.className=cls;return n};
const dateRange=values=>{const dates=[...new Set(values.map(v=>new Date(v).toISOString().slice(0,10)))];return dates.length?dates[0]+(dates.length>1?' to '+dates[dates.length-1]:''):'not yet available'};
function metrics(root,id){const section=el('section',null,'department-research-metrics');section.dataset.kuResearchMetrics='true';section.setAttribute('aria-label','Research at a glance');section.setAttribute('aria-busy','true');const dl=el('dl',null,'department-research-metric-grid');const values=[];['PhDs awarded','Research paper count','Citations to these papers'].forEach(label=>{const item=el('div');const value=el('dd','—');item.append(el('dt',label),value);dl.append(item);values.push(value)});const note=el('p','Loading research records…','hint');section.append(dl,note);const host=root.querySelector('.department-research-copy')||root,paragraph=host.querySelector(':scope>p'),heading=host.querySelector(':scope>h2');if(paragraph)paragraph.after(section);else if(heading)heading.after(section);else host.append(section);
get(id).then(r=>{[r.phds,r.paperCount,r.citations].forEach((v,i)=>values[i].textContent=v==null?'—':v.toLocaleString('en-IN'));note.textContent=(r.phdDate?'PhDs verified through '+r.phdDate+'. ':'PhD total awaiting verified departmental records. ')+(r.paperCount==null?'Publication and citation counts await usable records.':r.citationCoverage+' of '+r.papers.length+' papers have citation counts. Citation dates: '+dateRange(r.citationDates)+'.');const details=el('details'),summary=el('summary','About these figures');details.append(summary,el('p',r.note+' The paper counter includes journal articles, review articles and full conference papers; other output types and flagged unpublished works remain listed but are excluded. Publication snapshots: '+dateRange(r.publicationDates)+'.'));section.append(details);const link=el('a','View publications →');link.href=id==='environmental-science'?base+'departments/environmental-science-publications.html':'#publications';section.append(link)}).catch(()=>{note.textContent='Research figures are temporarily unavailable; missing data are not shown as zero.'}).finally(()=>section.setAttribute('aria-busy','false'));
}
function showFeed(feed,id){if(feed.dataset.kuDepartmentPublication===id)return;if(globalThis.KUPublications){globalThis.KUPublications.render(feed,{departmentId:id});return}if(Array.from(document.scripts).some(s=>s.src&&new URL(s.src,location.href).pathname.endsWith('/assets/js/publications.js')))return;const script=document.createElement('script');script.src=base+'assets/js/publications.js';script.onerror=()=>{feed.textContent='Publication display could not load.'};document.head.append(script)}
const match=location.pathname.match(/\/departments\/([a-z0-9-]+)\.html$/);if(!match)return;
const mount=()=>{const existing=document.querySelector('#publication-feed[data-department]');const id=existing?existing.dataset.department:match[1].replace(/-publications$/,'');const root=document.getElementById('research');if(root&&!root.querySelector('[data-ku-research-metrics]'))metrics(root,id);let feed=existing;const section=document.getElementById('publications');if(section&&!feed){feed=el('div','Loading publications…');feed.id='publication-feed';feed.dataset.department=id;section.querySelectorAll(':scope>p').forEach(p=>{if(p.textContent.trim()==='Publication records will be added here.')p.remove()});section.append(feed)}if(feed)showFeed(feed,id);const intro=document.querySelector('.department-publications-page .page-intro>p:last-child');if(intro&&intro.textContent.includes('our faculty'))intro.textContent=intro.textContent.replace('our faculty','our teaching team and PhD students')};
let pending=false;const schedule=()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;mount()})};new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});mount();
})();
