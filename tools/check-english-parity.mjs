import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {readCheckedTranslation} from './lib/english-parity.mjs';
import {englishArchiveCards} from './lib/english-archive-cards.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const count=(s,p)=>(s.match(p)||[]).length;
const assert=(ok,message)=>{if(!ok)throw Error(message);};
const pages=new Set();
for(const f of fs.readdirSync(path.join(root,'content/english-parity')).filter(f=>f.endsWith('.json'))){
 const r=JSON.parse(read('content/english-parity/'+f));readCheckedTranslation(root,'content/english-parity/'+f,read(r.source));
 const en=read(r.target),ja=read(r.source);
 for(const pattern of [/<section\b/g,/<table\b/g,/<svg\b/g])assert(count(en,pattern)===count(ja,pattern),`${r.target}: sections or figures no longer match Japanese`);
 assert(en.includes(`hreflang="ja" href="https://jpinv.com/${encodeURI(r.source.replace(/index\.html$/,''))}"`),`${r.target}: Japanese language link missing`);
 assert(!/__PARITY_PROTECTED_|JII\s*KEEP/.test(en),`${r.target}: unfinished text`);pages.add(r.target);
}
const jp=read('content/governance/curriculum-ja.md'),english=read('content/governance/curriculum-en.md');
const record=JSON.parse(read('content/governance/curriculum-en.parity.json'));
for(const theme of ['foundations','cg-code','market-restructuring','capital-efficiency','frontier'])pages.add(`en/governance/${theme}/index.html`);
assert(hash(jp)===record.sourceSha256,'Japanese governance source changed; review the English curriculum');
assert(hash(english)===read('content/governance/curriculum-en.md.sha256').trim(),'English governance checksum differs');
const urls=s=>[...s.matchAll(/^\*\*SOURCE URL:\*\*\s+(\S+)/gm)].map(m=>({url:m[1],start:m.index}));
const jpSections=urls(jp),enSections=urls(english);
assert(JSON.stringify(jpSections.map(x=>x.url))===JSON.stringify(enSections.map(x=>x.url)),'Governance articles changed order or were omitted');
for(let i=0;i<jpSections.length;i++){
 const j=jp.slice(jpSections[i].start,jpSections[i+1]?.start),e=english.slice(enSections[i].start,enSections[i+1]?.start);
 const years=new Set(j.match(/\b(?:19|20)\d{2}\b/g)||[]);
 for(const year of years)assert(e.includes(year),`${enSections[i].url}: missing source year ${year}`);
 const percentages=new Set([...j.matchAll(/([\d.]+)\s*[%％]/g)].map(m=>Number(m[1])));
 const englishPercentages=new Set([...e.matchAll(/([\d.]+)\s*%/g)].map(m=>Number(m[1])));
 for(const value of percentages)assert(englishPercentages.has(value),`${enSections[i].url}: missing ${value}% from Japanese`);
 const rel=new URL(enSections[i].url).pathname.replace(/^\//,'');pages.add('en/'+rel+'index.html');
}
assert(count(english,/```mermaid/g)===count(jp,/```mermaid/g),'Governance diagrams omitted');
for(const f of fs.readdirSync(path.join(root,'content/compounders/parity'))){
 const r=JSON.parse(read('content/compounders/parity/'+f)),source=read(r.source),target=read(r.target);
 assert(hash(source)===r.sourceSha256,`${r.key}: Japanese profile source changed`);
 for(const pattern of [/<section\b/g,/<table\b/g,/<svg\b/g,/data-compounder-chart\b/g])assert(count(source,pattern)===count(target,pattern),`${r.key}: source sections, tables or figures omitted`);
 for(const t of r.translations)assert(source.slice(t.start,t.end)===t.ja&&t.en&&!/JII\s*KEEP|\d+ TOKEN/.test(t.en),`${r.key}: translation boundary or unfinished text`);
 pages.add('en/compounders/'+r.key+'/index.html');
}
const data=JSON.parse(read('content/compounders/profile-data.json')),metadata=JSON.parse(read('content/compounders/metadata-parity.json'));
assert(hash(JSON.stringify(metadata.translations.map(({key,ja})=>({key,ja}))))===metadata.sourceSha256,'Metadata Japanese source checksum differs');
for(const t of metadata.translations){const[kind,key,field]=t.key.split('.'),value=data[kind][key][field];assert(value.ja===t.ja&&value.en===t.en,`${t.key}: English metadata needs review`);}
const archive=read('en/compounders/archive/index.html');
for(const[ticker,card]of englishArchiveCards(root,data))assert(archive.includes(card.trim()),`${ticker}: English archive card is stale`);
const policy=JSON.parse(read('content/english-parity-policy.json'));
const founder=read('en/founder-message/index.html').match(/<article class="ci-longform[^>]*>([\s\S]*?)<\/article>/)[1].replaceAll('\r\n','\n');
assert(hash(founder)===policy.founderMessageSha256,'The intentionally distinct English Founder’s message changed');
for(const file of pages){
 const html=read(file);assert(/<html lang="en"/.test(html),`${file}: wrong language`);
 assert(count(html,/<h1\b/g)===1,`${file}: needs one main heading`);
 const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert(new Set(ids).size===ids.length,`${file}: duplicate element IDs`);
 const route='/'+file.replace(/index\.html$/,'');assert(html.includes(`rel="canonical" href="https://jpinv.com${route}"`),`${file}: incorrect canonical URL`);
 for(const m of html.matchAll(/\bhref="([^"\s]+)"/g)){
  const href=m[1];if(!href.startsWith('#'))continue;
  assert(ids.includes(decodeURIComponent(href.slice(1))),`${file}: missing anchor ${href}`);
 }
 assert(!/fthe company|JII\s*KEEP|\d+ TOKEN/.test(html),`${file}: translation artifact remains`);
}
assert(read('sitemap.xml').includes('<loc>https://jpinv.com/en/services/express-translation/</loc>'),'Express page missing from search sitemap');
console.log(`English parity: PASS (${pages.size} rebuilt pages, 35 source-bound archive cards, 38 bilingual metadata records, preserved Founder’s message).`);
