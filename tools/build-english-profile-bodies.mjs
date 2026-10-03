import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const folder=path.join(root,'content/compounders/parity');
for(const filename of fs.readdirSync(folder).filter(s=>s.endsWith('.json'))){
 const record=JSON.parse(fs.readFileSync(path.join(folder,filename),'utf8'));
 const source=fs.readFileSync(path.join(root,record.source),'utf8');
 if(hash(source)!==record.sourceSha256)throw Error(`${record.key}: Japanese source changed; review the English translation first.`);
 let at=0,html='';
 for(const t of record.translations){
  if(t.start<at||source.slice(t.start,t.end)!==t.ja)throw Error(`${record.key}: invalid translation boundary`);
  if(!t.en||/JII\s*KEEP|\d+ TOKEN/.test(t.en))throw Error(`${record.key}: incomplete translation`);
  html+=source.slice(at,t.start)+t.en;at=t.end;
 }
 html+=source.slice(at);
 html=html.replace(/href="\/compounders\//g,'href="/en/compounders/');
 html=html.replace(/data-share-url="https:\/\/jpinv.com\/compounders\//g,'data-share-url="https://jpinv.com/en/compounders/').replace(/lang="ja"/g,'lang="en"');
 // Comments retain source annotations; all reader-facing Japanese must be translated.
 const visible=html.replace(/<!--[\s\S]*?-->/g,'');
 if(/[\u3041-\u3096\u30a1-\u30fa\u3400-\u9fff]/.test(visible))throw Error(`${record.key}: untranslated Japanese remains: ${(visible.match(/.{0,35}[\u3041-\u3096\u30a1-\u30fa\u3400-\u9fff].{0,35}/g)||[]).slice(0,5).join(' | ')}`);
 for(const pattern of [/<section\b/g,/<table\b/g,/<svg\b/g,/data-compounder-chart\b/g]){
  if((source.match(pattern)||[]).length!==(html.match(pattern)||[]).length)throw Error(`${record.key}: section, table or figure count changed`);
 }
 fs.writeFileSync(path.join(root,record.target),html);
 console.log(`Built ${record.target}: ${record.translations.length} source-bound translations`);
}
