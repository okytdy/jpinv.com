# Governance Curriculum Integration — Pre-Push QA Report

**Status: PASS**

Date: 2026-05-17
Scope: 27-post / 5-theme governance reform curriculum integrated into the jpinv.com static site (English at `/en/governance/`, Japanese at `/governance/`).

---

## 1. File inventory

| Tree | Expected | Found | Result |
|---|---|---|---|
| `/en/governance/index.html` (EN hub) | 1 | 1 | OK |
| `/en/governance/toolbox/index.html` (EN toolbox) | 1 | 1 | OK |
| `/en/governance/{theme}/index.html` (EN theme intros) | 5 | 5 | OK |
| `/en/governance/{theme}/{post}/index.html` (EN posts) | 27 | 27 | OK |
| `/governance/index.html` (JA hub) | 1 | 1 | OK |
| `/governance/toolbox/index.html` (JA toolbox stub) | 1 | 1 | OK |
| `/governance/{theme}/index.html` (JA theme intros) | 5 | 5 | OK |
| `/governance/{theme}/{post}/index.html` (JA post stubs) | 27 | 27 | OK |
| **Total HTML pages** | **68** | **68** | **OK** |

Theme distribution confirmed across both locales:
- `foundations/` — 4 posts (1.1–1.4)
- `cg-code/` — 5 posts (2.1–2.5)
- `market-restructuring/` — 5 posts (3.1–3.5)
- `capital-efficiency/` — 5 posts (4.1–4.5)
- `frontier/` — 8 posts (5.1–5.8)

= 4 + 5 + 5 + 5 + 8 = 27 posts per locale. Matches spec.

## 2. Homepage callouts

| Page | `governance-callout` block | Link target | Result |
|---|---|---|---|
| `/en/index.html` | 1 | `/en/governance/` | OK |
| `/index.html` | 1 | `/governance/` | OK |

Both callouts are properly styled (`compounders-callout-inner` re-used layout), labelled (`NEW · CURRICULUM` / `新刊 · カリキュラム`), and link to the correct locale hub.

## 3. Sitemap

- `sitemap.xml` parses cleanly via `xml.etree.ElementTree.parse()` — no well-formedness errors. Root tag: `urlset` (namespace `sitemaps.org/schemas/sitemap/0.9`).
- Total `<url>` entries: **106**.
- `<loc>` entries with `https://jpinv.com/en/governance/...`: **34** (1 hub + 1 toolbox + 5 themes + 27 posts).
- `<loc>` entries with `https://jpinv.com/governance/...` (excluding `/en/`): **34** (mirror).
- Each governance URL carries proper `xhtml:link rel="alternate"` hreflang pairs.
- 106 `<lastmod>` tags — one per URL.

## 4. Internal-link sampling

Five random pages picked: `governance/toolbox/`, `en/governance/foundations/1.4-stewardship-code-2014/`, `en/governance/frontier/5.7-activism-engagement-2025/`, `governance/foundations/1.3-abenomics-third-arrow/`, `en/governance/frontier/5.8-working-groups-landscape/`.

For each, every `href="/..."` target was tested against the filesystem (file exists, or directory has an `index.html`). **100% resolved.** No 404s. This covers governance cross-links (next/prev, theme back-links, related-post lists), main-nav links (`/en/`, `/en/compounders/`, `/サービス/`, `/会社概要/`, etc.), and asset links (`/favicon.svg`, `/apple-touch-icon.png`).

## 5. CSS / styling consistency

Spot-checked `en/governance/foundations/1.2-pre-reform-architecture/index.html` (post) and `en/governance/index.html` (hub):
- Post: 43× `--ink`, 19× `--accent`, 12× `--serif` references in embedded styles. `:root` variable block present.
- Hub: 46× `--ink`, 20× `--accent`, 18× `--serif`. `:root` block present.

Mass-check across all 68 pages: **0 pages** missing the `--ink` CSS variable. Token set is uniform with the rest of jpinv.com.

