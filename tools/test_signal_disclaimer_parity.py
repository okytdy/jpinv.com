"""Check the Python producer against the Node disclosure parity gate."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import build_signal_pages as pages


class SignalDisclosureParity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('tools', 'content/compounders/articles',
                       'compounders/signals/TEST', 'en/compounders/signals/TEST'):
            (self.root / folder).mkdir(parents=True)
        shutil.copy(Path(pages.ROOT, 'tools/sync-english-research-disclaimers.mjs'),
                    self.root / 'tools')
        self.records = json.loads(Path(pages.ROOT,
            'content/compounders/disclaimer-parity.json').read_text(encoding='utf-8'))
        # Text-node escaping must also agree for ASCII quotes and HTML characters.
        for record in self.records['translations']:
            record['en'] += ' "quote" \'apostrophe\' & <example>'
        (self.root / 'content/compounders/disclaimer-parity.json').write_text(
            json.dumps(self.records, ensure_ascii=False), encoding='utf-8')
        self.source = self.root / 'compounders/signals/TEST/index.html'
        self.target = self.root / 'en/compounders/signals/TEST/index.html'
        self.source.write_text(pages.DISC_JP, encoding='utf-8')
        with patch.object(pages, 'ROOT', str(self.root)):
            self.generated = pages.source_matched_disclosure()
        self.target.write_text(self.generated, encoding='utf-8')

    def gate(self, *args):
        return subprocess.run(['node', str(self.root /
            'tools/sync-english-research-disclaimers.mjs'), *args],
            capture_output=True, text=True, encoding='utf-8')

    def test_generated_disclosure_passes_and_sync_is_idempotent(self):
        result = self.gate('--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.target.read_text(encoding='utf-8'), self.generated)

    def test_changed_english_is_rejected(self):
        self.target.write_text(self.generated.replace('IR) consultancy',
            'IR) investment advisor', 1), encoding='utf-8')
        result = self.gate('--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('English disclosures are out of sync', result.stderr)

    def test_unreviewed_japanese_is_rejected_by_both_builders(self):
        changed = pages.DISC_JP.replace('IRコンサルティング事業', '未確認事業', 1)
        self.source.write_text(changed, encoding='utf-8')
        with patch.object(pages, 'ROOT', str(self.root)), patch.object(pages, 'DISC_JP', changed):
            with self.assertRaisesRegex(ValueError, 'Japanese disclosure changed'):
                pages.source_matched_disclosure()
        result = self.gate('--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Japanese disclosure changed', result.stderr)


if __name__ == '__main__':
    unittest.main()
