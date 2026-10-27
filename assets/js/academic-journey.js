"use strict";
(()=>{
const profile=document.querySelector('#faculty-profile');
if(!profile)return;
const base=document.body.dataset.base||'../';
const id=new URLSearchParams(location.search).get('id');
let journeys={};
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
};
new MutationObserver(render).observe(profile,{childList:true,subtree:true});
render();
fetch(base+'data/academic-journeys.json').then(response=>{if(!response.ok)throw Error('Academic journey data unavailable');return response.json()}).then(data=>{if(data&&typeof data==='object'&&!Array.isArray(data))journeys=data;render()}).catch(()=>render());
})();
