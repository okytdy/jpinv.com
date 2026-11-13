'use strict';

const $ = id => document.getElementById(id);
const yen = (value, decimals = 0) => new Intl.NumberFormat('en-US', {style:'currency',currency:'JPY',minimumFractionDigits:decimals,maximumFractionDigits:decimals}).format(value);
const pct = (value, digits = 2) => `${Number(value).toFixed(digits)}%`;
const signed = (value, digits = 2, suffix = '%') => `${value < 0 ? '−' : value > 0 ? '+' : ''}${Math.abs(value).toFixed(digits)}${suffix}`;
const signedYen = (value, digits = 2) => `${value < 0 ? '−' : value > 0 ? '+' : ''}${yen(Math.abs(value),digits)}`;
const date = (day, year = true, month = 'short') => new Intl.DateTimeFormat('en-GB', {day:'numeric',month,...(year ? {year:'numeric'} : {}),timeZone:'Asia/Tokyo'}).format(new Date(`${day}T12:00:00+09:00`));
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const tabNames = ['portfolio','performance','about'];
let data, chartMode = 'return', activeTab = 'portfolio', chartObserver;
const dialogOrigins = new Map();

function researchArticles(holding){
  if(!holding) return [];
  const articles=Array.isArray(holding.research_articles)&&holding.research_articles.length?holding.research_articles:[{title:holding.research_title||'Substack article',url:holding.research_url,published_date:holding.research_date}];
  return articles.map(article=>({...article,published_date:article.published_date||holding.research_date})).sort((a,b)=>(b.published_date||'').localeCompare(a.published_date||''));
}

function setSigned(element,value,text){element.textContent=text;element.classList.toggle('negative',value<0);element.classList.toggle('positive',value>0);}

function selectTab(name,{focus=false,push=false}={}){
  const aliases={overview:'portfolio',holdings:'portfolio',activity:'portfolio','how-it-works':'about'};
  name=aliases[name]||name;
  if(!tabNames.includes(name)) name='portfolio';
  activeTab=name;
  tabNames.forEach(tab=>{
    const selected=tab===name;
    $(`tab-${tab}`).setAttribute('aria-selected',String(selected));
    $(`tab-${tab}`).tabIndex=selected?0:-1;
    $(`panel-${tab}`).hidden=!selected;
  });
  if(push&&location.hash!==`#${name}`) history.pushState(null,'',`#${name}`);
  if(focus) $(`tab-${name}`).focus();
  if(name==='performance'&&data) requestAnimationFrame(renderChart);
}

function renderHoldings(){
  $('holdings-count').textContent=`(${data.snapshot.holdings.length})`;
  $('holdings-body').innerHTML=data.snapshot.holdings.map(h=>`<tr>
    <td><button type="button" class="company-button" data-holding="${esc(h.ticker)}" aria-haspopup="dialog"><span class="company-name">${esc(h.name)}</span><span class="company-meta">${esc(h.ticker)} · ${h.shares.toLocaleString('en-US')} shares</span></button></td>
    <td class="number" data-label="Weight">${pct(h.weight_pct,2)}</td>
    <td class="number" data-label="Avg. cost">${yen(h.average_cost,2)}</td>
    <td class="number" data-label="Close">${yen(h.mark,2)}</td>
    <td class="number ${h.return_pct<0?'negative':'positive'}" data-label="Return">${signed(h.return_pct,2)}<span class="return-amount">${signedYen(h.unrealized)}</span></td>
  </tr>`).join('');
}

function renderAllocation(){
  const colors=['#536747','#8b7957','#607b82','#916c74','#716a85','#7b8756'];
  const parts=data.snapshot.holdings.map((h,i)=>({label:h.name,weight:h.weight_pct,color:colors[i%colors.length]}));
  parts.push({label:'Cash',weight:data.snapshot.cash_weight_pct,color:'#d6dccf'});
  $('allocation-bar').innerHTML=parts.map(p=>`<span title="${esc(p.label)} ${pct(p.weight,2)}" style="width:${p.weight}%;background:${p.color}"></span>`).join('');
  $('allocation-bar').setAttribute('aria-label',parts.map(p=>`${p.label} ${pct(p.weight,2)}`).join(', '));
  $('allocation-legend').innerHTML=parts.map(p=>`<span><i style="background:${p.color}"></i>${esc(p.label)} <strong>${pct(p.weight,2)}</strong></span>`).join('');
}

