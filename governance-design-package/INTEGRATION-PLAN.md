---
title: "Integration Plan — wiring the interactive layer into jpinv.com"
prepared: "2026-05-17"
status: "Ready for implementation after Claude Design pass"
---

# Integration Plan

How the 5 new interactive components plug into the existing jpinv.com static-site tree.

## File layout after integration

```
jpinv.com/
├── index.html                                                [callout already in place]
├── en/index.html                                             [callout already in place]
├── en/governance/
│   ├── index.html                                            [REPLACE: embed timeline + quiz]
│   ├── compliance/index.html                                 [NEW: compliance dashboard page]
│   ├── working-groups/index.html                             [NEW: working-groups dashboard page]
│   ├── quiz/index.html                                       [NEW: full multi-mode quiz page]
│   ├── toolbox/index.html                                    [REPLACE: notebook UI on the markdown data]
│   ├── timeline/index.html                                   [NEW: full-screen timeline page]
│   └── ... existing post tree (27 posts + 5 theme intros) ...
├── governance/                                               [Japanese mirror — same structure]
├── governance-design-package/
│   ├── DESIGN-BRIEF.md                                       [this brief]
│   ├── INTEGRATION-PLAN.md                                   [this file]
│   ├── CLAUDE-DESIGN-HANDOFF.md                              [final handoff]
│   ├── data/
│   │   ├── timeline.json                                     [93 events]
│   │   ├── compliance.json                                   [10 topics]
│   │   ├── working-groups.json                               [14 groups + 24 calendar items]
│   │   ├── links-notebook.json                               [85 link entries]
│   │   └── quiz-bank.json                                    [34 questions]
│   └── prototypes/
│       ├── timeline.html                                     [working prototype]
│       ├── compliance-dashboard.html                         [working prototype]
│       ├── notebook.html                                     [working prototype]
│       ├── quiz.html                                         [working prototype]
│       └── working-groups.html                               [working prototype]
└── ...
```

## Page-by-page plan

### Curriculum hub · `/en/governance/index.html` (replace)

The current hub has a stats band, a theme-card grid, a 5-question knowledge check, and a "three ways to read" section. The Claude-Design pass should:

1. **Add a timeline section** above the theme grid. Use the polished `timeline.html` rendering. The timeline is the visual hero — the kind of thing screen-shotted on Twitter.
2. **Keep the theme grid** essentially as-is.
3. **Keep the 5-question knowledge check**, but reframe it as "Quick check — try the full quiz at `/en/governance/quiz/` →".
4. **Add three new feature cards** linking to:
   - `/en/governance/compliance/` — "Compliance Dashboard"
   - `/en/governance/working-groups/` — "Working Groups · What's next"
   - `/en/governance/quiz/` — "Full quiz · 34 questions"
5. **Keep the IR Toolbox keystone callout** but link it to the new interactive `/en/governance/toolbox/` (which is the notebook UI on the same data).

Estimated effort: 1 design sprint.

### Compliance Dashboard · `/en/governance/compliance/index.html` (new)

Standalone page hosting the polished compliance dashboard. Layout:

- Top nav + curriculum sub-nav (Compliance is highlighted as current page)
- Page header: "Japanese Governance Compliance Dashboard · as-of date"
- The compliance dashboard component (full-width)
- Footer with "Methodology" link → small page explaining data sources / limitations + last-refresh date

Estimated effort: half a design sprint.

### Working Groups Dashboard · `/en/governance/working-groups/index.html` (new)

Standalone page hosting the polished working-groups dashboard. Layout:

- Top nav + sub-nav (Working Groups is highlighted)
- Page header: "What Japan's Regulators Are Working On Now · as-of date"
- The working-groups dashboard component (full-width)
- Footer cross-link to Theme 5.8 ("Working Groups That Are Writing Japan's Next Governance Rules")

Estimated effort: half a design sprint.

### Quiz · `/en/governance/quiz/index.html` (new)

Standalone page hosting the polished multi-mode quiz. Layout:

- Top nav + sub-nav (Quiz is highlighted)
- Page header: "Test Your Governance Fluency · 34 questions, 5 themes, 4 modes"
- The quiz component (full-width, centred on a max-width 760px column)
- Footer with "Read the curriculum →" cross-link

Estimated effort: half a design sprint.

### Notebook · `/en/governance/toolbox/index.html` (replace)

Current page is a long-form markdown rendering of the IR Toolbox. Replace with the interactive notebook UI. Layout:

- Top nav + sub-nav
- Page header: "The IR Toolbox — Japan Governance Reference Library"
- The notebook component (sidebar + card grid)
- Footer with "Source list (download as JSON / CSV)" links

Estimated effort: half a design sprint.

### Timeline · `/en/governance/timeline/index.html` (new)

