"""Install JII's approved conflicts-and-positions disclosure on every research page.

The rewrite is intentionally idempotent: old conflicts paragraphs and a prior false
statement about JII having no investment opinions are removed before the approved
paragraph for the page language is inserted.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DISCLOSURE_JA = (
    '<p><b>利益相反に関する開示。</b> JII、その役員および関係者は、JIIの調査レポートで取り上げる企業の有価証券を保有せず、売買も行いません。'
    'JIIが対象企業から有償で業務を受託している場合は、その事実を該当するレポートで開示します。'
    'JIIが公表する情報は情報提供を目的とするものであり、投資助言や特定の有価証券の売買を勧めるものではありません。</p>'
)

DISCLOSURE_EN = (
    '<p><b>Conflicts of interest.</b> JII, its officers, and related parties do not hold or trade securities of companies covered in JII research. '
    'If JII has a paid engagement with a company covered in a publication, that relationship is disclosed in the relevant publication. '
    "JII's publications are for informational purposes only and do not constitute investment advice or a recommendation to buy or sell any security.</p>"
)

SECTION_RE = re.compile(r'<section class="disclaimer".*?</section>', re.DOTALL)
PUBLICATION_NOTE_RE = re.compile(r'<section class="publication-note".*?</section>', re.DOTALL)
PARAGRAPH_RE = re.compile(r'<p(?:\s[^>]*)?>.*?</p>', re.DOTALL)
OLD_CONFLICT_MARKERS = (
    '利益相反および保有状況',
    '利益相反およびポジション',
    '利益相反・ポジション',
    '利益相反に関する開示。',
    'Conflicts &amp; positions.',
    'Conflicts & positions.',
    'Conflicts of interest and positions.',
    'Conflicts of interest.',
)
FALSE_OPINION_RE = re.compile(
    r'\s*JII does not have an investment opinion on any security discussed\.',
    re.IGNORECASE,
)
FALSE_OPINION_JA_RE = re.compile(
    r'\s*JII\s*は[^。]*投資意見[^。]*(?:持ちません|有しません|有していません)。'
)


def rewrite_disclaimer(section: str, disclosure: str, note_class: str) -> str:
    def remove_old_conflict(match: re.Match[str]) -> str:
        paragraph = match.group(0)
        return '' if any(marker in paragraph for marker in OLD_CONFLICT_MARKERS) else paragraph

    section = PARAGRAPH_RE.sub(remove_old_conflict, section)
    section = FALSE_OPINION_RE.sub('', section)
    section = FALSE_OPINION_JA_RE.sub('', section)

    note = re.search(rf'<p class="{note_class}"', section)
    insertion = '  ' + disclosure + '\n'
    if note:
        return section[: note.start()] + insertion + section[note.start() :]

    closing_divs = [match.start() for match in re.finditer(r'</div>', section)]
    if len(closing_divs) < 2:
        raise ValueError('Disclaimer section has no expected closing wrapper')
    closing = closing_divs[-2]
    return section[:closing] + insertion + section[closing:]


def rewrite_publication_note(section: str, disclosure: str) -> str:
    def remove_old_conflict(match: re.Match[str]) -> str:
        paragraph = match.group(0)
        return '' if any(marker in paragraph for marker in OLD_CONFLICT_MARKERS) else paragraph

    section = PARAGRAPH_RE.sub(remove_old_conflict, section)
    section = FALSE_OPINION_RE.sub('', section)
    section = FALSE_OPINION_JA_RE.sub('', section)
    closing = section.rfind('</details>')
    if closing < 0:
        raise ValueError('Publication note has no closing details element')
    return section[:closing] + disclosure + section[closing:]


def update_file(path: Path, language: str) -> bool:
    original = path.read_bytes().decode('utf-8')
    disclosure = DISCLOSURE_EN if language == 'en' else DISCLOSURE_JA
    note_class = 'd-jp-note' if language == 'en' else 'd-en-note'

    def update_match(match: re.Match[str]) -> str:
        try:
            return rewrite_disclaimer(match.group(0), disclosure, note_class)
        except ValueError as error:
            raise ValueError(f'{path.relative_to(ROOT)}: {error}') from error

    updated, disclaimer_count = SECTION_RE.subn(update_match, original)

    def update_publication_note(match: re.Match[str]) -> str:
        try:
            return rewrite_publication_note(match.group(0), disclosure)
        except ValueError as error:
            raise ValueError(f'{path.relative_to(ROOT)}: {error}') from error

    updated, publication_note_count = PUBLICATION_NOTE_RE.subn(update_publication_note, updated)
    if disclaimer_count + publication_note_count == 0:
        return False
    # Removing a multi-line legacy paragraph can leave indentation-only lines.
    # Keep the resulting HTML and `git diff --check` clean.
    updated = re.sub(r'(?m)^[ \t]+(?=\r?$)', '', updated)
    if updated != original:
        path.write_bytes(updated.encode('utf-8'))
    return True


def main() -> None:
    counts = {'ja': 0, 'en': 0}
    for language, directory in (('ja', ROOT / 'compounders'), ('en', ROOT / 'en' / 'compounders')):
        for path in directory.rglob('*.html'):
            if update_file(path, language):
                counts[language] += 1
    print(f"Updated research disclosure pages: ja={counts['ja']}, en={counts['en']}")


if __name__ == '__main__':
    main()
