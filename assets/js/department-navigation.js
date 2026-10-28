"use strict";
(()=>{
if(window.KUDepartmentNavigation||!/\/departments\/[^/]+\.html$/.test(location.pathname))return;window.KUDepartmentNavigation=true;
const base=document.body.dataset.base||'../';document.body.classList.add('department-navigation-page');const css=document.createElement('link');css.rel='stylesheet';css.href=base+'assets/css/department-navigation.css';document.head.append(css);
let pending=false;const reconcile=()=>{
pending=false;const header=document.querySelector('body>header.brandrow'),menu=header&&header.querySelector(':scope>.menu'),nav=header&&header.querySelector(':scope>#navigation');
if(header&&menu&&nav){header.classList.add('has-mobile-menu');const open=menu.getAttribute('aria-expanded')==='true';const text=open?'Close university menu ×':'University menu ☰';if(menu.textContent!==text)menu.textContent=text;const label=open?'Close university navigation':'Open university navigation';if(menu.getAttribute('aria-label')!==label)menu.setAttribute('aria-label',label);if(nav.getAttribute('aria-label')!=='University navigation')nav.setAttribute('aria-label','University navigation')}
const breadcrumb=document.querySelector('main .breadcrumb'),sections=document.querySelector('main .department-nav');if(!breadcrumb||!sections)return;
let row=document.querySelector('main .department-context-row');if(!row){row=document.createElement('div');row.className='department-context-row';breadcrumb.before(row)}if(breadcrumb.parentElement!==row)row.prepend(breadcrumb);if(sections.parentElement!==row)row.append(sections);if(!sections.hasAttribute('tabindex'))sections.tabIndex=0;
};
const schedule=()=>{if(!pending){pending=true;requestAnimationFrame(reconcile)}};const observer=new MutationObserver(schedule);observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-expanded']});reconcile();
document.addEventListener('click',e=>{const header=document.querySelector('body>header.brandrow');if(!header||header.contains(e.target))return;const menu=header.querySelector(':scope>.menu');if(menu&&menu.getAttribute('aria-expanded')==='true')menu.click()});
})();
