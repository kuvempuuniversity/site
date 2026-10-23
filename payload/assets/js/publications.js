"use strict";
(()=>{
const base=document.body.dataset.base||'./';
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined&&text!==null)n.textContent=String(text);if(cls)n.className=cls;return n};
const clean=value=>String(value||'').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'').replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi,'').replace(/<[^>]*>/g,'').replace(/\s+/g,' ').trim();
const safe=value=>{try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password?u.href:null}catch{return null}};
const anchor=(text,url)=>{const href=safe(url);if(!href)return null;const a=el('a',text);a.href=href;a.target='_blank';a.rel='noopener noreferrer';return a};
const types={'journal-article':'Journal article (source classification)','preprint':'Preprint','conference-paper':'Conference paper','book':'Book'};
let loading;
function load(){if(!loading)loading=Promise.all([
fetch(base+'data/publications.json').then(r=>{if(!r.ok)throw Error('Publication data unavailable');return r.json()}),
fetch(base+'data/publication-sync-status.json').then(r=>{if(!r.ok)throw Error('Sync status unavailable');return r.json()}).catch(()=>null)
]);return loading}
function statusText(data,status,facultyId){
const all=status&&status.faculty?Object.entries(status.faculty):[];
const entries=facultyId?all.filter(([id])=>id===facultyId):all;
const failures=entries.filter(([,s])=>s.status==='failed');
const dates=entries.map(([,s])=>s.last_success).filter(Boolean).sort();
const stamp=facultyId?(entries[0]&&entries[0][1].last_success):data.last_successful_sync;
let text='Records may be incomplete. Citation metrics are not included. ';
if(stamp)text+='Last successful '+(facultyId?'profile retrieval':'full ORCID retrieval')+': '+stamp+' (UTC offset shown). ';
else if(dates.length)text+='Partial retrieval; successful records date from '+dates[0]+'. ';
else text+='No successful ORCID retrieval date is available. ';
if(failures.length)text+='Refresh failed for '+failures.map(([id])=>id).join(', ')+': previously imported records may be retained. ';
if(stamp&&Date.now()-Date.parse(stamp)>14*24*60*60*1000)text+='This ORCID snapshot is more than 14 days old. ';
text+=data.automatic_refresh?'Weekly refresh is configured; check the retrieval date for freshness.':'Scheduled refresh is not enabled.';
return text;
}
async function render(target,options={}){
target.setAttribute('aria-busy','true');
try{
const [data,status]=await load();if(!Array.isArray(data.publications))throw Error('Invalid publication data');
const rows=data.publications.filter(p=>options.facultyId?(p.faculty_ids||[]).includes(options.facultyId):(p.departments||[]).includes(options.departmentId)).sort((a,b)=>(Number(b.year)||0)-(Number(a.year)||0)||clean(a.title).localeCompare(clean(b.title)));
target.replaceChildren(el('p',rows.length+' imported '+(rows.length===1?'entry':'entries')+'. Shown newest first.','hint'));
if(!rows.length){const s=status&&status.faculty&&status.faculty[options.facultyId];let message='Publications have not yet been imported for this profile.';if(s&&s.status==='failed')message='The ORCID refresh failed. No cached publication entries are available.';else if(s&&s.status==='no_public_publications')message='No eligible public publications were returned by ORCID at the last successful check.';target.append(el('p',message+' This does not establish that the researcher has no publications.'))}
rows.forEach(p=>{
const card=el('article',undefined,'notice');card.append(el('h3',clean(p.title)));
if(p.authors_display)card.append(el('div',clean(p.authors_display)+(p.authors_truncated?' (abbreviated)':''),'hint'));
const meta=[clean(p.journal),p.year||'Undated',clean(p.reference),types[p.type]||clean(p.type)].filter(Boolean);card.append(el('div',meta.join(' · '),'hint'));
const links=el('div',undefined,'actions');links.style.marginTop='12px';
const doi=String(p.doi||'').replace(/^https?:\/\/(dx\.)?doi\.org\//i,'').trim();
const paper=doi&&/^10\.\d{4,9}\/\S+$/i.test(doi)?anchor('Open publication / DOI ↗','https://doi.org/'+doi):anchor('Open publication ↗',p.url);
if(paper)links.append(paper);
const provenance=Array.isArray(p.provenance)&&p.provenance.length?p.provenance:[{source_name:p.source_name,source_url:p.source_url}];
const unique=new Map();provenance.forEach(s=>{const url=safe(s.source_url);if(url)unique.set((s.source_name||'Source')+'|'+url,{name:s.source_name||'Source',url})});
unique.forEach(s=>{const a=anchor(s.name+' profile ↗',s.url);if(a)links.append(a)});
if(!paper){const search=anchor('Find title on Google Scholar ↗','https://scholar.google.com/scholar?q='+encodeURIComponent(clean(p.title)));links.append(search)}
card.append(el('div','Metadata source: '+[...new Set(provenance.map(s=>s.source_name||'Source'))].join(' + '),'hint'),links);target.append(card);
});
const note=statusText(data,status,options.facultyId);target.append(el('p',note,'event-note'));
if(options.departmentId){const coverage=document.querySelector('#publication-coverage');if(coverage)coverage.textContent=data.coverage+' '+note;const section=target.closest('section');if(section){const h=section.querySelector('h2');if(h)h.textContent='Publications';const intro=section.querySelector('p');if(intro&&intro.id!=='publication-coverage')intro.textContent='Publications and scholarly outputs associated with department faculty, collected from public ORCID records with legacy source information preserved. These are not necessarily works conducted at Kuvempu University.';const old=section.querySelector('p > a[href*="scholar.google.com/citations"]');if(old){old.href='https://orcid.org/';old.textContent='About ORCID ↗'}}}
}catch(error){target.replaceChildren(el('p','The imported publication list could not load. Use the faculty ORCID and Google Scholar profile links.','event-note'));if(options.departmentId){const note=document.querySelector('#publication-coverage');if(note)note.textContent='Publication data could not load. Refresh status is unavailable.'}console.error(error)}finally{target.setAttribute('aria-busy','false')}
}
window.KUPublications={render};
const target=document.querySelector('#publication-feed[data-department]');if(target)render(target,{departmentId:target.dataset.department});
})();
