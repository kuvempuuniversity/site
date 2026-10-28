"use strict";
(()=>{
const grid=document.getElementById('programmes');if(!grid||document.getElementById('department-card-image-styles'))return;
const style=document.createElement('style');style.id='department-card-image-styles';style.textContent=`
#programmes>.programme{display:grid;grid-template-columns:40% minmax(0,1fr);grid-template-rows:auto 1fr auto;gap:8px 20px;align-items:start;min-height:190px;padding:0;overflow:hidden}
#programmes>.programme>.department-card-image{grid-column:1;grid-row:1/4;align-self:stretch;position:relative;min-width:0;width:100%;height:100%;margin:0;background:#e9ecdf}
#programmes .department-card-image>a{position:absolute;inset:0;display:block;width:100%;height:100%;margin:0}
#programmes .department-card-image>a:focus-visible{outline-offset:-4px}
#programmes .department-card-image img{position:absolute;inset:0;display:block;width:100%;height:100%;object-fit:cover;border:0;border-radius:0}
#programmes .department-card-image figcaption{display:none}
#programmes>.programme>p,#programmes>.programme>h3,#programmes>.programme>a{grid-column:2;min-width:0}
#programmes>.programme>p{margin:26px 24px 5px 0}
#programmes>.programme>h3{margin:0 24px 12px 0;overflow-wrap:anywhere}
#programmes>.programme>h3>a{font:inherit;margin:0;text-decoration:none}
#programmes>.programme>h3>a:hover{text-decoration:underline;text-underline-offset:5px}
#programmes>.programme>a{margin:0 24px 26px 0;align-self:end;justify-self:start}
@media(max-width:1100px){#programmes>.programme{gap:8px 14px}#programmes>.programme>p{margin-top:20px;margin-right:20px}#programmes>.programme>h3{margin-right:20px}#programmes>.programme>a{margin-right:20px;margin-bottom:20px}}
@media(max-width:760px){#programmes{grid-template-columns:1fr}#programmes>.programme{grid-template-columns:36% minmax(0,1fr);min-height:170px}}
`;document.head.append(style);
const base=document.body.dataset.base||'./';
const fallback=()=>{const canvas=document.createElement('canvas');canvas.width=canvas.height=512;const c=canvas.getContext('2d');if(!c)return null;c.fillStyle='#e9ecdf';c.fillRect(0,0,512,512);c.strokeStyle='#8c9a89';c.lineWidth=5;c.strokeRect(174,178,164,140);c.beginPath();c.arc(290,214,13,0,Math.PI*2);c.stroke();c.beginPath();c.moveTo(188,300);c.lineTo(235,250);c.lineTo(275,286);c.lineTo(300,261);c.lineTo(325,300);c.stroke();return canvas.toDataURL('image/png')};
grid.querySelectorAll('.programme').forEach(card=>{card.querySelectorAll('.department-card-image').forEach(n=>n.remove());const heading=card.querySelector('h3'),name=heading?.textContent.trim(),a=card.querySelector(':scope>a[href]');if(!name||!a)return;const href=a.getAttribute('href'),match=href.match(/departments\/([a-z0-9-]+)\.html(?:[?#].*)?$/);if(!match)return;const titleLink=document.createElement('a');titleLink.href=href;titleLink.textContent=name;heading.replaceChildren(titleLink);const figure=document.createElement('figure');figure.className='department-card-image';const imageLink=document.createElement('a');imageLink.href=href;imageLink.setAttribute('aria-label','Explore '+name);const image=document.createElement('img');image.width=image.height=512;image.loading='lazy';image.decoding='async';image.alt='';image.addEventListener('error',()=>{const png=fallback();if(png)image.src=png},{once:true});image.src=base+'assets/img/departments/cards/'+match[1]+'-card.png';imageLink.append(image);figure.append(imageLink);card.prepend(figure)});
})();
