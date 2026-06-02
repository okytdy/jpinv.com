# Policy Map — weekly milestone scan log

Each weekly run appends one dated block: sources scanned, new candidates staged, duplicates skipped, and any source that failed to load (logged visibly — never silently dropped). Candidates land in `compounders/policymap/data/milestones_inbox.json` with `notification_status: "pending"` and go live only after Teddy approves and runs `tools/policymap_promote_milestones.py`.

---

## Run 2026-06-02 (weekly) — scan window: 2026-05-23 → 2026-06-02 (10 days)

**Result: 0 new candidates staged · 0 duplicates skipped.** Quiet window — no institutional-grade policy decision/enactment/data print with a clean subtheme fit landed inside the 10-day window.

Note on method: `web_fetch` is provenance-gated in this environment (only URLs surfaced by a prior search/user message are fetchable), so direct fetches of the configured `news_jp` index pages were not permitted. Scanning was performed via WebSearch against each body's Japanese primary-source pages and recent releases. Flagged for Teddy: if direct index fetch is wanted, the feeds need to be pre-seeded into provenance.

Feeds scanned:
- METI (経済産業省) — OK (via search). Late-May items: Monozukuri White Paper 2026 (5/29, white paper — not a money-flow decision), GENIAC-PRIZE 2026 AI-compute contest (~¥1bn, 5/29 — small/contest), AZEC LEAF forum, METI–Philippines stockpiling MOU. None material enough / clean-fit. None staged.
- ANRE (資源エネルギー庁) — OK (via search). No offshore-wind public-offer result or fuel-subsidy decision in window. Nothing staged.
- FSA (金融庁) — OK (via search). CG Code revision: public comment closed 5/15; final revision expected ~June (2015/18/21 all June) but NOT yet published as of 6/2 → not a milestone yet (watch for June finalization → markets-06). Nothing staged.
- Bank of Japan (日本銀行) — OK (via search). Held policy rate at 0.75% on 4/28 (outside window); next MPM mid-June. Market leans toward a June hike but nothing decided in window. Nothing staged.
- JPX / TSE (日本取引所グループ) — OK (via search). Only routine items (option adjustments, index-methodology consultations). Immaterial. Nothing staged.
- MLIT (国土交通省) — OK (via search). No material decision in window. Nothing staged.
- MHLW (厚生労働省) — OK (via search). 5/20 NHI drug-price list update is a routine list application, not a new decision; FY2026 drug-price revision already告示 earlier. Minimum-wage council not until ~July. Nothing staged.
- MAFF (農林水産省) — OK (via search). No material decision surfaced in window. Nothing staged.
- Ministry of Defense (防衛省) — OK (via search). FY2026 budget approved Dec 2025; no new in-window procurement/contract decision surfaced. National Intelligence Council Establishment Bill passed the Upper House ~5/27 but does NOT map cleanly to any defense subtheme (missiles / air-defense / drones / production base / econ-security supply chains / sovereign cloud) → skipped per "no clean fit, do not mis-tag." Nothing staged.
- Cabinet Office (内閣府) — OK (via search). 骨太の方針 (Basic Policy) not yet decided (2025 edition was 6/13; 2026 edition still pending as of 6/2). Nothing staged.
- Digital Agency (デジタル庁) — OK (via search). Only guidebooks/explainers (dashboard design guide 5/1, government-AI explainer 5/13). Immaterial. Nothing staged.
- Children and Families Agency (こども家庭庁) — OK (via search, covered under prior labor/childcare scan). No new in-window decision. Nothing staged.
- Japan Tourism Agency / JNTO (観光庁) — OK (via search). JNTO April-2026 inbound estimate (3.692mn, −5.5% YoY) published 5/20 — outside the 10-day window AND a monthly print (not a milestone-grade event; a YoY decline). Not staged.

Failures: none (all feeds reached via WebSearch; note the web_fetch provenance limitation above).
Email draft: none created (Step 7 triggers only on ≥1 new candidate).

