from __future__ import annotations

import datetime as dt
import json
import sys
import unittest
import urllib.error
from unittest import mock
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from edinet_client import EdinetApiError, EdinetClient, parse_large_holding_csv
from new5_feed import _is_initial_new5
from build_data import normalize_filing
from rank_filers import _apply_repair_marker
from validate_refresh import business_days_after, validate


class FakeClient(EdinetClient):
    def __init__(self, body: bytes):
        super().__init__("test-key", pause=0)
        self.body = body

    def _get(self, url: str) -> bytes:
        return self.body


class EdinetClientTests(unittest.TestCase):
    def test_list_documents_accepts_successful_results(self):
        body = json.dumps({"metadata": {"status": "200"},
                           "results": [{"docID": "S100TEST"}]}).encode()
        self.assertEqual(FakeClient(body).list_documents("2026-08-28")[0]["docID"],
                         "S100TEST")

    def test_list_documents_accepts_real_empty_day(self):
        body = json.dumps({"metadata": {"status": "200"}, "results": []}).encode()
        self.assertEqual(FakeClient(body).list_documents("2026-08-30"), [])

    def test_list_documents_rejects_application_level_401(self):
        body = json.dumps({"StatusCode": 401, "message": "invalid key"}).encode()
        with self.assertRaises(EdinetApiError) as caught:
            FakeClient(body).list_documents("2026-08-28")
        self.assertEqual(caught.exception.status, "401")

    def test_list_documents_rejects_missing_results(self):
        body = json.dumps({"metadata": {"status": "200"}}).encode()
        with self.assertRaises(EdinetApiError):
            FakeClient(body).list_documents("2026-08-28")

    def test_csv_download_rejects_application_level_error(self):
        body = json.dumps({"StatusCode": 429, "message": "rate limited"}).encode()
        with self.assertRaises(EdinetApiError) as caught:
            FakeClient(body).fetch_document_csv("S100TEST")
        self.assertEqual(caught.exception.status, "429")

    def test_transport_error_does_not_expose_api_key(self):
        client = EdinetClient("top-secret")
        error = urllib.error.HTTPError(
            "https://example.test/?Subscription-Key=top-secret", 403,
            "Forbidden", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(EdinetApiError) as caught:
                client.list_documents("2026-08-28")
        self.assertNotIn("top-secret", str(caught.exception))


class ParserTests(unittest.TestCase):
    def test_member_and_group_ratios_remain_distinct(self):
        sample = (
            "要素ID\t項目名\tコンテキストID\t値\n"
            "jplvh_cor:HoldingRatioOfShareCertificatesEtc\t保有割合\t"
            "FilingDateInstant_FilerLargeVolumeHolder1Member\t0.0447\n"
            "jplvh_cor:HoldingRatioOfShareCertificatesEtc\t保有割合\t"
            "FilingDateInstant\t0.0621\n"
        )
        parsed = parse_large_holding_csv(("\ufeff" + sample).encode("utf-16"))
        self.assertEqual(parsed["current_pct"], 4.47)
        self.assertEqual(parsed["group_current_pct"], 6.21)

    def test_initial_report_classification_uses_document_identity(self):
        self.assertTrue(_is_initial_new5({
            "docTypeCode": "350", "docDescription": "大量保有報告書"}))
        self.assertFalse(_is_initial_new5({
            "docTypeCode": "360", "docDescription": "変更報告書"}))
        self.assertFalse(_is_initial_new5({
            "docTypeCode": "350", "docDescription": "訂正大量保有報告書"}))

    def test_group_ratio_drives_public_classification(self):
        filing = normalize_filing({
            "investor_id": "test-fund",
            "is_change_report": False,
            "filing_date": "2026-08-28",
            "issuer_code": "1234",
            "current_pct": 4.47,
            "group_current_pct": 6.21,
        })
        self.assertEqual(filing["current_holding_ratio"], 6.21)
        self.assertEqual(filing["member_current_holding_ratio"], 4.47)
        self.assertEqual(filing["move_type"], "new_5pct")


class TallyRepairTests(unittest.TestCase):
    def test_false_scan_markers_are_reopened_once(self):
        tally = {
            "scanned": ["2026-08-11", "2026-08-12", "2026-08-13", "2026-08-14"],
            "filers": {"E1": {"last": "2026-08-12"}},
        }
        self.assertEqual(_apply_repair_marker(tally, "2026-08-12"), 2)
        self.assertEqual(tally["scanned"], ["2026-08-11", "2026-08-12"])
        self.assertEqual(_apply_repair_marker(tally, "2026-08-12"), 0)

    def test_repair_refuses_possible_double_count(self):
        tally = {
            "scanned": ["2026-08-13"],
            "filers": {"E1": {"last": "2026-08-13"}},
        }
        with self.assertRaises(RuntimeError):
            _apply_repair_marker(tally, "2026-08-12")


class FreshnessTests(unittest.TestCase):
    def test_business_day_age_skips_weekend(self):
        self.assertEqual(business_days_after(dt.date(2026, 8, 28),
                                             dt.date(2026, 8, 31)), 1)

    def test_validation_rejects_false_fresh_feed(self):
        feed = {
            "meta": {
                "source_status": "ok",
                "rows_count": 1,
                "latest_filing_date": "2026-08-12",
                "ingestion": {"documents_seen": 10},
            },
            "rows": [{"id": "edinet-S100OLD", "filing_date": "2026-08-12"}],
        }
        errors = validate(feed, today=dt.date(2026, 8, 31),
                          max_stale_business_days=3)
        self.assertTrue(any("business days old" in error for error in errors))

    def test_validation_accepts_recent_feed(self):
        feed = {
            "meta": {
                "source_status": "ok",
                "rows_count": 1,
                "latest_filing_date": "2026-08-28",
                "ingestion": {"documents_seen": 200},
            },
            "rows": [{"id": "edinet-S100NEW", "filing_date": "2026-08-28"}],
        }
        self.assertEqual(validate(feed, today=dt.date(2026, 8, 31),
                                  max_stale_business_days=3), [])


if __name__ == "__main__":
    unittest.main()
