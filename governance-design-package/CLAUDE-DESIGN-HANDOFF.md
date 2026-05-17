---
title: "Claude Design Handoff — Japan Governance Curriculum Interactive Layer"
to: "Teddy"
from: "Orchestrator agent"
date: "2026-05-17"
status: "Ready to upload to claude.ai/design"
---

# Claude Design Handoff

This package is ready to upload to **`https://claude.ai/design`**. It contains everything Claude Design needs to produce a polished, production-grade interactive layer for the Japan governance curriculum at `jpinv.com`.

## What's in this package

```
governance-design-package/
├── CLAUDE-DESIGN-HANDOFF.md     ← this file (start here)
├── DESIGN-BRIEF.md              ← the design brief (read second)
├── INTEGRATION-PLAN.md          ← where each component lands in the site (read third)
├── QA-REPORT.md                 ← QA validation pass
├── data/                        ← 5 JSON files, the data layer
│   ├── timeline.json            ← 93 events, 1989-2026
│   ├── compliance.json          ← 10 topics, segment-level data
│   ├── working-groups.json      ← 14 groups + 24 upcoming calendar items
│   ├── links-notebook.json      ← 85 link entries across 9 categories
│   └── quiz-bank.json           ← 34 questions, 5 themes, 3 difficulty levels
└── prototypes/                  ← 5 working HTML/CSS/JS prototypes
    ├── timeline.html            ← ~1,200 lines · horizontal timeline with slide-out panel
    ├── compliance-dashboard.html ← ~1,100 lines · Chart.js stacked-bar/donut/trend
    ├── working-groups.html      ← ~1,050 lines · mission-control card grid
    ├── notebook.html            ← ~1,160 lines · faceted search + card grid
    └── quiz.html                ← ~836 lines  · 4-mode quiz with localStorage
```

## What was built

Five interactive components, each with:

- **A data layer** (JSON) — populated from the curriculum's research dossiers + JPX/FSA/METI primary sources
- **A working prototype** (single self-contained HTML file) — demonstrates the desired interaction model
- **A documentation comment block** at the top of each prototype — describes the data contract, interaction model, design intent, and intentional rough edges

The prototypes use the jpinv.com CSS variables and typography directly. They are not pixel-final — they are deliberately rough at the visual level so Claude Design has clear room to add polish.

## What each component does

| # | Component | Data | Goal |
|---|---|---|---|
| 1 | **Horizontal timeline** | 93 events 1989-2026 | An IR rep sees the entire reform arc in one screen, then drills into any moment |
| 2 | **Compliance dashboard** | 10 topics × segment counts | Turn JPX disclosure-list data into a benchmarkable view |
| 3 | **IR Notebook** | 85 reference links | A searchable, filterable replacement for the markdown IR Toolbox |
| 4 | **Multi-mode quiz** | 34 questions | Test fluency, by theme, by difficulty, with weak-area review |
| 5 | **Working-groups dashboard** | 14 active bodies | Live view of what's coming next 90 days / 12 months |

## How the data was sourced

Every data point in the JSON files is anchored in a primary FSA / JPX / METI / SSBJ / MoJ / GPIF source, or in the JII curriculum's research dossiers (which themselves are primary-source linked). The QA pass confirmed:

- **All 5 JSON files parse as valid JSON**
- **Every `curriculum_slug` value (~230 across the 5 files) maps to a real, on-disk curriculum page** at `/en/governance/...` — slug normalisation pass completed
- **External URLs are confined to approved issuer domains** (jpx.co.jp, fsa.go.jp, meti.go.jp, ssb-j.jp, moj.go.jp, gpif.go.jp, jira.or.jp, kantei.go.jp, cao.go.jp)
- **All 5 prototypes structurally sound** — valid HTML, standard CSS variables, fetch with inline fallback, top-of-file doc-comments

## Suggested upload order to Claude Design

When opening **`claude.ai/design`**, hand it the files in this order:

### Step 1 — Load context

Upload `DESIGN-BRIEF.md` first. This is the master spec — Claude Design will use it to understand the audience, design language, and component-by-component requirements.

Then upload `INTEGRATION-PLAN.md` — so Claude Design knows where each polished component ultimately lands on the live site.

### Step 2 — Polish each component (one session each)

For each of the 5 prototypes, open a session, upload:

1. The prototype HTML file (e.g., `prototypes/timeline.html`)
2. The corresponding data file (e.g., `data/timeline.json`)
3. Ask: *"Polish this prototype to production quality, keeping the data contract intact. Match the jpinv.com design language exactly (CSS variables in the brief). Address the intentional rough edges documented at the top of the file. Stay self-contained — no external libraries other than the CDN ones already used."*

