(()=>{
 'use strict';
 const topic=document.getElementById('inq_type');
 const note=document.getElementById('trial-inquiry-note');
 const message=document.getElementById('inq_msg');
 const trial=topic?.querySelector('option[data-inquiry="translation-trial"]');
 if(!topic||!note||!message||!trial)return;
 const previousDescription=message.getAttribute('aria-describedby');
 if(!topic.value&&new URLSearchParams(window.location.search).get('inquiry')==='translation-trial')topic.value=trial.value;
 function update(){
  const selected=topic.selectedOptions[0]===trial;note.hidden=!selected;
  const description=[previousDescription,selected?note.id:null].filter(Boolean).join(' ');
  if(description)message.setAttribute('aria-describedby',description);else message.removeAttribute('aria-describedby');
 }
 topic.addEventListener('change',update);update();
})();