function renderActivity(){
  const actions=[...data.snapshot.activity].reverse();
  const seenBuys=new Set();
  const priorBuys=new Set();
  data.snapshot.activity.forEach(a=>{if(a.type==='buy'){if(seenBuys.has(a.ticker)) priorBuys.add(a.id);seenBuys.add(a.ticker);}});
  $('activity-list').innerHTML=actions.map(a=>{
    const meta=`<div class="feed-meta"><time datetime="${a.date}">${date(a.date)}</time><span class="action-label ${a.type==='sell'?'sell':''}">${a.type==='opening_cash'?'Start':a.type==='buy'?'Buy':a.type==='sell'?'Sell':esc(a.type)}</span></div>`;
    if(a.type==='opening_cash') return `<article class="feed-item">${meta}<h3>The portfolio begins</h3><p>${yen(Number(a.amount))} in hypothetical cash.</p></article>`;
    const holding=data.snapshot.holdings.find(h=>h.ticker===a.ticker);
    const company=holding?.name||a.ticker;
    if(a.type==='buy'||a.type==='sell'){
      const verb=a.type==='sell'?'Trimmed':priorBuys.has(a.id)?'Added':'Opened';
      const allocation=a.target_allocation_pct?` ${Number(a.target_allocation_pct)}% ${verb==='Opened'?'in':'to'}`:a.type==='sell'?'':' a position in';
      const heading=a.type==='sell'?`Trimmed ${esc(company)}`:`${verb}${allocation} ${esc(company)}`;
      return `<article class="feed-item">${meta}<h3>${heading} <span class="feed-ticker">${esc(a.ticker)}</span></h3><p>${a.shares.toLocaleString('en-US')} shares at ${yen(a.effective_price,2)} each.</p><div class="feed-links">${holding?`<button type="button" data-holding="${esc(a.ticker)}" aria-haspopup="dialog">Position &amp; research →</button>`:'<span></span>'}<button type="button" data-entry="${esc(a.id)}" aria-haspopup="dialog">Entry details</button></div></article>`;
    }
    if(a.type==='dividend') return `<article class="feed-item">${meta}<h3>Dividend from ${esc(company)} <span class="feed-ticker">${esc(a.ticker)}</span></h3><p>${yen(Number(a.amount),2)} received.</p></article>`;
    return `<article class="feed-item">${meta}<h3>${esc(company)} <span class="feed-ticker">${esc(a.ticker||'')}</span></h3><p>${a.type==='split'?'Share split recorded.':'Portfolio record updated.'}</p></article>`;
  }).join('');
  const more=$('activity-more');
  more.hidden=actions.length<=3;
  more.textContent=`View all ${actions.length} actions`;
}

function showDialog(id,origin){
  const dialog=$(id);
  dialogOrigins.set(dialog,origin);
  dialog.showModal();
  dialog.querySelector('h2').focus({preventScroll:true});
}

