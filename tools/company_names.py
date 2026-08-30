"""Normalize English listed-company names for public display.

JPX's English company master is authoritative for identity, but its typography
is not normalized: many rows omit spaces after commas or between a name and a
corporate suffix. Keep the source spelling and capitalization while repairing
those display-only spacing defects.
"""
from __future__ import annotations

import re


OFFICIAL_DISPLAY_OVERRIDES = {
    "2371": "Kakaku.com, Inc.",
    "3064": "MonotaRO Co., Ltd.",
    "6088": "SIGMAXYZ Holdings Inc.",
    "6533": "Orchestra Holdings Inc.",
    "6706": "DKK Co., Ltd.",
    "7743": "SEED CO., LTD.",
    "9788": "NAC CO., LTD.",
}


def normalize_company_name_en(name: str, ticker: str = "") -> str:
    """Return a clean public-display name without changing the company's identity."""
    code = str(ticker or "").strip()
    if code in OFFICIAL_DISPLAY_OVERRIDES:
        return OFFICIAL_DISPLAY_OVERRIDES[code]

    value = re.sub(r"\s+", " ", str(name or "").strip())
    if not value:
        return value

    # JPX examples include "Colan Totte.Co.,Ltd." and "HIOKI E.E.CORPORATION".
    value = re.sub(r"\.(?=(?:Co|CO)\.,)", " ", value)
    value = re.sub(
        r"\.(?=(?:Corporation|CORPORATION|Inc|INC|Ltd|LTD|Limited|LIMITED)\b)",
        ". ",
        value,
    )
    value = re.sub(r",(?=\S)", ", ", value)
    value = re.sub(r"\s+,", ",", value)
    value = re.sub(r"\s{2,}", " ", value).strip()
    value = re.sub(r"\b(Ltd|LTD|Inc|INC|Corp|CORP)$", r"\1.", value)
    return value
