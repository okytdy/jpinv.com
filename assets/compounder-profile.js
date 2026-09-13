(function () {
  'use strict';

  function slugify(value, fallback) {
    var slug = String(value || '')
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9\u3040-\u30ff\u3400-\u9fff]+/g, '-')
      .replace(/^-+|-+$/g, '');
    return slug || fallback;
  }

  function directSections(flow) {
    return Array.prototype.filter.call(flow.children, function (node) {
      return node.matches && node.matches('section.section, section.research-section, section.source-shelf');
    });
  }

  function sectionHeading(section) {
    return section.querySelector(
      ':scope > .research-title, :scope > .section-head > .section-title:not(.cp-promoted-title), :scope > h2'
    );
  }

  function createTocItem(section, index) {
    var heading = sectionHeading(section);
    if (!heading || section.classList.contains('source-shelf')) return null;
    if (!section.id) section.id = slugify(heading.textContent, 'section-' + (index + 1));
    var labelNode = section.querySelector(':scope > .section-label, :scope > .section-head > .section-num');
    return {
      id: section.id,
      index: String(index + 1).padStart(2, '0'),
      title: heading.textContent.trim(),
      label: labelNode ? labelNode.textContent.trim() : ''
    };
  }

  function makeRail(items, facts, isJa) {
    var aside = document.createElement('aside');
    aside.className = 'cp-research-rail';
    aside.setAttribute('aria-label', isJa ? '記事内ナビゲーション' : 'Article navigation');

    var inner = document.createElement('div');
    inner.className = 'cp-rail-inner';
    var title = document.createElement('p');
    title.className = 'cp-rail-title';
    title.textContent = isJa ? 'このページ' : 'On this page';
    inner.appendChild(title);

    var list = document.createElement('ol');
    list.className = 'cp-rail-list';
    items.forEach(function (item) {
      var li = document.createElement('li');
      var link = document.createElement('a');
      link.href = '#' + item.id;
      var number = document.createElement('span');
      number.className = 'cp-rail-index';
      number.textContent = item.index;
      var text = document.createElement('span');
      text.textContent = item.title;
      link.appendChild(number);
      link.appendChild(text);
      li.appendChild(link);
      list.appendChild(li);
    });
    inner.appendChild(list);

    if (facts && facts.length) {
      var dl = document.createElement('dl');
      dl.className = 'cp-rail-facts';
      facts.slice(0, 4).forEach(function (fact) {
        var group = document.createElement('div');
        var dt = document.createElement('dt');
        var dd = document.createElement('dd');
        dt.textContent = fact.label;
        dd.textContent = [fact.value, fact.context].filter(Boolean).join(' · ');
        group.appendChild(dt);
        group.appendChild(dd);
        dl.appendChild(group);
      });
      inner.appendChild(dl);
    }

    aside.appendChild(inner);
    return aside;
  }

  function makeMobileToc(items, isJa) {
    var details = document.createElement('details');
    details.className = 'cp-mobile-toc';
    var summary = document.createElement('summary');
    summary.textContent = isJa ? 'このページの内容' : 'On this page';
    var list = document.createElement('ol');
    items.forEach(function (item) {
      var li = document.createElement('li');
      var link = document.createElement('a');
      link.href = '#' + item.id;
      link.textContent = item.title;
      li.appendChild(link);
      list.appendChild(li);
    });
    details.appendChild(summary);
    details.appendChild(list);
    return details;
  }

  function parsePageData() {
    var node = document.getElementById('compounder-profile-data');
    if (!node) return {};
    try { return JSON.parse(node.textContent); } catch (_) { return {}; }
  }

  function wrapTables(root, isJa) {
    root.querySelectorAll('table').forEach(function (table) {
      if (table.closest('.profile-table-wrap, .underwriting-scroll, .valuation-matrix-wrap, .cp-table-scroll')) return;
      var wrapper = document.createElement('div');
      wrapper.className = 'cp-table-scroll';
      wrapper.tabIndex = 0;
      wrapper.setAttribute('aria-label', isJa ? '表（横方向にスクロールできます）' : 'Table; scroll horizontally when needed');
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    });
  }

  function buildLayout() {
    var root = document.querySelector('article.compounder-profile');
    if (!root || root.querySelector(':scope > .cp-layout')) return;
    var isJa = (document.documentElement.lang || '').toLowerCase().indexOf('ja') === 0;
    var header = root.querySelector(':scope > .cp-profile-header');
    if (!header) return;

    var flow = root.querySelector(':scope > .external-ai-profile-copy');
    var layout = document.createElement('div');
    layout.className = 'cp-layout';

    if (flow) {
      flow.classList.add('cp-article-flow');
      root.insertBefore(layout, flow);
      layout.appendChild(flow);
    } else {
      flow = document.createElement('div');
      flow.className = 'cp-article-flow';
      var nodes = Array.prototype.slice.call(root.children);
      var headerIndex = nodes.indexOf(header);
      var contentNodes = nodes.slice(headerIndex + 1).filter(function (node) {
        return !node.matches('.share-bar, .publication-note, .disclaimer, .meth, script');
      });
      root.insertBefore(layout, header.nextSibling);
      contentNodes.forEach(function (node) { flow.appendChild(node); });
      layout.appendChild(flow);
    }

    var pageData = parsePageData();
    var items = directSections(flow).map(createTocItem).filter(Boolean);
    if (items.length) {
      flow.insertBefore(makeMobileToc(items, isJa), flow.firstChild);
      var rail = makeRail(items, pageData.secondaryMetrics || [], isJa);
      layout.appendChild(rail);

      if ('IntersectionObserver' in window) {
        var links = Array.prototype.slice.call(rail.querySelectorAll('a[href^="#"]'));
        var byId = new Map(links.map(function (link) { return [link.getAttribute('href').slice(1), link]; }));
        var observer = new IntersectionObserver(function (entries) {
          var visible = entries.filter(function (entry) { return entry.isIntersecting; })
            .sort(function (a, b) { return a.boundingClientRect.top - b.boundingClientRect.top; });
          if (!visible.length) return;
          links.forEach(function (link) { link.removeAttribute('aria-current'); });
          var active = byId.get(visible[0].target.id);
          if (active) active.setAttribute('aria-current', 'true');
        }, { rootMargin: '-18% 0px -70% 0px', threshold: 0 });
        directSections(flow).forEach(function (section) { if (byId.has(section.id)) observer.observe(section); });
      }
    }

    wrapTables(flow, isJa);
    root.classList.add('cp-ready');
  }

  async function buildChart() {
    var container = document.querySelector('[data-compounder-chart]');
    var data = window.COMPOUNDER_CHART_DATA;
    if (!container || !window.LightweightCharts || container.dataset.cpChartReady) return;
    if (!data && container.dataset.chartSrc) {
      try {
        var response = await fetch(container.dataset.chartSrc);
        if (response.ok) data = await response.json();
      } catch (_) { return; }
    }
    if (!data) return;
    container.dataset.cpChartReady = 'true';

    var chart = window.LightweightCharts.createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight || 430,
      layout: { background: { color: '#fafbfc' }, textColor: '#4a5566', fontFamily: 'DM Mono, monospace', fontSize: 10 },
      grid: { vertLines: { color: '#edf0f3' }, horzLines: { color: '#edf0f3' } },
      rightPriceScale: { borderColor: '#d6dee8' },
      timeScale: { borderColor: '#d6dee8', timeVisible: false },
      crosshair: { mode: 1 }
    });
    var topix = chart.addLineSeries({ color: 'rgba(48,68,102,.72)', lineWidth: 1.5, priceLineVisible: false, lastValueVisible: true });
    topix.setData(data.topix_rebased || []);
    var sma = chart.addLineSeries({ color: '#9a7838', lineWidth: 1.5, lineStyle: 2, priceLineVisible: false, lastValueVisible: false });
    sma.setData(data.sma60 || []);
    var candles = chart.addCandlestickSeries({ upColor: '#2f6f4f', downColor: '#a8322a', borderUpColor: '#2f6f4f', borderDownColor: '#a8322a', wickUpColor: '#2f6f4f', wickDownColor: '#a8322a' });
    candles.setData(data.candles || []);
    if (data.peak_close) {
      var isJa = (document.documentElement.lang || '').toLowerCase().indexOf('ja') === 0;
      var peakLabel = container.dataset.peakMarkerLabel || (isJa ? '最高終値' : 'peak close');
      var postPeakLabel = container.dataset.postPeakMarkerLabel || (isJa ? '高値後の安値終値' : 'post-peak low close');
      var windowLowLabel = container.dataset.windowLowMarkerLabel || (isJa ? '期間安値終値' : 'window low close');
      function markerText(point, label) {
        var value = Number(point.value).toLocaleString(isJa ? 'ja-JP' : 'en-US');
        return isJa ? value + '円 ' + label : '¥' + value + ' ' + label;
      }
      var markers = [
        { time: data.peak_close.time, position: 'aboveBar', color: '#2f6f4f', shape: 'arrowDown', text: markerText(data.peak_close, peakLabel) }
      ];
      if (data.post_peak_low_close) {
        markers.push({ time: data.post_peak_low_close.time, position: 'belowBar', color: '#a8322a', shape: 'arrowUp', text: markerText(data.post_peak_low_close, postPeakLabel) });
      } else if (data.window_low_close) {
        markers.push({ time: data.window_low_close.time, position: 'belowBar', color: '#a8322a', shape: 'arrowUp', text: markerText(data.window_low_close, windowLowLabel) });
      }
      candles.setMarkers(markers);
    }
    var volume = chart.addHistogramSeries({ color: 'rgba(48,68,102,.38)', priceFormat: { type: 'volume' }, priceScaleId: 'volume' });
    volume.setData(data.volume || []);
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: .83, bottom: 0 }, borderColor: '#d6dee8' });
    chart.timeScale().fitContent();
    var resize = function () { chart.applyOptions({ width: container.clientWidth, height: container.clientHeight || 430 }); };
    window.addEventListener('resize', resize, { passive: true });
  }

  buildLayout();
  buildChart();
})();
