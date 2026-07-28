# Search Console canonical fix — what you need to do

**Date:** July 28, 2026
**Everything on the code side is done and verified.** Two things are left, and both are yours.

---

## Step 1 — Commit and push (GitHub Desktop)

Open GitHub Desktop. You will see about 300 changed files in the left panel, all under
`jpinv.com`. That is expected: 218 signal-log pages, ~80 other pages that gained an
`x-default` tag, `sitemap.xml`, `compounders/index.html`, the two profiles galleries,
`tools/build_signal_pages.py`, and this SEO_Work folder.

**Summary** (the one-line field at the bottom left):

```
SEO: fix "Google chose different canonical" — noindex signal logs, consolidate profiles gallery, repair hreflang
```

**Description:**

```
Search Console validation for 'Duplicate, Google chose different canonical than user'
failed three times (Jul 3, Jul 18, Jul 27). Two duplicate clusters were the cause.

1. The 216 per-ticker pages under /compounders/signals/ are filtered slices of the feed.
   Median pairwise text similarity between any two was 0.65 (EN) / 0.73 (JA); the median
   EN page had 69 unique words out of 334. Now noindex,follow. The two hub pages stay
   indexable. build_signal_pages.py patched so the GitHub Actions feed refresh keeps it.

2. /compounders/profiles/ duplicates /compounders/ — 97% of the EN gallery's tokens also
   appear on the hub. Both galleries now canonicalize to their hubs.

sitemap.xml: 369 URLs -> 173. Removed 206 signal URLs and 2 gallery URLs; added 12 live
indexable pages that had never been submitted (the seven /サービス/ pages, /会社概要/,
/料金/, /お問い合わせ/, and 8088 initiation in both languages). Normalized 21 blocks from
hreflang="ja-JP" to "ja" so the sitemap stops contradicting the pages. Added x-default
across all 389 ja/en pairs. Bumped lastmod on the 91 changed URLs.
```

Then click **Commit to main**, then **Push origin** in the top bar.

Give GitHub Pages a couple of minutes to rebuild before doing Step 2.

---

## Step 2 — Search Console

Go to https://search.google.com/search-console and pick the `https://jpinv.com/` property.

**a) Resubmit the sitemap.** Sitemaps → click `sitemap.xml` → resubmit. It shrank from
369 URLs to 173, and Google needs to see the new file before it re-evaluates anything.

**b) Request validation.** Indexing → Pages → open **Duplicate, Google chose different
canonical than user** → click **Validate Fix**.

Validation takes days to a couple of weeks. Google recrawls a sample first, so the status
will sit on "Started" for a while. That is normal.

---

## What to expect, so the result doesn't surprise you

The 216 signal pages will not move into the "indexed" bucket. They will move to
**Excluded by 'noindex' tag**. That is the fix working. They were never actually being
indexed — Google was already discarding them as duplicates. The change makes the exclusion
deliberate and stops it counting as an error against the site.

The pages still work for visitors, still get crawled, and still pass link equity to the
Compounder profiles. The same information stays indexable at `/compounders/feed/`,
`/compounders/universe/` and the two signal hubs.

If validation fails again, the next place to look is the five Japanese governance section
hubs — they are thin (747–998 characters) and 46–50% identical to one another. That is
documented in `_OPEN_TASKS.md` under the July 28 entry.

---

## One thing outside the repo

`4 Delivery/5 JII Compounders/8 Assembly & Build/scripts/ship_compounder.py` was also
patched — it was writing `hreflang="ja-JP"` and omitting `x-default` into the sitemap on
every ship, which is where 21 of the bad blocks came from. That file lives outside the
website repo, so it is not part of this push. Nothing for you to do; just know it changed.
