(function () {
  "use strict";

  var isJa = document.documentElement.lang === "ja";
  var capitalList = document.querySelector('[data-feed-list="capital"]');
  var ownershipList = document.querySelector('[data-feed-list="ownership"]');

  function parts(iso) {
    var value = String(iso || "").slice(0, 10).split("-");
    if (value.length !== 3) return null;
    return { year: Number(value[0]), month: Number(value[1]), day: Number(value[2]) };
  }

  function shortDate(iso) {
    var value = parts(iso);
    if (!value) return "";
    if (isJa) return value.month + "月" + value.day + "日";
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][value.month - 1] + " " + value.day;
  }

  function longDate(iso) {
    var value = parts(iso);
    if (!value) return "";
    if (isJa) return value.year + "年" + value.month + "月" + value.day + "日";
    return ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][value.month - 1] + " " + value.day + ", " + value.year;
  }

  function trimText(value, limit) {
    var text = String(value || "").replace(/\s+/g, " ").trim();
    if (text.length <= limit) return text;
    var cut = text.slice(0, limit - 1);
    var lastSpace = cut.lastIndexOf(" ");
    if (lastSpace > limit * .66) cut = cut.slice(0, lastSpace);
    return cut.replace(/[.,;:、。\s]+$/, "") + "…";
  }

  function capitalLabel(row) {
    if (isJa && row.label_jp) return row.label_jp;
    if (!isJa && row.label_en) return row.label_en;
    var code = String(row.class || "").toUpperCase();
    if (code.indexOf("MBO") === 0 || code.indexOf("TOB") >= 0) return "MBO";
    if (code.indexOf("BUYBACK") === 0) return isJa ? "自社株買い" : "Buyback";
    if (code.indexOf("DIVIDEND") >= 0) return isJa ? "配当" : "Dividend";
    if (code.indexOf("CANCEL") >= 0) return isJa ? "株式消却" : "Cancellation";
    if (code.indexOf("CAPITAL_COST") >= 0) return isJa ? "資本コスト" : "Cost of capital";
    return trimText(isJa ? (row.tag_jp || row.tag) : (row.tag || row.tag_en), 18);
  }

  function makeSignalRow(options) {
    var li = document.createElement("li");
    var link = document.createElement("a");
    var time = document.createElement("time");
    var body = document.createElement("span");
    var strong = document.createElement("strong");
    var ticker = document.createElement("b");
    var detail = document.createElement("em");
    var tag = document.createElement("small");

    link.href = options.href;
    time.dateTime = String(options.date || "").slice(0, 10);
    time.textContent = shortDate(options.date);
    strong.textContent = options.name + " ";
    ticker.textContent = options.ticker;
    strong.appendChild(ticker);
    detail.textContent = options.detail;
    tag.textContent = options.tag;
    body.appendChild(strong);
    body.appendChild(detail);
    link.appendChild(time);
    link.appendChild(body);
    link.appendChild(tag);
    li.appendChild(link);
    return li;
  }

  function renderCapital(payload) {
    if (!capitalList || !payload) return;
    var rows = Array.isArray(payload.home_rows) ? payload.home_rows : payload.rows;
    if (!Array.isArray(rows)) return;
    var chosen = rows.slice(0, 4);
    if (!chosen.length) return;

    var fragment = document.createDocumentFragment();
    chosen.forEach(function (row) {
      var label = capitalLabel(row);
      var detail = isJa ? label + "に関する新しい開示。" : "New " + label.toLowerCase() + " disclosure.";
      fragment.appendChild(makeSignalRow({
        href: isJa ? "/compounders/feed/" : "/en/compounders/feed/",
        date: row.date,
        name: (isJa ? row.name_jp : row.name_en) || row.name_jp || row.name_en,
        ticker: row.ticker,
        detail: detail,
        tag: label
      }));
    });
    capitalList.replaceChildren(fragment);
    var asof = document.querySelector('[data-feed-asof="capital"]');
    if (asof) asof.textContent = isJa ? longDate(chosen[0].date) + "までの最新開示" : "Latest disclosures through " + longDate(chosen[0].date);
  }

  function ownershipDetail(row) {
    var ratio = Number(row.current_holding_ratio || 0).toFixed(2).replace(/\.00$/, "");
    var label = row.summary_en && row.summary_en.label ? row.summary_en.label : "";
    if (isJa) {
      var jpLabel = row.summary_ja && row.summary_ja.label ? row.summary_ja.label : "";
      return (row.filer_raw_name || "新たな株主") + "が" + ratio + "%を新規保有" + (jpLabel ? "。保有目的は" + jpLabel + "。" : "。");
    }
    var owner = String(row.filer_name_en || "").trim();
    var subject = owner && owner.length <= 48 ? owner : "A new shareholder";
    return subject + " reported a new " + ratio + "% position" + (label ? " with " + label.toLowerCase() + "." : ".");
  }

  function renderOwnership(payload) {
    if (!ownershipList || !payload || !Array.isArray(payload.rows)) return;
    var chosen = payload.rows.filter(function (row) {
      return row.issuer_code && (row.issuer_name || row.issuer_name_en) && Number(row.current_holding_ratio) >= 5;
    }).slice(0, 4);
    if (!chosen.length) return;

    var fragment = document.createDocumentFragment();
    chosen.forEach(function (row) {
      var ratio = Number(row.current_holding_ratio || 0).toFixed(2).replace(/\.00$/, "") + "%";
      fragment.appendChild(makeSignalRow({
        href: isJa ? "/compounders/active-investors/" : "/en/compounders/active-investors/",
        date: row.filing_date,
        name: (isJa ? row.issuer_name : row.issuer_name_en) || row.issuer_name || row.issuer_name_en,
        ticker: row.issuer_code,
        detail: trimText(ownershipDetail(row), isJa ? 78 : 120),
        tag: ratio
      }));
    });
    ownershipList.replaceChildren(fragment);
    var asof = document.querySelector('[data-feed-asof="ownership"]');
    if (asof) asof.textContent = isJa ? longDate(chosen[0].filing_date) + "までの新規保有" : "Latest new positions through " + longDate(chosen[0].filing_date);
  }

  if (capitalList && window.fetch) {
    capitalList.setAttribute("aria-busy", "true");
    fetch("/compounders/feed/data/hero.json", { credentials: "same-origin" })
      .then(function (response) { if (!response.ok) throw new Error("capital feed"); return response.json(); })
      .then(renderCapital)
      .catch(function () { /* Keep the dated HTML fallback. */ })
      .then(function () { capitalList.setAttribute("aria-busy", "false"); });
  }

  if (ownershipList && window.fetch) {
    ownershipList.setAttribute("aria-busy", "true");
    fetch("/compounders/active-investors/data/new5_home.json", { credentials: "same-origin" })
      .then(function (response) { if (!response.ok) throw new Error("ownership feed"); return response.json(); })
      .then(renderOwnership)
      .catch(function () { /* Keep the dated HTML fallback. */ })
      .then(function () { ownershipList.setAttribute("aria-busy", "false"); });
  }
})();
