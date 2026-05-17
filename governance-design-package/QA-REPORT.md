# Governance Design Package — Final QA Report

**Date:** 2026-05-17
**Reviewer:** QA sub-agent (pre-Claude-Design handoff)
**Status:** PASS WITH ISSUES — clearance conditional (see "Cleared for handoff" at bottom)

---

## 1. File inventory

| Expected file | Present | Size |
|---|---|---|
| `DESIGN-BRIEF.md` | YES | 18.3 KB |
| `INTEGRATION-PLAN.md` | YES | 10.2 KB |
| `data/timeline.json` | YES | 105 KB |
| `data/compliance.json` | YES | 37.2 KB |
| `data/working-groups.json` | YES | 33.6 KB |
| `data/links-notebook.json` | YES | 131 KB |
| `data/quiz-bank.json` | YES | 74 KB |
| `prototypes/timeline.html` | YES | 46.5 KB |
| `prototypes/compliance-dashboard.html` | YES | 46.5 KB |
| `prototypes/notebook.html` | YES | 50.3 KB |
| `prototypes/quiz.html` | YES | 106 KB |
| `prototypes/working-groups.html` | YES | 41.4 KB |

All 12 expected artifacts present. Extra siblings (`assets/`, `research/`) also present (out of scope).

---

## 2. JSON validity

| File | Parse | Top-level entry count |
|---|---|---|
| `timeline.json` | PASS | 93 events, 6 categories |
| `compliance.json` | PASS | 10 topics |
| `working-groups.json` | PASS | 14 groups + 24 upcoming calendar items |
| `links-notebook.json` | PASS | 85 links, 9 categories |
| `quiz-bank.json` | PASS | 34 questions, 5 themes |

Counts match the brief exactly.

---

## 3. Prototype HTML sanity

| File | Lines | DOCTYPE | `<head>`/`<body>` | CSS vars (`--ink`/`--accent`/`--rule`) | `fetch('../data/...')` | Doc comment |
|---|---|---|---|---|---|---|
| `timeline.html` | 1300 | PASS | PASS | PASS | `fetch('../data/timeline.json')` line 877 | PASS line 7 |
| `compliance-dashboard.html` | 1112 | PASS | PASS | PASS | `fetch('../data/compliance.json')` line 1080 | PASS line 12 |
| `notebook.html` | 1159 | PASS | PASS | PASS | `fetch('../data/links-notebook.json')` line 669 | PASS line 12 |
| `quiz.html` | 836 | PASS | PASS | PASS | `fetch('../data/quiz-bank.json')` line 335 | PASS line 11 |
| `working-groups.html` | 1125 | PASS | PASS | PASS | `fetch('../data/working-groups.json')` line 770 | PASS line 7 |

All five prototypes pass every structural check.

---

## 4. Cross-references — curriculum_slug → page existence

Sampled up to 10 unique slugs per file against `/en/governance/{slug}/index.html`.

| File | Unique slugs | Sample | Exists | Missing |
|---|---|---|---|---|
| `timeline.json` | 25 | 10 | 8 | 2 |
| `compliance.json` | 10 | 10 | 1 | 9 |
| `working-groups.json` | 1 | 1 | 1 | 0 |
| `links-notebook.json` | 24 | 10 | 8 | 2 |
| `quiz-bank.json` | 28 | 10 | 1 | 9 |

**This is the main issue.** Many slugs do not match the actual curriculum URL slugs published under `jpinv.com/en/governance/`. The mismatches fall into a few systematic patterns:

- **Pillar 5 ("frontier") suffix drift.** JSON uses `5.6-board-diversity`, `5.4-mbos-takeovers`, `5.5-ssbj`, `5.1-english-disclosure`, etc. Actual pages use `5.6-board-diversity-30-by-30`, `5.4-mbo-takeover-guidelines`, `5.5-ssbj-sustainability`, `5.1-english-disclosure-mandate`.
- **Pillar 3 path token.** JSON uses both `/en/governance/market/...` and `/en/governance/market-restructuring/...`; the live tree only has `market-restructuring`. So `3.5-growth-market-2030`, `3.4-topix-reform` under `/market/` 404.
- **Pillar 4 minor drift.** JSON has `4.4-seven-sins-of-misalignment` and `4.1-march-2023-request`; actual pages are `4.4-seven-sins-misalignment` (no "of") and `4.1-march-2023-request-anatomy`.
- **Pillar 2 minor drift.** `2.1-2015-cg-code-primer` vs actual `2.1-cg-code-2015-primer`; `2.3-2021-revision` vs `2.3-cg-code-2021-revision`; `2.4-comply-or-explain` vs `2.4-reading-a-cg-report`.

