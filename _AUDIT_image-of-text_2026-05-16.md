# Image-of-Text & Alt-Text Audit — jpinv.com

**Date:** 2026-05-16
**Scope:** Every public page under `jpinv.com/` and `jpinv.com/en/`, plus the redirect stubs and the internal `/availability/` page.
**Method:** Walked the local source tree at `C:\Users\okuya\OneDrive\Desktop\JII\3 Pipeline\5 Assets\Website\jpinv.com`, parsed every `.html` file with a Python HTMLParser, extracted every `<img>`, `<picture>`, `<source>`, inline `<svg>`, and CSS `background-image` / `url()` reference, and reviewed each in context.

---

## Headline Finding

**The site has no image-of-text problem to fix.** Every page that contains substantive copy renders that copy as semantic HTML. The diagnostic-card sample, the process flow, the plans grid, the case grid, the FAQ, the compounder report scorecards and stat strips, the methodology framework — all are real HTML built from `<h*>`, `<p>`, `<ul>`, `<dl>`, `<button>`, and CSS. There is no embedded image of paragraph copy, no scanned process diagram, no rasterised heading anywhere on the public surface.

What does exist is a small, well-contained set of real images, each of which is already either (a) given a localised informative `alt`, or (b) marked decorative with `aria-hidden="true"` and paired with a visible text label. JP and EN copies are in parity on alt semantics, and mobile and desktop variants of the logo use identical alt text.

So, against the brief: no semantic replacement was needed, no alt text needed to be added or corrected, and no JP/EN parity gap was introduced by the existing markup. Source files were not modified. Items worth your review are listed at the bottom.

---

## Pages Audited

| Path | Role | `<img>` | inline `<svg>` | CSS `url(image)` |
|------|------|--------|----------------|------------------|
| `/index.html` | JP landing | 3 | 0 | 0 |
| `/en/index.html` | EN landing | 3 | 0 | 0 |
| `/index-ja.html`, `/index-en.html` | language-redirect stubs | 0 | 0 | 0 |
| `/お問い合わせ/`, `/サービス/`, `/会社概要/`, `/料金/` | JP anchor-redirect stubs | 0 | 0 | 0 |
| `/compounders/index.html` | JP series index | 0 | 0 | 0 |
| `/en/compounders/index.html` | EN series index | 0 | 0 | 0 |
| `/compounders/methodology/index.html` | JP methodology | 0 | 0 | 0 |
| `/compounders/methodology/ja/index.html` | JP methodology duplicate route | 0 | 0 | 0 |
| `/en/compounders/methodology/index.html` | EN methodology | 0 | 0 | 0 |
| `/compounders/universe/index.html` | JP universe | 0 | 0 | 0 |
| `/en/compounders/universe/index.html` | EN universe | 0 | 0 | 0 |
| `/compounders/4194/index.html` | JP Visional report | 0 | 3 (share icons) | 0 |
| `/en/compounders/4194/index.html` | EN Visional report | 0 | 3 (share icons) | 0 |
| `/compounders/4475/index.html` | JP JustSystems report | 0 | 3 (share icons) | 0 |
| `/en/compounders/4475/index.html` | EN JustSystems report | 0 | 3 (share icons) | 0 |
| `/compounders/4776/index.html` | JP Cybozu report | 0 | 3 (share icons) | 0 |
| `/en/compounders/4776/index.html` | EN Cybozu report | 0 | 3 (share icons) | 0 |
| `/availability/index.html` | internal scheduler (not in sitemap) | 0 | 0 | 0 |

The hundreds of `background-image` CSS rules across these files are all `linear-gradient(...)` or `radial-gradient(...)` declarations or solid colors — there is no rasterised image being used as a CSS background anywhere.

---

## Inventory of Every Real Image

### 1. Brand logo — wordmark and monogram

| Where | Element | Variant | Alt | Verdict |
|-------|---------|---------|-----|---------|
| `/index.html:457` | `<img>` | wordmark, desktop | `Japan Investor Interface logo` | Informative, correct |
| `/index.html:458` | `<img>` | monogram, mobile | `Japan Investor Interface logo` | Informative, correct |
| `/en/index.html:442` | `<img>` | wordmark, desktop | `Japan Investor Interface logo` | Informative, correct |
| `/en/index.html:443` | `<img>` | monogram, mobile | `Japan Investor Interface logo` | Informative, correct |

