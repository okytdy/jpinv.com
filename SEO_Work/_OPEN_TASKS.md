# jpinv.com — open website and SEO work

**Last updated:** 2026-11-10

## November 10 search maintenance

- Refined the reported search titles/descriptions and added one contextual service link to four paired governance guides. Existing article wording, heading fits and corporate page layouts are preserved.
- Replaced the homepage's refresh-frequency promise with the latest disclosure date; refreshed its static fallback from the existing feed snapshots. The live feed itself was current.
- Added homepage photo descriptions and cleaned the retired investor-meeting-preparation redirect: current destination, noindex, accessible fallback, no meta refresh.
- Added a hidden referring-page field to the existing enquiry flow. It carries only the JII page path and is submitted with the visitor's enquiry; it makes no separate tracking request.
- Updated the sitemap modification dates and generated human indexes. Search-only governance rebuilds use npm run build:governance-search to preserve hand-fitted editorial markup.
- Verify Bing's next crawl against the deployed pages before treating old report counts as outstanding site defects. Japanese search summaries stay concise rather than being padded to an English character-count target.

Teddy's November 10 direction: keep visible changes compact; do not accumulate explanatory paragraphs as an SEO fix.

JII now has one commercial path: an IR team arrives with a real disclosure or meeting, starts with one translation or interpretation assignment, and can then reserve future quarterly work. Practical IR consultation follows from the document or meeting in front of us. It is not a separate diagnostic product.

The material in the numbered folders records earlier SEO research. Some of it describes the retired overseas-IR diagnostic offer. Treat those passages as historical research, not current positioning. The live pages and this file are the current source of truth.

## Current priorities

1. Send the first focused cold-email batch to listed-company IR teams with near-term earnings dates.
2. Measure replies, qualified conversations, paid first jobs, and second-job reservations. Do not substitute page traffic for revenue evidence.
3. Add one short, concrete case example once a client permits it. An anonymized before/after translation excerpt is more useful than a broad claim.
4. Submit the updated `sitemap.xml` in Google Search Console after this release is live.
5. Review search queries monthly. Keep pages that support urgent translation, disclosure translation, interpretation, and recurring quarterly work. Do not recreate retired diagnostic landing pages.

## Site rule

Every commercial page should answer five questions without making a Japanese IR team learn JII's internal system:

- What can JII take off my desk?
- Can it meet my deadline?
- Who will handle the work?
- How are confidentiality and quality handled?
- What do I send to get a reply?

## Technical follow-ups

- Watch Search Console after the legacy service URLs redirect to their current destinations.
- Keep the redirect stubs out of the human and XML sitemaps.
- Preserve Japanese and English language pairs when adding or removing a page.
- Run `tools/build_sitemap_page.py`, `tools/bump_nav_version.py`, and the navigation test after changing shared navigation.

## Historical technical context

`_HANDOFF_2026-07-28_search_console.md` explains the canonical and noindex work completed in July 2026. The numbered folders contain the earlier audit, keyword research, and content inventory. They are useful evidence, but the 2026-08-14 revenue architecture above overrides their product positioning.
