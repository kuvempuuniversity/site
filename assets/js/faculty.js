"use strict";
(()=>{
const base=document.body.dataset.base||'./';
const directory=document.querySelector('#people');
const profile=document.querySelector('#faculty-profile');
if(!directory&&!profile)return;
const el=(tag,text,cls)=>{const node=document.createElement(tag);if(text)node.textContent=text;if(cls)node.className=cls;return node};
const link=(text,url,external=false)=>{const a=el('a',text);a.href=url;if(external){a.target='_blank';a.rel='noopener noreferrer'}return a};
const photo=(f,directoryPhoto=false)=>{const img=el('img');img.src=base+'assets/img/faculty/'+f.photo;img.alt='Portrait of '+f.name;img.width=directoryPhoto?240:160;img.height=directoryPhoto?320:160;img.loading='lazy';img.style.cssText=directoryPhoto?'width:100%;max-width:240px;height:auto;aspect-ratio:3/4;object-fit:cover;object-position:center top;border-radius:8px':'width:160px;height:160px;object-fit:cover;border-radius:8px;max-width:100%';img.addEventListener('error',()=>{img.replaceWith(el('p','Photograph unavailable.','hint'))},{once:true});return img};
const suppliedLastNames={'yogendra-kambalagere':'Kambalagere','madhusudhana-n':'N','krishnamurthy-sv':'Krishnamurthy','rakesh-tiwari':'Tiwari','nanda-appaji':'Appaji'};
const lastName=f=>f.last_name||suppliedLastNames[f.id]||f.name.trim().split(/\s+/).pop();
const scholarly=f=>{const links=el('div',undefined,'actions');links.append(link('Google Scholar ↗',f.scholar_url,true),link('ORCID ↗','https://orcid.org/'+f.orcid,true));if(f.personal_website){try{const u=new URL(f.personal_website);if(['https:','http:'].includes(u.protocol)&&!u.username&&!u.password)links.append(link('Personal website ↗',u.href,true))}catch{}}return links};
const target=profile||directory;target.setAttribute('aria-busy','true');
fetch(base+'data/faculty.json').then(r=>{if(!r.ok)throw Error('Faculty HTTP '+r.status);return r.json()}).then(data=>{
if(!Array.isArray(data.faculty))throw Error('Invalid faculty dataset');
if(directory&&!profile){
const heading=el('h2','Faculty & research interests');const intro=el('p','Meet the faculty listed in the department information supplied for this prototype.');const grid=el('div',undefined,'event-grid');grid.style.cssText='display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:24px';
data.faculty.filter(f=>f.department_id==='environmental-science').sort((a,b)=>lastName(a).localeCompare(lastName(b),'en',{sensitivity:'base'})||a.name.localeCompare(b.name,'en',{sensitivity:'base'})).forEach(f=>{const card=el('article',undefined,'panel');const profileUrl=base+'faculty/profile.html?id='+encodeURIComponent(f.id);const portraitLink=link('',profileUrl);portraitLink.setAttribute('aria-label','View profile of '+f.name);portraitLink.style.cssText='display:block;width:100%;max-width:240px;border-radius:8px';const portrait=photo(f,true);portrait.style.display='block';portraitLink.append(portrait);const h=el('h3');const nameLink=link(f.name,profileUrl);nameLink.style.textDecoration='none';h.append(nameLink);card.append(portraitLink,h,el('p',f.designation));if(f.research_interests)card.append(el('p',f.research_interests));card.append(scholarly(f));const more=el('p');more.append(link('View profile →',base+'faculty/profile.html?id='+encodeURIComponent(f.id)));card.append(more);grid.append(card)});directory.replaceChildren(heading,intro,grid);
}else if(profile){
const id=new URLSearchParams(location.search).get('id');const f=data.faculty.find(item=>item.id===id);if(!f){document.title='Faculty profile not found — Kuvempu University';profile.replaceChildren(el('h1','Faculty profile not found'),link('Return to Environmental Science faculty →',base+'departments/environmental-science.html#people'));return}
document.title=f.name+' — Kuvempu University';const back=el('p',undefined,'breadcrumb');back.append(link('Home',base+'index.html'),document.createTextNode(' / '),link(f.department,base+'departments/'+f.department_id+'.html#people'));
const layout=el('div',undefined,'faculty-profile-layout');layout.style.cssText='display:flex;flex-wrap:wrap;align-items:flex-start;gap:32px;margin-top:24px';
const identity=el('div',undefined,'panel faculty-profile-identity');identity.style.cssText='flex:0 1 260px;min-width:0;max-width:100%;box-sizing:border-box;overflow-wrap:anywhere';const name=el('h1',f.name);name.style.cssText='font-size:clamp(1.5rem,3vw,2rem);line-height:1.2';identity.append(photo(f,true),name,el('p',f.designation),el('p',f.department));if(f.email){const contact=el('p');contact.append(link(f.email,'mailto:'+f.email));identity.append(contact)}identity.append(scholarly(f));
const details=el('div',undefined,'faculty-profile-details');details.style.cssText='flex:1 1 480px;min-width:0;max-width:100%;overflow-wrap:anywhere';layout.append(identity,details);profile.replaceChildren(back,layout);
const sectionHeading=text=>{const h=el('h2',text);h.style.cssText='font-size:1.15rem;font-weight:500;line-height:1.4;margin:1.5rem 0 .65rem';return h};
if(typeof f.biography==='string'&&f.biography.trim())details.append(el('p',f.biography,'faculty-biography'));
if(f.research_interests)details.append(sectionHeading('Research interests'),el('p',f.research_interests));
const modules=el('ul');const taught=Array.isArray(f.modules_taught)&&f.modules_taught.length?f.modules_taught:['Topic 1','Topic 2','Topic 3'];taught.forEach(topic=>modules.append(el('li',topic)));details.append(sectionHeading('Modules taught'),modules);
details.append(sectionHeading('Select Publication'));const works=el('div');works.append(el('p','Loading publications…'));details.append(works);
const renderWorks=()=>window.KUPublications.render(works,{facultyId:f.id});
if(window.KUPublications){renderWorks()}else{const script=document.createElement('script');script.src=base+'assets/js/publications.js';script.onload=renderWorks;script.onerror=()=>works.replaceChildren(el('p','Publication display could not load. Use the ORCID or Google Scholar links in this profile.'));document.head.append(script)}
}
}).catch(error=>{target.replaceChildren(el('h2','Faculty information'),el('p','Faculty information could not load. Please try again later.'));console.error(error)}).finally(()=>target.setAttribute('aria-busy','false'));
})();
