import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const checkOnly=process.argv.includes('--check');
const records=JSON.parse(fs.readFileSync(path.join(root,'content/compounders/disclaimer-parity.json'),'utf8')).translations;
const normalize=s=>s.replace(/<[^>]*>/g,'').replace(/\s+/g,' ').trim();
const translations=new Map(records.map(r=>[r.ja,r.en]));
const escape=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const bodyPattern=/<div class="disclaimer-body">([\s\S]*?)<\/div>/g;
function sync(source,target){
 if(!fs.existsSync(target))return;
 const ja=fs.readFileSync(source,'utf8').replaceAll('\r\n','\n'),en=fs.readFileSync(target,'utf8').replaceAll('\r\n','\n');
 const blocks=[...ja.matchAll(bodyPattern)];let i=0;
 const result=en.replace(bodyPattern,()=>{
  const block=blocks[i++];if(!block)throw Error(`Unpaired disclosure: ${target}`);
  const paragraphs=[...block[1].matchAll(/<p\b([^>]*)>([\s\S]*?)<\/p>/g)].filter(m=>!m[1].includes('d-en-note'));
  return '<div class="disclaimer-body">\n'+paragraphs.map(m=>{
   const key=normalize(m[2]);
   // A few Japanese archive pages already contain English disclosure paragraphs.
   const text=translations.get(key)||(!/[\u3041-\u3096\u30a1-\u30fa\u3400-\u9fff]/.test(key)?key.replace(/&quot;/g,'"').replace(/&apos;|&#39;/g,"'").replace(/&amp;/g,'&'):null);
   if(!text)throw Error(`Japanese disclosure changed; review translation: ${source}: ${key}`);
   return `<p>${escape(text)}</p>`;
  }).join('\n')+'\n</div>';
 });
 if(i!==blocks.length)throw Error(`Missing English disclosure: ${target}`);
 if(result!==en){
  if(checkOnly)throw Error(`English disclosures are out of sync: ${path.relative(root,target)}`);
  fs.writeFileSync(target,result);console.log(`Synced ${path.relative(root,target)}`);
 }
}
function walk(folder){return fs.readdirSync(folder,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(folder,e.name)):[path.join(folder,e.name)]);}
for(const source of walk(path.join(root,'compounders')).filter(f=>f.endsWith('index.html'))){
 if(/[/\\](ja|en)[/\\]/.test(path.relative(root,source)))continue;
 sync(source,path.join(root,'en',path.relative(root,source)));
}
for(const source of walk(path.join(root,'content/compounders/articles')).filter(f=>f.endsWith(`${path.sep}ja.html`)))sync(source,source.replace(/ja\.html$/,'en.html'));
