# PUSH-READY · Japan Governance Reform Curriculum Integration

**Date prepared:** 2026-05-17
**Repo:** `https://github.com/okytdy/jpinv.com.git`
**Branch:** `main`
**Status:** Ready to commit and push. QA PASS.

---

## What was added

A complete 27-post governance-reform curriculum at `/en/governance/` (English, fully populated) and `/governance/` (Japanese, hub + theme intros translated, individual posts as bilingual stubs linking to the English versions). Plus two homepage callouts and an updated sitemap.

### Page count
- **34 English pages** under `en/governance/` (1 hub + 5 theme intros + 27 posts + 1 toolbox)
- **34 Japanese pages** under `governance/` (1 hub + 5 theme intros + 27 stubs + 1 toolbox stub)
- **2 homepage edits** (`index.html`, `en/index.html`) — added curriculum callout below the JII Compounders callout
- **1 sitemap edit** — added 68 new URL entries (204 governance-related lines)

### Total
**~70 file changes** (68 new HTML pages + 2 edited homepages + 1 edited sitemap + this PUSH-READY.md + the QA report)

---

## Where to look first (visual sanity check)

Open these in a browser (or via `python3 -m http.server`) before pushing:

1. `/index.html` — Japanese homepage with the new "新刊 · カリキュラム" callout below JII Compounders
2. `/en/index.html` — English homepage with the new "NEW · CURRICULUM" callout below JII Compounders
3. `/en/governance/` — English curriculum hub (5 theme cards + 5-question knowledge check + stats band)
4. `/en/governance/foundations/` — Theme 1 intro
5. `/en/governance/foundations/1.1-lost-decades-roe-gap/` — A representative full post (with Mermaid)
6. `/en/governance/foundations/1.2-pre-reform-architecture/` — Has the keiretsu Mermaid network diagram
7. `/en/governance/toolbox/` — The IR Toolbox keystone page
8. `/governance/` — Japanese curriculum hub

---

## File tree (new / modified)

```
jpinv.com/
├── index.html                                            [MODIFIED — JA homepage callout]
├── sitemap.xml                                           [MODIFIED — 68 new URLs]
├── PUSH-READY.md                                         [NEW — this file]
├── GOVERNANCE_QA_REPORT.md                               [NEW — QA pass report]
├── en/
│   ├── index.html                                        [MODIFIED — EN homepage callout]
│   └── governance/                                       [NEW DIRECTORY]
│       ├── index.html                                    [hub + knowledge check]
│       ├── toolbox/index.html                            [keystone reference]
│       ├── foundations/
│       │   ├── index.html                                [theme 1 intro]
│       │   ├── 1.1-lost-decades-roe-gap/index.html
│       │   ├── 1.2-pre-reform-architecture/index.html
│       │   ├── 1.3-abenomics-third-arrow/index.html
│       │   └── 1.4-stewardship-code-2014/index.html
│       ├── cg-code/                                      [theme 2 intro + 5 posts]
│       ├── market-restructuring/                         [theme 3 intro + 5 posts]
│       ├── capital-efficiency/                           [theme 4 intro + 5 posts]
│       └── frontier/                                     [theme 5 intro + 8 posts]
└── governance/                                           [NEW DIRECTORY — mirrors en/governance]
    ├── index.html                                        [Japanese hub]
    ├── toolbox/index.html                                [JA stub linking to EN]
    └── {foundations,cg-code,market-restructuring,capital-efficiency,frontier}/
        ├── index.html                                    [JA theme intros — translated]
        └── {post-slugs}/index.html × 27                  [JA stubs linking to EN]
```

---

## Suggested commit message

```
Add Japan Governance Reform Curriculum (27 posts, bilingual)

- New: /en/governance/ — 5 themes, 27 posts, knowledge check, IR Toolbox
- New: /governance/   — Japanese hub + theme intros (full) + post stubs (Phase 1; full JA translation pending)
- Modified: index.html and en/index.html — added curriculum callout below JII Compounders
- Modified: sitemap.xml — added 68 governance URLs with hreflang pairs
- New: GOVERNANCE_QA_REPORT.md, PUSH-READY.md

Curriculum content is anchored to primary FSA / JPX / METI / SSBJ / MoJ / GPIF sources.
Visual modules use Mermaid (CDN) + native markdown tables. Mobile-responsive.
Interactive 5-question knowledge check on the English hub.
~63,000 words of curriculum prose.

Phase 1 ships with full EN content; Japanese full translation will follow.
Each Japanese post stub renders the EN title + summary and links through
to the EN page with a "英語版を読む (Read in English)" CTA.
```

---

## Pre-push checklist

