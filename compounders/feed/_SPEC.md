# JII Compounders · Capital-Allocation Inflection Feed — Build Spec

**Status:** v1 spec, frozen 2026-05-17. Anything not in this document is out of scope for v1.
**Owner sequence:** Orchestrator → Data-Ingest → Classifier → Backfill → Frontend → Search-Index → Deploy.
**Lives at:** `https://jpinv.com/en/compounders/feed/` (EN), `https://jpinv.com/compounders/feed/` (JP).
**Repo path:** `compounders/feed/` inside the existing jpinv.com GitHub Pages repo.

---

## 1. Reader and purpose

The reader is a PM who has already read the JII Compounders methodology and accepts Principle 6 (the opacity discount is real; capital-policy changes are the catalyst). They want the **subset of all Japanese disclosures that is evidence the catalyst is firing** — at any TSE-listed name, not only the ~80 in the standing universe — so they can decide whether to start work on a name.

The feed is therefore a **live screen for Principle-6 events across the entire TSE.** It is a discovery surface, not a ticker.

## 2. What qualifies as an "inflection" (classifier taxonomy)

Eight classes. Each row in the feed is tagged with exactly one class. The classifier is the heart of the system; everything else is plumbing.

| Code | Class | Trigger (Japanese disclosure pattern) | Quantitative gate |
|---|---|---|---|
| `COC` | Cost-of-capital awareness | 「資本コストや株価を意識した経営」 — initial publication OR material update OR introduction of ROIC/WACC/ROE targets into 中期経営計画 | Material if first publication, or if numeric target moves ≥10% |
| `BUYBACK` | Buyback authorisation at scale | 自己株式の取得に係る事項の決定 / 取得状況に関するお知らせ | ≥1% of shares outstanding OR ≥¥1bn for sub-¥100bn mkt cap |
| `CANCEL` | Treasury cancellation | 自己株式の消却 | ≥0.5% of shares outstanding |
| `DIV` | Material dividend change | 配当予想の修正 / 剰余金の配当 | Payout-ratio jump ≥10pp, OR special div ≥ recurring annual, OR first-ever dividend, OR introduction of progressive policy |
| `CROSS` | Cross-shareholding unwind (policy) | 政策保有株式の縮減方針 OR specific 売却 ≥¥500M | Must be framed as policy/programme, not single tactical sale |
| `MBO` | Take-private / tender | TOB公開買付 / MBO実施 / 親会社による完全子会社化 | Any disclosure |
| `COMP` | Comp-linked KPI revision | 役員報酬制度の改定 introducing ROIC/ROCE/TSR linkage | Must add a capital-efficiency metric to comp |
| `GOV` | Governance code signal | コーポレートガバナンス・コードへの対応 flipping "explain → comply" on Principle 1-4, 1-5, 5-2 (capital-policy principles) | Material if any flip on the named principles |

**Exclusion list (filter OUT, even if keyword matches):** 決算短信 (earnings), 月次売上 (monthly sales), IR説明会 schedules, 株式分割 (splits), 新株予約権 issuance/exercise, ストックオプション grants, treasury movements explicitly tied to option-exercise hedging, materials translation notices.

## 3. Data sources

| Source | Endpoint | Auth | Purpose | Refresh |
|---|---|---|---|---|
| EDINET API (FSA) | `https://api.edinet-fsa.go.jp/api/v2/documents.json` + `/documents/{docID}` | API key (free, registered) | Structured 臨報 / 有報 / コーポレートガバナンス報告書 | 30 min |
| TDnet | `https://www.release.tdnet.info/inbs/I_main_00.html` and daily index pages | None (polite HTML scrape, 1 req/sec) | Same-day press releases that miss EDINET, especially 自己株式取得 and 配当修正 | 15 min during 09:00–16:00 JST, hourly off-hours |
| TSE listed company master | JPX official CSV | None | Ticker → name, sector, market, market-cap-tier | Daily |

EDINET DB (the paid third-party) is **not used** in v1. We only need disclosure metadata; the free official API delivers that.

## 4. Storage shape (committed JSON in the repo)

