"use strict";
(()=>{
if(window.KUDepartmentProfileLoader)return;
window.KUDepartmentProfileLoader=true;
const base=document.body.dataset.base||'../';
const match=location.pathname.match(/\/(faculty|students)\/profile\.html$/);
if(match){
const id=new URLSearchParams(location.search).get('id');
fetch(base+'data/profile-redirects.json').then(r=>{if(!r.ok)throw Error('Profile redirects unavailable');return r.json()}).then(data=>{const entry=data[match[1]+':'+id];if(entry&&['faculty','students'].includes(entry.role)&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(entry.id))location.replace(base+entry.role+'/profile.html?id='+encodeURIComponent(entry.id))}).catch(error=>console.warn(error));
return;
}
if(!/\/departments\/[^/]+\.html$/.test(location.pathname))return;
const style=document.createElement('style');style.id='department-profile-directory-styles';style.textContent=`
#people>.event-grid,#students>.event-grid{display:grid!important;grid-template-columns:repeat(auto-fill,min(100%,302px))!important;gap:24px!important;justify-content:start}
#people>.event-grid>.panel,#students>.event-grid>.panel{box-sizing:border-box;width:100%;min-width:0;height:620px;padding:30px;display:flex;flex-direction:column;overflow-wrap:anywhere}
#people>.event-grid>.panel>h3,#students>.event-grid>.panel>h3{min-height:0!important;margin-bottom:4px!important}
#people>.event-grid>.panel>h3+p,#students>.event-grid>.panel>h3+p{margin-top:0!important}
#people>.event-grid>.panel>p:last-child,#students>.event-grid>.panel>p:last-child{margin-top:auto;margin-bottom:0}
#study>.event-grid{padding-top:1.5em;padding-top:1lh}
`;document.head.append(style);
const load=name=>{if(Array.from(document.scripts).some(s=>{try{return new URL(s.src,location.href).pathname.endsWith('/assets/js/'+name)}catch{return false}}))return;const script=document.createElement('script');script.src=base+'assets/js/'+name;document.head.append(script)};
let observer;
const ready=()=>{const faculty=document.getElementById('people'),students=document.getElementById('students');if(faculty)load('faculty.js');if(students)load('research-students.js');if(faculty&&students&&observer)observer.disconnect()};
observer=new MutationObserver(ready);observer.observe(document.body,{childList:true,subtree:true});ready();
window.addEventListener('load',()=>observer.disconnect(),{once:true});
})();