Suggested order (from `DESIGN-BRIEF.md`):
1. **Timeline first** — it's the visual hero. Most viral surface.
2. **Compliance dashboard** — most operationally useful. Needs design taste on Chart.js styling.
3. **Working-groups dashboard** — mission-control feel.
4. **Notebook** — sidebar + card-grid is well-trodden; design lift is moderate.
5. **Quiz** — interaction already works; polish is mostly animation.

### Step 3 — Cross-cutting system pass

After all five components are polished, do a cross-cutting design-system pass:

Upload all 5 polished prototypes and ask: *"Extract the reusable design patterns into a small shared CSS file: the slide-out detail panel, the faceted-filter rail, the status pulse dot, the KPI tile, the card-grid empty state. Output a single `governance-shared.css` file that the implementation engineer can include alongside each component."*

### Step 4 — Integration into the live site

After Claude Design returns the polished prototypes, the implementation step is mechanical:

- Each polished prototype maps to a page under `/en/governance/` and `/governance/`
- The data files stay where they are (or get baked into HTML at build time per `INTEGRATION-PLAN.md`)
- Add the new pages to `sitemap.xml` (the plan has the exact `<url>` blocks)
- Add the navigation entries to the curriculum hub and footer

All of this is laid out in `INTEGRATION-PLAN.md`.

## Headline data stats

| File | Size | Content |
|---|---|---|
| `timeline.json` | 104 KB | 93 events across 6 categories spanning Dec 1989 to May 2026 |
| `compliance.json` | 40 KB | 10 topics with segment-level disclosed/under-consideration/not-disclosed counts, trend arrays, and best-practice sample companies |
| `working-groups.json` | 36 KB | 14 working groups (FSA / TSE / METI / SSBJ / MoJ) + 24 upcoming calendar items |
| `links-notebook.json` | 132 KB | 85 reference links across 9 categories with bilingual title/summary/tags |
| `quiz-bank.json` | 76 KB | 34 multi-choice questions across 5 themes, 3 difficulty levels, with bilingual content |

## QA pass summary

See `QA-REPORT.md` for the full structural/data validation. Headline:

- **Status: PASS** — package is structurally complete
- All 12 expected files exist
- All 5 JSON files parse cleanly with matching entry counts
- All 5 prototypes have valid HTML structure, standard CSS variables, fetch calls with inline fallback, and documentation comment blocks
- Slug-normalization pass completed — every `curriculum_slug` in every JSON now maps to a real on-disk page
- External URLs verified to come from approved issuer domains

**Cleared for Claude Design handoff: YES.**

## What to expect from Claude Design

Each prototype is intentionally rough at the polish level. Common patterns Claude Design will likely improve:

- **Animation timing & easing** — the prototypes use understated transitions; design will make them feel intentional
- **Mobile responsiveness fine-tuning** — the prototypes have working mobile fallbacks but the breakpoints can be refined
- **Empty states & loading states** — currently minimal
- **Microcopy and tooltip phrasing** — could be sharpened
- **Visual hierarchy in dense areas** — timeline cluster around 2014-15 / 2022-23, compliance KPI tiles, working-groups upcoming calendar
- **Cross-component visual consistency** — the design-system pass will catch any drift

## What stays the same after Claude Design

These are fixed contracts that should NOT change in the design pass:

- **Data file schemas** — the prototypes' polished versions consume the same JSON shape
- **CSS variable names + values** (`--ink`, `--accent`, etc.) — these match the rest of jpinv.com and changing them breaks the site's visual coherence
- **Typography stack** — Noto Serif JP / Noto Sans JP / DM Mono
- **The 5-component split** — each component is a standalone page on the live site; don't merge or split them
- **The fetch-with-fallback pattern** — keeps the prototypes runnable offline

## Files to NOT upload to Claude Design

These are internal artifacts not relevant to the design pass:

- `QA-REPORT.md` — for internal record only
- `research/` folder (if any) — out of scope
- The 27 curriculum markdown files under `/jpinv-governance-curriculum/` — those are the source of the data but design doesn't need them directly

## A note on the agent architecture

For the record, this package was built by:

- 1 **orchestrator** (this conversation)
- 5 **data sub-agents** in parallel — one per JSON file
- 5 **prototype sub-agents** in parallel — one per HTML prototype
- 1 **QA sub-agent** at the end
- Plus the orchestrator's direct work on `DESIGN-BRIEF.md`, `INTEGRATION-PLAN.md`, the slug-normalization script, and this handoff

Total elapsed time: about an hour of clock time, but the parallelism made it feel shorter.

---

## tl;dr

Open `claude.ai/design`. Upload `DESIGN-BRIEF.md` and `INTEGRATION-PLAN.md` first to set context. Then iterate on each of the 5 prototype HTML files with their corresponding data file. After 5 component sessions + 1 cross-cutting style-system session, the implementation engineer can wire everything into the live `jpinv.com` site per `INTEGRATION-PLAN.md`.

The data is solid. The prototypes work. Design pass is the next step.

Welcome back when ready.