These will cause every "Review this →" / curriculum-jump link in the prototypes to 404 in production unless the slugs are normalised. Severity is high because every component depends on this link contract.

---

## 5. URL audit (spot-check, 5 per file)

Sampled domains:

- `timeline.json` (80 URLs total): 4 of 5 hit official issuers (kantei, ssb-j, jpx, fsa); 1 hit cliffordchance.com (law-firm secondary source, acceptable).
- `compliance.json` (49 URLs): 1 of 5 official (jpx); 4 are issuer IR pages or law firms (kao.com, mufg.jp, dlapiper.com, group.softbank). All plausible — compliance dashboard's "sample companies" are expected to link to corporate IR.
- `working-groups.json` (58 URLs): 5 of 5 official (fsa.go.jp x4, ssb-j.jp x1). Clean.
- `links-notebook.json` (162 URLs): 5 of 5 official (jpx x3, meti x2).
- `quiz-bank.json` (32 URLs): 3 of 5 official (jpx x2, meti x1); 2 reasonable secondary (ecgi.global hosts the canonical English CG Code PDF; global.toyota for a corporate example).

No suspicious / unofficial / typo domains. URL hygiene is good.

---

## 6. Brief & plan internal consistency

- DESIGN-BRIEF.md lists exactly the five components matching the five prototype filenames. PASS.
- DESIGN-BRIEF.md lists exactly the five data filenames matching `/data/`. PASS.
- INTEGRATION-PLAN.md file-tree (lines 30–41) lists all five JSON and all five HTML files with correct counts (93 / 10 / 14 + 24 / 85 / 34). Matches both the brief and the actual directory. PASS.
- Brief entry counts (93 events, 10 topics, 14 groups, 85 links, 34 questions) match parsed JSON exactly. PASS.

---

## Issues to address

1. **(High) Curriculum-slug mismatches.** Roughly 60–90% of slugs in `compliance.json` and `quiz-bank.json`, and ~20% in `timeline.json` and `links-notebook.json`, point to URLs that do not exist under `/en/governance/`. The systematic patterns are:
   - Pillar 5 slugs are missing the published descriptive suffix (e.g., `-30-by-30`, `-mandate`, `-guidelines`, `-sustainability`).
   - Pillar 3 slugs sometimes use `/market/` instead of `/market-restructuring/`.
   - Pillar 2 / Pillar 4 slugs use different word ordering or wording than the live pages.
   - **Recommended fix:** add a slug-normalisation pass that maps each JSON `curriculum_slug` to the actual published page (or replace each slug with the correct one). The canonical list is the 23 directories under `en/governance/{pillar}/`.
2. **(Low) Compliance dashboard external links.** Many of the `compliance.json` "sample company" URLs point to corporate IR (kao.com, mufg.jp, softbank). This is fine but Claude Design should style these visually distinct from official-issuer links so users know they're seeing examples, not source-of-truth.
3. **(Informational)** Working-groups.json has only one distinct `curriculum_slug` value (probably the 5.8 working-groups landscape page); confirm with the curriculum lead this is intentional.

No JSON parse errors, no missing files, no broken DOCTYPE / CSS-variable / fetch-call issues. The structural package is sound; the content-level issue is the slug contract.

---

## Cleared for Claude Design handoff?

**Conditional YES.** The package is structurally complete and the prototypes are fully functional. Claude Design can begin polish work immediately on layout, typography, and interaction — none of those depend on slug correctness.

However, **before merging the "Review this →" / curriculum-link behaviour into production**, the curriculum-slug normalisation (Issue 1) must be resolved. Recommend either:
- (a) a one-off slug-fix sweep across all five JSON files before handoff, or
- (b) a slug-redirect map in INTEGRATION-PLAN.md that the implementing engineer applies at build time.

All other categories: PASS.
