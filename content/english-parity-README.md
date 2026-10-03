# English content parity

Japanese copy is authoritative. The English Founder’s message is intentionally
distinct and must be edited independently.

Run `npm run build:english-parity` to regenerate the synchronized core pages,
governance curriculum, eleven restored archive bodies, disclosures, profile
pages and archive cards. Run `npm run check:english-parity` before publishing.
The check also runs on GitHub pushes and pull requests.

The core-page maps in `content/english-parity/`, profile-body maps in
`content/compounders/parity/`, archive-card map and English governance source
record the Japanese source they translate. If Japanese content changes, review
and update the corresponding English copy and source checksum together. Never
refresh a checksum merely to bypass a failed check. Core-page checksums ignore
navigation cache versions and line endings; the copy and page structure remain
protected.

`metadata-parity.json` records the reviewed company descriptions and article
metadata. `disclaimer-parity.json` translates each Japanese disclosure paragraph
with its original scope. New disclosure wording fails the build until reviewed.
`tools/build_signal_pages.py` uses the same source-matched disclosure map, so
scheduled signal rebuilds retain the English corrections.

After navigation changes, run `tools/bump_nav_version.py`. After adding pages,
rebuild `tools/build_sitemap_page.py` and update the XML sitemap with reciprocal
language alternates. Verify mobile wrapping, language switching and diagrams in
the local preview as well as running the repository’s checks.
