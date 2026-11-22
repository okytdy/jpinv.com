from __future__ import annotations

import http.client
import io
import json
import sys
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from edinet_client import EdinetApiError, EdinetClient


class TransportRetryTests(unittest.TestCase):
    def setUp(self):
        self.client = EdinetClient("test-secret", timeout=30)
        self.sleep = self.enterContext(mock.patch("edinet_client.time.sleep"))
        self.urlopen = self.enterContext(mock.patch("edinet_client.urllib.request.urlopen"))

    @staticmethod
    def response(body):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = body
        return response

    def test_read_timeout_retries_the_complete_request(self):
        first = self.response(b"")
        first.__enter__.return_value.read.side_effect = TimeoutError("read timed out")
        body = json.dumps({"metadata": {"status": "200"},
                           "results": [{"docID": "S100TEST"}]}).encode()
        self.urlopen.side_effect = [first, self.response(body)]
        self.assertEqual(self.client.list_documents("2026-11-20"), [{"docID": "S100TEST"}])
        self.assertEqual(self.urlopen.call_count, 2)
        first.__exit__.assert_called_once()
        self.sleep.assert_called_once_with(1)
        self.assertEqual(self.urlopen.call_args.kwargs["timeout"], 30)

    def test_transient_connection_failures_recover(self):
        for error in (TimeoutError("test-secret"), ConnectionResetError("test-secret"),
                      urllib.error.URLError("test-secret"),
                      http.client.IncompleteRead(b"partial")):
            with self.subTest(error=type(error).__name__):
                self.urlopen.reset_mock()
                self.urlopen.side_effect = [error, self.response(b"complete")]
                self.assertEqual(self.client._get("https://example.test"), b"complete")
                self.assertEqual(self.urlopen.call_count, 2)

    def test_retries_stop_and_errors_are_redacted(self):
        for error in (TimeoutError("test-secret"), urllib.error.URLError("test-secret")):
            with self.subTest(error=type(error).__name__):
                self.urlopen.reset_mock()
                self.sleep.reset_mock()
                self.urlopen.side_effect = error
                with self.assertRaises(EdinetApiError) as caught:
                    self.client.list_documents("2026-11-20")
                self.assertNotIn("test-secret", str(caught.exception))
                self.assertIn("3 attempt(s)", str(caught.exception))
                self.assertEqual(self.urlopen.call_count, 3)
                self.assertEqual(self.sleep.call_args_list, [mock.call(1), mock.call(2)])

    def test_retryable_http_statuses_recover(self):
        for status in (429, 500, 502, 503, 504):
            with self.subTest(status=status):
                self.urlopen.side_effect = [urllib.error.HTTPError(
                    "https://example.test/?Subscription-Key=test-secret", status,
                    "test-secret", {}, None), self.response(b"complete")]
                self.assertEqual(self.client._get("https://example.test"), b"complete")

    def test_permanent_http_statuses_fail_immediately(self):
        for status in (400, 401, 403, 404):
            with self.subTest(status=status):
                self.urlopen.reset_mock()
                self.sleep.reset_mock()
                self.urlopen.side_effect = urllib.error.HTTPError(
                    "https://example.test/?Subscription-Key=test-secret", status,
                    "test-secret", {}, None)
                with self.assertRaises(EdinetApiError) as caught:
                    self.client.list_documents("2026-11-20")
                self.assertEqual(caught.exception.status, str(status))
                self.assertNotIn("test-secret", str(caught.exception))
                self.urlopen.assert_called_once()
                self.sleep.assert_not_called()

    def test_download_timeout_recovers_without_partial_data(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("holding.csv", b"complete CSV")
        first = self.response(b"")
        first.__enter__.return_value.read.side_effect = TimeoutError("read timed out")
        self.urlopen.side_effect = [first, self.response(buffer.getvalue())]
        self.assertEqual(self.client.fetch_document_csv("S100TEST"), b"complete CSV")


if __name__ == "__main__":
    unittest.main()
