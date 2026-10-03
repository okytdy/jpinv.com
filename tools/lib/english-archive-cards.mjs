import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const escape=value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const labels={
 '終値':'Last close','直近終値':'Last close','倍':'x',
 'ネットキャッシュ / 時価総額':'Net cash / MC','純現金 / 時価総額':'Net cash / MC',
 '純現金＋有価証券 / 時価総額':'Net cash + securities / MC',
 'ネット負債 / 時価総額':'Net debt / MC','純有利子負債 / 時価総額':'Net debt / MC','ネットデット / 時価総額':'Net debt / MC',
 'P / B 調整後':'Adjusted P / B','配当利回り':'Dividend yield','営業利益率':'Operating margin'
};
export function englishArchiveCards(root,data){
 const source=fs.readFileSync(path.join(root,'compounders/archive/index.html'),'utf8');
 const reviewed=new Map(JSON.parse(fs.readFileSync(path.join(root,'content/compounders/archive-card-parity.json'),'utf8')).cards.map(c=>[c.ticker,c]));
 const output=new Map();
 for(const m of source.matchAll(/<a\b(?=[^>]*\bclass="[^" ]*card[^" ]*")(?=[^>]*\bdata-ticker="([^" ]+)")[^>]*>[\s\S]*?<\/a>/g)){
  const record=reviewed.get(m[1]);if(!record)throw Error(`Missing reviewed English archive card ${m[1]}`);
  if(crypto.createHash('sha256').update(m[0].replaceAll('\r\n','\n')).digest('hex')!==record.sourceSha256)throw Error(`Japanese archive card ${m[1]} changed; review its translation.`);
  const company=data.companies[m[1]],date=m[0].match(/data-date="([^"]+)"/)[1];
  const formatted=new Date(date+'T00:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
  let card=m[0].replace('href="/compounders/','href="/en/compounders/')
   .replace(/(<h3 class="card-name">)[\s\S]*?(<\/h3>)/,`$1${escape(company.name.en)}$2`)
   .replace(/(<p class="card-jp">)[\s\S]*?(<\/p>)/,`$1${escape(company.name.ja)}$2`)
   .replace(/(<span class="card-sector">)[\s\S]*?(<\/span>)/,`$1${escape(record.sector)}$2`)
   .replace(/(<p class="card-hook">)[\s\S]*?(<\/p>)/,`$1<b>${escape(record.hook)}</b>$2`);
  card=card.replace(/>([^<>]+)</g,(all,text)=>{
   const key=text.trim();let en=labels[key];
   if(/^東証/.test(key))en=key.replace('東証プライム','TSE PRIME').replace('東証スタンダード','TSE STANDARD').replace('東証グロース','TSE GROWTH');
   if(/^\d{4}年\d+月\d+日\s*(?:公開|更新)$/.test(key))en=`${key.includes('更新')?'Updated':'Published'} ${formatted}`;
   if(/^約[\d.,]+$/.test(key))en=key.replace('約','~');
   if(/^[\d,]+円$/.test(key))en='¥'+key.replace('円','');
   return en===undefined?all:'>'+text.replace(key,escape(en))+'<';
  });
  const visible=card.replace(/<p class="card-jp">[\s\S]*?<\/p>/,'');
  if(/[\u3041-\u3096\u30a1-\u30fa\u3400-\u9fff]/.test(visible))throw Error(`Untranslated card label ${m[1]}`);
  output.set(m[1],card);
 }
 return output;
}