## 6. Nav + footer consistency

| Element | EN post | EN hub | JA post | JA hub | Mass-check (all 68) |
|---|---|---|---|---|---|
| `<nav id="main-nav">` | 1 | 1 | 1 | 1 | 0 missing |
| `footer-grid` block | 4 | 4 | 4 | 4 | 0 missing |
| `footer-locale-switcher` | 2 | 2 | 2 | 2 | (consistent) |

Governance nav-link present on every spot-checked page (4-5 occurrences each, counting main-nav + mobile menu + footer + breadcrumbs).

## 7. hreflang correctness

Spot-checked EN post (`1.2-pre-reform-architecture`) and JA post (same slug):

EN canonical/hreflang block:
- `rel="canonical" href="https://jpinv.com/en/governance/foundations/1.2-pre-reform-architecture/"`
- `hreflang="en"` → `/en/governance/...`
- `hreflang="ja"` → `/governance/...`
- `hreflang="x-default"` → `/governance/...` (JA default — fine for this site)

JA canonical/hreflang block:
- `rel="canonical" href="https://jpinv.com/governance/foundations/1.2-pre-reform-architecture/"`
- Both hreflangs correct, x-default also set.

Mass-check: **0 pages** missing canonical; **0 pages** with fewer than 2 hreflang entries.

## 8. Mermaid rendering

`en/governance/foundations/1.2-pre-reform-architecture/index.html`:
- 1× `mermaid.esm.min.mjs` script import — OK
- 1× `<pre class="mermaid">` (or equivalent) diagram block — OK (the keiretsu diagram)

Mermaid is wired up correctly on the one post that requires it.

## 9. Interactive knowledge check

`en/governance/index.html` (EN hub):
- `kcheck` references: 69 (style rules + 5 question containers + interaction state)
- `kcheck-opt` references: 32 (5 questions × ~4 options each + style rules + JS handler)
- Exactly **5** `data-q=` question identifiers found — matches spec.
- Click handler / `.kcheck-explain` reveal logic confirmed present in inline `<script>`.

## 10. Mobile sanity

`<meta name="viewport" content="width=device-width, initial-scale=1.0">` present on all 68 generated pages (mass-check returned 0 missing).

---

## Issues to address

None blocking. Two minor observations (not failures):

1. **Toolbox JA is a stub** — by design per spec, but worth confirming with the user that the JA toolbox shipping as a stub rather than full-translation is intentional for v1. Same for the 27 JA post stubs (intentional per spec).
2. **`x-default` hreflang points to JA** — currently `x-default` resolves to the Japanese URL on both locales. Reasonable for a Japan-focused site, but if the editorial intent is "default = English for global readers", swap on a future pass. Not a launch blocker.

## Recommended next steps before push

1. Visually smoke-test 2-3 pages in a browser at 375 px and 1280 px widths — automated checks don't catch responsive-layout regressions or font-loading delays.
2. Submit `sitemap.xml` to Google Search Console after deploy and watch the index-coverage report for the first 48 hours.
3. Confirm with the editorial owner that JA post stubs (which currently re-point readers to the EN curriculum or hold placeholder copy) are acceptable for soft launch, or whether the JA hub callout copy should mention "EN curriculum first, JA translations rolling out."
4. Tag the release in source control before the push (`v-governance-launch-2026-05-17` or similar) so a rollback target exists.
5. After push, re-run a single `curl -I` on `/en/governance/` and `/governance/` against the live host to confirm 200 OK and correct `Content-Type: text/html; charset=utf-8`.

---

**Bottom line:** The integration is structurally clean — 68 pages, 0 missing assets, 0 broken internal links among the sampled set, sitemap well-formed and complete, all SEO meta + responsive meta + locale meta + nav + footer + CSS tokens uniform across every generated page. Cleared for push pending the visual/responsive smoke test in step 1 above.
