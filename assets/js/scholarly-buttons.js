"use strict";
(()=>{
if(window.KUScholarlyButtons)return;window.KUScholarlyButtons=true;
const style=document.createElement('style');style.textContent=`
#people .actions,#faculty-profile .actions,#publication-feed .actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
a.scholarly-button{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:40px;max-width:100%;box-sizing:border-box;padding:7px 11px;border:1px solid #b6c3bc;border-radius:6px;background:#fff;color:#234134;font:inherit;font-size:.875rem;line-height:1.35;text-decoration:none;vertical-align:middle}
a.scholarly-button:hover{background:#f1f5f2;border-color:#496657;text-decoration:none}
a.scholarly-button:focus-visible{outline:3px solid #234134;outline-offset:3px}
.scholarly-button img{display:block;width:24px;height:24px;object-fit:contain;flex:none}
.scholarly-button-label{display:flex;flex-direction:column;text-align:left}
`;
document.head.append(style);
const assets={scholar:'https://scholar.google.com/favicon.ico',orcid:'https://commons.wikimedia.org/wiki/Special:Redirect/file/ORCID_iD.svg',doi:'https://commons.wikimedia.org/wiki/Special:Redirect/file/DOI_logo.svg'};
const selector='#people .actions a, #faculty-profile .actions a, #publication-feed .actions a';
function classify(a){
let url;try{url=new URL(a.href)}catch{return null}
if(!['http:','https:'].includes(url.protocol)||url.username||url.password)return null;
if(url.hostname==='scholar.google.com'&&url.pathname==='/citations')return {kind:'scholar',label:'Google Scholar',url};
if(url.hostname==='orcid.org'&&/^\/\d{4}-\d{4}-\d{4}-\d{3}[\dX]\/?$/.test(url.pathname))return {kind:'orcid',label:'ORCID iD',url};
if(['doi.org','dx.doi.org'].includes(url.hostname)&&/^\/10\.\d{4,9}\/.+/.test(url.pathname)){url.protocol='https:';url.hostname='doi.org';return {kind:'doi',label:'View publication',url}}
if(/^Open publication(?:\s|$)/.test(a.textContent.trim()))return {kind:'publication',label:'Open publication',url};
return null;
}
function enhance(){
document.querySelectorAll(selector).forEach(a=>{
if(a.dataset.scholarlyButton)return;
const match=classify(a);if(!match)return;
a.dataset.scholarlyButton=match.kind;a.classList.add('scholarly-button');a.href=match.url.href;a.target='_blank';a.rel='noopener noreferrer';
const label=document.createElement('span');label.className='scholarly-button-label';label.textContent=match.label;
a.setAttribute('aria-label',match.label+(match.kind==='orcid'?' (unauthenticated)':'')+' — opens in a new tab');
a.title=match.kind==='orcid'?'View ORCID record '+match.url.pathname.slice(1)+' (manually supplied; not authenticated through ORCID sign-in)':match.kind==='doi'?match.url.href:match.kind==='publication'?'Open publication':match.label+' profile';
a.replaceChildren();
if(assets[match.kind]){const icon=document.createElement('img');icon.src=assets[match.kind];icon.alt='';icon.setAttribute('aria-hidden','true');icon.width=24;icon.height=24;icon.loading='lazy';icon.referrerPolicy='no-referrer';icon.addEventListener('error',()=>{icon.hidden=true;icon.style.display='none'},{once:true});a.append(icon)}
a.append(label);
});
}
let queued=false;
const observer=new MutationObserver(()=>{if(queued)return;queued=true;queueMicrotask(()=>{queued=false;enhance()})});
observer.observe(document.body,{childList:true,subtree:true});enhance();
})();