```
compounders/feed/
  _SPEC.md                ← this file
  data/
    feed.json             ← rolling list, last 730 days, newest first
    by-ticker/
      4776.json           ← per-ticker archive, all matches ever
      4475.json
      ...                 ← only created when a ticker has ≥1 match
    index.json            ← {ticker → match_count, last_match_iso} for the search box
    _meta.json            ← last_refresh_iso, last_edinet_doc_id, run_count, error_log
  index.html              ← EN page (also at en/compounders/feed/)
  index-ja.html           ← JP page
```

`feed.json` row shape:
```json
{
  "id": "EDINET-S100ABCD-2026-05-17T08:23:00Z",
  "ts": "2026-05-17T08:23:00+09:00",
  "ticker": "4776",
  "name_en": "Cybozu, Inc.",
  "name_jp": "サイボウズ株式会社",
  "class": "BUYBACK",
  "tag": "Buyback · 2.1% of S/O · ¥3.0bn",
  "summary_en": "Authorised buyback of up to 1,400,000 shares (2.1% of S/O) for ¥3.0bn, through 2026-11-14.",
  "summary_jp": "自己株式 140 万株 (発行済 2.1%) 上限 30 億円 を 2026 年 11 月 14 日まで取得決議。",
  "source": "EDINET",
  "doc_url": "https://disclosure2.edinet-fsa.go.jp/...",
  "profile_url": "/en/compounders/4776/"
}
```

`feed.json` is capped at 5,000 rows (>2 years of typical Principle-6 hit-rate). Older rows roll into a yearly archive `data/archive/{YYYY}.json`.

## 5. Page UX

Single page, three regions:
1. **Header bar.** Title "Capital-Allocation Inflection Feed", one-sentence positioning ("Only the disclosures that move the multiple."), filter chips for the 8 classes (default all on), and a search box.
2. **Search box.** Type a 4-digit ticker → instantly filters feed to that ticker. If the ticker has no matches in 2 years, show a one-line "No Principle-6 disclosures in the last 24 months — this name has not given the market a reason to re-rate."
3. **Feed list.** Reverse-chronological, virtualised for performance. Each row: timestamp (relative + absolute on hover), ticker (linked to EDINET/TDnet source AND to JII profile when one exists), class chip, one-line tag, expandable for the EN/JP summary.

Filtering and search are pure client-side over `feed.json` (so they work on GitHub Pages). No backend.

## 6. Search behaviour

`index.json` is loaded eagerly so the search box has autocomplete from keystroke one. On ticker selection, the page fetches `data/by-ticker/{ticker}.json` lazily and replaces the feed with that ticker's full back-catalogue.

## 7. Backfill (2 years)

One-shot job, run locally by Claude during this build, that walks EDINET 2024-05-17 → today and TDnet daily indexes for the same range, runs every match through the classifier, and produces the initial `feed.json` + per-ticker JSONs. Result is committed once. After that, the cron only appends new matches.

## 8. Update loop (GitHub Actions cron)

`.github/workflows/feed-refresh.yml`:
- Cron: `*/30 * * * *` (every 30 min)
- Steps: checkout → install Python deps → run `tools/feed_refresh.py` → if `feed.json` changed, commit with message `feed: +{N} matches @ {iso}` → push back to `main` → GitHub Pages serves new JSON within ~60s.

Idempotency: each match has a deterministic `id`; the refresh script dedupes against the existing `feed.json` before append.

## 9. Out of scope for v1 (do not build)

- Email/Substack push, RSS, in-page alerts, sentiment scoring, classification confidence display, multi-language disclosures beyond JP, per-user filtering, login, comments, share-to-X buttons.

## 10. Done definition

- `/en/compounders/feed/` renders and loads `feed.json` with ≥1,800 backfilled rows over 2 years.
- Search a known ticker (4776, 4475, 4194) and see its full disclosure history.
- The cron has executed at least one append-cycle in GitHub Actions and committed a new row.
- A `PUSH-READY.md` exists in `5 Assets/Website/` matching the team's existing deploy-note discipline.
- A `GOVERNANCE_QA_REPORT.md`-equivalent for this feature exists alongside.
