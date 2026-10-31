"use strict";
(()=>{
if(window.KUDepartmentNavigation||!/\/departments\/[^/]+\.html$/.test(location.pathname))return;window.KUDepartmentNavigation=true;
const base=document.body.dataset.base||'../';document.body.classList.add('department-navigation-page','department-people-cards');
const css=document.createElement('link');css.rel='stylesheet';css.href=base+'assets/css/department-navigation.css';document.head.append(css);
const cardsCss=document.createElement('link');cardsCss.rel='stylesheet';cardsCss.href=base+'assets/css/department-people-cards.css';document.head.append(cardsCss);
if(!Array.from(document.scripts).some(s=>s.src&&new URL(s.src,location.href).pathname.endsWith('/assets/js/department-research.js'))){const research=document.createElement('script');research.src=base+'assets/js/department-research.js';document.head.append(research)}
const annotateCards=()=>{
document.querySelectorAll('main #people>.event-grid>.panel,main #students>.event-grid>.panel').forEach(card=>{
const heading=card.querySelector(':scope>h3');if(!heading)return;heading.classList.add('department-card-name');
const paragraphs=[];for(let node=heading.nextElementSibling;node;node=node.nextElementSibling)if(node.tagName==='P')paragraphs.push(node);
paragraphs.forEach(p=>p.classList.remove('department-card-position','department-card-excerpt','department-card-link'));
const more=paragraphs[paragraphs.length-1];if(more)more.classList.add('department-card-link');
if(paragraphs.length>1)paragraphs[0].classList.add('department-card-position');
paragraphs.slice(1,-1).forEach(p=>p.classList.add('department-card-excerpt'));
});
};
let pending=false;const reconcile=()=>{
pending=false;const facultyHeading=document.querySelector('main #people>h2');if(facultyHeading&&facultyHeading.textContent.trim()==='Faculty & research interests')facultyHeading.textContent='Teaching team';
document.querySelectorAll('main #people>p').forEach(p=>{if(p.textContent.trim()==='Meet our faculty and explore their research interests.')p.textContent='Meet our teaching team and explore their expertise.'});
annotateCards();const header=document.querySelector('body>header.brandrow'),menu=header&&header.querySelector(':scope>.menu'),nav=header&&header.querySelector(':scope>#navigation');
if(header&&menu&&nav){header.classList.add('has-mobile-menu');const open=menu.getAttribute('aria-expanded')==='true';const text=open?'Close university menu ×':'University menu ☰';if(menu.textContent!==text)menu.textContent=text;const label=open?'Close university navigation':'Open university navigation';if(menu.getAttribute('aria-label')!==label)menu.setAttribute('aria-label',label);if(nav.getAttribute('aria-label')!=='University navigation')nav.setAttribute('aria-label','University navigation')}
const breadcrumb=document.querySelector('main .breadcrumb'),sections=document.querySelector('main .department-nav');if(!breadcrumb||!sections)return;
let row=document.querySelector('main .department-context-row');if(!row){row=document.createElement('div');row.className='department-context-row';breadcrumb.before(row)}if(breadcrumb.parentElement!==row)row.prepend(breadcrumb);if(sections.parentElement!==row)row.append(sections);if(!sections.hasAttribute('tabindex'))sections.tabIndex=0;
};
const schedule=()=>{if(!pending){pending=true;requestAnimationFrame(reconcile)}};const observer=new MutationObserver(schedule);observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-expanded']});reconcile();
document.addEventListener('click',e=>{const header=document.querySelector('body>header.brandrow');if(!header||header.contains(e.target))return;const menu=header.querySelector(':scope>.menu');if(menu&&menu.getAttribute('aria-expanded')==='true')menu.click()});
})();