```bash
cd "C:\Users\okuya\OneDrive\Desktop\JII\3 Pipeline\5 Assets\Website\jpinv.com"

# 1. Sanity: confirm the new tree is in place
ls en/governance/ governance/
ls en/governance/foundations/ en/governance/toolbox/

# 2. View one page in a browser (or via local server)
python -m http.server 8000
# open http://localhost:8000/en/governance/
# open http://localhost:8000/governance/
# Ctrl+C when done

# 3. Confirm git sees the changes
git status

# 4. Stage everything
git add en/governance/ governance/ index.html en/index.html sitemap.xml PUSH-READY.md GOVERNANCE_QA_REPORT.md

# 5. Commit (suggested message above; paste with -m or use multi-line via -F)
git commit -m "Add Japan Governance Reform Curriculum (27 posts, bilingual)"

# 6. Push
git push origin main
```

---

## What is intentionally NOT in this commit

- **Full Japanese translation** of the 27 individual posts. Phase 1 ships with hub + theme intros translated; each post stub displays the Japanese title and a short context paragraph then links to the English full version. This is by design — professional Japanese translation of ~63,000 words will be a Phase 2 follow-up where quality matters.
- **The /jpinv-governance-curriculum/ source markdown directory.** That lives separately at `C:\Users\okuya\OneDrive\Desktop\JII\jpinv-governance-curriculum\` and is not part of this repo. It is the canonical source from which the HTML was generated and should be kept for future regeneration.
- **The build script.** `build-curriculum-html.py` lives in the temporary outputs directory and was used to generate the 68 pages from the curriculum markdown. If you want to regenerate (e.g., after editing source markdown), copy it into the repo or a tooling repo and run.
- **Chart.js / Recharts graphs.** Several visual modules are markdown tables that contain time-series data ready for promotion to charts (Theme 1.1 ROE gap, Theme 5.2 cross-shareholding ratio, Theme 5.6 female-director ratio, Theme 5.7 shareholder proposals). The `visual-modules.md` design brief in the curriculum source lists which tables are ideal candidates. Charts can be added in a follow-up commit when you bring in Claude Design.

---

## QA pass summary

See `GOVERNANCE_QA_REPORT.md` for the full structural and link QA report. Headline:

- **Status: PASS** — 68/68 governance HTML pages present.
- Homepage callouts on both locales link correctly.
- Sitemap well-formed XML with 106 total URLs (the 38 pre-existing + 68 new).
- All sampled internal links resolve on disk.
- All sampled pages contain the standard nav + footer + CSS token block + canonical + hreflang + viewport.
- Mermaid script + diagram render path confirmed on Theme 1.2.
- Knowledge check on EN hub has 5 questions wired correctly.

Two minor non-blocking observations:
- Japanese posts ship as stubs by design (Phase 1).
- `x-default` hreflang points to JA — confirm with editorial owner that this matches site policy.

---

## Roadmap after this push

**Phase 2 (when you bring in Claude Design):**
- Promote inline tables to Chart.js / D3 / Recharts visualizations on:
  - Theme 1.1 (ROE/ROIC gap)
  - Theme 5.2 (cross-shareholding ratio time-series)
  - Theme 5.6 (female-director ratio)
  - Theme 5.7 (shareholder-proposal counts)
- Add a richer infographic for Theme 4.1 (PBR decomposition / equity-spread relationship)
- Add a working-groups org-chart visualization for Theme 5.8
- Expand the knowledge check from 5 questions to a per-theme quiz battery (5 × 5 = 25 questions)
- Consider a "Progress" feature with localStorage tracking (which posts have been read)

**Phase 3 (Japanese full translation):**
- Replace each JA post stub with the full Japanese translation.
- Re-run the build script with the populated Japanese markdown source.

**Phase 4 (maintenance):**
- Monthly: refresh the TSE disclosure-list count on Theme 4.3 and Toolbox.
- Quarterly: verify every external URL in the Toolbox.
- Annually: add a new Theme 5 post for the year's most material new working-group output.
- When CG Code 4.0 is published (expected 2026-2027 from the FSA Expert Panel): add a Theme 6.

---

## Source documents

- Canonical curriculum source: `C:\Users\okuya\OneDrive\Desktop\JII\jpinv-governance-curriculum\` (all 27 markdown posts + 6 research dossiers + verification reports)
- HTML generator script: `build-curriculum-html.py` (in temporary outputs; copy into a tools repo if you want to regenerate after editing source)
- QA report: `./GOVERNANCE_QA_REPORT.md`
- This file: `./PUSH-READY.md`

---

*All work compiled 2026-05-16 to 2026-05-17. Push at your discretion.*
