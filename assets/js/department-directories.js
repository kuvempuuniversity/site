"use strict";
(()=>{
if(window.KUDepartmentDirectories||!/\/departments\/[^/]+\.html$/.test(location.pathname))return;
window.KUDepartmentDirectories=true;
const style=document.createElement('style');style.id='department-directory-disclosure-styles';style.textContent=`
main #people[data-ku-directory-collapsed="true"]>:not(.ku-directory-heading),main #students[data-ku-directory-collapsed="true"]>:not(.ku-directory-heading){display:none!important}
.ku-directory-heading{margin-bottom:0}
.ku-directory-toggle{display:flex;align-items:center;justify-content:space-between;gap:20px;width:100%;min-height:56px;padding:12px 0;border:0;background:transparent;color:inherit;font:inherit;text-align:left;cursor:pointer}
.ku-directory-toggle:focus-visible{outline:3px solid currentColor;outline-offset:6px;border-radius:3px}
.ku-directory-affordance{display:flex;align-items:center;gap:12px;flex-shrink:0;font-size:13px;font-weight:400;color:var(--muted)}
.ku-directory-arrow{font-size:22px;line-height:1;color:var(--ink)}
main #people[data-ku-directory-collapsed="false"]>.ku-directory-heading,main #students[data-ku-directory-collapsed="false"]>.ku-directory-heading{margin-bottom:20px}
@media(max-width:600px){.ku-directory-toggle{gap:12px;align-items:flex-start}.ku-directory-affordance{padding-top:5px}.ku-directory-hint{max-width:90px;font-size:12px}}
@media print{main #people[data-ku-directory-collapsed]>:not(.ku-directory-heading),main #students[data-ku-directory-collapsed]>:not(.ku-directory-heading){display:revert!important}.ku-directory-affordance{display:none}}
`;document.head.append(style);
const states=new WeakMap();let pending=false,hashPending=true;
function setOpen(section,open){
const state=states.get(section);if(!state)return;state.open=open;
const value=String(!open);if(section.dataset.kuDirectoryCollapsed!==value)section.dataset.kuDirectoryCollapsed=value;
const button=section.querySelector(':scope>.ku-directory-heading>.ku-directory-toggle');if(!button)return;
if(button.getAttribute('aria-expanded')!==String(open))button.setAttribute('aria-expanded',String(open));
const label=(section.id==='people'?'Teaching team':'Research students')+(open?': collapse':': expand to view all');if(button.getAttribute('aria-label')!==label)button.setAttribute('aria-label',label);
const hint=button.querySelector('.ku-directory-hint'),arrow=button.querySelector('.ku-directory-arrow');const text=open?'Collapse':'Expand to view all',symbol=open?'▾':'▸';
if(hint.textContent!==text)hint.textContent=text;if(arrow.textContent!==symbol)arrow.textContent=symbol;
}
function revealHash(hash=location.hash){
let id;try{id=decodeURIComponent(hash.slice(1))}catch{return true}if(!id)return true;
const target=document.getElementById(id);if(!target)return false;const section=target.closest('main #people,main #students');if(!section)return true;if(!states.has(section))return false;setOpen(section,true);return true;
}
function mount(){
pending=false;
document.querySelectorAll('main #people,main #students').forEach(section=>{
const heading=section.querySelector(':scope>h2');if(!heading)return;
if(!states.has(section))states.set(section,{open:false});
let button=heading.querySelector(':scope>.ku-directory-toggle');
if(!button){
heading.classList.add('ku-directory-heading');button=document.createElement('button');button.type='button';button.className='ku-directory-toggle';
const title=document.createElement('span');title.textContent=section.id==='people'?'Teaching team':'Research students';
const affordance=document.createElement('span');affordance.className='ku-directory-affordance';const hint=document.createElement('span');hint.className='ku-directory-hint';const arrow=document.createElement('span');arrow.className='ku-directory-arrow';arrow.setAttribute('aria-hidden','true');affordance.append(hint,arrow);button.append(title,affordance);heading.replaceChildren(button);
button.addEventListener('click',()=>setOpen(section,!states.get(section).open));
}
setOpen(section,states.get(section).open);
});
if(hashPending)hashPending=!revealHash();
}
const schedule=()=>{if(!pending){pending=true;requestAnimationFrame(mount)}};
new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});
window.addEventListener('hashchange',()=>{hashPending=true;schedule()});
document.addEventListener('click',event=>{const link=event.target instanceof Element&&event.target.closest('a[href]');if(!link)return;try{const url=new URL(link.href,document.baseURI);if(url.origin===location.origin&&url.pathname===location.pathname&&url.search===location.search&&url.hash)revealHash(url.hash)}catch{}});
mount();
})();
