import {refresh} from './publication-cloud-layout.js';
export function compact(section,collection){
const layout=section.querySelector('.publication-overview');if(!layout)return;
section.classList.add('ku-compact-strip');
const labels=['PhDs awarded','Research paper count','Citations to these papers'];
const dl=layout.querySelector('.department-research-metric-grid');if(dl)Array.from(dl.children).forEach((row,index)=>{const dt=row.querySelector(':scope>dt');if(dt&&labels[index])dt.textContent=labels[index]});
layout.querySelectorAll('.publication-overview-counts>h3,.publication-overview-themes>h3,figcaption').forEach(node=>node.remove());
const figure=layout.querySelector('figure');if(figure)figure.setAttribute('aria-label','Recurring publication title terms');
section.querySelectorAll(':scope>.hint,:scope>details').forEach(node=>node.remove());
const coverage=document.getElementById('publication-coverage');if(coverage)coverage.remove();
if(!section.querySelector(':scope>[data-ku-metrics-info]')){const link=document.createElement('a');link.dataset.kuMetricsInfo='true';link.textContent='About these figures →';link.href=new URL('../../about-research-metrics.html',import.meta.url).href;section.append(link)}
if(!document.getElementById('compact-research-strip-styles')){const style=document.createElement('style');style.id='compact-research-strip-styles';style.textContent=`
.ku-compact-strip{padding:12px 16px!important;margin:16px 0!important}
.ku-compact-strip .publication-overview{gap:16px!important;align-items:stretch!important;margin-bottom:0!important}
.ku-compact-strip .publication-overview-counts,.ku-compact-strip .publication-overview-themes{height:180px;min-height:0;box-sizing:border-box}
.ku-compact-strip .department-research-metric-grid{height:180px;grid-template-columns:1fr;grid-template-rows:repeat(3,1fr);gap:0;margin:0}
.ku-compact-strip .department-research-metric-grid>div{display:flex;flex-direction:column;align-items:flex-start;justify-content:center;gap:0;padding:4px 0;border-bottom:1px solid var(--line)}
.ku-compact-strip .department-research-metric-grid>div:last-child{border-bottom:0}
.ku-compact-strip .department-research-metric-grid dt{font:400 12px/1.3 Arial,Helvetica,sans-serif}
.ku-compact-strip .department-research-metric-grid dd{order:-1;margin:0 0 3px;font-size:26px;line-height:1.05;font-weight:600}
.ku-compact-strip .publication-overview-themes{padding-left:16px}
.ku-compact-strip .publication-theme-terms{height:180px!important;min-height:0!important;margin:0!important;overflow:auto}
.ku-compact-strip .publication-theme-terms.is-packed{overflow:hidden}
.ku-compact-strip .publication-theme-terms>li{font-size:max(12px,calc(var(--term-size,16px)*.8*var(--cloud-scale,1)));line-height:1.05}
.ku-compact-strip>a{display:inline-block;font:400 11px/1.4 Arial,Helvetica,sans-serif;margin:6px 10px 0 0}
@media(max-width:760px){.ku-compact-strip .publication-overview{gap:12px!important}.ku-compact-strip .publication-overview-themes{padding:0;border:0}.ku-compact-strip .publication-theme-terms>li{font-size:max(12px,calc(var(--term-size,16px)*.7*var(--cloud-scale,1)))}}
@media print{.ku-compact-strip .publication-overview-counts,.ku-compact-strip .publication-overview-themes,.ku-compact-strip .department-research-metric-grid,.ku-compact-strip .publication-theme-terms{height:auto!important;overflow:visible}}
`;document.head.append(style)}
const cloud=layout.querySelector('.publication-theme-terms');if(cloud)refresh(cloud);
}
