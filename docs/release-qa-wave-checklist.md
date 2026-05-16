# Release QA: manual WAVE accessibility review checklist

Use this checklist after the automated release gates pass and before publishing a public-site release. Automated axe coverage catches blockers in CI, but WAVE is still required for visual/contextual review of semantics, reading order, headings, labels, and language-specific content.

## Route source of truth

The tested route list lives in `qa/routes.cjs`.

- `publicRoutes`: content routes covered by axe smoke tests.
- `lighthouseRoutes`: core JP/EN routes that fail CI on agreed Lighthouse regressions.
- `visualRoutes`: key pages covered by Playwright `toHaveScreenshot()` baselines.
- `rfqRoutes`: pricing pages covered by the RFQ pre-fill visual flow.
- `redirectRoutes`: redirect-only contact URLs checked for accessible fallback links.

When adding a new public page, add it to `publicRoutes` first, then opt it into Lighthouse, visual, or RFQ coverage with the route flags when appropriate.

## Automated release gates

Run before WAVE review:

```bash
npm run qa
```

The release must not ship with failures in these gates:

- Lighthouse CI performance budget regressions on core JP/EN pages.
- Serious or critical axe violations on public content routes.
- Playwright visual screenshot diffs for key pages or the RFQ flow.

## Manual WAVE pass

For each route in `publicRoutes` and each redirect in `redirectRoutes`:

1. Open the local preview URL or staging URL in Chrome.
2. Run the WAVE browser extension.
3. Record the route, reviewer, date, browser version, and WAVE extension version in the release QA notes.
4. Confirm there are no WAVE **Errors**.
5. Confirm any WAVE **Contrast Errors** are either fixed or documented with an approved design exception.
6. Review WAVE **Alerts** manually; resolve anything that affects comprehension, navigation, form completion, or SEO-critical structure.
7. Verify the page has exactly one logical primary heading and a sensible heading hierarchy.
8. Verify landmark regions are meaningful and that the skip link reaches main content.
9. Verify images and SVG logos have appropriate alternative text or are correctly hidden when decorative.
10. Verify links and buttons have unique, descriptive accessible names in both Japanese and English contexts.
11. Verify keyboard-only navigation reaches menus, CTAs, accordions, forms, and locale switchers in a logical order.
12. Verify visible focus is clear against the page background.
13. For RFQ/contact forms, verify labels, required fields, inline errors, status messages, and success messages are announced or exposed correctly.
14. For Japanese pages, verify `lang="ja"`; for English pages, verify `lang="en"`.
15. For responsive review, repeat WAVE and keyboard checks at desktop width and a 390 px mobile viewport.

## RFQ flow manual checks

For every route in `rfqRoutes`:

- Click at least one RFQ CTA.
- Confirm focus/scroll moves to the contact section without trapping the keyboard.
- Confirm service type, document type, source context, and message fields are pre-filled as intended.
- Submit an empty form and confirm inline validation is clear and associated with each field.
- Fill representative valid data without submitting to production endpoints unless the release plan explicitly includes a test submission.

## Sign-off template

```text
Release:
Reviewer:
Date:
Environment:
Automated gates: PASS / FAIL
WAVE extension version:
Routes reviewed:
Findings:
Exceptions approved by:
Ship decision: GO / NO-GO
```
