import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readCheckedTranslation, englishRoute } from './lib/english-parity.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const ROUTES={
 '/':'/en/','/すぐわかるJII/':'/en/about-jii/','/特急翻訳/':'/en/services/express-translation/',
 '/沿革/':'/en/history/','/会社概要/':'/en/company/','/代表メッセージ/':'/en/founder-message/',
 '/サービス/':'/en/services/','/サービス/開示翻訳/':'/en/services/disclosure-translation/',
 '/サービス/IR通訳/':'/en/services/ir-interpretation/','/サービス/継続IR支援/':'/en/services/ongoing-ir-support/',
 '/サービス/招集通知・有報・統合報告書翻訳/':'/en/services/annual-agm-translation/',
 '/サービス/AIと機密保持/':'/en/services/ai-confidentiality/',
 '/料金/':'/en/pricing/','/お問い合わせ/':'/en/contact/','/faq/':'/en/faq/','/privacy/':'/en/privacy/','/sitemap/':'/en/sitemap/'
};
const esc=value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const japanese=/[\u3040-\u30ff\u3400-\u9fff]/;
const sourceFolder=path.join(ROOT,'content/english-parity');
let pages=0;
for(const filename of fs.readdirSync(sourceFolder).filter(x=>x.endsWith('.json'))){
 const filenameRelative=`content/english-parity/${filename}`;
 const record=JSON.parse(fs.readFileSync(path.join(sourceFolder,filename),'utf8'));
 const source=fs.readFileSync(path.join(ROOT,record.source),'utf8');
 const translation=readCheckedTranslation(ROOT,filenameRelative,source);
 const dictionary=new Map(translation.translations.map(x=>[x.ja,x.en]));
 for(const [ja,en] of dictionary)if(!en)throw new Error(`${filename}: untranslated ${ja}`);
 const translate=value=>{
   const key=value.trim();
   if(!japanese.test(key))return value;
   const en=dictionary.get(key);
   if(en===undefined)throw new Error(`${filename}: missing translation: ${key}`);
   return value.slice(0,value.indexOf(key))+esc(en)+value.slice(value.indexOf(key)+key.length);
 };
 const placeholders=[];
 let html=source.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>|<!--[\s\S]*?-->/gi,chunk=>{
   if(/^<script type="application\/ld\+json">/.test(chunk)){
     const json=JSON.parse(chunk.replace(/^<script[^>]*>/,'').replace(/<\/script>$/,''));
     const walk=value=>{
       if(typeof value==='string'){
         if(value.startsWith('https://jpinv.com/'))return 'https://jpinv.com'+englishRoute(value.slice('https://jpinv.com'.length),ROUTES);
         return dictionary.get(value)||value;
       }
       if(Array.isArray(value))return value.map(walk);
       if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([key,v])=>[key,key==='inLanguage'?'en':walk(v)]));
       return value;
     };
     chunk='<script type="application/ld+json">'+JSON.stringify(walk(json)).replaceAll('</','<\\/')+'</script>';
   }
   placeholders.push(chunk);return `__PARITY_PROTECTED_${placeholders.length-1}__`;
 });
 html=html.replace(/>([^<]+)</g,(_,text)=>'>'+translate(text)+'<');
 html=html.replace(/((?:content|alt|aria-label|placeholder|data-rfq-message)=")([^"]+)(")/g,(_,a,b,c)=>a+translate(b)+c);
 html=html.replace(/<html lang="ja"/,'<html lang="en"');
 const jpRoute='/' + record.source.replace(/index\.html$/,'');
 const enRoute='/' + record.target.replace(/index\.html$/,'');
 html=html.replace(/<link rel="(?:canonical|alternate)"[^>]*>\s*/g,'');
 html=html.replace('</title>','</title>\n'+[
   `<link rel="canonical" href="https://jpinv.com${encodeURI(enRoute)}">`,
   `<link rel="alternate" hreflang="ja" href="https://jpinv.com${encodeURI(jpRoute)}">`,
   `<link rel="alternate" hreflang="en" href="https://jpinv.com${encodeURI(enRoute)}">`,
   `<link rel="alternate" hreflang="x-default" href="https://jpinv.com${encodeURI(jpRoute)}">`
 ].join('\n'));
 html=html.replace(/(<meta property="og:url" content=")[^"]+("[^>]*>)/,`$1https://jpinv.com${encodeURI(enRoute)}$2`);
 html=html.replace(/(<meta property="og:locale" content=")[^"]+("[^>]*>)/,'$1en_US$2');
 html=html.replace(/href="([^"#]+)"/g,(_,href)=>`href="${englishRoute(href,ROUTES)}"`);
 // Alternates must remain reciprocal rather than being localized as navigation.
 html=html.replace(/(<link rel="alternate" hreflang="(?:ja|x-default)" href=")[^"]+("[^>]*>)/g,`$1https://jpinv.com${encodeURI(jpRoute)}$2`);
 html=html.replace(/__PARITY_PROTECTED_(\d+)__/g,(_,i)=>placeholders[Number(i)]);
 if(filename==='methodology.json'){
   // Japanese phrases fit as unbroken units; their longer English equivalents
   // must wrap naturally on phones.
   html=html.replace('.jp-keep { display: inline-block; white-space: nowrap; }','.jp-keep { display: inline; white-space: normal; }')
     .replace(/([A-Za-z.,])(<span class="jp-keep">)/g,'$1 $2');
 }
 // Keep source form routing while making the English page's source explicit.
 if(filename==='express.json'){
   html=html.replace('【特急翻訳】緊急のお問い合わせ — jpinv.com /特急翻訳/','Express translation inquiry — jpinv.com /en/services/express-translation/')
     .replace('value="特急翻訳 (urgent IR translation)"','value="Express translation"')
     .replace('value="/特急翻訳/"','value="/en/services/express-translation/"')
     .replace('）。</p>',').</p>');
 }
 html=html.replace(/<span class="footer-locale-switcher">[\s\S]*?<\/span>/,`<span class="footer-locale-switcher">Language: <a href="${encodeURI(enRoute)}" class="current" aria-current="page" lang="en">EN</a> · <a href="${encodeURI(jpRoute)}" data-locale-route lang="ja">JP</a></span>`);
 html=html.replace(/<span class="hero-lang">[\s\S]*?<\/span>/,`<span class="hero-lang"><a href="${encodeURI(enRoute)}" class="current" aria-current="page" lang="en">EN</a><a href="${encodeURI(jpRoute)}" data-locale-route lang="ja">JP</a></span>`);
 const destination=path.join(ROOT,record.target);fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,html);
 console.log(`Built ${record.target} from ${record.source}: ${dictionary.size} checked translations`);pages++;
}
console.log(`Built ${pages} English pages from their approved Japanese sources.`);
