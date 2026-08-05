/* ===================================================================
   jpinv.com — homepage hero behavior.

   Two jobs, and nothing else:
     1. rotate the four slides
     2. fill the live capital-policy panel from
        /compounders/feed/data/hero.json

   The slide markup is in index.html and en/index.html so that the h1 is
   real HTML. This file never writes headings.

   FAILURE IS THE DESIGN PROBLEM HERE. A live panel that renders empty
   is worse than no panel, so the markup ships with real rows already in
   it, written at build time. If the fetch fails, times out, or returns
   something unexpected, those rows stay on screen and the label says
   the date they were written instead of claiming to be live.

   Created August 3, 2026.
   =================================================================== */
(function () {
  "use strict";

  var hero = document.querySelector(".jh");
  if (!hero) return;

  var isEn = /^\/en(\/|$)/.test(location.pathname);
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------- 1. Slide rotation ---------------- */

  var slides = [].slice.call(hero.querySelectorAll(".jh-slide"));
  var dotWrap = hero.querySelector(".jh-dots");

  if (slides.length > 1 && dotWrap) {
    var i = 0, timer = null;

    slides.forEach(function (s, n) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", (isEn ? "Slide " : "スライド ") + (n + 1));
      b.setAttribute("aria-current", n === 0 ? "true" : "false");
      b.addEventListener("click", function () { go(n); restart(); });
      dotWrap.appendChild(b);
    });
    var dots = [].slice.call(dotWrap.children);

    function go(n) {
      slides[i].classList.remove("is-on");
      dots[i].setAttribute("aria-current", "false");
      i = (n + slides.length) % slides.length;
      slides[i].classList.add("is-on");
      dots[i].setAttribute("aria-current", "true");
    }
    function restart() {
      if (timer) clearInterval(timer);
      if (!reduce) timer = setInterval(function () { go(i + 1); }, 7000);
    }

    slides[0].classList.add("is-on");
    restart();

    /* Stop while the tab is hidden; a slider running in a background tab
       is wasted work and lands the visitor on a random slide. */
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { if (timer) clearInterval(timer); }
      else { restart(); }
    });
    hero.addEventListener("mouseenter", function () { if (timer) clearInterval(timer); });
    hero.addEventListener("mouseleave", restart);
  }

  /* ---------------- 2. The live panel ---------------- */

  var rowsEl = hero.querySelector(".jh-rows");
  if (!rowsEl) return;
  var labelEl = hero.querySelector(".jh-plabel span");
  var statsEl = hero.querySelector(".jh-stats");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c];
    });
  }
  function nf(n) { return Number(n || 0).toLocaleString("en-US"); }
  function shortDate(iso) {
    var p = String(iso || "").split("-");
    return p.length === 3 ? p[1] + "." + p[2] : "";
  }

  var ctrl = new AbortController();
  var giveUp = setTimeout(function () { ctrl.abort(); }, 4000);

  fetch("/compounders/feed/data/hero.json", { signal: ctrl.signal, cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (d) {
      clearTimeout(giveUp);
      if (!d || !d.rows || !d.rows.length) return;   // keep what is already on screen

      rowsEl.innerHTML = d.rows.slice(0, 6).map(function (r) {
        return '<li><span class="jh-date">' + esc(shortDate(r.date)) + '</span>' +
               '<span class="jh-tag">' + esc(isEn ? r.label_en : r.label_jp) + '</span>' +
               '<span class="jh-name"><span class="jh-tick">' + esc(r.ticker) + '</span>' +
               esc(isEn ? r.name_en : r.name_jp) + '</span></li>';
      }).join("");

      if (statsEl && d.counts) {
        statsEl.innerHTML =
          stat(d.counts.last30, isEn ? "disclosures, 30 days" : "開示件数・直近30日") +
          stat(d.counts.watched, isEn ? "names watched" : "追跡銘柄") +
          stat(d.counts.profiles, isEn ? "research profiles" : "銘柄レポート");
      }

      if (labelEl) {
        labelEl.textContent = isEn
          ? "TSE capital actions · refreshed every 30 minutes"
          : "東証・資本政策開示 ／ 30分ごとに更新";
      }
    })
    .catch(function () {
      clearTimeout(giveUp);
      /* Deliberately silent. The build-time rows stay visible, and the label
         in the markup already says when they were written, so nothing on
         screen claims to be live when it is not. */
    });

  function stat(v, label) {
    return "<span><b>" + nf(v) + "</b><span>" + esc(label) + "</span></span>";
  }

  /* ---------------- 3. News tabs ----------------
     Switches which list is visible and points 詳しく見る at the active tab's
     page.

     THIS BLOCK USED TO SAY: "No fetch: the lists are rebuilt whenever the site
     is built, and a half-day-old news row is not a failure the way an empty
     panel is."

     Both halves of that were wrong, and it froze the news section for days at a
     time. There is no site build. jpinv.com is a static repo served by GitHub
     Pages; nothing regenerates index.html on deploy. And the rows were not half
     a day old — they only ever changed when someone ran build_news_data.py by
     hand without --no-bake and committed the result, so on August 5, 2026 the
     大量保有報告 tab was showing filings from July 31.

     Meanwhile the workflow rebuilt compounders/feed/data/news.json every 30
     minutes and nothing on the site ever read it. The drift was visible inside a
     single commit: news.json carried two August 4 capital rows while the baked
     HTML beside it still showed five from August 3.

     So the news section now does exactly what the hero panel above already does,
     and for the same reason. Same failure design too: if the fetch fails, times
     out, or returns something unexpected, the baked rows stay on screen. They
     were described as a no-JavaScript fallback before there was any JavaScript
     for them to fall back from. Now that is true. */

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
      var tail = r.filer_en + " → " + r.ticker + " " +
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
