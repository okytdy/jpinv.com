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