A standalone full-screen timeline page for deep timeline exploration. Embedded version lives on the hub; standalone version is for users who arrive directly via a shared link. Layout:

- Top nav + sub-nav
- Page header: "Japan Governance Reform · 1989 → 2026"
- The timeline component (full-width, full-height)
- Footer with "Share this view" (URL-hash-encodes current filter state)

Estimated effort: half a design sprint.

### Japanese mirror · `/governance/...` (new)

Mirror all of the above under `/governance/` for the Japanese site. The data files are bilingual, so no extra data work is needed. The UI strings need professional Japanese — the prototypes already have an EN/JA toggle wired in and use the `_ja` fields from the JSON.

Estimated effort: 1 design sprint (after the EN pass is settled).

## Data refresh cadence

| Data file | Refresh cadence | Trigger |
|---|---|---|
| `timeline.json` | Quarterly | After each FSA Action Programme / TSE follow-up announcement |
| `compliance.json` | Monthly | When TSE publishes new monthly disclosure-list |
| `working-groups.json` | Quarterly | After each major WG meeting cycle |
| `links-notebook.json` | Quarterly | URL re-verification + new artifact additions |
| `quiz-bank.json` | As-needed | When new curriculum posts are added |

A simple cron / GitHub Action can fetch the relevant JPX/FSA pages, parse, and bump the JSONs. Out of scope for this design pass — a Phase-3 automation item.

## Build-time vs runtime data loading

The prototypes use `fetch('../data/foo.json')` at runtime. For production, two options:

**Option A: Keep runtime fetch.** Pro: data refreshes don't require rebuilds. Con: an extra HTTP round-trip on each page load (mitigated by HTTP/2 and caching).

**Option B: Bake data into the HTML at build time** via a small Node/Python script. Pro: instant render, no extra HTTP round-trip. Con: data refreshes require a rebuild + commit.

**Recommendation:** Option A for now. Switch to B only if performance metrics show a problem.

## Backwards-compatibility notes

- The current `/en/governance/toolbox/` page (markdown-rendered) should keep working until the notebook replacement is deployed. The notebook UI can be A/B-tested as a feature flag (?ui=notebook) before full cutover.
- The 5-question knowledge check on the current hub should be preserved on the hub even after the full quiz page launches — it's the entry hook.
- All existing `/en/governance/{theme}/{post}/` URLs must keep working. The interactive layer adds on top of them, doesn't replace them.

## Sitemap.xml updates

After integration, append these new URLs to `sitemap.xml`:

```xml
<url><loc>https://jpinv.com/en/governance/compliance/</loc><priority>0.9</priority></url>
<url><loc>https://jpinv.com/en/governance/working-groups/</loc><priority>0.9</priority></url>
<url><loc>https://jpinv.com/en/governance/quiz/</loc><priority>0.85</priority></url>
<url><loc>https://jpinv.com/en/governance/timeline/</loc><priority>0.9</priority></url>
<url><loc>https://jpinv.com/governance/compliance/</loc><priority>0.9</priority></url>
<url><loc>https://jpinv.com/governance/working-groups/</loc><priority>0.9</priority></url>
<url><loc>https://jpinv.com/governance/quiz/</loc><priority>0.85</priority></url>
<url><loc>https://jpinv.com/governance/timeline/</loc><priority>0.9</priority></url>
```

Each pair needs the hreflang `<xhtml:link>` declarations (mirror the existing pattern).

## Suggested commit-by-commit order

Each item below is one ship-able commit:

1. **Polish timeline → embed on hub** (the existing hub gets a timeline section)
2. **Compliance dashboard standalone page**
3. **Working-groups dashboard standalone page**
4. **Full-quiz standalone page**
5. **Notebook replaces toolbox markdown** (with feature flag fallback for 30 days)
6. **Full-screen timeline standalone page**
7. **Japanese mirror of all of the above** (single bigger commit)
8. **Sitemap.xml + footer + nav updates** (cleanup pass)
9. **Cross-cutting design-system extraction** (refactor reusable patterns into shared CSS classes)

## Performance targets

- Each new page <300 KB total transfer (incl. fonts)
- Largest Contentful Paint <2.5s on 3G
- Time to Interactive <3.5s on 3G
- Lighthouse Accessibility ≥ 95 on every new page
- Lighthouse SEO ≥ 95 on every new page

## What stays the same

- Top nav, footer, locale switcher
- The 27 curriculum posts (unchanged)
- The 5 theme intro pages (unchanged)
- The /compounders/ section (unchanged)
- The services / pricing / company / faq pages (unchanged)
- The homepage callouts (already point to the right URLs)
- The CG colour palette and typography (mandatory — no changes)

---

*Implementation can begin as soon as the Claude Design polish pass is complete.*