---

## 2026-06-02 — weekly scan
**Window:** 2026-05-23 → 2026-06-02 (scan_window_days = 10). Method: search-first (WebSearch each feed query for 2026年5月/6月, then fetch only surfaced official-domain result URLs).

**Feeds scanned (13):**
- METI (経済産業省) — OK, 0 in-window. Surfaced: 5th semicon supply-chain application round (began 2026-04-07, out of window), 分野別投資戦略 ver.3 (2025-12-26), FY2026 GX概算要求 PR. No in-window decision.
- ANRE / 資源エネルギー庁 — OK, 0 in-window. Offshore-wind 4th round slated autumn 2026; resource-cost 40% pass-through rule (FY2025). Nothing dated in window.
- FSA (金融庁) — OK, 0 in-window. CG Code revision = *proposal* (改訂案) published 2026-04-10 (out of window + consultation, not a decision). Stewardship Code revision already live (2025-06-01).
- BOJ (日本銀行) — OK, 0 in-window. Last MPM 2026-04-28 (press conf 04-30), both out of window; next MPM mid-June (after window). Policy rate 0.75% (set 2025-12). June 2026 = scheduled interim assessment of JGB taper plan, but lands after this window.
- JPX / TSE — OK, 0 in-window. TSE cost-of-capital follow-up update 2026-04-28 (out of window); TOPIX index revision (2026-05) = routine index methodology, not a policy milestone. Excluded.
- MLIT (国土交通省) — OK, 0 in-window. 総合物流施策大綱 2026–2030 閣議決定 2026-03-31 (out of window); 2026-05-20 was an info-sharing meeting only.
- MHLW (厚生労働省) — OK, 0 in-window. FY2026 medical-fee revision already live (2026-02-13); drug-price告示 2026-03-05 (applied 04-01); 診療報酬本体 phased implementation 2026-06-01 = implementation of an already-recorded decision (skipped per dedupe). NHI new-drug listing applied 2026-05-20 = routine listing (immaterial). Min-wage council not yet (summer).
- MOD (防衛省) — OK, 0 in-window. No specific in-window contract/procurement award surfaced; FY2026 budget already live (2025-12-26).
- Cabinet Office (内閣府) — OK, 0 in-window. 骨太の方針2026 NOT yet Cabinet-decided as of 06-02 (draft early June, 閣議決定 mid-to-late June → next window). Econ-security 特定重要物資 latest designation 2026-02 (capacitors/filters + uranium), out of window.
- Digital Agency (デジタル庁) — OK, 0 in-window. Late-May procurement notices = routine (excluded). Gov-cloud migration of 164 bodies completed Feb 2026.
- Children & Families Agency (こども家庭庁) — OK, 0 in-window. こども誰でも通園 nationwide benefit already live (2026-04-01 labor-08); 子育て支援金 payroll deduction from May = administrative, not a new decision.
- MAFF (農林水産省) — OK, 0 in-window. スマート農業をめぐる情勢 (2026-05) = routine status briefing; 省力化投資促進プラン was 2025-06-13. Nothing in window.
- Japan Tourism Agency (観光庁) — OK, 0 in-window. Inbound consumption Q1-2026 released 2026-04-15 (out of window); 2025 annual ¥9.46tn already reflected (live 2026-01-01 consumer-07). Next Q2 print ~mid-July.

**Failures:** none. All WebSearch queries returned results; no fetch errors.

**Candidates staged:** 0.
**Duplicates skipped:** 0 (no in-window items reached the dedupe stage).
**Notes:** Quiet pre-mid-June window — the material near-term catalysts (骨太の方針2026 閣議決定, BOJ June MPM + JGB-taper interim assessment, possibly minimum-wage council) all fall just AFTER 2026-06-02 and should surface in next week's run. Inbox left empty (last_scan = 2026-06-02). No live data touched; no review email drafted (Step 7 fires only on new candidates).

---
