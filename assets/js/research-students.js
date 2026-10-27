"use strict";
(()=>{
const profile=document.getElementById('research-student-profile');
const directory=location.pathname.endsWith('/departments/environmental-science.html')?document.getElementById('students'):null;
if(!profile&&!directory)return;
const base=document.body.dataset.base||'../';
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n};
const text=value=>typeof value==='string'?value.trim():'';
const suppliedLastNames={'rakshit-g-hosamani':'Hosamani','shiva-naik-h':'Naik','sujeetkumar-m-dongre':'Dongre','mahesh-k-patil':'Patil'};
const lastName=s=>text(s.last_name)||suppliedLastNames[s.id]||text(s.name).split(/\s+/).pop();
const compareStudents=(a,b)=>lastName(a).localeCompare(lastName(b),'en',{sensitivity:'base'})||a.name.localeCompare(b.name,'en',{sensitivity:'base'});
const url=value=>{if(!text(value))return null;try{const u=new URL(value,location.href);return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password?u:null}catch{return null}};
const link=(label,value)=>{const u=url(value);if(!u)return null;const a=el('a',label);a.href=u.href;if(u.origin!==location.origin){a.target='_blank';a.rel='noopener noreferrer';a.setAttribute('aria-label',label+' — opens in a new tab')}return a};
const departments={'environmental-science':'Environmental Science','applied-botany':'Applied Botany'};
const portrait=(s,directoryPhoto=false)=>{
const fallback=new URL(base+'assets/img/students/photo-placeholder.svg',location.href).href;
const u=url(s.photo_url);const img=el('img');let usingPlaceholder=!u||u.href===fallback;
img.alt=usingPlaceholder?'Photograph to be added for '+s.name:'Portrait of '+s.name;
img.width=directoryPhoto?240:408;img.height=directoryPhoto?320:544;img.loading=directoryPhoto?'lazy':'eager';img.style.cssText='display:block;width:100%;'+(directoryPhoto?'max-width:240px;':'')+'height:auto;aspect-ratio:3/4;object-fit:cover;object-position:center top;border-radius:8px';
img.addEventListener('error',()=>{if(!usingPlaceholder){usingPlaceholder=true;img.alt='Photograph to be added for '+s.name;img.src=fallback}else img.replaceWith(el('p','Photograph to be added.','hint'))});
img.src=u?u.href:fallback;return img;
};
const label=(parent,title,value)=>{if(!text(value))return;const p=el('p');p.append(el('strong',title+': '),document.createTextNode(value.trim()));parent.append(p)};
const profileLinks=s=>{
const actions=el('div',undefined,'actions faculty-profile-links');actions.setAttribute('role','group');actions.setAttribute('aria-label','Academic and professional profiles');
const add=(name,value,hosts)=>{const u=url(value);if(!u||hosts&&!hosts.includes(u.hostname))return;const a=link(name,u.href);a.classList.add('scholarly-button');a.title=name;a.setAttribute('aria-label',name+' — opens in a new tab');
if(name==='LinkedIn'||name==='Personal website'){a.dataset.scholarlyButton='profile';a.replaceChildren();if(name==='LinkedIn'){const icon=el('span','in','faculty-linkedin-icon');icon.setAttribute('aria-hidden','true');a.append(icon)}else{const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('width','24');svg.setAttribute('height','24');svg.setAttribute('aria-hidden','true');const path=document.createElementNS(ns,'path');path.setAttribute('d','M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0M3 12h18M12 3c4 4 4 14 0 18-4-4-4-14 0-18');path.setAttribute('fill','none');path.setAttribute('stroke','currentColor');path.setAttribute('stroke-width','1.5');svg.append(path);a.append(svg)}}actions.append(a)};
add('Google Scholar',s.scholar_url,['scholar.google.com']);if(/^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/.test(text(s.orcid)))add('ORCID','https://orcid.org/'+s.orcid,['orcid.org']);add('Personal website',s.personal_website);add('LinkedIn',s.linkedin_url,['linkedin.com','www.linkedin.com']);return actions;
};
const target=profile||directory;target.setAttribute('aria-busy','true');
fetch(base+'data/research-students.json').then(r=>{if(!r.ok)throw Error('Student data unavailable');return r.json()}).then(data=>{
if(!data||!Array.isArray(data.students))throw Error('Invalid student data');
const students=data.students.filter(s=>s&&s.published===true&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(s.id)&&text(s.name)&&Object.prototype.hasOwnProperty.call(departments,s.department_id));
if(directory){
const heading=el('h2','Research students');const members=students.filter(s=>s.department_id==='environmental-science').sort(compareStudents);
if(!members.length){directory.replaceChildren(heading,el('p','Research student profiles will be added here.'));return}
const grid=el('div',undefined,'event-grid');grid.style.cssText='display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:24px';
members.forEach(s=>{const card=el('article',undefined,'panel');const destination=base+'students/profile.html?id='+encodeURIComponent(s.id);const image=portrait(s,true);if(image){const a=link('View profile of '+s.name,destination);a.style.cssText='display:block;width:100%;max-width:240px;border-radius:8px;margin-bottom:16px';a.replaceChildren(image);card.append(a)}const h=el('h3');const name=link(s.name,destination);name.style.textDecoration='none';h.append(name);card.append(h);if(text(s.programme))card.append(el('p',s.programme));const more=el('p');more.append(link('View profile →',destination));card.append(more);grid.append(card)});directory.replaceChildren(heading,grid);return;
}
const id=new URLSearchParams(location.search).get('id');const s=students.find(student=>student.id===id);
if(!s){document.title='Research student profile not found — Kuvempu University';profile.replaceChildren(el('h1','Research student profile not found'),el('p','This profile is not available.'),link('Return to research students →',base+'departments/environmental-science.html#students'));return}
const department=departments[s.department_id];const departmentUrl=base+'departments/'+s.department_id+'.html#students';
const nav=document.getElementById('student-department-link');if(nav){nav.href=departmentUrl;nav.textContent=department+' research students →'}
document.title=s.name+' — Research student — Kuvempu University';
const breadcrumb=el('p',undefined,'breadcrumb');breadcrumb.append(link('Home',base+'index.html'),document.createTextNode(' / '),link(department,departmentUrl),document.createTextNode(' / '+s.name));
const layout=el('div',undefined,'faculty-profile-layout');const figure=el('figure',undefined,'faculty-profile-portrait');const image=portrait(s);if(image){figure.append(image);layout.append(figure)}else layout.style.gridTemplateColumns='minmax(0,1fr)';
const details=el('div',undefined,'faculty-profile-details');const identity=el('header',undefined,'faculty-profile-identity');identity.append(el('h1',s.name,'faculty-profile-name'),el('p',[text(s.programme),department].filter(Boolean).join(', '),'faculty-profile-affiliation'));
if(text(s.email)&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s.email)){const p=el('p',undefined,'faculty-profile-email');const a=el('a',s.email);a.href='mailto:'+s.email;p.append(a);identity.append(p)}
const actions=profileLinks(s);if(actions.children.length)identity.append(actions);details.append(identity);
if(text(s.biography))details.append(el('p',s.biography,'faculty-biography'));
label(details,'Research interests',s.research_interests);label(details,'Academic journey',s.academic_journey);label(details,'Supervisor',s.supervisor);label(details,'Co-supervisor',s.co_supervisor);label(details,'Registration year',s.registration_year==null?'':String(s.registration_year));
if(text(s.research_summary)){details.append(el('h2','Research overview'),el('p',s.research_summary))}
const publications=Array.isArray(s.publications)?s.publications.filter(p=>p&&text(p.title)):[];details.append(el('h2','Publications'));
if(!publications.length)details.append(el('p','Publication details will be added here.'));
else{const list=el('div');publications.forEach(p=>{const item=el('article',undefined,'notice');const h=el('h3');const a=link(p.title,p.link);h.append(a||document.createTextNode(p.title));item.append(h);const citation=[text(p.authors),text(p.venue),p.year==null?'':String(p.year)].filter(Boolean).join(' · ');if(citation)item.append(el('p',citation,'hint'));list.append(item)});details.append(list)}
layout.append(details);
// Reuse faculty-scoped presentation without invoking the faculty data loader.
const shell=el('div');shell.id='faculty-profile';shell.append(breadcrumb,layout);profile.replaceChildren(shell);
if(!window.KUScholarlyButtons){const script=el('script');script.src=base+'assets/js/scholarly-buttons.js';document.head.append(script)}
}).catch(error=>{target.replaceChildren(el(profile?'h1':'h2',profile?'Research student profile':'Research students'),el('p','Student information could not load. Please try again later.'));console.error(error)}).finally(()=>target.setAttribute('aria-busy','false'));
})();
