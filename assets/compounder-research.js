(async function(){
  var container = document.querySelector('[data-compounder-chart]');
  var data = window.COMPOUNDER_CHART_DATA;
  if(!container || !window.LightweightCharts) return;
  if(!data && container.dataset.chartSrc){
    try{
      var response = await fetch(container.dataset.chartSrc);
      if(response.ok) data = await response.json();
    }catch(_){ return; }
  }
  if(!data) return;
  var chart = LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: 430,
    layout: { background: { color: '#fafbfc' }, textColor: '#4a5566', fontFamily: 'DM Mono, monospace', fontSize: 10 },
    grid: { vertLines: { color: '#edf0f3' }, horzLines: { color: '#edf0f3' } },
    rightPriceScale: { borderColor: '#d6dee8' },
    timeScale: { borderColor: '#d6dee8', timeVisible: false },
    crosshair: { mode: 1 }
  });
  var topix = chart.addLineSeries({ color:'rgba(122,130,144,.84)', lineWidth:1.5, priceLineVisible:false, lastValueVisible:true });
  topix.setData(data.topix_rebased || []);
  var sma = chart.addLineSeries({ color:'#9a7838', lineWidth:1.5, lineStyle:2, priceLineVisible:false, lastValueVisible:false });
  sma.setData(data.sma60 || []);
  var candles = chart.addCandlestickSeries({ upColor:'#56640f', downColor:'#b91c1c', borderUpColor:'#56640f', borderDownColor:'#b91c1c', wickUpColor:'#56640f', wickDownColor:'#b91c1c' });
  candles.setData(data.candles || []);
  if(data.peak_close && data.post_peak_low_close){
    candles.setMarkers([
      {time:data.peak_close.time,position:'aboveBar',color:'#56640f',shape:'arrowDown',text:'¥2,200 peak close'},
      {time:data.post_peak_low_close.time,position:'belowBar',color:'#b91c1c',shape:'arrowUp',text:'¥1,177 post-peak low'}
    ]);
  }
  var volume = chart.addHistogramSeries({ color:'rgba(48,68,102,.38)', priceFormat:{type:'volume'}, priceScaleId:'volume' });
  volume.setData(data.volume || []);
  chart.priceScale('volume').applyOptions({ scaleMargins:{top:.83,bottom:0}, borderColor:'#d6dee8' });
  chart.timeScale().fitContent();
  function resize(){ chart.applyOptions({width:container.clientWidth}); }
  window.addEventListener('resize', resize, {passive:true});
})();
