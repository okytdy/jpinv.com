"""
JII Compounders - LLM cost cage with $10/month hard cap.

Multi-layer defense:
  L1  per-call envelope (max input chars, max output tokens, max estimated cost)
  L2  daily cap (max calls per JST day)
  L3  month-to-date ledger with soft warn at $7 and hard stop at $9
  L4  persistent doc_id cache (separate file; see pdf_enricher)

Ledger lives at tools/llm_ledger.json (committed). Reset is idempotent on month
rollover. Designed so the worst-possible runaway path still stays under $10/month.

Public API:
    BudgetLedger.load(path) -> BudgetLedger
    .can_call(estimated_cost_usd) -> (bool, reason)
    .record_call(actual_cost_usd) -> None
    .status() -> dict
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
from pathlib import Path
from typing import Tuple

LOG = logging.getLogger(__name__)
JST = _dt.timezone(_dt.timedelta(hours=9))

# Hard policy values - do not weaken without an explicit user decision.
HARD_CAP_USD = 9.00         # stop completely at $9 MTD
SOFT_CAP_USD = 7.00         # warn at $7 MTD
DAILY_CALL_CAP = 50         # max LLM calls per JST day
MAX_INPUT_CHARS = 5_000     # truncate PDFs before sending
MAX_OUTPUT_TOKENS = 900     # ~$0.0045 ceiling per call at Haiku output rate
MAX_PER_CALL_USD = 0.012    # belt-and-suspenders per-call clip


class BudgetLedger:
    def __init__(self, path: Path, data: dict) -> None:
        self._path = path
        self._data = data

    @classmethod
    def load(cls, path: Path) -> "BudgetLedger":
        if not path.exists():
            data = cls._fresh_ledger()
        else:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        ledger = cls(path, data)
        ledger.maybe_reset_month()
        return ledger

    @staticmethod
    def _fresh_ledger() -> dict:
        now = _dt.datetime.now(JST)
        return {
            "month": now.strftime("%Y-%m"),
            "mtd_cost_usd": 0.0,
            "calls_this_month": 0,
            "by_day": {},
            "last_call_iso": "",
            "hard_cap_usd": HARD_CAP_USD,
            "soft_cap_usd": SOFT_CAP_USD,
            "daily_call_cap": DAILY_CALL_CAP,
            "tripped_soft": False,
        }

    def maybe_reset_month(self) -> None:
        now = _dt.datetime.now(JST)
        cur = now.strftime("%Y-%m")
        if self._data.get("month") != cur:
            archive = self._data.copy()
            self._data = self._fresh_ledger()
            self._data["previous_month_archive"] = {
                "month": archive.get("month"),
                "mtd_cost_usd": archive.get("mtd_cost_usd"),
                "calls_this_month": archive.get("calls_this_month"),
            }
            self._flush()

    def can_call(self, estimated_cost_usd: float) -> Tuple[bool, str]:
        if estimated_cost_usd > MAX_PER_CALL_USD:
            return False, f"per-call estimate ${estimated_cost_usd:.4f} > cap ${MAX_PER_CALL_USD:.4f}"
        today = _dt.datetime.now(JST).strftime("%Y-%m-%d")
        today_calls = int(self._data["by_day"].get(today, 0))
        if today_calls >= DAILY_CALL_CAP:
            return False, f"daily cap reached: {today_calls}/{DAILY_CALL_CAP}"
        if self._data["mtd_cost_usd"] + estimated_cost_usd > HARD_CAP_USD:
            return False, f"hard cap reached: ${self._data['mtd_cost_usd']:.2f} MTD"
        return True, "ok"

    def record_call(self, actual_cost_usd: float) -> None:
        now = _dt.datetime.now(JST)
        today = now.strftime("%Y-%m-%d")
        self._data["mtd_cost_usd"] = round(float(self._data["mtd_cost_usd"]) + float(actual_cost_usd), 6)
        self._data["calls_this_month"] = int(self._data["calls_this_month"]) + 1
        self._data["by_day"][today] = int(self._data["by_day"].get(today, 0)) + 1
        self._data["last_call_iso"] = now.isoformat(timespec="seconds")
        if (not self._data.get("tripped_soft")) and self._data["mtd_cost_usd"] >= SOFT_CAP_USD:
            LOG.warning("LLM budget: SOFT CAP TRIPPED at $%.2f MTD - approaching $%.2f hard cap",
                        self._data["mtd_cost_usd"], HARD_CAP_USD)
            self._data["tripped_soft"] = True
        self._flush()

    def status(self) -> dict:
        return dict(self._data)

    def _flush(self) -> None:
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, sort_keys=True)
            f.write("\n")


def estimate_cost_usd(input_tokens: int, output_tokens: int,
                       input_per_M: float = 1.0, output_per_M: float = 5.0) -> float:
    """Estimate cost in USD for an Anthropic call (default: Haiku 4.5 pricing).

    Per Anthropic published rates (May 2026): Haiku 4.5 ~ $1/M input, $5/M output.
    We over-estimate by 10% as a safety margin.
    """
    raw = (input_tokens / 1_000_000) * input_per_M + (output_tokens / 1_000_000) * output_per_M
    return round(raw * 1.10, 6)
