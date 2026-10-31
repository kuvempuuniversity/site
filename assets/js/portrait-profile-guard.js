"use strict";
(()=>{
const root=document.getElementById('portrait-profile');
if(!root)return;
const shell=root.querySelector(':scope>#faculty-profile');
if(!shell)return;
shell.id='portrait-profile-content';
const restore=()=>{shell.id='faculty-profile'};
if(document.readyState==='complete')restore();else window.addEventListener('load',restore,{once:true});
})();
