#!/usr/bin/env python3
"""Rebuild the seven-gate Compounders universe from current local market data.

Run after the shared 5 Capital refresh. A complete EDINET DB broad screen is
fetched on each run; filing-date valuation fields are used only to recover
filing-derived book equity, free cash flow, and net debt before repricing them.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import html
import json
import math
import re
import sys
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
JII = REPO.parents[3]
ENGINE = JII / "5 Capital" / "_engine"
JQ = JII / "5 Capital" / "_J-Quants"
EDB_CACHE = JII / "5 Capital" / "_data" / "edinetdb_debt_cash.json"
OUTPUT = REPO / "tools" / "_compounder_universe"
CONDITIONS = [
    {"metric": "operating-margin", "operator": "gte", "value": 15},
    {"metric": "equity-ratio", "operator": "gte", "value": 40},
    {"metric": "revenue-cagr-3y", "operator": "gte", "value": 5},
    {"metric": "operating-income", "operator": "gte", "value": 1},
    {"metric": "total-assets", "operator": "gte", "value": 1},
    {"metric": "current-liabilities", "operator": "gte", "value": 0},
    {"metric": "ev", "operator": "gte", "value": -999999999},
    {"metric": "fcf-yield", "operator": "gte", "value": -999},
    {"metric": "pbr", "operator": "gte", "value": 0},
    {"metric": "market-cap", "operator": "gte", "value": 1},
]


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def excluded(path):
    if not path.exists():
        raise RuntimeError(f"Required exclusion file missing: {path}")
    codes = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        code = line.split("#", 1)[0].strip().upper()
        if code:
            codes.add(code[:4])
    return codes


def _screen_page(edinetdb, conditions):
    companies = []
    offset = 0
    as_of = ""
    while True:
        payload = edinetdb.screener(
            conditions=json.dumps(conditions, separators=(",", ":")),
            sort="operating-margin", order="desc", limit=500, offset=offset,
        )
        as_of = max(as_of, str((payload.get("meta") or {}).get("data_as_of") or ""))
        data = payload.get("data") or {}
        batch = data.get("companies") or []
        companies.extend(batch)
        offset += len(batch)
        total = int(data.get("total") or 0)
        if not batch or offset >= total:
            if offset != total:
                raise RuntimeError(f"Incomplete EDINET DB page: {offset}/{total}")
            break
    return as_of, companies


def fetch_screen():
    sys.path.insert(0, str(ENGINE))
    import edinetdb

    # The three financial gates are the only valid prefilter. Requiring a
    # filing-date market cap would lose recent IPOs that can pass today.
    base_date, base = _screen_page(edinetdb, CONDITIONS[:3])
    full_date, full = _screen_page(edinetdb, CONDITIONS)
    seen = {r["secCode"] for r in full}
    missing = [r for r in base if r["secCode"] not in seen]
    for r in missing:
        payload = edinetdb.company(r["edinetCode"])
        r["_fallback_latest_financials"] = (payload.get("data") or {}).get("latest_financials")
    return {"as_of": min(base_date, full_date), "total": len(base),
            "standard_count": len(full), "supplemental_count": len(missing),
            "companies": full + missing}


def latest_local_close():
    files = sorted((JQ / "daily").glob("????-??-??.csv.gz"))
    if not files:
        raise RuntimeError("No J-Quants Standard daily close cache")
    path = files[-1]
    close_date = path.name[:10]
    closes = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            value = number(row.get("C"))
            if value is not None and value > 0:
                closes[str(row.get("Code") or "")[:4]] = value
    return close_date, closes


def evaluate(snapshot, *, run_date):
    close_date, closes = latest_local_close()
    if (dt.date.fromisoformat(run_date) - dt.date.fromisoformat(close_date)).days > 4:
        raise RuntimeError(f"Latest close is stale: {close_date}")
    if (dt.date.fromisoformat(run_date) - dt.date.fromisoformat(snapshot["as_of"])).days > 3:
        raise RuntimeError(f"EDINET DB screen is stale: {snapshot['as_of']}")

    share_path = JQ / "shares_consolidated.json"
    forecast_path = JQ / "forward_fundamentals.json"
    for cache_path in (share_path, forecast_path):
        updated = dt.datetime.fromtimestamp(cache_path.stat().st_mtime).date().isoformat()
        if updated < close_date:
            raise RuntimeError(f"J-Quants Standard cache is older than the close: {cache_path.name} ({updated})")
    shares = load_json(share_path)
    forecasts = load_json(forecast_path)
    supplements = load_json(REPO / "tools" / "compounder_universe_supplements.json")
    debt_cache = load_json(EDB_CACHE)
    debt = debt_cache.get("records") or {}
    known_ja = load_json(JII / "4 Delivery" / "5A JII Compounder Profiles" /
                         "1 Screen & Watchlist" / "universe_refresh" / "data" / "jp_strings.json")
    excludes = excluded(JII / "_Context" / "restricted_tickers.txt")
    excludes |= excluded(JII / "4 Delivery" / "5A JII Compounder Profiles" /
                         "1 Screen & Watchlist" / "universe_refresh" / "going_private_tickers.txt")

    passes, rejected = [], []
    for c in snapshot["companies"]:
        sec = str(c.get("secCode") or "")
        ticker = sec[:4]
        if len(ticker) != 4 or ticker in excludes or c.get("is_delisted") or c.get("listing_status") == "delisted":
            continue
        filing = c.get("_fallback_latest_financials")
        if filing:
            c = dict(c)
            for source, target in (("operating_income", "operating-income"),
                                   ("total_assets", "total-assets"),
                                   ("current_liabilities", "current-liabilities")):
                value = number(filing.get(source))
                c[target] = value / 1_000_000 if value is not None else None
        n = {key: number(c.get(key)) for key in (
            "operating-income", "total-assets", "current-liabilities", "market-cap",
            "ev", "pbr", "fcf-yield", "operating-margin", "equity-ratio", "revenue-cagr-3y")}
        forecast = forecasts.get(ticker) or {}
        forecast_op = number(forecast.get("forecast_op"))
        price, share_count = closes.get(ticker), number(shares.get(ticker))
        supplement = supplements.get(ticker) or {}
        supplement_current = bool(supplement and run_date <= supplement["valid_through"])
        # A completed cancellation can make the last financial-summary share
        # count stale even when the cache itself was refreshed today. Keep a
        # dated issuer-source correction active until the next report catches up.
        if supplement.get("share_override_after_action"):
            if supplement_current:
                share_count = number(supplement.get("shares_ex_treasury"))
            else:
                share_count = None
        if supplement_current and (forecast_op is None or forecast_op <= 0):
            forecast_op = number(supplement.get("forecast_op_yen"))
        if supplement_current and not share_count:
            share_count = number(supplement.get("shares_ex_treasury"))
        reasons = []
        if not price or not share_count:
            reasons.append("missing_close_or_shares")
        if not forecast_op or forecast_op <= 0:
            reasons.append("missing_positive_forward_EBIT")
        required = ("operating-income", "total-assets", "current-liabilities",
                    "operating-margin", "equity-ratio", "revenue-cagr-3y")
        if not all(n[key] is not None for key in required):
            reasons.append("missing_filing_metric")
        if not filing and not all(n[key] is not None for key in ("market-cap", "ev", "pbr", "fcf-yield")):
            reasons.append("missing_filing_valuation_inputs")
        if reasons:
            rejected.append({"ticker": ticker, "reason": reasons})
            continue
        capital_employed = n["total-assets"] - n["current-liabilities"]
        if capital_employed <= 0 or (not filing and n["market-cap"] <= 0):
            rejected.append({"ticker": ticker, "reason": ["invalid_filing_denominator"]})
            continue
        mc_myen = price * share_count / 1_000_000
        if filing:
            loans_yen = sum(number(filing.get(key)) or 0 for key in
                            ("short_term_loans", "current_portion_lt_loans", "long_term_loans"))
            cash_yen = number(filing.get("cash"))
            book_yen = number(filing.get("shareholders_equity")) or number(filing.get("net_assets"))
            cf_op_yen = number(filing.get("cf_operating"))
            cf_inv_yen = number(filing.get("cf_investing"))
            if cash_yen is None or not book_yen or cf_op_yen is None or cf_inv_yen is None:
                rejected.append({"ticker": ticker, "reason": ["missing_supplemental_filing_inputs"]})
                continue
            filing_net_debt = (loans_yen - cash_yen) / 1_000_000
            book_equity_myen = book_yen / 1_000_000
            fcf_myen = (cf_op_yen + cf_inv_yen) / 1_000_000
        else:
            # EDINET DB EV and market cap share the annual filing basis.
            filing_net_debt = n["ev"] - n["market-cap"]
            book_equity_myen = n["market-cap"] / n["pbr"] if n["pbr"] > 0 else 0
            fcf_myen = n["fcf-yield"] / 100 * n["market-cap"]
        current_ev = mc_myen + filing_net_debt
        roce = n["operating-income"] / capital_employed * 100
        ev_ebit = current_ev / (forecast_op / 1_000_000)
        pbr = mc_myen / book_equity_myen if book_equity_myen > 0 else None
        fcf_yield = fcf_myen / mc_myen * 100
        gates = {
            "roce": roce >= 15,
            "ev_ebit_forward": 2 <= ev_ebit <= 12,
            "operating_margin": n["operating-margin"] >= 15,
            "equity_ratio": n["equity-ratio"] >= 40,
            "revenue_cagr_3y": n["revenue-cagr-3y"] >= 5,
            "pbr": pbr is not None and pbr >= 1,
            "fcf_yield": fcf_yield >= 4,
        }
        if not all(gates.values()):
            rejected.append({"ticker": ticker, "reason": [key for key, ok in gates.items() if not ok]})
            continue
        debt_record = debt.get(ticker) or {}
        row = {
            "ticker": ticker,
            "name_ja": (known_ja.get(ticker) or {}).get("name_ja") or c.get("filerName") or "",
            "name_en": c.get("name_en") or c.get("companyNameEn") or "",
            "sector_ja": (known_ja.get(ticker) or {}).get("industry_ja") or c.get("industry") or "",
            "price_jpy": price,
            "shares_ex_treasury": int(share_count),
            "market_cap_myen": mc_myen,
            "roce_pct": roce,
            "ev_ebit_forward": ev_ebit,
            "operating_margin_pct": n["operating-margin"],
            "equity_ratio_pct": n["equity-ratio"],
            "revenue_cagr_3y_pct": n["revenue-cagr-3y"],
            "pbr": pbr,
            "fcf_yield_pct": fcf_yield,
            "composite": roce / ev_ebit,
            "forecast_date": forecast.get("forecast_date") or (supplement.get("forecast_date") if supplement_current else None),
            "forecast_oi_myen": forecast_op / 1_000_000,
            "forecast_source_url": supplement.get("forecast_source_url") if supplement_current else None,
            "share_source_url": supplement.get("share_source_url") if supplement_current else None,
            "fiscal_year": c.get("fiscalYear"),
            "edinet_code": c.get("edinetCode"),
            "net_debt_myen": filing_net_debt,
            "debt_cache_fiscal_year": debt_record.get("fiscal_year"),
            "filing_input_basis": "direct_filing" if filing else "screener_rebased",
            "filing_submit_date": filing.get("submit_date") if filing else None,
            "filing_source_url": filing.get("edinet_view_url") if filing else None,
            "gates": gates,
        }
        passes.append(row)
    passes.sort(key=lambda r: (-r["market_cap_myen"], r["ticker"]))
    return {
        "run_date": run_date,
        "close_date": close_date,
        "edinet_as_of": snapshot["as_of"],
        "broad_pool": snapshot["total"],
        "pass_count": len(passes),
        "rejected_count": len(rejected),
        "passes": passes,
        "rejected": rejected,
    }


def verify_forward_periods(result):
    """Fail closed when a cached company forecast covers an ended fiscal year."""
    sys.path.insert(0, str(ENGINE))
    import jq_v2

    close = result["close_date"]
    cache_path = OUTPUT / f"forecast_periods_{result['run_date']}.json"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cache = load_json(cache_path) if cache_path.exists() else {}
    verified, expired = [], []
    for candidate in result["passes"]:
        ticker = candidate["ticker"]
        cached_op = candidate["forecast_oi_myen"] * 1_000_000
        cached = cache.get(ticker)
        if cached and cached.get("close") == close and cached.get("cached_op") == cached_op:
            matches = cached["matches"]
        else:
            try:
                rows = jq_v2.fins_summary(code=ticker + "0")
            except RuntimeError as error:
                if "HTTP 429" not in str(error):
                    raise
                time.sleep(70)
                rows = jq_v2.fins_summary(code=ticker + "0")
            matches = []
            for row in rows:
                disclosed = str(row.get("DiscDate") or "")[:10]
                if not disclosed or disclosed > close:
                    continue
                for op_key, period_key in (("NxFOP", "NxtFYEn"), ("FOP", "CurFYEn")):
                    op = number(row.get(op_key))
                    period = str(row.get(period_key) or "")[:10]
                    if op is not None and period and abs(op - cached_op) <= max(1, cached_op * 1e-8):
                        matches.append((disclosed, period))
            cache[ticker] = {"close": close, "cached_op": cached_op, "matches": matches}
            temporary = cache_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            temporary.replace(cache_path)
            time.sleep(2.5)
        if not matches:
            expired.append({"ticker": ticker, "reason": ["unverified_forward_forecast_period"]})
            continue
        disclosed, period = max(matches)
        if period <= close:
            expired.append({"ticker": ticker, "reason": ["forecast_fiscal_year_ended"],
                            "forecast_period_end": period})
            continue
        candidate["forecast_period_end"] = period
        candidate["forecast_period_verified_at"] = result["run_date"]
        verified.append(candidate)
    result["passes"] = verified
    result["pass_count"] = len(verified)
    result["rejected"].extend(expired)
    result["rejected_count"] = len(result["rejected"])
    result["forward_period_rejections"] = expired
    return result


def export_watchlist(result):
    target = REPO / "_watchlist_v4_compounders.csv"
    with target.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        prior = {r["sec_code"][:4]: r for r in reader}
    if not fields or "sec_code" not in fields:
        raise RuntimeError("Site watchlist schema changed")
    rows = []
    for rank, r in enumerate(result["passes"], 1):
        ticker = r["ticker"]
        old = prior.get(ticker) or {}
        row = {key: "" for key in fields}
        profile = REPO / "compounders" / ticker
        profile_url = (f"/en/compounders/{ticker}/initiation/" if (profile / "initiation/index.html").exists()
                       else f"/en/compounders/{ticker}/" if (profile / "index.html").exists()
                       else "")
        row.update({
            "rank": rank, "sec_code": ticker + "0", "edinet_code": r["edinet_code"],
            "filer_name": r["name_ja"], "name_en": r["name_en"], "industry": r["sector_ja"],
            "screen_date_utc": result["run_date"], "quote_date": result["close_date"],
            "yfinance_ticker": ticker + ".T", "ev_ebit_basis": "forward",
            "roce_pct": f'{r["roce_pct"]:.4f}',
            "ev_ebit_forward": f'{r["ev_ebit_forward"]:.4f}',
            "opm_pct": f'{r["operating_margin_pct"]:.4f}',
            "equity_ratio_pct": f'{r["equity_ratio_pct"]:.4f}',
            "rev_cagr_3yr_pct": f'{r["revenue_cagr_3y_pct"]:.4f}',
            "pbr_current": f'{r["pbr"]:.4f}',
            "fcf_yield_current_pct": f'{r["fcf_yield_pct"]:.4f}',
            "forecast_oi_mjpy": f'{r["forecast_oi_myen"]:.4f}',
            "forecast_disclosure_date": r["forecast_date"],
            "fy_end": old.get("fy_end", ""),
            "current_price_jpy": r["price_jpy"],
            "shares_issued": r["shares_ex_treasury"],
            "current_mc_mjpy": f'{r["market_cap_myen"]:.4f}',
            "current_ev_mjpy": f'{r["market_cap_myen"] + r["net_debt_myen"]:.4f}',
            "composite_score": f'{r["composite"]:.4f}',
            "status": "active", "published_url": profile_url,
        })
        rows.append(row)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_pages(result):
    sector_en = {
        "ガラス・土石製品": "Glass & Ceramics", "ゴム製品": "Rubber Products",
        "サービス業": "Services", "その他金融業": "Other Financial Services",
        "その他製品": "Other Products", "医薬品": "Pharmaceuticals",
        "卸売業": "Wholesale Trade", "化学": "Chemicals", "機械": "Machinery",
        "建設業": "Construction", "小売業": "Retail Trade",
        "証券、商品先物取引業": "Securities & Commodity Futures",
        "情報・通信業": "Information & Communication", "食料品": "Food Products",
        "精密機器": "Precision Instruments", "繊維製品": "Textiles & Apparel",
        "電気機器": "Electric Appliances", "不動産業": "Real Estate",
        "輸送用機器": "Transportation Equipment",
    }
    rows = result["passes"]
    if not rows or len(rows) != result["pass_count"] or len({r["ticker"] for r in rows}) != len(rows):
        raise RuntimeError("Invalid qualified roster")
    if any(not all(r["gates"].values()) for r in rows):
        raise RuntimeError("A rendered company fails a numeric gate")
    date, close = result["run_date"], result["close_date"]
    close_day = dt.date.fromisoformat(close)
    run_day = dt.date.fromisoformat(date)
    close_ja = f"{close_day.year}年{close_day.month}月{close_day.day}日"
    run_ja = f"{run_day.year}年{run_day.month}月{run_day.day}日"

    def row_markup(r, rank, lang):
        ticker = r["ticker"]
        link = REPO / ("en/compounders" if lang == "en" else "compounders") / ticker
        rel = "initiation/" if (link / "initiation/index.html").exists() else ""
        ticker_html = (f'<a href="/{"en/" if lang == "en" else ""}compounders/{ticker}/{rel}">{ticker}</a>'
                       if (link / "index.html").exists() or rel else ticker)
        name = html.escape(r["name_en"] if lang == "en" else r["name_ja"])
        sector = html.escape(sector_en.get(r["sector_ja"], r["sector_ja"]) if lang == "en" else r["sector_ja"])
        mc = r["market_cap_myen"] / 1000
        if lang == "en":
            mc_text = f"¥{mc:,.0f}bn" if mc >= 10 else f"¥{mc:.1f}bn"
        else:
            oku = r["market_cap_myen"] / 100
            mc_text = (f"{oku / 10000:.2f}兆円" if oku >= 10000 else
                       f"{oku:,.0f}億円" if oku >= 100 else f"{oku:,.1f}億円")
        cells = [rank, ticker_html, name, sector, mc_text,
                 f'{r["roce_pct"]:.1f}%', f'{r["ev_ebit_forward"]:.1f}x',
                 f'{r["operating_margin_pct"]:.1f}%', f'{r["equity_ratio_pct"]:.1f}%',
                 f'{r["revenue_cagr_3y_pct"]:.1f}%', f'{r["pbr"]:.1f}x',
                 f'{r["fcf_yield_pct"]:.1f}%', f'{r["composite"]:.1f}',
                 "—"]
        classes = ["cell-rank", "cell-tk", "cell-name", "cell-ind"] + ["cell-num"] * 9 + ["cell-status status-active"]
        data = (f'data-status="active" data-mc="{r["market_cap_myen"]:.6f}" '
                f'data-roce="{r["roce_pct"]:.6f}" data-evebit="{r["ev_ebit_forward"]:.6f}" '
                f'data-pbr="{r["pbr"]:.6f}" data-fcfy="{r["fcf_yield_pct"]:.6f}" '
                f'data-score="{r["composite"]:.6f}" data-sec="{ticker}0"')
        body = "\n".join(f'      <td class="{cls}">{value}</td>' for cls, value in zip(classes, cells))
        return f"    <tr {data}>\n{body}\n    </tr>\n"

    for lang, relative in (("ja", "compounders/universe/index.html"),
                           ("en", "en/compounders/universe/index.html")):
        path = REPO / relative
        source = path.read_text(encoding="utf-8")
        en = lang == "en"
        title = "Screen-qualified" if en else "該当銘柄"
        criteria = ("Screen criteria (all seven; price-based metrics use the latest close): ROCE ≥15% · "
                    "company-forecast EV/EBIT 2–12x · operating margin ≥15% · equity ratio ≥40% · "
                    "3-year revenue CAGR ≥5% · P/B ≥1.0x · FCF yield ≥4%" if en else
                    "抽出条件：ROCE 15%以上・EV/EBIT（会社予想営業利益ベース）2〜12倍・"
                    "営業利益率 15%以上・自己資本比率 40%以上・売上高の年平均成長率（過去3年）5%以上・"
                    "PBR 1.0倍以上・FCF利回り 4%以上")
        headers = (["#", "Code", "Company", "Sector", "Market Cap", "ROCE", "EV/EBIT (company forecast)",
                    "Op Margin", "Equity Ratio", "Rev CAGR (3y)", "P/B", "FCF Yield", "Composite", "Latest Signal"]
                   if en else
                   ["#", "証券コード", "企業名", "業種", "時価総額", "ROCE", "EV/EBIT（会社予想）",
                    "営業利益率", "自己資本比率", "売上高年平均成長率（3年）", "PBR", "FCF利回り",
                    "ROCE÷EV/EBIT", "直近の開示"])
        th = "".join(f'<th class="cell-num">{v}</th>' if 4 <= i <= 12 else f"<th>{v}</th>"
                     for i, v in enumerate(headers))
        body = "".join(row_markup(r, i + 1, lang) for i, r in enumerate(rows))
        asof = (f"As of {date} · prices at the {close} close" if en else
                f"{close_ja}終値時点（{run_ja}更新）")
        chip = f"Screen-qualified ({len(rows)})" if en else f"{len(rows)}銘柄"
        count_label = f"({len(rows)})" if en else f"（{len(rows)}銘柄）"
        controls = (f'<div class="controls"><div class="ctrl-group"><span class="ctrl-label">'
                    f'{"Showing:" if en else "該当銘柄："}</span><span class="btn lane-chip">'
                    f'{chip}</span></div><div class="ctrl-group" style="margin-left:auto;">'
                    f'<span class="ctrl-label">{"Sort:" if en else "並べ替え："}</span>'
                    f'<button class="btn sort-trigger active" data-sort="mc" data-dir="desc">{"Market Cap" if en else "時価総額"}</button>'
                    f'<button class="btn sort-trigger" data-sort="score" data-dir="desc">{"Composite" if en else "ROCE÷EV/EBIT"}</button>'
                    '<button class="btn sort-trigger" data-sort="roce" data-dir="desc">ROCE</button>'
                    '<button class="btn sort-trigger" data-sort="evebit" data-dir="asc">EV/EBIT</button>'
                    f'<button class="btn sort-trigger" data-sort="pbr" data-dir="desc">{"P/B" if en else "PBR"}</button>'
                    f'<button class="btn sort-trigger" data-sort="fcfy" data-dir="desc">{"FCF Yield" if en else "FCF利回り"}</button>'
                    '</div></div>')
        block = ("<!-- UNIVERSE:LANES START (generated by refresh_compounder_universe.py) -->\n"
                 '<style>.lane { margin-top:4px; }.lane-head { padding:30px 0 12px; }'
                 '.lane-title { font-family:var(--serif); font-size:21px; font-weight:400; '
                 'color:var(--ink-mid); margin:0 0 8px; }.lane-title .lane-count { '
                 'font-family:var(--mono); font-size:13px; color:var(--accent-deep); margin-left:6px; }'
                 '.lane-criteria { font-family:var(--mono); font-size:11px; color:var(--text-mid); '
                 'margin:0 0 4px; line-height:1.8; max-width:960px; }.lane-asof { '
                 'font-family:var(--mono); font-size:10px; color:var(--text-dim); margin:0 0 2px; '
                 'text-transform:uppercase; }.lane table { border-top:1px solid var(--rule); }'
                 '.table-scroll { overflow-x:auto; overscroll-behavior-inline:contain; }'
                 '.table-scroll table { min-width:1450px; }.table-scroll .cell-name { min-width:160px; }'
                 '.lane-chip { border-color:var(--accent); color:var(--accent-deep); }</style>\n'
                 + controls + "\n" + f'<section class="lane" id="lane-screen"><div class="lane-head">'
                 f'<h2 class="lane-title">{title}<span class="lane-count">{count_label}</span></h2>'
                 f'<p class="lane-criteria">{criteria}</p><p class="lane-asof">{asof}</p></div>\n'
                 f'<div class="table-scroll"><table id="universe" class="universe-table">'
                 f'<thead><tr>{th}</tr></thead><tbody>\n'
                 + body + '</tbody></table></div></section>\n<!-- UNIVERSE:LANES END -->')
        pattern = re.compile(r"<!-- UNIVERSE:LANES START.*?<!-- UNIVERSE:LANES END -->", re.S)
        if len(pattern.findall(source)) != 1:
            raise RuntimeError(f"Universe marker count changed: {path}")
        source = pattern.sub(lambda _: block, source)
        if en:
            source = re.sub(
                r'(    <h1>[^<]*</h1>\s*)<p>.*?</p>',
                lambda match: match.group(1) +
                '<p>Tokyo Stock Exchange companies meeting all seven screening criteria. '
                'Price-based metrics use the latest close. Compare valuation, returns on capital, '
                'growth, and free cash flow. <a href="/en/compounders/methodology/">Methodology →</a></p>',
                source, count=1, flags=re.S)
            source = re.sub(r'    <span>Last refreshed .*?</span>',
                            f'    <span>Last refreshed {date}. Market cap uses the {close} close and shares excluding treasury. '
                            'Every listed name passes all seven criteria.</span>', source, count=1)
        else:
            page_title = '7条件に該当する銘柄｜JII Compounders'
            description = ('東証上場銘柄のうち、7つの条件に該当する銘柄を時価総額、'
                           '会社予想EV/EBIT、収益性、FCF利回りなどで比較できます。')
            source = re.sub(r'<title>[^<]*</title>', f'<title>{page_title}</title>', source, count=1)
            source = re.sub(r'<meta name="description" content="[^"]*">',
                            f'<meta name="description" content="{description}">', source, count=1)
            source = re.sub(r'<meta property="og:title" content="[^"]*">',
                            f'<meta property="og:title" content="{page_title}">', source, count=1)
            source = re.sub(r'<meta property="og:description" content="[^"]*">',
                            f'<meta property="og:description" content="{description}">', source, count=1)
            source = source.replace(
                '<div class="hero-eyebrow">JII COMPOUNDERS &middot; UNIVERSE</div>',
                '<div class="hero-eyebrow">JII COMPOUNDERS &middot; 銘柄一覧</div>', 1)
            source = re.sub(r'    <h1>[^<]*</h1>',
                            '    <h1>7条件に該当する銘柄</h1>', source, count=1)
            source = re.sub(
                r'(    <h1>7条件に該当する銘柄</h1>\s*)<p>.*?</p>',
                lambda match: match.group(1) +
                '<p>7つの条件に該当する東証上場銘柄を掲載しています。株価を用いる指標は直近の終値で計算し、'
                '時価総額、資本効率、成長率、フリーキャッシュフロー利回りなどを比較できます。'
                '<a href="/compounders/methodology/">6つの着眼点 →</a></p>',
                source, count=1, flags=re.S)
            source = re.sub(r'    <span>最終更新.*?</span>',
                            f'    <span>最終更新：{run_ja}。時価総額は{close_ja}の終値と'
                            '自己株式を除いた発行済株式数で算出しています。</span>', source, count=1)
        old_keys = 'const headerKeys = [null, null, null, null, "mc", "roce", "evebit", null, null, null, "fcfy", "score", null];'
        new_keys = 'const headerKeys = [null, null, null, null, "mc", "roce", "evebit", null, null, null, "pbr", "fcfy", "score", null];'
        if old_keys in source:
            source = source.replace(old_keys, new_keys, 1)
        elif new_keys not in source:
            raise RuntimeError(f"Sort script changed: {path}")
        observed = re.findall(r'data-sec="([0-9A-Z]{4})0"', source)
        if len(observed) != len(rows) or set(observed) != {r["ticker"] for r in rows}:
            raise RuntimeError(f"Rendered roster mismatch: {path}")
        path.write_text(source, encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--snapshot", type=Path, help="Use a saved complete EDINET DB response")
    parser.add_argument("--render", action="store_true", help="Update both public universe pages")
    args = parser.parse_args()
    snapshot = load_json(args.snapshot) if args.snapshot else fetch_screen()
    if len(snapshot["companies"]) != snapshot["total"]:
        raise RuntimeError("EDINET DB broad screen is incomplete")
    result = verify_forward_periods(evaluate(snapshot, run_date=args.date))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    snap_path = OUTPUT / f"edinet_screen_{args.date}.json"
    out_path = OUTPUT / f"qualified_{args.date}.json"
    snap_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.render:
        render_pages(result)
        export_watchlist(result)
    print(json.dumps({"snapshot": str(snap_path), "qualified": str(out_path),
                      "edinet_as_of": result["edinet_as_of"], "close_date": result["close_date"],
                      "broad_pool": result["broad_pool"], "pass_count": result["pass_count"]}))


if __name__ == "__main__":
    main()
