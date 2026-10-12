# Approved Compounder Profile template

Version 1.2 — approved by Teddy on October 12, 2026.

The approved publication baseline is commit
`30d0df0893750ccdd6fc1e04882ab9ef18b33214` (PR #512), incorporating the
guidance/growth panels in PR #510 and the Japanese label correction in PR #511.
NSD is the worked example of the refinements; NJS remains the shared page shell.

## Carry forward

- Keep the seven section roles and bilingual headings: Summary, Business,
  Performance, Outlook, Financial position and shareholder returns, Share price
  and valuation, and What to watch. Figure selection and count follow the company's
  evidence; NSD's seven figures are not a quota for other companies.
- Use shared qualitative column/role headings once above the aligned rows. Keep
  their accessible header associations and readable mobile layout. The same rule
  applies across the figure family, rather than to a single figure.
- Put explanatory notes and document/page attribution beneath figures. Identify
  JII's calculations or compilation. The final source shelf is `参考資料` / `Sources`.
- Keep featured-card metrics on the accepted light background, in compact label/value
  rows with restrained 16px values and subordinate period notes. Expand ROCE on first
  use as `投下資本利益率（ROCE）` / `Return on capital (ROCE)`.
- Keep the six headline metric roles. When a sales-growth comparison is supplied,
  show the amount first and the growth below it in smaller parentheses, followed by
  its period. Preserve forecast/actual status and the dates of price, cash and shares.
- Introduce EV at the first visible use as `企業価値（EV）` / `enterprise value (EV)`,
  including a deck or masthead metric. Independently introduce it again at the first
  use in running body prose; a masthead, figure or note definition does not satisfy
  this body-text requirement. Later uses in that prose may remain `EV`. For the initial
  forward ratio, use `企業価値（EV） / 予想営業利益` / `Enterprise value (EV)/forecast EBIT`,
  adapting the earnings measure when appropriate. The forecast qualifier belongs
  to earnings. The Japanese initial ratio label has a clean line break between its
  numerator and denominator.

## Make guidance and plan comparisons useful

Current-year guidance figures use the latest reported cumulative quarter and latest
full-year company guidance available at the report's snapshot date. Show the actual,
guidance, progress rate and difference. State the reporting period, guidance revision
date, accounting scope and common unit. Put the rate where phone readers can see it;
the amounts remain accessible through horizontal scrolling.

Use `通期予想との差額` for guidance less cumulative actuals, with a note naming the
actual period used. This is JII's subtraction, not a separately disclosed company
forecast for the remaining quarters. Preserve the original precision so actual plus
difference reconciles to guidance. A progress rate alone does not establish whether
the company is ahead or behind its seasonal schedule.

Medium-term plans show the actual base, target, years between them and total growth
and/or CAGR (`年平均成長率`). Distinguish company targets from JII forecasts. Use
percentage points for margin changes; do not calculate CAGR from a zero/negative base
or treat a margin movement as revenue/profit growth. Separate current-year progress
and medium-term growth into titled panels when their periods differ.

## Author and verify the next company

Read original Japanese issuer and analyst passages before drafting, including captions,
column headings, legends and calculation notes. Record the source/page, observed wording,
intended meaning and chosen Japanese. Distinguish observed source language from JII's own
descriptive wording. Complete Japanese first, then translate the accepted payload into
English. Carry forward the layout and rules; research the next company's argument,
figures, values, dates, sources, forecast ownership and earnings denominator anew.

The shared implementation is in `tools/lib/compounder-profile-template.mjs`,
`assets/compounder-profile.css`, `tools/lib/compounder-figure-labels.mjs` and
`tools/lib/compounder-ev-first-use.mjs`. The profile-system checker rejects repeated
figure labels, broken header associations and an undefined first EV use. Its regression
tests run in the visual-first workflow.

Run the complete profile/archive/homepage build and dependent checks. Verify Japanese
and English desktop/390px presentation, the profile library and hub, and both main
homepages' Reports feed. Preserve source precision and bilingual arithmetic. Publish
through a reviewed commit/PR with successful checks, then verify the live outputs.
The owning local Compounder workflow's master and standards remain the full research,
authoring and release instructions.
