---
title: "Japan Governance Curriculum · Interactive Design Brief"
prepared_for: "Claude Design (claude.ai/design)"
prepared_by: "jpinv.com editorial · orchestrator agent"
date: "2026-05-17"
status: "Ready for design pass"
---

# Design Brief — Japan Governance Reform Curriculum, Interactive Layer

## Why we're here

The Japan Governance Reform Curriculum lives at `https://jpinv.com/en/governance/` (English, fully populated) and `https://jpinv.com/governance/` (Japanese hub + theme intros translated, individual posts as stubs). Twenty-seven primary-source-anchored blog posts, organised into five themes, plus an IR Toolbox reference page. ~63,000 words of editorial-grade material.

The text is the foundation. What this brief asks Claude Design to build is **the interactive layer that turns that foundation into a learning experience**: a timeline that lets an IR rep see the whole arc at a glance, a compliance dashboard that turns disclosure-list data into actionable knowledge, a notebook for the reference library, a multi-mode quiz for fluency testing, and a working-groups dashboard for what's coming next.

## Who it's for

Three audiences, in order of importance:

1. **An IR representative at a Japanese listed company** who needs to be conversant with the whole reform arc within a week of being assigned to the role. The dominant persona — every design choice should serve them.
2. **Overseas investors and analysts** who want to read Japan's governance system through a primary-source-anchored explainer. They will arrive via the English homepage callout.
3. **Board secretariats and CFO offices** preparing for AGM season, MTM disclosure, or engagement dialogue.

What none of these audiences are: a casual visitor. They are professionals who will return to the site multiple times. The interactive layer should reward repeat use (progress tracking, bookmarks, recent-views).

## Design language (mandatory — match the rest of jpinv.com exactly)

```
--ink:        #1a2a4a   /* primary text and emphasis */
--ink-mid:    #172641
--ink-soft:   #304466
--rule:       #d6dee8   /* subtle borders */
--rule-soft:  #e8edf3
--bg:         #ffffff
--bg-mid:     #f5f7fa
--bg-soft:    #fafbfc
--text:       #1f2937
--text-mid:   #4a5566
--text-dim:   #5f6875
--accent:     #9a7838   /* muted gold — used for labels, key highlights, accent lines */
--accent-soft:#f4eee4   /* very pale gold background tint */
--bad:        #b91c1c
--warn:       #8a682b
--ok:         #2f6f4f

--serif: 'Noto Serif JP', 'Yu Mincho', serif
--sans:  'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif
--mono:  'DM Mono', monospace
```

Aesthetic: editorial, muted, professional. No rainbow palettes. No glassmorphism. Subtle borders preferred to shadows. The accent gold is for emphasis only — never for large fills. Headlines in serif; body in sans; metadata and labels in mono uppercase with letter-spacing.

For chart colours, the existing convention is `--ok #2f6f4f` for compliant / disclosed / good, `--warn #8a682b` for partial / under consideration, and `--bad #b91c1c` for non-compliant / not disclosed.

## The five interactive components

### 1. Horizontal Timeline · 1989 → 2026

**Goal:** Let an IR rep see the full sweep of Japan's governance arc in one screen, then drill into any moment.

**Data:** `data/timeline.json` — 93 events spanning Dec 1989 (Nikkei peak) to May 2026 (FIEA effective). Each event has `date`, `category` (one of six), `importance` (1–5), bilingual title/summary, source URL, and a `curriculum_slug` linking back to the relevant curriculum post.

**Prototype:** `prototypes/timeline.html` (~1,200 lines, self-contained).

**Interaction model:**
- Horizontal rail, decade markers (1990s, 2000s, 2010s, 2020s) as bold vertical labels, year ticks between
- Events plotted as **dots**, sized by importance (1=small, 5=large), coloured by category
- Above/below alternating layout to reduce collision (the prototype uses greedy packing; the design pass should consider force-directed layout or carefully hand-tuned positioning for the worst clusters around 2014-15 and 2022-23)
- Hover tooltip with title + date
- **Click → slide-out right panel** with full bilingual detail, source link, and a primary CTA "Read full curriculum post →" that navigates to `curriculum_slug`
- Filters above the rail: category chip multi-select, importance ≥ slider, EN/JA toggle
- Year-jump dropdown or scrubber for quick navigation

