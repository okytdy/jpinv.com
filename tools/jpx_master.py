"""
JII Compounders - JPX listed-company master lookup.

Provides a free, daily-cached bilingual ticker -> {name_en, name_jp, sector, market} map
sourced from the official JPX listed-company master:
    https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls
    https://www.jpx.co.jp/english/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_e.xls

The cache lives at tools/jpx_cache.json (committed). The cron path is pure-stdlib +
fast: no XLS download, no I/O beyond reading the JSON. Use `python tools/jpx_master.py
--refresh` to regenerate the cache (requires xlrd; once a month is plenty).

Public API:
    lookup(ticker: str) -> dict | None
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

LOG = logging.getLogger(__name__)
_CACHE_PATH = Path(__file__).resolve().parent / "jpx_cache.json"
_cache: Optional[dict] = None


def _load_cache() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    if not _CACHE_PATH.exists():
        LOG.warning("jpx_cache.json missing - lookup will return empty rows")
        _cache = {"_meta": {}, "tickers": {}}
        return _cache
    with _CACHE_PATH.open("r", encoding="utf-8") as f:
        _cache = json.load(f)
    return _cache


def lookup(ticker: str) -> Optional[dict]:
    """Return {name_en, name_jp, market_jp, market_en, sector_jp, sector_en} or None."""
    if not ticker:
        return None
    tickers = _load_cache().get("tickers", {})
    return tickers.get(str(ticker).strip())


def name_en(ticker: str, fallback: str = "") -> str:
    row = lookup(ticker) or {}
    return row.get("name_en") or fallback


def name_jp(ticker: str, fallback: str = "") -> str:
    row = lookup(ticker) or {}
    return row.get("name_jp") or fallback


def refresh() -> None:
    """Re-download both XLS files and rewrite the cache.

    Requires xlrd. Not called on the hot cron path - run manually monthly.
    """
    import urllib.request
    import xlrd  # type: ignore

    urls = {
        "jp": "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls",
        "en": "https://www.jpx.co.jp/english/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_e.xls",
    }
    tmpdir = Path("/tmp")
    fp = {}
    for lang, url in urls.items():
        dest = tmpdir / f"jpx_{lang}.xls"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (JII-Feed/1.0)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            dest.write_bytes(r.read())
        fp[lang] = dest

    def parse(path: Path) -> dict:
        wb = xlrd.open_workbook(str(path))
        sh = wb.sheet_by_index(0)
        out = {}
        for r in range(1, sh.nrows):
            raw = sh.cell_value(r, 1)
            ticker = str(int(raw)) if isinstance(raw, float) else str(raw).strip()
            if not ticker or ticker == "-":
                continue
            out[ticker] = {
                "name": sh.cell_value(r, 2),
                "market": sh.cell_value(r, 3),
                "sector": sh.cell_value(r, 5) if sh.ncols > 5 else "",
            }
        return out

    jp = parse(fp["jp"])
    en = parse(fp["en"])
    all_t = sorted(set(jp.keys()) | set(en.keys()))
    out = {}
    for t in all_t:
        j = jp.get(t, {})
        e = en.get(t, {})
        out[t] = {
            "name_jp": j.get("name", ""),
            "name_en": e.get("name", ""),
            "market_jp": j.get("market", ""),
            "market_en": e.get("market", ""),
            "sector_jp": (j.get("sector") or "") if j.get("sector") != "-" else "",
            "sector_en": (e.get("sector") or "") if e.get("sector") != "-" else "",
        }

    import datetime as _dt
    payload = {
        "_meta": {
            "source_urls": urls,
            "tickers_count": len(out),
            "generated_at": _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=9))).isoformat(timespec="seconds"),
            "note": "Regenerate monthly by running `python tools/jpx_master.py --refresh`.",
        },
        "tickers": out,
    }
    with _CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"wrote {_CACHE_PATH}: {len(out)} tickers")


if __name__ == "__main__":
    if "--refresh" in sys.argv:
        refresh()
    else:
        # Smoke test
        for t in ["4071", "4776", "409A", "5843", "9999"]:
            print(f"{t}: {lookup(t)}")
