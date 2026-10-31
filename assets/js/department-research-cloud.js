import {render} from './publication-themes.js';
export function renderResearch(section,collection){
const root=section.closest('#research');if(!root)return;
section.dataset.kuResearchCloud='true';render(section,collection);
if(!section.querySelector('.publication-overview'))return;
if(!document.getElementById('department-research-cloud-styles')){const style=document.createElement('style');style.id='department-research-cloud-styles';style.textContent=`
#research .department-research-split.ku-research-cloud-layout{display:block}
#research .department-research-metrics[data-ku-research-cloud] .publication-overview{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:32px;align-items:start;margin-bottom:20px}
#research .department-research-metrics .publication-overview h3{font:600 16px/1.4 Arial,Helvetica,sans-serif;margin:0 0 20px}
#research .ku-research-cloud-layout>.department-research-copy>p{max-width:75ch}
@media(max-width:760px){#research .department-research-metrics[data-ku-research-cloud] .publication-overview{grid-template-columns:1fr;gap:28px}}
`;document.head.append(style)}
const split=root.querySelector('.department-research-split');if(split)split.classList.add('ku-research-cloud-layout');
root.querySelectorAll(':scope>img.department-photo,:scope>.department-research-image,.department-research-split>.department-research-image').forEach(node=>node.remove());
}
