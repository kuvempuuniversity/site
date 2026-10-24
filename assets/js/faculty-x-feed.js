"use strict";
(()=>{
const profile=document.querySelector('#faculty-profile');
if(!profile||!document.body.classList.contains('faculty-profile-page'))return;
let observer,timer;
const mount=()=>{
const portrait=profile.querySelector('.faculty-profile-portrait');
if(!portrait)return;
if(observer)observer.disconnect();clearTimeout(timer);
const account=profile.querySelector('.faculty-profile-links a[href^="https://x.com/"]');
if(!account)return;
let url;try{url=new URL(account.href)}catch{return}
if(url.hostname!=='x.com'||!/^\/[A-Za-z0-9_]{1,15}\/?$/.test(url.pathname))return;
const username=url.pathname.split('/')[1];
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n};
const style=el('style');style.textContent='.faculty-profile-page .faculty-profile-sidebar{width:100%;max-width:408px;min-width:0}.faculty-profile-page .faculty-x-feed{margin-top:28px;max-width:100%;min-width:0}.faculty-profile-page .faculty-x-feed>summary{cursor:pointer;font-size:16px;font-weight:500;line-height:1.5;padding:0 0 12px}.faculty-profile-page .faculty-x-feed-body{min-width:0;max-width:100%}.faculty-profile-page .faculty-x-feed-body iframe{max-width:100%!important}.faculty-profile-page .faculty-x-feed-note{font-size:12px;line-height:1.5;color:var(--muted);margin:8px 0}.faculty-profile-page .faculty-x-feed-fallback{font-size:14px;margin:12px 0 0}';document.head.append(style);
const sidebar=el('div',undefined,'faculty-profile-sidebar');portrait.replaceWith(sidebar);sidebar.append(portrait);
const feed=el('details',undefined,'faculty-x-feed');const summary=el('summary','Recent posts on X');const body=el('div',undefined,'faculty-x-feed-body');const note=el('p','Up to 4 posts, supplied by X. If unavailable, use the link below.','faculty-x-feed-note');const fallback=el('p',undefined,'faculty-x-feed-fallback');const more=el('a','View posts on X ↗');more.href=account.href;more.target='_blank';more.rel='noopener noreferrer';fallback.append(more);feed.append(summary,body,note,fallback);sidebar.append(feed);
let activated=false;
const activate=()=>{
if(activated)return;activated=true;
const timeline=el('a','Posts from @'+username,'twitter-timeline');timeline.href='https://twitter.com/'+username;timeline.dataset.tweetLimit='4';timeline.dataset.dnt='true';timeline.dataset.chrome='noheader nofooter noborders transparent';timeline.dataset.theme='light';timeline.dataset.ariaPolite='polite';timeline.target='_blank';timeline.rel='noopener noreferrer';body.append(timeline);
const fail=()=>{note.textContent='The X feed could not load. Use the link below to view posts.'};
if(window.twttr&&window.twttr.widgets){window.twttr.widgets.load(body);return}
const script=el('script');script.src='https://platform.twitter.com/widgets.js';script.async=true;script.charset='utf-8';script.addEventListener('load',()=>{if(window.twttr&&window.twttr.widgets)window.twttr.widgets.load(body);else fail()},{once:true});script.addEventListener('error',fail,{once:true});document.head.append(script);
};
const desktop=window.matchMedia('(min-width:901px)');
const updateLabel=()=>{summary.textContent=desktop.matches?'Recent posts on X':feed.open?'Hide recent posts on X':'Show recent posts on X'};
feed.addEventListener('toggle',()=>{updateLabel();if(feed.open)activate()});
const adapt=()=>{feed.open=desktop.matches;updateLabel();if(feed.open)activate()};
desktop.addEventListener('change',adapt);adapt();
};
observer=new MutationObserver(mount);observer.observe(profile,{childList:true,subtree:true});timer=setTimeout(()=>observer.disconnect(),30000);mount();
})();
