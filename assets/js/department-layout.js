"use strict";
(()=>{
if(window.KUDepartmentLayout)return;
const isEnvironmental=location.pathname.endsWith('/departments/environmental-science.html');
const isBotany=location.pathname.endsWith('/departments/applied-botany.html');
if(!isEnvironmental&&!isBotany)return;window.KUDepartmentLayout=true;
const base=document.body.dataset.base||'../';
const name=isEnvironmental?'Environmental Science':'Applied Botany';
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text)n.textContent=text;return n};
const style=el('style');style.textContent=`
.department-landing{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);margin:24px 0 30px;border:1px solid var(--line);background:#fffdf7;overflow:hidden}
.department-landing-image{margin:0;position:relative;min-height:510px;background:#e0e7d8}
.department-landing-image img{position:absolute;inset:0;display:block;width:100%;height:100%;object-fit:cover}
.department-landing-copy{display:flex;flex-direction:column;justify-content:center;gap:22px;min-width:0;padding:32px}
.department-landing .page-intro{padding:0}
.department-landing .page-intro h1{font-size:clamp(32px,3.5vw,48px);line-height:1.12;letter-spacing:-.035em;margin:10px 0 14px;overflow-wrap:anywhere}
.department-landing .eyebrow{margin:0;font-size:10px}
.department-landing .page-intro>p:last-child{margin-bottom:0}
.department-landing .department-hero{margin:0;padding:26px}
.department-landing .department-hero h2{font-size:clamp(25px,2.4vw,34px);line-height:1.2;letter-spacing:-.025em}
.department-landing .department-hero p{font-size:14px;line-height:1.65}
.department-landing .actions{gap:12px;margin-top:20px;font-size:13px}
.department-landing .btn{padding:11px 14px;gap:10px}
.department-feature-card.panel{padding:0;overflow:hidden}
.department-feature-card>img{display:block;width:100%;height:auto;aspect-ratio:16/10;object-fit:cover}
.department-feature-copy{padding:24px}
.department-feature-copy h3{font-size:19px}
.department-feature-copy p{margin:0;font-size:14px;line-height:1.7}
.department-research-split{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:38px;align-items:center}
.department-research-copy{min-width:0}
.department-research-copy h2{font-size:clamp(30px,3vw,42px);line-height:1.15}
.department-research-copy p{font-size:15px;line-height:1.8}
.department-research-copy h3{margin-top:26px;font-size:19px}
.department-research-image{margin:0;min-width:0;background:#e0e7d8}
.department-research-image img.department-photo{display:block;width:100%;height:auto;max-height:none;object-fit:contain}
.department-publications-page .page-intro{padding:25px 0}
.department-publications-page .page-intro h1{font-size:clamp(36px,5vw,58px)}
@media(max-width:900px){.department-landing-copy{padding:22px}.department-landing .department-hero{padding:22px}.department-research-split{gap:24px}}
@media(max-width:760px){.department-landing,.department-research-split{grid-template-columns:1fr}.department-landing-image{min-height:0;aspect-ratio:4/3}.department-landing-copy{padding:24px;gap:20px}.department-landing .page-intro h1{font-size:36px}.department-landing .department-hero h2{font-size:28px}.department-research-image img.department-photo{height:auto}.department-research-split{gap:24px}}
`;
document.head.append(style);
const intro=document.querySelector('.page-intro'),hero=document.querySelector('.department-hero');
if(intro&&hero){
const note=intro.querySelector('.event-note');if(note){if(isEnvironmental)note.remove();else note.textContent='Events in the legacy demonstration below are fictional.'}
if(isBotany){const eyebrow=intro.querySelector('.eyebrow');if(eyebrow)eyebrow.textContent='Department';const pending=hero.querySelector('p');if(pending&&pending.textContent.startsWith('Space for'))pending.remove()}
const landing=el('section','department-landing');landing.setAttribute('aria-label',name+' introduction');
const figure=el('figure','department-landing-image');const image=el('img');image.src=base+'assets/img/placeholders/'+(isEnvironmental?'home-research-background.png':'home-campus-life.png');image.alt='Illustrative photograph for '+name;image.decoding='async';image.setAttribute('fetchpriority','high');figure.append(image);
const copy=el('div','department-landing-copy');intro.replaceWith(landing);copy.append(intro,hero);landing.append(figure,copy);
}
if(!isEnvironmental)return;
document.querySelectorAll('.department-section .photo-caption').forEach(n=>n.remove());
document.querySelectorAll('.review-note').forEach(n=>n.remove());
const cards=document.querySelectorAll('#study .event-grid .panel');
const cardImages=['home-research-background.png','environmental-science-tools.png','environmental-science-fieldwork.png'];
const cardNames=['Research','Technology and data','Real-world questions'];
cards.forEach((card,index)=>{if(index>=cardImages.length)return;const copy=el('div','department-feature-copy');copy.append(...Array.from(card.childNodes));const img=el('img');img.src=base+'assets/img/placeholders/'+cardImages[index];img.alt='Illustrative image: '+cardNames[index];img.loading='lazy';img.decoding='async';card.classList.add('department-feature-card');card.append(img,copy)});
const research=document.querySelector('#research');
if(research){const image=research.querySelector('img.department-photo');if(image){const copy=el('div','department-research-copy');Array.from(research.childNodes).forEach(node=>{if(node!==image)copy.append(node)});const figure=el('figure','department-research-image');figure.append(image);const split=el('div','department-research-split');split.append(copy,figure);research.append(split)}}
const publicationPage=base+'departments/environmental-science-publications.html';
document.querySelectorAll('a[href="#publications"]').forEach(a=>{a.href=publicationPage});
const publications=document.querySelector('#publications');if(publications)publications.remove();
if(location.hash==='#publications')location.replace(publicationPage);
const people=document.querySelector('#people');
if(people){const tidy=()=>{Array.from(people.children).filter(n=>n.tagName==='P'&&n.textContent.includes('department information supplied for this prototype')).forEach(n=>{n.textContent='Meet our faculty and explore their research interests.'})};tidy();const watch=new MutationObserver(tidy);watch.observe(people,{childList:true})}
})();
