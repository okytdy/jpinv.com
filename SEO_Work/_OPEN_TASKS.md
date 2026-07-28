# jpinv.com — Open SEO Tasks

**Last updated:** 2026-05-16
**Status of master plan:** Phase 1 shipped (7 service LPs, 6 articles, sitemap, SEO docs all live on main).

> **For future AI sessions:** When Teddy asks "what tasks do we have on the table today" or similar, surface this file. Full context is in `SEO_Work/00_Master/seo_master_summary.md`. Backups of pre-Phase-1 working state are in `SEO_Work/_BACKUP/`.

---

## Open (in priority order)

### High — do next session

1. **Restructure `/サービス/index.html` into a 7-card hub** *(~30 min of work)*
   The page currently describes one service. It needs to become a hub that links to the 7 new sub-LPs under `/サービス/{slug}/`. Without this, visitors landing on `/サービス/` won't discover the new pages and Google won't traverse them efficiently. Highest-leverage internal-link fix.

2. **Add `FAQPage` schema to `/faq/index.html`** *(~10 min)*
   Wraps existing FAQ Q&A in `FAQPage` JSON-LD so Google can render rich results. Same template applies to the FAQ sections on each sub-LP (each LP already has its own FAQ block).

3. **Add `Person` schema for 屋山テディ on `/会社概要/index.html`** *(~10 min)*
   Tie founder to `#organization`. Strengthens EEAT signals. Schema template is in `SEO_Work/00_Master/seo_master_summary.md` §8.1.

4. **Add a "サービス一覧" section to the homepage `/index.html`** *(~20 min)*
   Surface all 7 new sub-LPs from the home page so they pick up link equity from the highest-PageRank page on the site.

### Medium — this week

5. **CTA copy refresh** *(~30 min)*
   Replace "お問い合わせ" / "お見積もり" wording with "IRの伝わり方を相談する" type phrasing on existing pages per `SEO_Work/03_Positioning/positioning_changes.md`.

6. **Footer 3-column rewrite on every existing page** *(~30 min)*
   Add links from every page to the 7 new LPs and articles hub. New LPs already have this footer; the older pages do not. Single biggest internal-link boost remaining.

### Medium — this month

7. **EN versions of 7 LPs + 6 articles** *(~3–6 hours)*
   Create `/en/services/{slug}/` and `/en/articles/{slug}/`. After they exist, re-add the EN entries to `sitemap.xml` (they were stripped on 2026-05-16 to avoid 404s; see "Recently completed" below).

8. **Submit sitemap to Google Search Console** *(~5 min, user action)*
   Go to Search Console → Sitemaps → submit `sitemap.xml`. Optional: URL Inspection + "Request indexing" for 3–5 priority new URLs.

### Long-term — when time allows

9. **Externalise the inline CSS into one shared stylesheet** — significant HTML size reduction; touches every page; safer to do as its own dedicated work session.
10. **`loading="lazy"` on all images + WebP/AVIF conversion** — performance/Core Web Vitals.
11. **Substack ↔ jpinv.com cross-link strategy** — backlink building from existing Substack content.
12. **Set up monthly KW ranking review** — Search Console queries dashboard or equivalent.
13. **Additional authority articles** — 1–2 per month for compounding SEO. Pipeline candidates listed in `SEO_Work/06_Content/content_strategy.md` §8.

---

## Recently completed (2026-07-28) — Search Console canonical fix

Google Search Console sent three messages on July 27, 2026. One was good news: the
`Duplicate without user-selected canonical` issue was validated as fixed on 19 pages.
The other two were not. Validation **failed** again for `Duplicate, Google chose
different canonical than user` (it had already failed on July 3 and July 18), and a new
exclusion reason appeared, `Alternate page with proper canonical tag`.

**What the second reason turned out to be.** `Alternate page with proper canonical tag`
is not a defect here. The site has 147 meta-refresh redirect stubs at old URLs, each
canonicalizing to its new URL. GitHub Pages cannot serve a 301, so a meta refresh plus a
canonical is the correct workaround. None of those stubs is in the sitemap. Google is
reporting that it saw them and honored the canonical. Nothing to fix.

**What the first reason turned out to be.** Two separate duplicate clusters.

*Cluster one — the per-ticker signal logs.* Each page under `/compounders/signals/{ticker}/`
is a filtered slice of `/compounders/feed/`. The only text unique to a page is two to five
short disclosure summaries. Everything else — nav, hero, the full bilingual disclaimer,
footer — is byte-identical across all 216 pages. Measured July 28, 2026: median pairwise
text similarity between any two of them was 0.65 (EN) and 0.73 (JA); the median English
page carried 69 unique words out of 334; three pages had 3 unique tokens. Google clustered
them, picked one member as the representative, and rejected the self-canonical on the rest.

*Cluster two — the profiles gallery.* `/compounders/profiles/` renders the same card set
with the same blurbs as `/compounders/`. 97% of the English gallery's tokens (94% of the
Japanese) also appear on the hub. The only text unique to the gallery is the filter chrome.