The wordmark renders the brand name in Latin script (the brand itself is "Japan Investor Interface" — not translated), so an English alt is accurate on both the JP and EN pages. Mobile and desktop variants share the same alt string, satisfying the "same alt semantics across viewports" requirement. The logo `<a>` element also carries its own `aria-label` (`JII トップページへ` on JP, `JII Home` on EN), and on mobile the monogram is shown while the wordmark is hidden with CSS — when a screen reader walks the DOM both `<img>` elements still announce the same name, but the link `aria-label` is the primary handle.

### 2. About-section photo

| Where | Element | Source | Alt | Verdict |
|-------|---------|--------|-----|---------|
| `/index.html:763` | `<img class="about-photo">` | inline `data:image/jpeg;base64,...` | `屋山テディ` | Informative, correct (localised) |
| `/en/index.html:748` | `<img class="about-photo">` | inline `data:image/jpeg;base64,...` | `Teddy Okuyama` | Informative, correct (localised) |

A photo of a person carries no recoverable text content; the correct alt is the person's name, localised. This is what's in place.

### 3. Share-button icons (X, email, copy-link)

| Where | Count | How marked |
|-------|-------|------------|
| `/compounders/4194/`, `/4475/`, `/4776/` | 3 each | inline `<svg aria-hidden="true">` |
| `/en/compounders/4194/`, `/4475/`, `/4776/` | 3 each | inline `<svg aria-hidden="true">` |

Each icon is wrapped in a button or anchor that carries both a localised `aria-label` and a visible text label, e.g.:

```html
<a class="share-btn share-x" aria-label="Xで共有">
  <svg viewBox="0 0 24 24" aria-hidden="true">…</svg>
  <span>X</span>
</a>
```

EN parity, sampled from `/en/compounders/4194/`:

```html
<a class="share-btn share-x" aria-label="Share on X">
  <svg viewBox="0 0 24 24" aria-hidden="true">…</svg>
  <span>X</span>
</a>
```

`aria-hidden` on the svg + visible text label + `aria-label` on the control is the textbook treatment for an icon-button. Nothing to change.

### 4. Favicons / app icons

`/favicon.svg`, `/favicon-16x16.png`, `/favicon-32x32.png`, `/apple-touch-icon.png` are referenced only via `<link rel="icon">` / `rel="apple-touch-icon">`. These are user-agent chrome, not page content, so no `alt` applies.

### 5. Open Graph / Twitter card images

| Page | `og:image` | `og:image:alt` |
|------|------------|----------------|
| `/index.html` | `/assets/logo-jii-wordmark.svg` | `Japan Investor Interface logo` |
| `/en/index.html` | `/assets/logo-jii-wordmark.svg` | `Japan Investor Interface logo` |
| `/compounders/4194/` | `/og/4194.png` | `JII Compounders 銘柄レポート · 4194` |
| `/en/compounders/4194/` | `/og/4194.png` | `JII Compounder Profile · 4194` |
| `/compounders/4475/` | `/og/4475.png` | `JII Compounders 銘柄レポート · 4475` |
| `/en/compounders/4475/` | `/og/4475.png` | `JII Compounder Profile · 4475` |
| `/compounders/4776/` | `/og/4776.png` | `JII Compounders 銘柄レポート · 4776` |
| `/en/compounders/4776/` | `/og/4776.png` | `JII Compounder Profile · 4776` |

Localisation of `og:image:alt` is consistent across the bilingual pair. These images are never rendered on the page itself; they appear only when a link is shared on social platforms. They are not in scope for this audit but the metadata is healthy.

---

## JP / EN Parity Check

Every JP page that contains an `<img>` or icon-SVG has an EN counterpart with the same image markup, the same `aria-hidden` treatment for decorative icons, and properly localised alt / `aria-label` strings. The differences I confirmed are:

