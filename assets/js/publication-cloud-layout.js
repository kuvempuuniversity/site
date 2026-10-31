const redraws=new WeakMap();
export function refresh(list){const redraw=redraws.get(list);if(redraw)redraw()}
export function pack(boxes,width,height,seed=1){
if(!boxes.length)return [];
const placed=[];let state=seed>>>0;const random=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296};
const valid=box=>box.x>=3&&box.y>=3&&box.x+box.width<=width-3&&box.y+box.height<=height-3&&!placed.some(p=>box.x<p.x+p.width+3&&box.x+box.width+3>p.x&&box.y<p.y+p.height+3&&box.y+box.height+3>p.y);
for(let index=0;index<boxes.length;index++){
const size=boxes[index];if(!(size.width>0&&size.height>0))return null;
let chosen=null;
if(index===0){const box={...size,x:(width-size.width)/2,y:(height-size.height)/2};if(valid(box))chosen=box}
else{const phase=random()*Math.PI*2;for(let step=1;step<=2000;step++){const radius=.72*Math.sqrt(step/2000),angle=phase+step*2.399963229728653;const box={...size,x:width/2+Math.cos(angle)*radius*width-size.width/2,y:height/2+Math.sin(angle)*radius*height-size.height/2};if(valid(box)){chosen=box;break}}}
if(!chosen)return null;placed.push(chosen);
}
return placed;
}
export async function arrange(list){
if(list.dataset.kuSpatialCloud)return;list.dataset.kuSpatialCloud='true';
const css=document.querySelector('link[data-ku-publication-themes]');
if(css&&!css.sheet){const loaded=await new Promise(resolve=>{const timer=setTimeout(()=>resolve(false),10000);const finish=ok=>{clearTimeout(timer);resolve(ok)};css.addEventListener('load',()=>finish(true),{once:true});css.addEventListener('error',()=>finish(false),{once:true})});if(!loaded)return}
if(document.fonts)await document.fonts.ready;
const items=Array.from(list.children),originalLabel=list.getAttribute('aria-label');let seed=2166136261;for(const item of items)for(const character of item.firstElementChild.textContent)seed=Math.imul(seed^character.codePointAt(0),16777619)>>>0;
let lastWidth=-1,pending=false;
const reset=()=>{list.classList.remove('is-packed','is-measuring');list.style.removeProperty('height');list.style.removeProperty('--cloud-scale');list.removeAttribute('tabindex');if(originalLabel)list.setAttribute('aria-label',originalLabel);items.forEach(item=>{item.hidden=false;for(const property of ['left','top','display'])item.style.removeProperty(property)})};
const draw=()=>{
pending=false;if(!list.isConnected)return;const width=Math.floor(list.clientWidth);if(width===lastWidth)return;lastWidth=width;reset();if(width<180){list.tabIndex=0;return}
list.style.visibility='hidden';
try{
list.classList.add('is-measuring');const height=180;
const attempt=(scale,count)=>{list.style.setProperty('--cloud-scale',String(scale));items.forEach((item,index)=>{item.hidden=index>=count;item.style.display=index>=count?'none':''});const boxes=items.slice(0,count).map(item=>{const box=item.getBoundingClientRect();return {width:Math.ceil(box.width),height:Math.ceil(box.height)}});const positions=pack(boxes,width,height,seed);if(!positions)return false;
list.classList.remove('is-measuring');list.classList.add('is-packed');list.style.height=height+'px';list.setAttribute('aria-label','Recurring title terms: '+count+' of '+items.length+' selected terms displayed; sizes reflect paper-title frequency');positions.forEach((box,index)=>{items[index].style.left=box.x.toFixed(2)+'px';items[index].style.top=box.y.toFixed(2)+'px'});return true};
for(const scale of [1,.88,.76,.64])if(attempt(scale,items.length))return;
for(const count of [24,20,16,12,8,1])if(count<items.length&&attempt(.76,count))return;
reset();list.tabIndex=0;
}catch{reset();list.tabIndex=0}finally{list.style.removeProperty('visibility')}
};
const schedule=()=>{if(!pending){pending=true;requestAnimationFrame(draw)}};
redraws.set(list,()=>{lastWidth=-1;schedule()});
if(typeof ResizeObserver!=='undefined'){const observer=new ResizeObserver(()=>{if(!list.isConnected){observer.disconnect();return}if(Math.floor(list.clientWidth)!==lastWidth)schedule()});observer.observe(list)}else window.addEventListener('resize',schedule);
schedule();
}
