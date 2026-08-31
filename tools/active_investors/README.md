# Active Investors in Japan

A bilingual, automated feature for `jpinv.com/[en/]compounders/`:

- **12 flip cards** — curated active investors. Front = name; flip for their latest
  5% filings and 1%+ position changes; **View more** opens the full filing table.
- **A live, TSE-wide "new 5%" feed** below the cards — *every* new 5%
  large-shareholding report from *any* filer, summarized in plain EN/JA.

Built from FSA **EDINET** large-shareholding filings (大量保有報告書 / 変更報告書),
with neutral English/Japanese summaries. It is the same architecture and house
style as the Capital-Allocation Feed.

---

## Where things live

```
tools/active_investors/
  common.py            # config load, investor attribution, move classification, atomic JSON
  edinet_client.py     # FSA EDINET API v2 client + defensive large-holding CSV parser
  summarize.py         # EN+JA summaries: deterministic template tier + optional Claude tier
  build_data.py        # writes the public data model (shared by seed + live)
  refresh.py           # UPDATE COMMAND for the 12 cards (seed / build-only / live)
  new5_feed.py         # UPDATE COMMAND for the TSE-wide new-5% feed
  config/
    investors.json     # <-- EDIT THIS to change the 12 cards, names, aliases, ranking
    editorial.json     # <-- hide / pin / override summaries
    seed_filings.json  # genuine seed data (used before you run live)
  requirements.txt     # anthropic (optional Claude tier); core is stdlib-only

compounders/active-investors/data/        # PUBLIC data the page fetches (committed)
  investors.json  filings.json  summaries.json  feed.json  new5_feed.json
  new5_home.json  roster.json  meta.json  _meta.json

assets/active-investors.css   assets/active-investors.js   # the shared UI component

en/compounders/active-investors/index.html   # standalone EN page (full mode)
compounders/active-investors/index.html       # standalone JA page (full mode)
# embedded section also injected into en/compounders/ and compounders/ landings
```

## Environment variables

| Var | Needed for | Notes |
|-----|-----------|-------|
| `EDINET_API_KEY` | live ingest (`refresh.py` default, `new5_feed.py`) | Free key from https://api.edinet-fsa.go.jp . All v2 endpoints require it. Never commit it. |
| `ANTHROPIC_API_KEY` | the Claude summary tier (optional) | If unset, summaries use the deterministic template tier (also neutral and factual). |
| `FEED_MAX_DOWNLOADS` | optional | Caps CSV downloads per `refresh.py` run (default 500). |
| `ACTIVE_INVESTORS_LLM_CAP_USD` | optional | Monthly soft cap for the Claude tier (default $5). |

## Run it manually

```bash
cd <repo root>

# 1) Seed (no keys needed) — populate the page from the genuine seed file:
python tools/active_investors/refresh.py --seed

# 2) Live — pull recent EDINET filings for the 12 investors and merge (needs EDINET_API_KEY):
export EDINET_API_KEY=xxxxxxxx
python tools/active_investors/refresh.py --days 7        # last 7 days
python tools/active_investors/refresh.py --date 2026-05-22   # one specific day
python tools/active_investors/refresh.py --days 60       # backfill (no shell timeout locally)

# 3) The TSE-wide new-5% feed:
python tools/active_investors/new5_feed.py --days 5 --max-downloads 150

# 4) After editing investors.json or editorial.json (no network):
python tools/active_investors/refresh.py --build-only

# 5) Confirm that the public feed is genuinely recent:
python tools/active_investors/validate_refresh.py --max-stale-business-days 3
```

Live runs are **idempotent and additive**: they start from the existing
`filings.json`, dedupe by EDINET doc id and by content (so a seed row and the
live row for the same filing collapse, preferring the live one with a real doc
id), and never drop history.

## Scheduling (production)

`.github/workflows/active-investors-refresh.yml` runs daily at 22:00 UTC
(~07:00 JST) and on demand. It refreshes the cards and the new-5% feed and
commits the JSON. **Set two repo secrets** (Settings → Secrets and variables →
Actions): `EDINET_API_KEY` (required) and `ANTHROPIC_API_KEY` (optional). No
server cron needed — GitHub Actions does it. Bump the `cron` line for more
frequent updates.

EDINET application errors such as 401 (invalid key), 429 (throttled), malformed
responses and transport failures are fatal. The workflow will not rewrite
`as_of_date` or commit timestamp-only output after an upstream failure. The
scheduled job scans a rolling 30-day window so restoring the key automatically
backfills short outages; use workflow dispatch with a larger window for longer
gaps.

The roster tally is resumable. Its one-time `--repair-after 2026-08-12`
recovery marker reopens the dates that the old client incorrectly recorded as
scanned during this incident. The marker is persisted after the first repair,
so later daily runs cannot count those dates twice.

## Change the 12 cards

Edit `config/investors.json`, then `python tools/active_investors/refresh.py --build-only`.

- **Swap who appears:** set `"homepage": true` on exactly the investors you want
  and give each a `"curated_rank"` (1 = first card). 12 is the current count
  (`homepage_size`).
- **Add an investor:** copy a block; fill `aliases` with the *exact* EDINET filer
  strings and EDINET codes the fund files under (this is how filings get
  attributed). Add Japanese and English name variants and any sub-entities /
  co-holder names.
- **Ranking mode:** `"ranking_mode": "curated"` (default; uses `curated_rank`) or
  `"activity"` (auto-ranks by qualifying-filing count and recency).
- Investors currently on the bench (set `homepage: true` to surface): BlackRock,
  Oasis Management, Norges Bank, Nippon Active Value Fund. **Note:** the live run
  already detects Oasis under its English filer name even though the EDINET-DB
  cross-reference missed it.

## Editorial controls

Edit `config/editorial.json`, then `--build-only`:

- `hidden_filing_ids` — hide specific filings (find ids in `filings.json`).
- `pinned_filing_ids` — float a filing to the top of its card.
- `hidden_investor_ids` — drop an investor.
- `summary_overrides` — replace the auto summary for a filing id with your own EN/JA text.

## What counts as a "move"

| move_type | rule | shown |
|-----------|------|-------|
| `new_5pct` | initial 大量保有報告書, holding ≥ 5% | yes |
| `increase` | change report, +1.00pp or more | yes |
| `decrease` | change report, −1.00pp or more, or a crossing back below 5% | yes |
| `other` | sub-1pp amendment, or a material filing whose per-filing delta isn't isolated | sub-1pp hidden; material filings shown |

## Known limitations

- **Joint holders / group totals.** EDINET reports a lead filer plus co-holders.
  The parser keeps both the reporting member's figure and the root-context group
  total when EDINET supplies both; the new-5% inclusion rule remains the filing's
  official initial-report classification rather than a brittle member-only
  percentage test.
- **English company names** are only present for seed rows; live rows show the
  Japanese issuer name + ticker. (A ticker→EN-name map could be wired later.)
- **Source links** point to the filer's public holdings list (kabutan), keyed by
  EDINET code; the EDINET doc id is stored on every live row so a switch to the
  official EDINET viewer is a one-line change.
- **EDINET-DB coverage** (used only to build the seed) misses a few funds (Miri,
  Oasis); the live FSA pipeline attributes them by filer name + code.
- Summaries are automated and intentionally neutral — they restate disclosure and
  do not infer intent. Always defer to the original Japanese filing.
