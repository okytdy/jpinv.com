/* Homepage news tabs. The hero uses a licensed photograph and has no data feed. */
(function () {
  "use strict";
  var isEn = /^\/en(\/|$)/.test(location.pathname);
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c];
    });
  }
  var newsTabs = [].slice.call(document.querySelectorAll(".nw-tabs button"));
  var newsLists = [].slice.call(document.querySelectorAll(".nw-list"));
  var newsMore = document.querySelector(".nw-more");
  newsTabs.forEach(function (btn) {
    btn.addEventListener("click", function () {
      newsTabs.forEach(function (b) { b.setAttribute("aria-selected", String(b === btn)); });
      newsLists.forEach(function (l) { l.hidden = l.getAttribute("data-list") !== btn.getAttribute("data-tab"); });
      if (newsMore) newsMore.setAttribute("href", btn.getAttribute("data-more"));
    });
  });

  /* ---------------- 4. Fill the news lists from news.json ----------------
     The markup written by tools/build_news_data.py is reproduced exactly here.
     If the two ever diverge the page changes shape on load, so any edit to
     rows_html() in that script has to be made here as well. */

  if (newsLists.length) {
    var listOf = {};
    newsLists.forEach(function (l) { listOf[l.getAttribute("data-list")] = l; });

    function newsDate(iso) {
      var p = String(iso || "").split("-");
      return p.length === 3 ? p[0] + "." + p[1] + "." + p[2] : "";
    }

    function reportRow(r) {
      var href = (isEn ? r.href_en : r.href_jp) || "#";
      var name = (isEn ? r.name_en : r.name_jp) || r.name_jp || "";
      return '<li><a href="' + esc(href) + '">' +
             '<span class="nw-date">' + newsDate(r.date) + '</span>' +
             '<span class="nw-tag">' + (isEn ? "Report" : "銘柄レポート") + '</span>' +
             '<span class="nw-tx"><b>' + esc(r.ticker) + '</b> ' + esc(name) +
             '</span></a></li>';
    }

    function capitalRow(r) {
      return '<li><span class="nw-date">' + newsDate(r.date) + '</span>' +
             '<span class="nw-tag">' + esc(isEn ? r.label_en : r.label_jp) + '</span>' +
             '<span class="nw-tx"><b>' + esc(r.ticker) + '</b> ' +
             esc(isEn ? r.name_en : r.name_jp) + '</span></li>';
    }

    function holdingRow(r) {
      var pct = (typeof r.pct === "number") ? " (" + r.pct.toFixed(2) + "%)" : "";
      var filer = (isEn ? r.filer_en : r.filer_jp) || r.filer_en || "";
      var tail = filer + " → " + r.ticker + " " +
                 (isEn ? r.issuer_en : r.issuer_jp) + pct;
      return '<li><span class="nw-date">' + newsDate(r.date) + '</span>' +
             '<span class="nw-tag">' + esc(isEn ? r.label_en : r.label_jp) + '</span>' +
             '<span class="nw-tx">' + esc(tail) + '</span></li>';
    }

    var render = { reports: reportRow, capital: capitalRow, holdings: holdingRow };

    var newsCtrl = new AbortController();
    var newsGiveUp = setTimeout(function () { newsCtrl.abort(); }, 4000);

    fetch("/compounders/feed/data/news.json", { signal: newsCtrl.signal, cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        clearTimeout(newsGiveUp);
        if (!d) return;
        Object.keys(render).forEach(function (which) {
          var el = listOf[which];
          var rows = d[which];
          /* An empty list is not an update. Leaving the baked rows in place is
             better than replacing five real ones with nothing. */
          if (!el || !rows || !rows.length) return;
          el.innerHTML = rows.map(render[which]).join("");
        });
      })
      .catch(function () {
        clearTimeout(newsGiveUp);
        /* Silent on purpose, exactly as the hero panel above. The baked rows
           stay on screen and carry real dates, so nothing claims to be newer
           than it is. */
      });
  }
})();
