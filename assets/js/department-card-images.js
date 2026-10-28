"use strict";
(()=>{
const grid=document.getElementById('programmes');if(!grid||document.getElementById('department-card-image-styles'))return;
const style=document.createElement('style');style.id='department-card-image-styles';style.textContent=`
#programmes>.programme{display:grid;grid-template-columns:112px minmax(0,1fr);grid-template-rows:auto 1fr auto;gap:8px 20px;align-items:start;min-height:190px}
#programmes>.programme>.department-card-image{grid-column:1;grid-row:1/-1;min-width:0;width:100%;margin:0}
#programmes .department-card-image img{display:block;width:100%;height:auto;aspect-ratio:1;object-fit:cover;background:#e9ecdf;border:1px solid var(--line);border-radius:4px}
#programmes .department-card-image figcaption{margin-top:7px;color:var(--muted);font-size:10px;line-height:1.4;overflow-wrap:anywhere}
#programmes>.programme>p,#programmes>.programme>h3,#programmes>.programme>a{grid-column:2;min-width:0}
#programmes>.programme>p{margin:0 0 5px}
#programmes>.programme>h3{margin:0 0 12px;overflow-wrap:anywhere}
#programmes>.programme>a{margin-top:0;align-self:end}
@media(max-width:1100px){#programmes>.programme{grid-template-columns:88px minmax(0,1fr);gap:8px 14px}}
@media(max-width:760px){#programmes{grid-template-columns:1fr}#programmes>.programme{grid-template-columns:96px minmax(0,1fr);min-height:170px}}
`;document.head.append(style);
const base=document.body.dataset.base||'./';
const fallback=name=>{const canvas=document.createElement('canvas');canvas.width=canvas.height=512;const c=canvas.getContext('2d');if(!c)return null;c.fillStyle='#e9ecdf';c.fillRect(0,0,512,512);c.strokeStyle='#bfc9b7';c.lineWidth=2;c.strokeRect(24,24,464,464);c.strokeStyle='#59675e';c.lineWidth=4;c.strokeRect(204,86,104,88);c.beginPath();c.moveTo(212,162);c.lineTo(244,130);c.lineTo(270,151);c.lineTo(287,135);c.lineTo(300,162);c.stroke();c.fillStyle='#143e34';c.textAlign='center';c.font='27px system-ui,sans-serif';let lines=[],line='';name.split(' ').forEach(word=>{const next=line?line+' '+word:word;if(c.measureText(next).width>410&&line){lines.push(line);line=word}else line=next});if(line)lines.push(line);lines.forEach((text,i)=>c.fillText(text,256,250+i*38));c.fillStyle='#59675e';c.font='18px system-ui,sans-serif';c.fillText('IMAGE PLACEHOLDER',256,395);return canvas.toDataURL('image/png')};
grid.querySelectorAll('.programme').forEach(card=>{if(card.querySelector('.department-card-image'))return;const name=card.querySelector('h3')?.textContent.trim(),a=card.querySelector('a[href]');if(!name||!a)return;const match=a.getAttribute('href').match(/departments\/([a-z0-9-]+)\.html(?:[?#].*)?$/);if(!match)return;const figure=document.createElement('figure');figure.className='department-card-image';const image=document.createElement('img');image.width=image.height=512;image.loading='lazy';image.decoding='async';image.alt=name+' department image';image.addEventListener('error',()=>{image.alt='Image placeholder for '+name;const png=fallback(name);if(png)image.src=png},{once:true});image.src=base+'assets/img/departments/cards/'+match[1]+'-card.png';const caption=document.createElement('figcaption');caption.textContent='Image: '+name;figure.append(image,caption);card.prepend(figure)});
})();