- About-photo alt: `屋山テディ` ↔ `Teddy Okuyama` (correct)
- Share-button `aria-label`s: `Xで共有 / メールで共有 / リンクをコピー` ↔ `Share on X / Share via email / Copy link` (correct)
- Share-button visible labels: `X / メール / リンクをコピー` ↔ `X / Email / Copy link` (correct)
- `og:image:alt`: `銘柄レポート` ↔ `Compounder Profile` (correct)
- Logo alt: identical English string on both sides (correct — the brand name is not translated)

No JP page references an image that the EN page lacks, or vice versa.

---

## Mobile / Desktop Parity Check

The site uses two visual variants of the logo (`nav-logo-img--desktop` shows the wordmark, `nav-logo-img--mobile` shows the monogram) and both carry identical alt text on both language sides. No mobile-only or desktop-only image exists elsewhere — responsiveness is achieved with CSS, not with separate image assets. Mobile and desktop walk the same DOM with the same alt semantics, as the brief required.

---

## Changes Made

**None.** No source file was modified. The audit confirmed the site already satisfies the brief's requirements:

1. **Image-of-text replaced with HTML/CSS where possible** — already done by construction; no patterns remain to replace.
2. **Localised alt on informative images** — already present on all four informative images (two logo elements per language are intentionally English because the brand wordmark is English; the about-photo alt is localised).
3. **Empty alt / aria-hidden on decorative images** — already in place on all 18 decorative share-icon SVGs.
4. **JP/EN parity** — confirmed.
5. **Mobile/desktop alt parity** — confirmed.

---

## Items Flagged for Your Review

These are out of strict scope for an image-of-text audit but came to the surface during the walkthrough. None of them is an accessibility bug — they are judgement calls for you.

### F-1 · `/og/4776.png` is referenced but does not exist on disk

`/compounders/4776/index.html` and `/en/compounders/4776/index.html` both set `og:image` to `https://jpinv.com/og/4776.png`, but the `/og/` folder contains only `4194.png` and `4475.png`. On X / LinkedIn / Slack the Cybozu report card will render with a broken image or a fallback. Either drop in `og/4776.png` to match its siblings, or change the meta tag to point at the logo wordmark the way the landing pages do.

### F-2 · `twitter:image:alt` meta tag is absent on every page

Every page declares `og:image:alt` but none declares `twitter:image:alt`. Twitter / X mostly inherits the OG value, so this is not a regression — it is a one-line tightening you may want to add for completeness on each page that already has `og:image:alt`. I did not add this because it falls outside "image-of-text" and you asked me to flag ambiguous changes rather than apply them.

### F-3 · The JP `<img alt="Japan Investor Interface logo">` is in English

This is a deliberate choice that matches the visual content of the wordmark (the wordmark itself is in Latin script). A JP screen reader will pronounce "Japan Investor Interface logo" letter-by-letter in English, which is fine but could optionally be rendered as `Japan Investor Interface ロゴ` for a slightly more natural reading. I did not change this — it's a brand-voice decision, not an accessibility defect.

### F-4 · The `about-photo` is inlined as a ~686 KB base64 JPEG

Not in scope for this audit, but worth flagging: the same large data-URI is duplicated in `index.html` and `en/index.html`. Moving it to `/assets/teddy.jpg` and referencing it with `<img src="/assets/teddy.jpg">` would shrink each HTML page by roughly half a megabyte, make the photo cacheable, and let the browser defer-load it. Pure performance, no accessibility impact.

### F-5 · The diagnostic-card sample reads `※ 右の図は構造のサンプルです`

In the JP `/index.html` the explanatory copy refers to the on-screen sample as `右の図` ("the diagram on the right"). On narrow viewports the sample drops below the explanation, so the directional cue ("on the right") can disorient a mobile screen-reader user. This is also out of scope but worth noting. The EN page uses `The card on the right is a sample structure.` and has the same caveat.

---

## Files Produced During the Audit

- `_AUDIT_image-of-text_2026-05-16.md` (this report) — saved in the Website folder.
- `outputs/audit.py`, `outputs/audit2.py`, `outputs/audit3.py`, `outputs/audit4.py`, `outputs/audit5.py` — the parsing scripts used to produce the inventory. Not part of the deploy; kept in the temporary outputs folder for traceability.
- `outputs/img_inventory.txt`, `outputs/css_url_inventory.txt` — raw inventory output, also temporary.