**Mobile:** The rail rotates to vertical, dots flow top-to-bottom on alternating sides of a centre axis.

**Design-pass priorities:**
- Polish the dense clusters (2014-15 and 2022-23 have ~8 events each within 24 months)
- Better visual hierarchy on importance — make the importance-5 dots feel like landmarks (perhaps a small inner gold ring)
- Smoother slide-out panel animation
- A "scroll the decade" affordance — currently it's a horizontal scroll with no visual reinforcement that more content exists offscreen
- Consider a mini-overview band above the main rail that shows the whole 1989-2026 span with a draggable lens (like Datadog's time selector)

### 2. Compliance Dashboard

**Goal:** Turn JPX's published disclosure-list data into a visual, drillable view that an IR rep can use to benchmark their own company.

**Data:** `data/compliance.json` — 10 topics (cost-of-capital, English disclosure, cross-shareholdings, board diversity, independent directors, TCFD, skills matrix, transitional measures, SSBJ Phase 1, MBO special committees). Each topic has segment-level counts, a trend array, sample companies, and primary-source URLs.

**Prototype:** `prototypes/compliance-dashboard.html` (~1,100 lines, Chart.js).

**Interaction model:**
- Horizontal topic tabs (sticky), with a numbered-card style. Tab counts: Prime / Standard / Growth.
- Per-topic detail view: 4 KPI tiles + stacked-bar (segments × status) + donut (aggregate) + trend line + sample-companies table + primary-source links
- **Click a bar segment → drill-down panel** showing the filtered company list ("Not disclosed companies on Prime as of 2026-03-31"). When the sample is limited, link out to the full JPX list.
- **Click a trend-line point → snapshot panel** showing that date's status across segments.
- EN/JA toggle.

**Mobile:** Tabs become a dropdown. Charts stack. Tables horizontal-scroll.

**Design-pass priorities:**
- Chart styling: the prototype uses Chart.js defaults — Claude Design should hand-tune colours to match the editorial palette (no shiny gradients, flat fills, ink-coloured grid lines).
- A "What this means for IR" plain-language summary alongside each chart.
- For topics where data is partly estimated, render the estimated portions with a dashed line / muted style — the data file already flags these with `"estimate": true`.
- Consider a "company self-check" widget: input your ticker, see where you sit in the distribution across all 10 topics.
- Heatmap view (rows = topics, columns = companies in your peer set) as a stretch idea.

### 3. IR Notebook

**Goal:** Replace the markdown-table IR Toolbox with a searchable, filterable, card-grid reference library.

**Data:** `data/links-notebook.json` — 85 entries across 9 categories (codes, market, lists, good-practice, guidelines, working-groups, faqs, data, investor). Each entry has bilingual title/summary/why-IR-cares, issuer, format, tags, EN+JA URLs, and a `curriculum_slug`.

**Prototype:** `prototypes/notebook.html` (~1,160 lines).

**Interaction model:**
- Sticky left sidebar with faceted filters: Category (9), Issuer (FSA / JPX / METI / SSBJ / MoJ / GPIF / JIRA), Format (PDF / HTML / Dashboard), Language (EN / JA / Both), Tag cloud
- Search bar at top (debounced 200ms, full-text across title/summary/tags)
- Sort: most recent / alphabetical / by category
- 3-column card grid (1-column mobile). Each card: issuer badge, title, summary, tag chips, "Open →" button
- Hover: lifts, shows "why IR cares" + curriculum-link
- Copy-link button with toast feedback
- "Open all in new tabs" group action when filtered to one category
- localStorage persists last-used filters and language

**Mobile:** Sidebar becomes a slide-in drawer.

**Design-pass priorities:**
- The card grid is the most-likely-revisited surface. It needs to feel inviting at first glance: better visual hierarchy in the cards (issuer badge as the dominant visual cue, title as the readable element, tags as small affordances).
- Tag-cloud rendering: currently a flat list. Could be sized by frequency, organised by colour by category.
- Empty state when no results: not just "no matches", but suggest filters to relax.
- Saved searches / bookmarks: localStorage already persists last filter; add explicit "Save this view" / "Saved views" UI.
- A "What's new" pill on entries updated in the last 30 days (data file has `last_revised`).

### 4. Multi-mode Quiz

**Goal:** Let an IR rep test fluency end-to-end, by theme, by difficulty — and learn from mistakes by linking back to the curriculum.

**Data:** `data/quiz-bank.json` — 34 questions across 5 themes, with `intro` / `intermediate` / `advanced` difficulty tags. Each question has bilingual stem/options/explanation, correct answer, source URL, and a `curriculum_slug` for the "Review this →" link.

**Prototype:** `prototypes/quiz.html` (~840 lines).

**Interaction model:**
- Start screen with 4 mode buttons: Quick check (5 random) / Full assessment (all 34) / By theme / By difficulty
- Question screen: progress bar, theme + difficulty badges, stem, 4 stacked option buttons, Submit
- On submit: highlight correct (green) / chosen-incorrect (red), reveal 2-3 sentence explanation + source link + "Read curriculum post →"
- Results screen: total score, per-theme breakdown bars, list of incorrect questions with links to curriculum posts, Retry / Try another mode
- localStorage saves personal best per mode

**Mobile:** Options stack. Progress bar full-width.

**Design-pass priorities:**
- The submit reveal is the moment of truth — make it feel satisfying. Check/cross animations (the prototype has SVG path draw-on at understated scale; design can dial up).
- A streak / spaced-repetition layer: track which questions a user has answered correctly N times and de-prioritise them.
- A "Daily question" widget for the curriculum hub — pulls one random question per day.
- Visual representation of progress through the curriculum (e.g., a hex-grid of all 34 questions with mastery state).
- Per-theme score breakdown: bar chart that links each bar to "weak areas → these curriculum posts will help".

### 5. Working Groups Dashboard

**Goal:** Give an IR rep a live operational view of which Japanese regulators are working on what, and what to expect in the next 90 days / 12 months.

**Data:** `data/working-groups.json` — 14 active/recent groups + 24 upcoming calendar items. Each group has issuer, chair, mandate, recent outputs, upcoming meetings/outputs, focus topics for 2026.

**Prototype:** `prototypes/working-groups.html` (~1,050 lines).

**Interaction model:**
- Header with "as-of" date + status filter (Active / Dormant / Completed)
- **"What's coming next 90 days" digest** call-out at top — a curated list extracted from `upcoming_calendar`
- **12-month horizontal calendar timeline** — colored markers by issuer, click to jump to the relevant group card
- Card grid: one card per working group with issuer badge, name (EN serif + JA), chair, status pulse-dot, mandate, recent outputs list, upcoming items list, focus topics chips
- Filters by issuer, status, sort by next-meeting date
- "By-issuer summary" bar at bottom — count per issuer

**Mobile:** Cards stack. Calendar horizontal-scrolls.

**Design-pass priorities:**
- This is the "mission control" component. Make it feel current and operational: status indicators (pulsing green dot for active, grey for dormant, strikethrough for completed) help a lot.
- The 90-day digest is the most-likely-shared surface. Style it as a "newsletter blurb" candidate — clean, copyable, with named items.
- The 12-month calendar timeline currently has marker overlap in busy months — design should solve collision with vertical stacking or hover-disambiguation.
- A "Subscribe to working-group calendar" feed (ICS export) as a future enhancement.
- Tags by topic across groups (e.g., "sustainability") to show which groups are working on the same topic.

## Cross-cutting design system additions

These are new patterns this curriculum needs that don't exist on the rest of the site:

### Slide-out detail panel
The timeline and compliance dashboard both use a right-anchored slide-out panel for detail. Design should define a standard width, animation, dismiss behaviour, and content layout for this pattern so it can be reused for future features (e.g., individual case-study deep-dives).

### Faceted filter rail
The IR Notebook uses a left sidebar of faceted filters. Define standard filter component states (idle / active / disabled / hovered), checkbox styling, count badges.

### Status pulse dot
The working-groups dashboard uses a small pulsing dot for "active". Define the size, colour mapping (active/dormant/completed), and animation timing.

### KPI tile
The compliance dashboard uses a 4-up grid of KPI tiles. Define a standard tile: label (mono uppercase) + big number + small delta indicator.

### Card-grid empty state
All three card-grid components (notebook, working groups, post lists) need an empty state. Define one reusable pattern.

## Interactions to add across the existing curriculum posts

Beyond the five new components, several enhancements to the existing 27 posts would significantly increase value. These are simpler — they should be feasible as small additions:

1. **Read-progress indicator** at the top of each post (scroll-bound progress bar).
2. **"Mark as read"** button at the end of each post (localStorage tracks read state; the curriculum hub shows aggregate progress).
3. **Per-post quick-quiz** at the bottom: 1-2 questions from the quiz bank tagged to that post, scored, with explanation reveals.
4. **"Cite this post"** button: opens a small popover with a clean citation in EN / JA, copyable to clipboard.
5. **Audio summary** (Phase 2): a 2-minute spoken summary of each post (TTS-generated, hosted as MP3 on the same path).

## Mobile + accessibility requirements

Non-negotiable:
- All five components must work fully on a 375px-wide viewport.
- Every chart needs a text-alternative summary for screen readers.
- Every interactive element is keyboard-reachable, with visible focus state.
- The colour palette is already designed for WCAG AA contrast.
- All text content is real text (not images) for translation accessibility.

## What is intentionally NOT in this brief

- **Native app**: this is a web-only project.
- **Account / login**: no accounts. Anonymous, localStorage-only persistence.
- **Comments / community**: out of scope.
- **Real-time data**: the JSON files are refreshed monthly (disclosure list) and quarterly (working groups). No live API integration this phase.

## Component dependencies

```
timeline.html       ── data/timeline.json
compliance-dashboard.html  ── data/compliance.json
notebook.html       ── data/links-notebook.json
quiz.html           ── data/quiz-bank.json
working-groups.html ── data/working-groups.json
```

Each prototype is self-contained and reads its data file via `fetch('../data/...')` with inline fallback. The design pass can rewire to a static-site build-time-bake or keep the fetch model.

## Where these components plug into the existing site

See `INTEGRATION-PLAN.md` for the page-by-page integration plan. Headline:

- The **timeline** becomes the visual hero of the English and Japanese curriculum hub pages (`/en/governance/` and `/governance/`).
- The **compliance dashboard** becomes its own page at `/en/governance/compliance/` and `/governance/compliance/`, linked from the hub and from Theme 4 posts.
- The **notebook** replaces the current `/en/governance/toolbox/` page with an interactive version (the markdown stays as the data source).
- The **quiz** is embedded on the curriculum hub (current 5-question version) and gets its own deeper page at `/en/governance/quiz/`.
- The **working-groups dashboard** becomes its own page at `/en/governance/working-groups/`, linked from the hub and from Theme 5.8.

## Suggested first sprint for Claude Design

Order of pass (each pass = polish + visual hierarchy + mobile + a11y + design-system formalisation):

1. **Timeline first** — it's the most viral surface (the kind of thing screen-shotted in a Twitter thread). Get it beautiful.
2. **Compliance dashboard second** — the most operationally useful component, but also the most chart-heavy and most in need of design taste on chart styling.
3. **Working-groups dashboard third** — high-utility, lower polish bar than the timeline.
4. **Notebook fourth** — its base form (sidebar + cards) is well-trodden territory; the design lift is moderate.
5. **Quiz fifth** — the interaction is already engaging; the polish lift is mostly animation feel.

After all five, do a **cross-cutting style-system pass** to formalise the slide-out panel, KPI tile, status pulse, and empty-state patterns into reusable CSS classes.

## Success criteria

- An IR rep coming to `/en/governance/` for the first time understands the scope of the curriculum in <60 seconds of looking at the timeline.
- An IR rep can answer "as of last month, what % of my segment was disclosing on cost of capital?" in <2 clicks on the compliance dashboard.
- An IR rep coming back monthly can find "what's new" in <30 seconds — between the working-groups dashboard and the notebook's "What's new" pill.
- Mobile load time <3 seconds on 3G.
- All five components score Lighthouse accessibility ≥ 95.

---

*All five prototypes are working today. Open them via a local server (`python -m http.server`) at `governance-design-package/prototypes/timeline.html` (and the four others). Each has a top-of-file comment block documenting its data contract, interaction model, and intentional rough edges.*

*Hand off to Claude Design at `https://claude.ai/design` by uploading this brief + the data files + the prototype HTML files.*