**Fixes applied:**

- ✅ `<meta name="robots" content="noindex,follow">` on all 216 per-ticker signal pages. The
  two hub pages `/compounders/signals/` and `/en/compounders/signals/` stay indexable. The
  pages remain crawlable and keep serving visitors who arrive from the hub.
- ✅ `tools/build_signal_pages.py` patched — `head()` takes a `noindex=` argument, passed
  `True` only for per-ticker pages. Without this the GitHub Actions feed refresh would undo
  the fix on its next run.
- ✅ `/compounders/profiles/` and `/en/compounders/profiles/` now canonicalize to their hubs,
  with their own hreflang removed (language annotations belong on canonical pages only) and
  `og:url` matched to the canonical.
- ✅ `sitemap.xml` rebuilt: 206 per-ticker signal URLs removed, 2 gallery URLs removed, 12
  live indexable pages added that had never been submitted (the seven `/サービス/` pages,
  `/会社概要/`, `/料金/`, `/お問い合わせ/`, and `8088` initiation in both languages). 369 URLs → 173.
- ✅ 21 sitemap blocks said `hreflang="ja-JP"` while the pages themselves said `ja`. A URL whose
  sitemap and page disagree on hreflang is a standard reason for Google to drop the language
  pairing and pick its own canonical. All normalized to `ja`.
- ✅ `x-default` added everywhere it was missing — 296 pages and 80 sitemap blocks. All 389
  ja/en page pairs now carry it, pointing at the Japanese URL, matching the root page.
- ✅ `<lastmod>` bumped to 2026-07-28 on the 91 URLs whose HTML changed, so Google has a reason
  to recrawl rather than waiting on its own schedule.
- ✅ Every `<loc>` and hreflang href in the sitemap normalized to percent-encoded form (the file
  had been mixing raw UTF-8 and percent-encoding for the same Japanese URLs).
- ✅ `4 Delivery/5 JII Compounders/8 Assembly & Build/scripts/ship_compounder.py` patched — it was
  the source of the `ja-JP` blocks and it omitted `x-default`, so every future ship would have
  reintroduced the problem. **This file is outside the website repo; it is not part of the push.**

**Verification:** all 543 pages re-parsed. Zero sitemap URLs are noindexed, are redirect stubs,
or point at a missing file. All 173 are self-canonical with `og:url` matching. hreflang is
reciprocal and self-referencing across the whole graph with no broken targets. Both signal hub
pages confirmed still indexable.

**Known follow-ups, none blocking:**

1. Fifteen stale ticker directories under `compounders/signals/` and `en/compounders/signals/`
   (4071, 4194, 4475, 4482, 4716, 4722, 4800, 4811, 7148, 7317, 7523, 8111, 8136, 8771, 9757) are
   left over from an earlier build. They are absent from `compounders/feed/data/watchlist_signals.json`,
   unlinked from either hub, and no longer in the sitemap. They are noindexed so they are harmless;
   deleting them would be tidier.
2. The five Japanese governance section hubs (`/governance/foundations/`, `/cg-code/`,
   `/market-restructuring/`, `/capital-efficiency/`, `/frontier/`) are thin — 747 to 998 characters
   each — and 46–50% identical to one another. Below the threshold that triggers clustering, but if
   Search Console starts flagging Japanese governance URLs, this is where to look.
3. Google will now report the 216 signal pages under *Excluded by 'noindex' tag* rather than as a
   duplicate error. That is the resolution, not a new problem.

---

## Recently completed (2026-05-16)

- ✅ SEO_Work documentation (audit, KW map, content strategy, internal links, positioning)
- ✅ 7 new service LPs under `/サービス/{slug}/` with Service + Breadcrumb schema
- ✅ `/articles/` hub + 6 authority articles with Article + Person (author) schema
- ✅ `sitemap.xml` updated, then trimmed to JA-only entries (EN URLs and `hreflang="en"` alternates removed pending creation of EN pages)
- ✅ All committed and pushed to origin/main

---

## Reference files inside this folder

- `00_Master/seo_master_summary.md` — comprehensive plan, schema templates, commit/push history, rollback notes
- `01_Audit/full_technical_audit.md`, `01_Audit/high_priority_fixes.md`, `01_Audit/current_url_inventory.csv`
- `02_Keywords/keyword_map.csv`, `02_Keywords/search_intent_analysis.md`
- `03_Positioning/positioning_changes.md` — CTA copy, tone guide, exact replace pairs
- `06_Content/content_strategy.md` — article spec + future article candidates
- `07_InternalLinks/internal_link_map.csv` — anchor text + placement spec for every internal link
- `_BACKUP/` — pre-Phase-1 safety nets (large; can be deleted once the user is confident Phase 1 is healthy in production)

---

## How to update this file

When a task is finished, move it from "Open" to "Recently completed" with the date. When new tasks emerge, add them under the appropriate priority. Keep the section "For future AI sessions" near the top.
