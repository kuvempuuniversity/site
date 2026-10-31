export function pack(boxes,width,height,seed=1){
if(!boxes.length)return [];
const placed=[];let state=seed>>>0;const random=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296};
const valid=box=>box.x>=4&&box.y>=4&&box.x+box.width<=width-4&&box.y+box.height<=height-4&&!placed.some(p=>box.x<p.x+p.width+5&&box.x+box.width+5>p.x&&box.y<p.y+p.height+5&&box.y+box.height+5>p.y);
for(let index=0;index<boxes.length;index++){
const size=boxes[index];if(!(size.width>0&&size.height>0))return null;
let chosen=null;
if(index===0){const box={...size,x:(width-size.width)/2,y:(height-size.height)/2};if(valid(box))chosen=box}
else{const phase=random()*Math.PI*2;for(let step=1;step<=1800;step++){const radius=.72*Math.sqrt(step/1800),angle=phase+step*2.399963229728653;const box={...size,x:width/2+Math.cos(angle)*radius*width-size.width/2,y:height/2+Math.sin(angle)*radius*height-size.height/2};if(valid(box)){chosen=box;break}}}
if(!chosen)return null;placed.push(chosen);
}
return placed;
}
export async function arrange(list){
if(list.dataset.kuSpatialCloud)return;list.dataset.kuSpatialCloud='true';
const css=document.querySelector('link[data-ku-publication-themes]');
if(css&&!css.sheet){const loaded=await new Promise(resolve=>{const timer=setTimeout(()=>resolve(false),10000);const finish=ok=>{clearTimeout(timer);resolve(ok)};css.addEventListener('load',()=>finish(true),{once:true});css.addEventListener('error',()=>finish(false),{once:true})});if(!loaded)return}
if(document.fonts)await document.fonts.ready;
const items=Array.from(list.children);let seed=2166136261;for(const item of items)for(const character of item.firstElementChild.textContent)seed=Math.imul(seed^character.codePointAt(0),16777619)>>>0;
let lastWidth=-1,pending=false;
const reset=()=>{list.classList.remove('is-packed','is-measuring');list.style.removeProperty('height');list.style.removeProperty('--cloud-scale');items.forEach(item=>{item.style.removeProperty('left');item.style.removeProperty('top')})};
const draw=()=>{
pending=false;if(!list.isConnected)return;const width=Math.floor(list.clientWidth);if(width===lastWidth)return;lastWidth=width;reset();if(width<180)return;
list.style.visibility='hidden';
try{
list.classList.add('is-measuring');const baseHeight=Math.max(300,Math.min(420,width*.82));
for(const scale of [1,.9,.8]){list.style.setProperty('--cloud-scale',String(scale));const boxes=items.map(item=>{const box=item.getBoundingClientRect();return {width:Math.ceil(box.width),height:Math.ceil(box.height)}});
for(const extra of [0,100,200]){const height=Math.ceil(baseHeight+extra),positions=pack(boxes,width,height,seed);if(!positions)continue;
list.classList.remove('is-measuring');list.classList.add('is-packed');list.style.height=height+'px';positions.forEach((box,index)=>{items[index].style.left=box.x.toFixed(2)+'px';items[index].style.top=box.y.toFixed(2)+'px'});return;
}}
reset();
}catch{reset()}finally{list.style.removeProperty('visibility')}
};
const schedule=()=>{if(!pending){pending=true;requestAnimationFrame(draw)}};
if(typeof ResizeObserver!=='undefined'){const observer=new ResizeObserver(()=>{if(!list.isConnected){observer.disconnect();return}if(Math.floor(list.clientWidth)!==lastWidth)schedule()});observer.observe(list)}else window.addEventListener('resize',schedule);
schedule();
}
