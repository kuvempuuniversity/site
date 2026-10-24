"use strict";
(()=>{
const profile=document.querySelector('#faculty-profile');
if(!profile)return;
let record,observer,timer;
const update=()=>{
const note=profile.querySelector('.faculty-metric-note');
if(!note||!record)return;
observer.disconnect();clearTimeout(timer);
const m=record.scholar_metrics;
if(!m||m.source!=='Google Scholar'||m.scope!=='all-time'||m.scholar_url!==record.scholar_url)return;
const fields=['total_citations','h_index','i10_index'];const date=Date.parse(m.retrieved_at);const cached=Number.isFinite(date)&&date<=Date.now()&&fields.every(key=>Number.isSafeInteger(m[key])&&m[key]>=0);
if(m.status==='failed')note.append(document.createTextNode(cached?' · Last successful values; latest refresh failed.':' · Latest refresh failed.'));
if(cached&&Date.now()-date>14*24*60*60*1000)note.append(document.createTextNode(' · Snapshot more than 14 days old.'));
};
observer=new MutationObserver(update);observer.observe(profile,{childList:true,subtree:true});timer=setTimeout(()=>observer.disconnect(),30000);
fetch((document.body.dataset.base||'./')+'data/faculty.json').then(r=>{if(!r.ok)throw Error('Profile data unavailable');return r.json()}).then(data=>{const id=new URLSearchParams(location.search).get('id');record=Array.isArray(data.faculty)?data.faculty.find(f=>f.id===id):null;update()}).catch(()=>{observer.disconnect();clearTimeout(timer)});
})();
