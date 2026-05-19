# JII Compounders Feed v2 — Expansion Beyond EDINET + TDnet

**Status:** design draft, 2026-05-19. Frozen scope is v1; this document specifies the v2 expansion.
**Author:** planning subagent. **Reviewer:** PM (single-person team — engineering hours are the binding constraint).

---

## 0. Premise

v1 catches anything that crosses EDINET or TDnet. That covers 開示 — the legally-required surface. v2 targets **pre-開示 inflection signal**: language that flips in management voice before (or in lieu of) a formal disclosure. Three candidate corpora: briefing decks, integrated reports, transcript Q&As. Below, each evaluated against the same seven dimensions.

---

## 1. Briefing decks (決算説明資料)

**Acquisition.** TDnet *does* index 決算説明資料 — they appear in the daily index alongside 短信, typically same-day or T+1. The v1 TDnet scraper already sees these rows; we currently filter them out via the exclusion list (because the parent 短信 is excluded). So acquisition cost is near-zero — flip a switch, then add a PDF download step. PDFs are public, free, no auth. Per-ticker poll is unnecessary; the TDnet daily index is a broadcast feed.

**Volume / cadence.** ~3,800 listed firms × 4 quarters = ~15,000 decks/year, clustering heavily in five 2-week windows (mid-May, mid-Aug, early-Nov, early-Feb, plus annual late-May). Peak day: ~400 decks. Off-peak: <20/day. Refresh cadence matches TDnet (15 min during market hours).

**Classifier impact.** All 8 classes still apply but trigger surfaces differ. Key gap: COC language in decks is visual. The WACC/ROIC chart on slide 14 is the actual signal, with one or two lines of body text like 「資本コストを上回るROICを~」. The current regex is prose-tuned and will under-fire. Fixes needed: (a) PDF→text with layout preservation (PyMuPDF, not pdfplumber — PyMuPDF keeps slide-anchor coordinates), (b) per-slide chunking so a hit is anchored to slide N, (c) loosen the COC regex to match 資本コスト within a 50-char window of a numeric percentage. No new event class needed — the existing 8 cover deck content.

**Storage.** feed.json row needs `slide_index` (int) and `excerpt` (str, ≤200 char OCR-or-text snippet) added under an optional `citation` object. Backward-compatible. `source` becomes `"TDNET-DECK"`. `doc_url` keeps deep-linking via `#page=N`.

**Frontend.** Row renders identically except the class chip gets a small "hint" modifier (lighter fill, dotted border) when source is a deck rather than a structured 開示. Hover/expand reveals the slide excerpt. Critical UX rule: a deck hint must never outrank a real 開示 in the feed — if both exist for the same ticker within 7 days, suppress the hint (collapse under the disclosure row).

**Cost / complexity.** ~3–5 engineering days. PyMuPDF + new regex tuning + storage migration + frontend chip variant. The expensive part isn't code — it's the classifier-tuning loop (sample 200 decks, hand-label, measure precision/recall). Budget another 3 days for that.

**Bottom line: SHIP THIS QUARTER.** Highest-value-per-hour by a wide margin. Source is free, indexed, already in our scraper's view, and adds the single most-requested signal (early COC).

---

## 2. Integrated reports (統合報告書)

**Acquisition.** No central registry. Three options: (a) crawl each company's IR page (3,800 sites, no consistent path) — brittle; (b) parse the YUHO (有価証券報告書) for the cross-reference URL — works only for EDINET filers and only after the YUHO is filed (annual, lagged); (c) Disclosure Net / GPIF's listing — partial coverage, not complete. Realistic path: TDnet sometimes carries 「統合報告書発行のお知らせ」 announcements — start there, then fetch the PDF from the linked URL. Coverage will be ~60% of names that publish one (the rest just quietly post to their IR page).

**Volume / cadence.** ~900 firms publish integrated reports annually (rising ~10%/yr). Almost all are 60–150 pages, JP-only, dense. Cluster: July–October. ~5–10/day at peak, near-zero off-season.

**Classifier impact.** Two new dimensions. (a) Capital-allocation framework changes — multi-year buyback intent, payout ratio targets, WACC disclosure with explicit hurdle. Existing classes catch most of this but the *prose density per signal* is 10× a deck. Expect false-positive rate to spike. (b) New candidate class `ALLOC` — "capital allocation framework, multi-year" — is tempting but probably overlaps too much with COC. Recommend: don't add a class, raise the bar (require numeric target + time horizon) for COC matches sourced from integrated reports.

**Storage.** Same `slide_index` field reused as `page_index`. Add `doc_type: "INTEGRATED"` for filtering. `excerpt` field is essential here — the page citation alone is too low-information.

**Frontend.** Same hint-style chip. But integrated-report hits are *retrospective explanations* of capital policy, not catalysts — they should probably default-off in the filter chips and be opt-in. Otherwise they will dominate August.