function openHolding(ticker,origin){
  const h=data.snapshot.holdings.find(row=>row.ticker===ticker);
  if(!h) return;
  const buys=data.snapshot.activity.filter(a=>a.type==='buy'&&a.ticker===ticker);
  const fields=[['Shares',h.shares.toLocaleString('en-US')],['Current weight',pct(h.weight_pct,3)],['Average cost',yen(h.average_cost,4)],['Latest close',yen(h.mark,2)],['Unrealized P&L',signedYen(h.unrealized)],['Return',signed(h.return_pct,2)],['First allocated',date(h.first_date)],['Latest allocation',date(h.last_date)],['Initial target',pct(h.initial_target_pct)],['Price date',date(h.mark_date)]];
  const articles=researchArticles(h);
  const links=`<section class="holding-research" aria-labelledby="holding-research-title"><h3 id="holding-research-title" class="detail-label">Research</h3><p class="resource-kind">Substack writeups</p><ul class="writeup-list">${articles.map(article=>`<li><a href="${esc(article.url)}">${esc(article.title)}&nbsp;↗</a>${article.published_date?`<time datetime="${esc(article.published_date)}">${date(article.published_date)}</time>`:''}</li>`).join('')}</ul>${h.model_url?`<div class="forecast-resource"><a href="${esc(h.model_url)}">Forecast model&nbsp;↗</a><p>Earnings assumptions${h.model_date?` · <time datetime="${esc(h.model_date)}">${date(h.model_date)}</time>`:''}</p></div>`:''}</section>`;
  $('position-content').innerHTML=`<div class="dialog-heading"><div><p>${esc(h.ticker)} · ${esc(h.japanese_name)} · ${esc(h.exchange)}</p><h2 id="position-title" tabindex="-1">${esc(h.name)}</h2></div><button type="button" class="dialog-close" data-close="position-dialog" aria-label="Close holding details">×</button></div>${links}<h3 class="detail-label">Position</h3><dl class="detail-grid">${fields.map(([label,value])=>`<div><dt>${label}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl><h3 class="detail-label">Allocations</h3><ul class="purchase-list">${buys.map(a=>`<li><div><time datetime="${a.date}">${date(a.date)}</time><span>${a.shares} shares · ${yen(a.effective_price,2)} each</span></div><button type="button" class="inline-button" data-entry="${esc(a.id)}" aria-haspopup="dialog">Entry details</button></li>`).join('')}</ul>`;
  showDialog('position-dialog',origin);
}

function openEntry(id,origin){
  const a=data.snapshot.activity.find(entry=>entry.id===id);
  if(!a) return;
  const h=data.snapshot.holdings.find(holding=>holding.ticker===a.ticker);
  const budget=Number(a.allocation_base)*Number(a.target_allocation_pct)/100;
  const spent=Math.abs(a.cash_change);
  const feePerShare=a.reference_price*Number(a.transaction_cost_rate);
  const rows=[['Session VWAP',yen(a.reference_price,10)],['Modeled cost / share',yen(feePerShare,10)],['Cost-inclusive price',yen(a.effective_price,10)],['Shares',a.shares.toLocaleString('en-US')],['Transaction cost',yen(a.transaction_cost,4)],['Cash '+(a.type==='sell'?'received':'used'),yen(spent,4)]];
  if(a.type==='buy'&&Number.isFinite(budget)) rows.push(['Allocation budget',yen(budget,4)],['Left in cash',yen(budget-spent,4)]);
  $('entry-content').innerHTML=`<div class="dialog-heading"><div><p>${esc(a.ticker)} · ${date(a.date)}</p><h2 id="entry-title" tabindex="-1">${esc(h?.name||a.ticker)} entry</h2></div><button type="button" class="dialog-close" data-close="entry-dialog" aria-label="Close entry details">×</button></div><dl class="entry-grid">${rows.map(([label,value])=>`<dt>${label}</dt><dd>${esc(value)}</dd>`).join('')}</dl><details class="disclosure"><summary>Reference data</summary><dl class="entry-grid compact"><dt>Session traded value</dt><dd>${yen(Number(a.reference_price_numerator))}</dd><dt>Session volume</dt><dd>${Number(a.reference_price_denominator).toLocaleString('en-US')} shares</dd><dt>Modeled cost</dt><dd>${pct(Number(a.transaction_cost_rate)*100,1)}</dd></dl><p>VWAP = traded value ÷ volume. Full precision is retained in the downloadable records.</p></details><p class="entry-footnote">Reference-priced paper entry. The market date may precede the recorded decision.</p>`;
  showDialog('entry-dialog',origin);
}

function renderChart(){
  if(!data||activeTab!=='performance'||$('panel-performance').hidden) return;
  const index=chartMode==='index';
  const baseline=index?100:0;
  const points=data.history.map(s=>({date:s.date,value:index?s.index:s.return_pct}));
  const min=Math.min(baseline,...points.map(p=>p.value));
  const max=Math.max(baseline,...points.map(p=>p.value));
  const range=Math.max(max-min,.04),lo=min-range*.4,hi=max+range*.4;
  const width=Math.max(280,$('chart').clientWidth),height=270,left=54,right=width-20,top=32,bottom=208;
  const x=i=>points.length===1?left+(right-left)/2:left+i/(points.length-1)*(right-left);
  const y=value=>top+(hi-value)/(hi-lo)*(bottom-top);
  const format=value=>index?value.toFixed(4):signed(value,4);
  let svg=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="chart-title chart-description"><title id="chart-title">${index?'Portfolio index':'Portfolio return'}</title><desc id="chart-description">${points.length} saved closing observations since ${date(data.inception_date)}. Latest ${format(points.at(-1).value)}. Opening capital equals ${baseline}${index?'':'%'}. No annualized return.</desc>`;
  for(const value of [hi,lo]) svg+=`<line x1="${left}" x2="${right}" y1="${y(value)}" y2="${y(value)}" stroke="#e2e6db"/><text x="0" y="${y(value)+4}">${index?value.toFixed(2):value.toFixed(2)+'%'}</text>`;
  svg+=`<line x1="${left}" x2="${right}" y1="${y(baseline)}" y2="${y(baseline)}" stroke="#a8b19f" stroke-dasharray="4 5"/><text x="${left}" y="${y(baseline)-10}">${baseline}${index?'':'%'}</text>`;
  if(points.length>1) svg+=`<polyline points="${points.map((p,i)=>`${x(i)},${y(p.value)}`).join(' ')}" fill="none" stroke="#536747" stroke-width="2"/>`;
  points.forEach((p,i)=>{svg+=`<circle cx="${x(i)}" cy="${y(p.value)}" r="${i===points.length-1?5:3}" fill="#536747"><title>${date(p.date)}: ${format(p.value)}</title></circle>`;});
  const latest=points.at(-1),last=points.length-1,anchor=points.length===1?'middle':'end';
  svg+=`<text x="${x(last)}" y="${y(latest.value)+26}" text-anchor="${anchor}" class="dot-label">${format(latest.value)}</text><text x="${x(last)}" y="250" text-anchor="${anchor}">${date(latest.date,false)}</text>`;
  if(points.length>1) svg+=`<text x="${x(0)}" y="250">${date(points[0].date,false)}</text>`;
  $('chart').innerHTML=svg+'</svg>';
  $('baseline-label').textContent=`Opening capital = ${index?'100':'0%'}`;
  $('history-note').textContent=`${points.length} saved closing observation${points.length===1?'':'s'} · net of recorded costs · since ${date(data.inception_date)}`;
}

