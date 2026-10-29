"use strict";
(()=>{
const profile=document.querySelector('#faculty-profile');
if(!profile)return;
const base=document.body.dataset.base||'../';
const id=new URLSearchParams(location.search).get('id');
let journeys={},faculty={};
const render=()=>{
const interests=profile.querySelector('.faculty-research-interests');
if(!interests)return;
let section=profile.querySelector('.faculty-academic-journey');
if(!section){
section=document.createElement('p');
section.className='faculty-research-interests faculty-academic-journey';
const heading=document.createElement('strong');
heading.textContent='Academic journey: ';
section.append(heading,document.createTextNode(''));
interests.after(section);
}
const text=typeof journeys[id]==='string'&&journeys[id].trim()?journeys[id].trim():'Information to be added.';
if(section.lastChild.textContent!==text)section.lastChild.textContent=text;
const f=faculty[id],identity=profile.querySelector('.faculty-profile-identity');if(!f||!identity)return;
const roles=Array.isArray(f.additional_roles)?f.additional_roles.filter(x=>typeof x==='string'&&x.trim()).map(x=>x.trim()):[];
const teaching=profile.querySelector('.faculty-teaching');
if(roles.length&&teaching&&!profile.querySelector('.faculty-additional-responsibilities')){
const p=document.createElement('p'),label=document.createElement('strong');
p.className='faculty-teaching faculty-additional-responsibilities';
label.textContent='Additional responsibilities: ';
const responsibilities=id==='hina-kousar'?"Faculty Advisor of Ladies' Hostel (2008 onwards); Director, Women's study centre from (2022 to 2026).":roles.join('; ').replace(/[.]+$/,'')+'.';
p.append(label,document.createTextNode(responsibilities));
teaching.after(p);
}
const notes=typeof f.additional_notes==='string'?f.additional_notes.trim():'';
const supervisor=typeof f.phd_supervisor==='string'?f.phd_supervisor.trim():'';
if(profile.querySelector('.faculty-additional-details')||(!notes&&!supervisor))return;
const extra=document.createElement('section');extra.className='faculty-additional-details';extra.setAttribute('aria-label','Additional profile details');
if(notes){const p=document.createElement('p');p.textContent=notes;extra.append(p)}
if(supervisor){const p=document.createElement('p'),label=document.createElement('strong');label.textContent='PhD supervisor: ';p.append(label,document.createTextNode(supervisor));extra.append(p)}
identity.after(extra);
};
new MutationObserver(render).observe(profile,{childList:true,subtree:true});
render();
fetch(base+'data/academic-journeys.json').then(response=>{if(!response.ok)throw Error('Academic journey data unavailable');return response.json()}).then(data=>{if(data&&typeof data==='object'&&!Array.isArray(data))journeys=data;render()}).catch(()=>render());
fetch(base+'data/faculty.json').then(response=>{if(!response.ok)throw Error('Faculty metadata unavailable');return response.json()}).then(data=>{if(data&&Array.isArray(data.faculty))faculty=Object.fromEntries(data.faculty.map(f=>[f.id,f]));render()}).catch(()=>{});
})();
