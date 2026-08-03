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
     The rows are baked into the page at build time; this only switches
     which list is visible and points 詳しく見る at the active tab's page.
     No fetch: the lists are rebuilt whenever the site is built, and a
     half-day-old news row is not a failure the way an empty panel is. */

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
})();