function renderBreakdown(){
  const s=data.snapshot;
  const rows=[['Price movement',s.pnl+s.costs-s.dividends],['Transaction costs',-s.costs],['Dividends',s.dividends],['Portfolio P&L',s.pnl]];
  $('return-breakdown').innerHTML=rows.map(([label,value],i)=>`<dt class="${i===3?'total':''}">${label}</dt><dd class="${i===3?'total ':''}${value<0?'negative':'positive'}">${signedYen(value,4)}</dd>`).join('');
}

document.querySelectorAll('[data-tab]').forEach(button=>{
  button.addEventListener('click',()=>selectTab(button.dataset.tab,{push:true}));
  button.addEventListener('keydown',event=>{
    const index=tabNames.indexOf(button.dataset.tab);
    const keyToIndex={ArrowRight:(index+1)%3,ArrowLeft:(index+2)%3,Home:0,End:2};
    if(event.key in keyToIndex){event.preventDefault();selectTab(tabNames[keyToIndex[event.key]],{focus:true,push:true});}
  });
});
addEventListener('popstate',()=>selectTab(location.hash.slice(1)));
addEventListener('hashchange',()=>selectTab(location.hash.slice(1)));
document.querySelectorAll('[data-chart]').forEach(button=>button.addEventListener('click',()=>{
  chartMode=button.dataset.chart;
  document.querySelectorAll('[data-chart]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
  renderChart();
}));
document.addEventListener('click',event=>{
  const holding=event.target.closest('button[data-holding]');
  const entry=event.target.closest('button[data-entry]');
  const close=event.target.closest('button[data-close]');
  if(holding) openHolding(holding.dataset.holding,holding);
  if(entry) openEntry(entry.dataset.entry,entry);
  if(close) $(close.dataset.close).close();
});
document.querySelectorAll('dialog').forEach(dialog=>{
  dialog.addEventListener('close',()=>{const origin=dialogOrigins.get(dialog);if(origin?.isConnected) origin.focus({preventScroll:true});});
  dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom) dialog.close();}});
});
$('activity-more').addEventListener('click',()=>{
  const expanded=$('activity-more').getAttribute('aria-expanded')!=='true';
  document.querySelector('.action-feed').classList.toggle('is-expanded',expanded);
  $('activity-more').setAttribute('aria-expanded',String(expanded));
  $('activity-more').textContent=expanded?'Show fewer actions':`View all ${data.snapshot.activity.length} actions`;
});
$('retry-load').addEventListener('click',init);

async function init(){
  $('retry-load').disabled=true;
  $('load-error').hidden=true;
  try{
    const response=await fetch('portfolio-data.json',{cache:'no-cache'});
    if(!response.ok) throw new Error('Snapshot unavailable');
    data=await response.json();
    const s=data.snapshot;
    $('asof').textContent=`TSE close · ${date(data.asof)}`;
    const startingCapital=data.initial_capital>=1000000?`¥${new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(data.initial_capital/1000000)} million`:yen(data.initial_capital);
    $('inception').textContent=`Started ${date(data.inception_date,true,'long')} · ${startingCapital} in hypothetical capital`;
    $('nav-value').textContent=yen(s.nav);
    setSigned($('total-return'),s.return_pct,signed(s.return_pct,2));
    $('total-pnl').textContent=signedYen(s.pnl,0);
    $('equity-weight').textContent=pct(100-s.cash_weight_pct,2);
    $('equity-detail').textContent=`${s.holdings.length} holdings`;
    $('cash-value').textContent=yen(s.cash);
    $('cash-detail').textContent=`${pct(s.cash_weight_pct,2)} of portfolio`;
    renderHoldings();renderAllocation();renderActivity();renderBreakdown();
    $('portfolio-content').hidden=false;
    selectTab(location.hash.slice(1));
    if(!chartObserver){chartObserver=new ResizeObserver(()=>{if(activeTab==='performance') renderChart();});chartObserver.observe($('chart'));}
  }catch(error){$('load-error').hidden=false;$('asof').textContent='Snapshot unavailable';console.error('Portfolio snapshot could not load:',error.message);}
  finally{$('retry-load').disabled=false;}
}
init();
