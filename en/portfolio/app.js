'use strict';
const $ = id => document.getElementById(id);
const yen = (v, decimals = 0) => new Intl.NumberFormat('en-US', {style:'currency', currency:'JPY', minimumFractionDigits:decimals, maximumFractionDigits:decimals}).format(v);
const pct = (v, digits = 2) => `${v.toFixed(digits)}%`;
const signed = (v, digits = 2, suffix = '%') => `${v < 0 ? '−' : v > 0 ? '+' : ''}${Math.abs(v).toFixed(digits)}${suffix}`;
const date = d => new Intl.DateTimeFormat('en-GB', {day:'numeric',month:'short',year:'numeric',timeZone:'Asia/Tokyo'}).format(new Date(`${d}T12:00:00+09:00`));
const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let data;
let chartMode = 'return';
let selectedHolding = null;
let detailOrigin = null;

function setSigned(el, v, text) {
  el.textContent = text;
  el.classList.toggle('negative', v < 0);
  el.classList.toggle('positive', v > 0);
}

function renderChart() {
  const history = data.history;
  const index = chartMode === 'index';
  const baseline = index ? 100 : 0;
  const points = history.map(s => ({date:s.date,value:index ? s.index : s.return_pct}));
  const min = Math.min(baseline,...points.map(p=>p.value));
  const max = Math.max(baseline,...points.map(p=>p.value));
  const range = Math.max(max-min,0.04);
  const lo = min-range*.8, hi = max+range*.8;
  const width = Math.max(260, $('chart').clientWidth);
  const mobile = width < 600;
  const left = mobile ? 49 : 65;
  const right = width - 25;
  const height = mobile ? 230 : 220;
  const plotTop = 28, plotBottom = height - 53;
  const y = v => plotTop+(hi-v)/(hi-lo)*(plotBottom-plotTop);
  const x = i => points.length===1 ? left+(right-left)*.45 : left+i/(points.length-1)*(right-left);
  const format = v => index ? v.toFixed(4) : signed(v,4);
  const latest = points[points.length-1];
  const baselineY = y(baseline);
  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="chart-title chart-description"><title id="chart-title">${index?'Portfolio index':'Portfolio return'} since 2 November 2026</title><desc id="chart-description">${points.length} closing observation${points.length===1?'':'s'}. Latest ${format(latest.value)}. Opening capital ${index?'equals 100':'is the zero-return baseline'}. No pre-launch history is shown.</desc>`;
  for (const v of [hi,lo]) svg += `<line x1="${left}" x2="${right}" y1="${y(v)}" y2="${y(v)}" stroke="#edf0e8"/><text x="0" y="${y(v)+4}">${index?v.toFixed(2):v.toFixed(2)+'%'}</text>`;
  svg += `<line x1="${left}" x2="${right}" y1="${baselineY}" y2="${baselineY}" stroke="#adb5a4" stroke-dasharray="4 5"/><text x="${left}" y="${baselineY-12}">${index?'100':'0%'}</text>`;
  if(points.length>1) svg += `<polyline points="${points.map((p,i)=>`${x(i)},${y(p.value)}`).join(' ')}" fill="none" stroke="#536747" stroke-width="2"/>`;
  points.forEach((p,i) => { svg += `<circle cx="${x(i)}" cy="${y(p.value)}" r="${i===points.length-1?5:3}" fill="#536747"><title>${date(p.date)}: ${format(p.value)}</title></circle>`; });
  const labelX = points.length===1 ? x(0) : x(points.length-1)-12;
  const anchor = points.length===1 ? 'middle' : 'end';
  svg += `<text x="${labelX}" y="${y(latest.value)+27}" text-anchor="${anchor}" class="dot-label">${format(latest.value)}</text><text x="${x(points.length-1)}" y="${height-11}" text-anchor="${points.length===1?'middle':'end'}">${date(latest.date)}</text>`;
  if(points.length>1) svg += `<text x="${x(0)}" y="${height-11}" text-anchor="start">${date(points[0].date)}</text>`;
  svg += '</svg>';
  $('chart').innerHTML = svg;
  $('baseline-label').textContent = `Opening capital = ${index?'100':'0%'}`;
  $('history-note').textContent = points.length===1 ? 'First session: one closing observation. The dashed line shows opening capital; a performance history will build from this date. No annualized return is shown.' : `${points.length} saved end-of-day observations. Net of recorded transaction costs, including cash and recorded dividends. Prices are dated, not live.`;
}

function renderDetail(ticker, origin) {
  selectedHolding = ticker;
  const panel = $('holding-detail');
  document.querySelectorAll('[data-holding]').forEach(b => b.setAttribute('aria-expanded',String(b.dataset.holding===ticker)));
  if(!ticker){panel.hidden=true;detailOrigin?.focus();return;}
  detailOrigin=origin||detailOrigin;
  const h = data.snapshot.holdings.find(h=>h.ticker===ticker);
  const first = data.snapshot.activity.find(a=>a.ticker===ticker && a.type==='buy');
  const fields = [
    ['First allocated',date(h.first_date)],['Latest allocation',date(h.last_date)],['Initial target',pct(h.initial_target_pct)],['Current weight',pct(h.weight_pct,3)],
    ['Whole shares held',h.shares.toLocaleString('en-US')],['Entry VWAP',yen(h.entry_vwap,4)],['Average cost / share',yen(h.average_cost,4)],['Market value',yen(h.market_value)],
    ['Purchase cost assumption',`${pct(first.transaction_cost_rate*100,1)} · ${yen(first.transaction_cost,2)}`],['Unrealized P&L',`${h.unrealized<0?'−':'+'}${yen(Math.abs(h.unrealized),2)}`],['Portfolio contribution',signed(h.contribution_pp,4,' pp')],['Price date',date(h.mark_date)]
  ];
  const budget=Number(first.allocation_base)*Number(first.target_allocation_pct)/100;
  panel.innerHTML = `<div class="detail-top"><div><p class="eyebrow">${escapeHtml(h.ticker)} · ${escapeHtml(h.japanese_name)}</p><h3 id="detail-heading" tabindex="-1">${escapeHtml(h.name)} allocation record</h3></div><button type="button" id="close-detail" aria-label="Close allocation details">Close ×</button></div><dl class="detail-grid">${fields.map(([k,v])=>`<div><dt>${escapeHtml(k)}</dt><dd>${escapeHtml(v)}</dd></div>`).join('')}</dl><a class="research-link" href="${escapeHtml(h.research_url)}">Read the research: ${escapeHtml(h.research_title)} ↗</a><p class="detail-note">Research published ${date(h.research_date)}. The first allocation used a ${yen(budget)} budget, including modeled costs. ${first.shares} whole shares used ${yen(-first.cash_change,2)}; ${yen(budget+first.cash_change,2)} of that budget stayed in cash. The initial target remains visible as the holding’s market weight changes.</p>`;
  panel.hidden=false;
  panel.setAttribute('role','region');panel.setAttribute('aria-labelledby','detail-heading');
  $('detail-heading').focus({preventScroll:true});
  panel.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'nearest'});
  $('close-detail').addEventListener('click',()=>renderDetail(null));
}

function renderHoldings() {
  $('holdings-count').textContent = `(${data.snapshot.holdings.length})`;
  $('holdings-body').innerHTML = data.snapshot.holdings.map(h=>`<tr><td><button type="button" class="company-button" data-holding="${escapeHtml(h.ticker)}" aria-controls="holding-detail" aria-expanded="false">${escapeHtml(h.name)}</button><span class="company-meta">${escapeHtml(h.ticker)} · ${escapeHtml(h.exchange)} · ${h.shares} shares</span></td><td data-label="First allocated">${date(h.first_date)}</td><td data-label="Weight · current / initial target" class="number"><span class="weight-main">${pct(h.weight_pct,3)}</span><span class="cell-sub">${pct(h.initial_target_pct)} target</span></td><td data-label="Avg. entry · incl. cost" class="number">${yen(h.average_cost,2)}<span class="cell-sub">VWAP ${yen(h.entry_vwap,4)}</span></td><td data-label="Latest close" class="number">${yen(h.mark,2)}<span class="cell-sub">${date(h.mark_date)}</span></td><td data-label="Unrealized return" class="number ${h.return_pct<0?'negative':'positive'}">${signed(h.return_pct,2)}<span class="cell-sub">${h.unrealized<0?'−':'+'}${yen(Math.abs(h.unrealized),2)}</span></td><td><button type="button" class="row-open" data-holding="${escapeHtml(h.ticker)}" aria-label="View ${escapeHtml(h.name)} allocation details" aria-expanded="false" aria-controls="holding-detail">+</button></td></tr>`).join('');
  document.querySelectorAll('[data-holding]').forEach(b=>b.addEventListener('click',()=>renderDetail(selectedHolding===b.dataset.holding?null:b.dataset.holding,b)));
}

function renderEntryCalculations() {
  const buys=data.snapshot.activity.filter(a=>a.type==='buy');
  $('entry-math').innerHTML=buys.map(a=>{
    const budget=Number(a.allocation_base)*Number(a.target_allocation_pct)/100;
    const costPerShare=a.reference_price*Number(a.transaction_cost_rate);
    const h=data.snapshot.holdings.find(h=>h.ticker===a.ticker);
    return `<article class="entry-example"><p class="entry-label">${escapeHtml(h?.name||a.ticker)} · ${date(a.date)}</p><div class="price-equation"><div><strong>${yen(a.reference_price,4)}</strong><span>Session VWAP</span></div><i aria-hidden="true">+</i><div><strong>${yen(costPerShare,4)}</strong><span>Purchase cost · ${pct(Number(a.transaction_cost_rate)*100,1)}</span></div><i aria-hidden="true">=</i><div class="entry-result"><strong>${yen(a.effective_price,4)}</strong><span>Modeled entry / share</span></div></div><p class="entry-total"><strong>${a.shares} whole shares → ${yen(-a.cash_change,2)}</strong> total cash used · ${yen(budget+a.cash_change,2)} of the ${yen(budget)} target budget remains in cash.</p><p class="entry-source">VWAP = ${yen(Number(a.reference_price_numerator))} traded value ÷ ${Number(a.reference_price_denominator).toLocaleString('en-US')} shares for the ${date(a.date)} TSE session. The ${pct(Number(a.transaction_cost_rate)*100,1)} cost is added once. Calculations use the unrounded VWAP.</p></article>`;
  }).join('');
}

function renderAllocation() {
  const colors=['#536747','#8b7957','#607b82','#916c74','#716a85','#7b8756'];
  const parts=data.snapshot.holdings.map((h,i)=>({label:h.name,weight:h.weight_pct,color:colors[i%colors.length]}));
  parts.push({label:'Cash',weight:data.snapshot.cash_weight_pct,color:'#dce0d4'});
  $('allocation-bar').innerHTML=parts.map(p=>`<span title="${escapeHtml(p.label)} · ${pct(p.weight,3)}" style="width:${p.weight}%;background:${p.color}"></span>`).join('');
  $('allocation-bar').setAttribute('aria-label',parts.map(p=>`${p.label} ${pct(p.weight,3)}`).join(', '));
  $('allocation-legend').innerHTML=parts.map(p=>`<span><i class="square" style="background:${p.color}"></i>${escapeHtml(p.label)} <strong>${pct(p.weight,3)}</strong></span>`).join('');
}

function renderReturnBridge() {
  const s=data.snapshot;
  const tradeCosts=s.costs;
  const priceProfit=s.pnl+tradeCosts-s.dividends;
  const amount=v=>`${v<0?'−':v>0?'+':''}${yen(Math.abs(v),4)}`;
  $('return-bridge').innerHTML=`<p class="eyebrow">Why the portfolio starts slightly below ¥10 million</p><p><span>${amount(priceProfit)} <small>price movement</small></span><b>+</b><span>−${yen(tradeCosts,4)} <small>recorded transaction costs</small></span>${s.dividends?`<b>+</b><span>${amount(s.dividends)} <small>recorded dividends</small></span>`:''}<b>=</b><span class="${s.pnl<0?'negative':'positive'}">${amount(s.pnl)} <small>portfolio P&amp;L</small></span></p><p class="bridge-note">More decimal places are shown here to keep the calculation clear; summary amounts are rounded to yen or sen.</p>`;
  if(data.history.length>1) $('return-bridge').querySelector('.eyebrow').textContent='What contributed to the portfolio’s return';
}

function renderActivity() {
  $('activity-list').innerHTML = [...data.snapshot.activity].reverse().map(a=>{
    if(a.type==='opening_cash') return `<article class="activity-entry"><time class="activity-date" datetime="${a.date}">${date(a.date)}</time><span class="activity-badge opening">Start</span><div class="activity-copy"><h3>The portfolio begins</h3><p>¥10 million of hypothetical capital. All cash before the first allocation.</p></div><div class="activity-value">${yen(Number(a.amount))}<span>Opening capital</span></div></article>`;
    if(a.type==='buy'||a.type==='sell') {
      const h=data.snapshot.holdings.find(h=>h.ticker===a.ticker);
      const name=h?.name||a.ticker;
      return `<article class="activity-entry"><time class="activity-date" datetime="${a.date}">${date(a.date)}</time><span class="activity-badge">${a.type==='buy'?'Buy':'Sell'}</span><div class="activity-copy"><h3>${escapeHtml(name)} <span class="muted">${escapeHtml(a.ticker)}</span> ${a.target_allocation_pct?'· '+pct(Number(a.target_allocation_pct))+' target':''}</h3><p>${a.shares} whole shares · session VWAP ${yen(a.reference_price,4)} · ${pct(Number(a.transaction_cost_rate)*100,1)} modeled cost. ${escapeHtml(a.note||'')}</p>${h?`<a href="${escapeHtml(h.research_url)}">Related research ↗</a>`:''}</div><div class="activity-value">${yen(Math.abs(a.cash_change),2)}<span>${a.cash_change<0?'Cash used, incl. cost':'Cash received, net of cost'}</span></div></article>`;
    }
    return `<article class="activity-entry"><time class="activity-date">${date(a.date)}</time><span class="activity-badge">${escapeHtml(a.type)}</span><div class="activity-copy"><h3>${escapeHtml(a.ticker||'')}</h3><p>${escapeHtml(a.note||'')}</p></div><div class="activity-value">${a.amount?yen(Number(a.amount),2):''}</div></article>`;
  }).join('');
}

async function init() {
  try {
    const response=await fetch('portfolio-data.json',{cache:'no-cache'});
    if(!response.ok) throw new Error('Snapshot unavailable');
    data=await response.json();
    const s=data.snapshot;
    $('asof').textContent=`Prices as of ${date(data.asof)} · TSE close`;
    $('nav-value').textContent=yen(s.nav);
    setSigned($('total-return'),s.return_pct,signed(s.return_pct,4));
    $('total-pnl').textContent=`${s.pnl<0?'−':'+'}${yen(Math.abs(s.pnl),2)} · after recorded costs`;
    $('equity-weight').textContent=pct(100-s.cash_weight_pct,3);
    $('equity-detail').textContent=`${s.holdings.length} holding${s.holdings.length===1?'':'s'} · ${yen(s.market_value)}`;
    $('cash-value').textContent=yen(s.cash);
    $('cash-detail').textContent=`${pct(s.cash_weight_pct,3)} of current portfolio value`;
    $('allocation-label').textContent=`${s.holdings.length} holding${s.holdings.length===1?'':'s'} · unallocated capital stays in cash`;
    // Put decisions above the longer performance record, without duplicating data.
    const content=$('portfolio-content');
    content.insertBefore($('allocation'),document.querySelector('.performance'));
    content.insertBefore($('holdings'),document.querySelector('.performance'));
    renderHoldings();renderActivity();renderEntryCalculations();renderAllocation();renderReturnBridge();
    $('portfolio-content').hidden=false;
    renderChart();
    new ResizeObserver(()=>renderChart()).observe($('chart'));
    document.querySelectorAll('[data-chart]').forEach(b=>b.addEventListener('click',()=>{chartMode=b.dataset.chart;document.querySelectorAll('[data-chart]').forEach(t=>{t.classList.toggle('selected',t===b);t.setAttribute('aria-pressed',String(t===b));});renderChart();}));
    const sectionLinks=[...document.querySelectorAll('.section-nav a[href^="#"]')];
    sectionLinks.forEach(a=>a.addEventListener('click',()=>{sectionLinks.forEach(t=>t.classList.toggle('active',t===a));}));
  } catch(error) { $('load-error').hidden=false; $('asof').textContent='Snapshot unavailable'; console.error('Portfolio snapshot could not load',error.message); }
}
init();
