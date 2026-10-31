import {arrange} from './publication-cloud-layout.js';
const stop=new Set('a an and are as at be been being but by can could did do does during each for from has have how if in into is it its may more most not of on or our over per study studies studying using use used uses with within without to the their these this those through under via was were what when where which while who will would about above across after against all also among analysis approach approaches assessment based between both case cases comparative comparison determination different effect effects evaluation evidence experimental experiments investigation investigations method methods new novel results review role some synthesis system systems toward towards very india karnataka shivamogga shimoga'.split(' '));
const clean=value=>String(value||'').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,' ').replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi,' ').replace(/<[^>]*>/g,' ').replace(/&(?:#x[0-9a-f]+|#\d+|[a-z]+);/gi,' ').normalize('NFKC').toLocaleLowerCase('en').replace(/[-‐‑–—]/g,' ');
export function extract(papers){
const counts=new Map();
for(const paper of papers){const tokens=clean(paper.title).match(/[\p{L}][\p{L}\p{M}\p{N}]*/gu)||[],seen=new Set();let run=[];
const flush=()=>{for(let i=0;i<run.length;i++)for(let n=1;n<=3&&i+n<=run.length;n++)seen.add(run.slice(i,i+n).join(' '));run=[]};
for(const token of tokens){if(token.length<3||stop.has(token))flush();else run.push(token)}flush();
for(const term of seen)counts.set(term,(counts.get(term)||0)+1);
}
const candidates=[...counts].filter(([,count])=>count>=2).map(([term,count])=>({term,count,words:term.split(' ').length}));
candidates.sort((a,b)=>b.count*(1+.25*(b.words-1))-a.count*(1+.25*(a.words-1))||b.words-a.words||a.term.localeCompare(b.term,'en'));
const selected=[];
for(const item of candidates){if(selected.some(other=>(' '+other.term+' ').includes(' '+item.term+' ')&&other.count===item.count))continue;selected.push(item);if(selected.length===28)break}
return selected;
}
export function emphasis(count,minimum,maximum){const ratio=maximum===minimum?.5:Math.max(0,Math.min(1,(count-minimum)/(maximum-minimum)));return {size:13+39*Math.pow(ratio,.8),weight:Math.round((400+400*ratio)/100)*100,colour:ratio>=.7?'var(--green)':ratio>=.35?'var(--ink)':'var(--muted)'}}
const el=(tag,text,cls)=>{const node=document.createElement(tag);if(text!=null)node.textContent=text;if(cls)node.className=cls;return node};
export function render(section,collection){
if(section.querySelector('.publication-overview'))return;
const dl=section.querySelector(':scope>dl');if(!dl)return;
const papers=collection.papers||[],terms=extract(papers).sort((a,b)=>b.count-a.count||b.words-a.words||a.term.localeCompare(b.term,'en'));
if(!document.querySelector('link[data-ku-publication-themes]')){const css=el('link');css.rel='stylesheet';css.href=new URL('../css/publication-themes.css',import.meta.url).href;css.dataset.kuPublicationThemes='true';document.head.append(css)}
const layout=el('div',null,'publication-overview'),left=el('div',null,'publication-overview-counts'),figure=el('figure',null,'publication-overview-themes');
left.append(el('h3','Research at a glance'));figure.append(el('h3','Themes in our publications'));
if(papers.length>=3&&terms.length>=6){
const list=el('ul',null,'publication-theme-terms');list.setAttribute('aria-label','Recurring title terms and the number of paper titles containing each term');const maximum=Math.max(...terms.map(t=>t.count)),minimum=Math.min(...terms.map(t=>t.count));
terms.forEach(term=>{const item=el('li'),appearance=emphasis(term.count,minimum,maximum);item.style.setProperty('--term-size',appearance.size.toFixed(1)+'px');item.style.fontWeight=String(appearance.weight);item.style.setProperty('--term-colour',appearance.colour);item.title=term.term+' — '+term.count+' paper titles';item.append(el('span',term.term),el('span',' — '+term.count+' paper titles','publication-theme-sr'));list.append(item)});figure.append(list);
}else figure.append(el('p','Not enough recurring title terms yet. Research themes will appear as publication records are added.','hint'));
figure.append(el('figcaption','Recurring terms extracted from '+papers.length+' available research-paper titles. Larger, bolder terms appear in more paper titles; selected location names are excluded. Positions are decorative, not measures of topic relationships. This is an indicative view, not author-supplied keywords or a measure of research impact.'));
layout.append(left,figure);section.prepend(layout);left.append(dl);const cloud=figure.querySelector('.publication-theme-terms');if(cloud)arrange(cloud).catch(()=>{});
}
