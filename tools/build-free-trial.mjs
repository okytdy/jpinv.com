import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const load=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const ja=load('content/free-trial/ja.json'),english=load('content/free-trial/en.json');
const fields={ホーム:['見出し','導入','主ボタン','AIリンク','AI注記'],開示翻訳:['見出し','導入','条件','進め方','主ボタン','AIリンク','AI説明'],問い合わせ:['選択項目','案内']};
for(const copy of [ja,english.copy])for(const [section,keys] of Object.entries(fields))for(const key of keys)if(typeof copy?.[section]?.[key]!=='string'||!copy[section][key].trim())throw Error(`Missing copy: ${section}.${key}`);
const hash=s=>createHash('sha256').update(s).digest('hex');
if(english.sourceSha256!==hash(JSON.stringify(ja)))throw Error('Review English against the current Japanese source before building.');
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const markers=(name,content)=>`<!-- jii-${name}:start -->\n${content}\n<!-- jii-${name}:end -->`;
function insert(html,name,content,before){
 const expression=new RegExp(`<!-- jii-${name}:start -->[\\s\\S]*?<!-- jii-${name}:end -->`);
 const block=markers(name,content);
 if(expression.test(html))return html.replace(expression,()=>block);
 const at=html.search(before);if(at<0)throw Error('Missing insertion point: '+name);
 return html.slice(0,at)+block+'\n'+html.slice(at);
}
function asset(html,name,tag){
 const escaped=name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 const expression=new RegExp(`\\s*<${tag}\\b[^>]*(?:href|src)=["']/assets/${escaped}\\?v=[^"']+["'][^>]*>${tag==='script'?'\\s*</script>':''}\\s*`,'g');
 html=html.replace(expression,'\n');
 const version=hash(fs.readFileSync(path.join(root,'assets',name))).slice(0,12);
 const element=tag==='link'?`<link rel="stylesheet" href="/assets/${name}?v=${version}">`:`<script defer src="/assets/${name}?v=${version}"></script>`;
 return html.replace('</head>',element+'\n</head>');
}
for(const locale of ['ja','en']){
 const copy=locale==='ja'?ja:english.copy,home=copy['ホーム'],service=copy['開示翻訳'];
 const directory=locale==='ja'?'':'en/';
 const route=locale==='ja'?'/サービス/開示翻訳/':'/en/services/disclosure-translation/';
 const contact=locale==='ja'?'/お問い合わせ/':'/en/contact/';
 const tool=place=>'https://tools.jpinv.com/ir-english-check/?source=website-'+locale+'-'+place;
 const h=key=>escape(home[key]),s=key=>escape(service[key]);
 const homeBlock=`<section class="jii-trial" id="free-sample" aria-labelledby="free-sample-title"><div class="wrap"><div class="jii-trial-main"><div><h2 class="mincho-lg" id="free-sample-title">${h('見出し')}</h2><p>${h('導入')}</p></div><a class="btn btn-primary jii-trial-cta" href="${encodeURI(route)}#free-trial">${h('主ボタン')}</a></div><div class="jii-trial-ai"><a href="${tool('home')}">${h('AIリンク')}</a><p>${h('AI注記')}</p></div></div></section>`;
 const homePath=path.join(root,directory,'index.html');let homeHtml=fs.readFileSync(homePath,'utf8');
 homeHtml=insert(homeHtml,'free-sample',homeBlock,/<section\b[^>]*class="voices"|<section\b[^>]*class="voices /);
 homeHtml=asset(homeHtml,'free-trial.css','link');fs.writeFileSync(homePath,homeHtml);
 const servicePath=path.join(root,decodeURI(route).slice(1),'index.html');let serviceHtml=fs.readFileSync(servicePath,'utf8');
 const serviceBlock=`<section class="jii-trial jii-trial-detail" id="free-trial" aria-labelledby="free-trial-title"><div class="wrap"><h2 class="mincho-lg" id="free-trial-title">${s('見出し')}</h2><p>${s('導入')}</p><p class="jii-trial-terms">${s('条件')}</p><p>${s('進め方')}</p><a class="btn btn-primary jii-trial-cta" href="${encodeURI(contact)}?inquiry=translation-trial#inquiry-form">${s('主ボタン')}</a><div class="jii-trial-ai"><a href="${tool('service')}">${s('AIリンク')}</a><p>${s('AI説明')}</p></div></div></section>`;
 serviceHtml=insert(serviceHtml,'trial-details',serviceBlock,/<section\b[^>]*id="process"/);
 if(!serviceHtml.includes('href="#free-trial"'))serviceHtml=serviceHtml.replace(/(<nav\b[^>]*class="sd-local"[^>]*>[\s\S]*?)(<\/nav>)/,(_,content,end)=>content+`<a href="#free-trial">${h('見出し')}</a>`+end);
 serviceHtml=asset(serviceHtml,'free-trial.css','link');fs.writeFileSync(servicePath,serviceHtml);
 const contactPath=path.join(root,decodeURI(contact).slice(1),'index.html');let contactHtml=fs.readFileSync(contactPath,'utf8');
 const option=`<option data-inquiry="translation-trial">${escape(copy['問い合わせ']['選択項目'])}</option>`;
 contactHtml=insert(contactHtml,'trial-option',option,/<option>(?:開示翻訳|Disclosure translation)/);
 const note=`<p class="note jii-trial-inquiry-note" id="trial-inquiry-note" hidden aria-live="polite">${escape(copy['問い合わせ']['案内'])}</p>`;
 contactHtml=insert(contactHtml,'trial-note',note,/<div class="field"><label for="inq_msg">/);
 contactHtml=asset(contactHtml,'free-trial.css','link');contactHtml=asset(contactHtml,'free-trial-inquiry.js','script');fs.writeFileSync(contactPath,contactHtml);
}
console.log('Built paired Japanese/English trial sections and inquiry guidance.');