**Cost / complexity.** ~2–3 weeks. Acquisition is the wall, not classification. Building the IR-page crawler is a 6-month maintenance project disguised as a 2-week build (anyone who has scraped 3,800 Japanese IR sites knows this). Recommend acquisition via TDnet-announcement-only — accept the 60% coverage as the price of staying inside one engineer-month.

**Bottom line: SHIP NEXT QUARTER.** Medium value, medium cost, and only after deck-classifier tuning has surfaced what the COC false-positive rate actually looks like — we need that calibration data before pointing the same machinery at 150-page documents.

---

## 3. Earnings transcript Q&As

**Acquisition.** No free option. Scripts Asia (~¥X00k/yr per seat, redistribution-restricted), QUICK 端末 (~¥1M+/yr), Reuters Eikon (¥2M+/yr). User has a Scripts Asia relationship via the existing translation pipeline — but that's per-document licensing, not a feed. Self-recording from IR webcasts is technically possible (Whisper-large-v3 on JP audio runs at ~0.3× realtime; quality on financial JP is ~88% WER post-tuning) but coverage of Q&A specifically requires a human (or LLM) to segment 質疑応答 from prepared remarks. Realistic free option: scrape Log Mi Finance and Kabutan transcripts — partial coverage, ~300 names, mostly large-cap, ~3-day lag.

**Volume / cadence.** ~3,800 firms × 4 calls = 15,200 calls/year. Q&A averages 30 minutes. Same five clustering windows as decks. Transcribed-and-published volume (if we go Log Mi route): ~80 transcripts/day at peak across all sources.

**Classifier impact.** Highest signal density of the three — management voluntary disclosure is where policy flips first ("we're reviewing our cross-shareholdings" three months before the formal 縮減方針). But: hallucination risk in transcripts (mis-attributed quotes, ASR errors mangling 「資本コスト」 → 「資本コース」) means a stricter classifier is required, and every hit needs a quote-level citation with the speaker name. New surface area for classes COC, CROSS, COMP especially. No new class needed.

**Storage.** Needs `speaker`, `timestamp_in_call`, `quote_jp` fields. Schema bloats meaningfully.

**Frontend.** Quote-card style render, very different from current rows. Speaker attribution mandatory. Probably gets a second-class visual treatment ("hint, unverified") because a Q&A line is not a 開示.

**Cost / complexity.** Free path (Log Mi scrape): ~2 weeks, ongoing whack-a-mole as sites change. Paid path (Scripts Asia data licence): probably blocked by licensing terms that prohibit republishing excerpts on a public site — needs a legal read before *any* engineering. The licensing risk is the real cost, not the build.

**Bottom line: PUNT.** Highest signal-per-row, lowest engineering ROI for a one-person team. Licensing alone could eat a quarter. Revisit when v1 + briefing decks have generated enough usage data to justify the legal work. Optional consolation: a *manual* "transcript watchlist" — PM flags 5–10 calls/quarter where Q&A language was striking, and those get a hand-curated entry. No infra.

---

## 4. Build order

1. **Briefing decks** (this quarter, 1–2 weeks calendar).
2. **Integrated reports, TDnet-announcement-sourced only** (next quarter, after deck precision is measured).
3. **Transcripts: punt** — revisit Q4 with licensing clarity.

---

## 5. Rejected approaches

- **適時開示 RSS / "TDnet RSS feeds."** No official RSS; the few third-party mirrors lag and break. Direct HTML scrape (v1's choice) is more reliable.
- **X/Twitter scraping for IR officer posts.** Signal exists (occasional JP IR accounts pre-announce tone shifts) but API costs + ToS + noise ratio make it not worth it for a single PM.
- **GPIF / METI ESG database crawls.** Slow, batch-released annually, no new signal beyond YUHO.
- **Shared-research / 株探 / Kabutan event tags.** Useful as a *validation* set, not a source — they post-process the same EDINET+TDnet stream we already consume.
- **Bloomberg BCAP / FactSet capital-allocation feeds.** Cost-prohibitive at single-seat scale; their classifier is generic, not Principle-6-tuned.
- **OpenAI / Claude as the classifier (no regex).** Tempting but the per-document cost at 15k decks/yr + 900 IRs/yr + backfill is real, and the v1 regex pipeline already works — wrong place to introduce LLM cost. Use LLMs only for the *excerpt summary* field, not the trigger decision.

---

## Critical Files for Implementation

- `compounders/feed/_SPEC.md` (v1 spec — basis for v2 schema migration)
- `compounders/feed/data/feed.json` (row schema add: `citation.page_index`, `citation.excerpt`, `doc_type`)
- `compounders/feed/index.html` (frontend — hint-chip variant, deck-hint suppression rule)
- `tools/feed_refresh.py` (classifier + ingest — needs PyMuPDF integration and per-slide chunker)
- `.github/workflows/feed-refresh.yml` (cron — peak-window backoff for deck-heavy days)
