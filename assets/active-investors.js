/* ===================================================================
   Active Investors in Japan — shared component.
   Renders the 9 flip cards + the TSE-wide "new 5%" live feed from
   /compounders/active-investors/data/{feed,new5_feed}.json.

   A host element opts in with:
     <div class="ai-root" data-ai-lang="en|ja"
          data-ai-mode="embed|full"
          data-ai-base="/compounders/active-investors/data"
          data-ai-fullhref="/en/compounders/active-investors/"></div>
   No build step, no dependencies. Safe to load on any page.
   =================================================================== */
(function () {
  "use strict";

  var I18N = {
    en: {
      moves: { new_5pct: "New 5%", increase: "Increase", decrease: "Decrease", other: "Filing" },
      all: "All", new_5pct: "New 5%", increase: "Increases", decrease: "Decreases",
      d30: "Last 30 days", d90: "Last 90 days",
      search: "Search fund, company or ticker…",
      feedSearch: "Search company or ticker…",
      viewMore: "View more", flipHint: "click to see recent moves",
      recent: "recent filings", latest: "latest", noMoves: "No qualifying filings in the selected window.",
      feedTitle: "New 5% Filings — TSE-wide", feedSub: "Live · every new 5% large-shareholding report · any filer",
      viewAll: "View the full tool", viewAllFilings: "View all new 5% filings",
      tracked: "Tracked", showing: "showing", of: "of", investors: "investors",
      colDate: "Filed", colCo: "Company", colTk: "Ticker", colType: "Type", colMove: "Move",
      colPrev: "Prev", colNew: "New", colChg: "Change", colSum: "Purpose / reason", colSrc: "Source",
      sourceNote: "Source disclosures (EDINET) are filed in Japanese. Summaries are automated; always refer to the original filing.",
      pp: "pts", loading: "Loading…", err: "Could not load the feed.",
      crossed5: "new 5% report", country: { "United States": "US", "United Kingdom": "UK", "Singapore": "SG",
        "Hong Kong": "HK", "Norway": "NO", "Japan": "JP" }
    },
    ja: {
      moves: { new_5pct: "新規5%", increase: "買い増し", decrease: "売却", other: "報告" },
      all: "すべて", new_5pct: "新規5%", increase: "買い増し", decrease: "売却",
      d30: "直近30日", d90: "直近90日",
      search: "ファンド・企業・コードで検索…",
      feedSearch: "企業・コードで検索…",
      viewMore: "詳細", flipHint: "クリックで最近の動き",
      recent: "件の提出", latest: "最新", noMoves: "選択期間に該当する提出はありません。",
      feedTitle: "新規5%報告 — 東証全体", feedSub: "ライブ・新規の大量保有報告書をすべて・提出者を問わず",
      viewAll: "ツール全体を見る", viewAllFilings: "すべての新規5%報告を見る",
      tracked: "追跡中", showing: "表示", of: "/", investors: "投資家",
      colDate: "提出日", colCo: "企業", colTk: "コード", colType: "種別", colMove: "動き",
      colPrev: "前", colNew: "現", colChg: "変化", colSum: "目的・事由", colSrc: "出所",
      sourceNote: "出所（EDINET）の開示は日本語です。要約は自動生成のため、必ず原文をご確認ください。",
      pp: "pt", loading: "読み込み中…", err: "フィードを読み込めませんでした。",
      crossed5: "大量保有報告書", country: {}
    }
  };

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]; }); }
  function fmtPct(x) { if (x == null || x === "") return ""; var n = Math.round(x * 100) / 100;
    return String(String(n).indexOf(".") < 0 ? n : n.toFixed(2).replace(/0+$/, "").replace(/\.$/, "")); }
  function fmtChg(x) { if (x == null) return ""; var s = x > 0 ? "+" : (x < 0 ? "−" : ""); return s + fmtPct(Math.abs(x)); }
  function daysAgoISO(n) { var d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); }

  function moveBadge(L, mt) { return '<span class="ai-badge ai-m-' + mt + '">' + esc(L.moves[mt] || mt) + "</span>"; }

  function intentChip(lang, row) {
    var s = (lang === "ja" ? row.summary_ja : row.summary_en) || {};
    var lab = s.label || ""; var it = row.intent || "unknown";
    if (!lab || it === "unknown") return "";
    return '<span class="ai-intent ai-i-' + it + '">' + esc(lab) + "</span>";
  }

  function docTypeLabel(lang, f) {
    var t = f.japanese_title || "";
    if (!t) return "";
    if (lang === "ja") return '<div class="ai-td-jp">' + esc(t) + "</div>";
    var en = /訂正/.test(t) ? "Correction report"
      : (/変更報告/.test(t) ? "Change report"
      : (/大量保有報告/.test(t) ? "Large-shareholding report" : ""));
    if (/特例/.test(t)) en += " (passive/quarterly)";
    en = en.replace(/^ +| +$/g, "");
    return en ? '<div class="ai-td-jp">' + esc(en) + "</div>" : "";
  }

  function isuLabel(lang, f) {
    var en = f.issuer_name_en, ja = f.issuer_name;
    return lang === "ja" ? (ja || en || "") : (en || ja || "");
  }

  function Component(root) {
    var lang = root.getAttribute("data-ai-lang") === "ja" ? "ja" : "en";
    var mode = root.getAttribute("data-ai-mode") === "full" ? "full" : "embed";
    var base = root.getAttribute("data-ai-base") || "/compounders/active-investors/data";
    var fullHref = root.getAttribute("data-ai-fullhref") || "/en/compounders/active-investors/";
    var L = I18N[lang];
    var state = { feed: null, new5: null, filterMove: "all", filterDays: 0, q: "", feedQ: "" };

    root.innerHTML = '<div class="ai-loading">' + esc(L.loading) + "</div>";

    Promise.all([
      fetch(base + "/feed.json", { cache: "no-store" }).then(function (r) { return r.json(); }),
      fetch(base + "/new5_feed.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : { rows: [] }; }).catch(function () { return { rows: [] }; })
    ]).then(function (res) {
      state.feed = res[0]; state.new5 = res[1] || { rows: [] };
      render();
    }).catch(function () { root.innerHTML = '<div class="ai-err">' + esc(L.err) + "</div>"; });

    function homepageInvestors() {
      return (state.feed.investors || []).filter(function (i) { return i.homepage; });
    }

    function render() {
      var html = "";
      if (root.getAttribute("data-ai-header") !== "off") html += header();
      if (mode === "full") html += controls();
      html += '<div class="ai-grid" id="ai-grid"></div>';
      html += feedSection();
      html += modalShell();
      root.innerHTML = html;
      renderGrid();
      renderFeed();
      wire();
    }

    function header() {
      var meta = state.feed.meta || {};
      var t = lang === "ja" ? "日本で動く投資家" : "Active Investors in Japan";
      var lede = lang === "ja"
        ? "EDINETの大量保有報告書をもとに、日本株で意味のある動きを見せる海外・能動的な機関投資家のライブ・ビュー。"
        : "A live view of foreign and active institutional investors making meaningful moves in Japanese equities, based on EDINET large-shareholding filings.";
      var upd = meta.as_of_date ? '<div class="ai-updated">' + (lang === "ja" ? "更新" : "Updated") +
        ' <b>' + esc(meta.as_of_date) + "</b></div>" : "";
      return '<div class="ai-head"><div class="ai-eyebrow">' + (lang === "ja" ? "投資家インテリジェンス" : "Investor intelligence") +
        '</div><h2 class="ai-title">' + esc(t) + '</h2><p class="ai-lede">' + esc(lede) + "</p>" + upd + "</div>";
    }

    function controls() {
      function chip(k, lbl, group, on) {
        return '<span class="ai-chip ' + (on ? "ai-on" : "") + '" data-grp="' + group + '" data-val="' + k + '">' + esc(lbl) + "</span>";
      }
      var moveChips = chip("all", L.all, "move", true) + chip("new_5pct", L.new_5pct, "move") +
        chip("increase", L.increase, "move") + chip("decrease", L.decrease, "move");
      var dayChips = chip("0", L.all, "days", true) + chip("30", L.d30, "days") + chip("90", L.d90, "days");
      return '<div class="ai-controls">' +
        '<div class="ai-chips">' + moveChips + "</div>" +
        '<div class="ai-chips">' + dayChips + "</div>" +
        '<input class="ai-search" id="ai-search" type="text" placeholder="' + esc(L.search) + '" aria-label="' + esc(L.search) + '">' +
        '<span class="ai-count" id="ai-count"></span></div>';
    }

    function filterMoves(filings) {
      var cutoff = state.filterDays ? daysAgoISO(state.filterDays) : "";
      return filings.filter(function (f) {
        if (state.filterMove !== "all" && f.move_type !== state.filterMove) return false;
        if (cutoff && (f.filing_date || "") < cutoff) return false;
        return true;
      });
    }

    function cardMatchesSearch(inv) {
      if (!state.q) return true;
      var q = state.q.toLowerCase();
      if ((inv.display_name || "").toLowerCase().indexOf(q) >= 0) return true;
      if ((inv.display_name_ja || "").indexOf(state.q) >= 0) return true;
      return (inv.filings || []).some(function (f) {
        return (isuLabel(lang, f) || "").toLowerCase().indexOf(q) >= 0 ||
          (f.issuer_code || "").toLowerCase().indexOf(q) >= 0;
      });
    }

    function renderGrid() {
      var grid = root.querySelector("#ai-grid");
      var invs = homepageInvestors().filter(cardMatchesSearch);
      var shownMoves = 0;
      grid.innerHTML = invs.map(function (inv, idx) {
        var moves = filterMoves(inv.filings || []);
        shownMoves += moves.length;
        return card(inv, moves, idx);
      }).join("");
      var cnt = root.querySelector("#ai-count");
      if (cnt) cnt.textContent = L.showing + " " + invs.length + " " + L.of + " " +
        homepageInvestors().length + " " + L.investors;
    }

    function card(inv, moves, idx) {
      var name = lang === "ja" ? (inv.display_name_ja || inv.display_name) : inv.display_name;
      var sub = lang === "ja" ? "" : (inv.display_name_ja ? '<div class="ai-name-ja">' + esc(inv.display_name_ja) + "</div>" : "");
      var cc = (L.country[inv.country] || inv.country || "");
      var st = inv.stats || {};
      var actN = (inv.filings || []).length;
      var front = '<div class="ai-face ai-front" tabindex="0" role="button" aria-label="' + esc(name) + '">' +
        '<div class="ai-cat"><span>' + esc(catLabel(inv.category)) + '</span><span class="ai-flag">' + esc(cc) + "</span></div>" +
        '<div><div class="ai-name">' + esc(name) + "</div>" + sub + "</div>" +
        '<div class="ai-front-foot"><div class="ai-activity"><b>' + actN + "</b> " + esc(L.recent) +
        (st.last_filing_date ? "<br>" + esc(L.latest) + " " + esc(st.last_filing_date) : "") + "</div>" +
        '<div class="ai-flip-hint">' + esc(L.flipHint) + " →</div></div></div>";
      var movesHtml;
      if (!moves.length) {
        movesHtml = '<div class="ai-empty-note">' + esc(L.noMoves) + "</div>";
      } else {
        movesHtml = '<ul class="ai-moves">' + moves.slice(0, 4).map(function (f) {
          var co = isuLabel(lang, f);
          var ratio = ratioCell(f);
          return '<li class="ai-move"><div class="ai-move-line">' + moveBadge(L, f.move_type) +
            '<span class="ai-move-co">' + esc(co) + '</span><span class="ai-move-tk">' + esc(f.issuer_code || "") + "</span>" +
            '<span class="ai-move-date">' + esc(f.filing_date) + "</span></div>" +
            '<div class="ai-move-ratio">' + ratio + " " + intentChip(lang, f) + "</div></li>";
        }).join("") + "</ul>";
      }
      var back = '<div class="ai-face ai-back" tabindex="0" role="button" aria-label="' + esc(name) + ' moves">' +
        '<div class="ai-back-head"><span class="ai-back-name">' + esc(name) + "</span>" +
        '<span class="ai-back-meta">' + moves.length + " " + esc(lang === "ja" ? "件" : (moves.length === 1 ? "move" : "moves")) + "</span></div>" +
        movesHtml +
        '<div class="ai-back-foot"><button type="button" class="ai-more-btn" data-inv="' + esc(inv.id) + '">' +
        esc(L.viewMore) + " →</button></div></div>";
      return '<div class="ai-card" data-inv="' + esc(inv.id) + '"><div class="ai-inner">' + front + back + "</div></div>";
    }

    function ratioCell(f) {
      var cur = f.current_holding_ratio, prev = f.previous_holding_ratio, chg = f.change_percentage_points;
      if (f.move_type === "new_5pct") return "0% → " + fmtPct(cur) + "%";
      if (prev != null && cur != null) {
        var dir = (chg || 0) >= 0 ? "ai-up" : "ai-down";
        return fmtPct(prev) + "% → " + fmtPct(cur) + "% <span class=\"" + dir + "\">(" + fmtChg(chg) + " " + L.pp + ")</span>";
      }
      return cur != null ? fmtPct(cur) + "%" : "";
    }

    function catLabel(c) {
      var m = lang === "ja"
        ? { activist: "アクティビスト", long_only: "ロングオンリー", institutional: "機関投資家", strategic: "事業会社" }
        : { activist: "Activist", long_only: "Long-only", institutional: "Institutional", strategic: "Strategic holder" };
      return m[c] || c || "";
    }

    /* ---------- live new-5% feed ---------- */
    function feedSection() {
      var rows = (state.new5 && state.new5.rows) || [];
      var viewall = mode === "embed"
        ? '<a class="ai-feed-viewall" href="' + esc(fullHref) + '">' + esc(L.viewAllFilings) + " →</a>"
        : "";
      var search = mode === "full"
        ? '<input class="ai-search ai-feed-search" id="ai-feed-search" type="text" placeholder="' + esc(L.feedSearch) + '" aria-label="' + esc(L.feedSearch) + '">'
        : "";
      return '<div class="ai-feed-wrap"><div class="ai-feed-head"><h3 class="ai-feed-title">' + esc(L.feedTitle) + "</h3>" +
        viewall + "</div><p class=\"ai-feed-sub\">" + esc(L.feedSub) + "</p>" + search +
        '<div class="ai-feed-list" id="ai-feed-list" aria-live="polite"></div>' +
        '<p class="ai-feed-foot">' + esc(L.sourceNote) + "</p></div>";
    }

    function renderFeed() {
      var box = root.querySelector("#ai-feed-list");
      if (!box) return;
      var rows = ((state.new5 && state.new5.rows) || []).slice();
      if (state.feedQ) {
        var q = state.feedQ.toLowerCase();
        rows = rows.filter(function (r) {
          return (r.issuer_name || "").toLowerCase().indexOf(q) >= 0 ||
            (r.issuer_name_en || "").toLowerCase().indexOf(q) >= 0 ||
            (r.issuer_code || "").toLowerCase().indexOf(q) >= 0 ||
            (r.filer_raw_name || "").toLowerCase().indexOf(q) >= 0;
        });
      }
      var limit = mode === "embed" ? 8 : rows.length;
      rows = rows.slice(0, limit);
      if (!rows.length) { box.innerHTML = '<div class="ai-loading">—</div>'; return; }
      box.innerHTML = rows.map(function (r) {
        var s = (lang === "ja" ? r.summary_ja : r.summary_en) || {};
        var co = lang === "ja" ? r.issuer_name : (r.issuer_name_en || r.issuer_name);
        var tracked = r.is_tracked ? '<span class="ai-feed-tracked">' + esc(L.tracked) + "</span>" : "";
        var src = r.source_url ? '<a class="ai-src" href="' + esc(r.source_url) + '" target="_blank" rel="noopener">Source ↗</a>' : "";
        return '<div class="ai-feed-row" tabindex="0" role="button">' +
          '<span class="ai-feed-date">' + esc(r.filing_date) + "</span>" +
          '<span class="ai-feed-ratio">0% → ' + fmtPct(r.current_holding_ratio) + "%</span>" +
          '<span class="ai-feed-tk">' + esc(r.issuer_code || "") + "</span>" +
          '<span class="ai-feed-co">' + esc(co) + "</span>" +
          '<span class="ai-feed-filer">' + esc(r.filer_raw_name) + "</span>" + tracked +
          '<span class="ai-feed-arrow">›</span>' +
          '<div class="ai-feed-expand">' + esc(lang === "ja" ? (r.summary_text_ja || "") : (r.summary_text_en || "")) + " " + src + "</div></div>";
      }).join("");
    }

    /* ---------- modal ---------- */
    function modalShell() {
      return '<div class="ai-modal" id="ai-modal" role="dialog" aria-modal="true" aria-label="Investor detail">' +
        '<div class="ai-modal-bg" data-close="1"></div>' +
        '<div class="ai-modal-panel"><div class="ai-modal-head" id="ai-modal-head"></div>' +
        '<div class="ai-modal-body" id="ai-modal-body"></div></div></div>';
    }

    function openModal(invId) {
      var inv = (state.feed.investors || []).filter(function (i) { return i.id === invId; })[0];
      if (!inv) return;
      var name = lang === "ja" ? (inv.display_name_ja || inv.display_name) : inv.display_name;
      var head = root.querySelector("#ai-modal-head");
      var body = root.querySelector("#ai-modal-body");
      var site = inv.website ? ' · <a class="ai-src" href="' + esc(inv.website) + '" target="_blank" rel="noopener">' +
        (lang === "ja" ? "ウェブ ↗" : "Website ↗") + "</a>" : "";
      head.innerHTML = '<div><h3 class="ai-modal-title">' + esc(name) + "</h3>" +
        '<div class="ai-modal-sub">' + esc(catLabel(inv.category)) + " · " + esc(inv.country || "") + site + "</div>" +
        '<p class="ai-modal-blurb">' + esc(lang === "ja" ? (inv.blurb_ja || "") : (inv.blurb_en || "")) + "</p></div>" +
        '<button type="button" class="ai-modal-close" data-close="1" aria-label="Close">×</button>';
      var rows = (inv.filings || []).map(function (f) { return tableRow(f); }).join("");
      body.innerHTML = '<table class="ai-table"><thead><tr>' +
        th(L.colDate) + th(L.colCo) + th(L.colTk) + th(L.colMove) + th(L.colPrev) + th(L.colNew) +
        th(L.colChg) + th(L.colSum) + th(L.colSrc) + "</tr></thead><tbody>" + rows + "</tbody></table>";
      var modal = root.querySelector("#ai-modal");
      modal.classList.add("ai-show");
      _lastFocus = document.activeElement;
      var closeBtn = modal.querySelector(".ai-modal-close");
      if (closeBtn) closeBtn.focus();
      document.addEventListener("keydown", onKeydown);
    }
    function th(x) { return "<th>" + esc(x) + "</th>"; }

    function tableRow(f) {
      var co = isuLabel(lang, f);
      var s = (lang === "ja" ? f.summary_ja : f.summary_en) || {};
      var cav = (f.caveats || []).length ? '<span class="ai-cav">⚠ ' + esc(f.caveats.join(" ")) + "</span>" : "";
      var jp = docTypeLabel(lang, f);
      var conf = f.confidence && f.confidence !== "high"
        ? ' <span class="ai-conf ai-c-' + f.confidence + '">' + esc(f.confidence) + "</span>" : "";
      var src = f.source_url ? '<a class="ai-src" href="' + esc(f.source_url) + '" target="_blank" rel="noopener">Source ↗</a>' : "";
      return "<tr>" +
        td(L.colDate, esc(f.filing_date)) +
        td(L.colCo, '<span class="ai-td-co">' + esc(co) + "</span>") +
        td(L.colTk, '<span class="ai-td-tk">' + esc(f.issuer_code || "") + "</span>") +
        td(L.colMove, moveBadge(L, f.move_type)) +
        td(L.colPrev, '<span class="ai-td-ratio">' + (f.previous_holding_ratio != null ? fmtPct(f.previous_holding_ratio) + "%" : (f.move_type === "new_5pct" ? "0%" : "—")) + "</span>") +
        td(L.colNew, '<span class="ai-td-ratio">' + (f.current_holding_ratio != null ? fmtPct(f.current_holding_ratio) + "%" : "—") + "</span>") +
        td(L.colChg, '<span class="ai-td-ratio">' + (f.change_percentage_points != null ? fmtChg(f.change_percentage_points) + " " + L.pp : "—") + "</span>") +
        td(L.colSum, '<div class="ai-td-sum">' + intentChip(lang, f) + (s.note ? " " + esc(s.note) : "") + (f.purpose_en ? '<span class="ai-purpose">' + esc(f.purpose_en) + "</span>" : "") + conf + cav + jp + "</div>") +
        td(L.colSrc, src) + "</tr>";
    }
    function td(label, html) { return '<td data-label="' + esc(label) + '">' + html + "</td>"; }

    var _lastFocus = null;
    function closeModal() {
      var modal = root.querySelector("#ai-modal");
      if (modal) modal.classList.remove("ai-show");
      document.removeEventListener("keydown", onKeydown);
      if (_lastFocus && _lastFocus.focus) _lastFocus.focus();
    }
    function onKeydown(e) { if (e.key === "Escape") closeModal(); }

    /* ---------- wiring ---------- */
    function wire() {
      // flip on click / Enter / Space
      root.querySelectorAll(".ai-card").forEach(function (cardEl) {
        var inner = cardEl.querySelector(".ai-inner");
        function flip(e) {
          if (e.target.closest(".ai-more-btn")) return;
          cardEl.classList.toggle("ai-flipped");
        }
        inner.addEventListener("click", flip);
        cardEl.querySelectorAll(".ai-face").forEach(function (face) {
          face.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") {
              if (e.target.closest(".ai-more-btn")) return;
              e.preventDefault(); cardEl.classList.toggle("ai-flipped");
            }
          });
        });
      });
      root.querySelectorAll(".ai-more-btn").forEach(function (b) {
        b.addEventListener("click", function (e) { e.stopPropagation(); openModal(b.getAttribute("data-inv")); });
      });
      // modal close
      var modal = root.querySelector("#ai-modal");
      if (modal) modal.addEventListener("click", function (e) { if (e.target.closest("[data-close]")) closeModal(); });
      // feed row expand + open source
      root.querySelectorAll(".ai-feed-row").forEach(function (rowEl) {
        rowEl.addEventListener("click", function (e) {
          if (e.target.closest("a")) return;
          rowEl.classList.toggle("ai-open");
        });
        rowEl.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); rowEl.classList.toggle("ai-open"); }
        });
      });
      // controls
      root.querySelectorAll(".ai-chip").forEach(function (ch) {
        ch.addEventListener("click", function () {
          var grp = ch.getAttribute("data-grp"), val = ch.getAttribute("data-val");
          ch.parentNode.querySelectorAll(".ai-chip").forEach(function (c) { c.classList.remove("ai-on"); });
          ch.classList.add("ai-on");
          if (grp === "move") state.filterMove = val;
          if (grp === "days") state.filterDays = parseInt(val, 10) || 0;
          renderGrid(); wireGridOnly();
        });
      });
      var s = root.querySelector("#ai-search");
      if (s) s.addEventListener("input", function () { state.q = s.value.trim(); renderGrid(); wireGridOnly(); });
      var fs = root.querySelector("#ai-feed-search");
      if (fs) fs.addEventListener("input", function () { state.feedQ = fs.value.trim(); renderFeed(); wireFeedOnly(); });
    }
    // Re-wire just the parts that get re-rendered by filters (cards / feed).
    function wireGridOnly() {
      root.querySelectorAll(".ai-card").forEach(function (cardEl) {
        var inner = cardEl.querySelector(".ai-inner");
        inner.addEventListener("click", function (e) { if (e.target.closest(".ai-more-btn")) return; cardEl.classList.toggle("ai-flipped"); });
        cardEl.querySelectorAll(".ai-face").forEach(function (face) {
          face.addEventListener("keydown", function (e) { if ((e.key === "Enter" || e.key === " ") && !e.target.closest(".ai-more-btn")) { e.preventDefault(); cardEl.classList.toggle("ai-flipped"); } });
        });
      });
      root.querySelectorAll(".ai-more-btn").forEach(function (b) {
        b.addEventListener("click", function (e) { e.stopPropagation(); openModal(b.getAttribute("data-inv")); });
      });
    }
    function wireFeedOnly() {
      root.querySelectorAll(".ai-feed-row").forEach(function (rowEl) {
        rowEl.addEventListener("click", function (e) { if (e.target.closest("a")) return; rowEl.classList.toggle("ai-open"); });
      });
    }
  }

  function init() {
    var roots = document.querySelectorAll(".ai-root");
    roots.forEach(function (r) { if (!r.getAttribute("data-ai-ready")) { r.setAttribute("data-ai-ready", "1"); Component(r); } });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
