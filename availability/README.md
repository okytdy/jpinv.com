# Availability — `jpinv.com/availability`

A standalone, public, single-page availability calendar. Static — no backend, no
database. Reads `data.json` on load and renders a weekly grid in 30-minute slots
between 08:00 and 19:00 JST, Mon–Fri. Color-coded only — no names, no companies.

## Files in this folder

```
availability/
├── index.html   # the whole app (HTML + CSS + JS, single file)
├── data.json    # the source of truth — your slot statuses
└── README.md    # this file
```

## How to deploy

Drop this `availability/` folder into the root of the GitHub repo that serves
`jpinv.com`, commit, push. GitHub Pages will then serve it at
`https://jpinv.com/availability/`.

The page is `<meta name="robots" content="noindex,nofollow">` and is not linked
from anywhere on the site. Only people you send the URL to will find it.

## Day-to-day workflow

### Viewing (you and clients)

Open `https://jpinv.com/availability/`. Defaults to the current week in JST.
Use the **← Prev / Next →** arrows or the **This week** button to navigate
(keyboard: ←, →, T).

### Editing (you only)

1. Open `https://jpinv.com/availability/?admin=1` — admin mode activates.
2. In the yellow admin bar, pick the status you want to paint with
   (Available / Booked / Tentative / Out of Office).
3. **Click** a slot to set it, or **click-and-drag** across multiple slots to
   paint a range. Works on mobile/touch too.
4. Changes are saved to your browser's `localStorage` as you go, so you can
   close the tab and resume later. An **unsaved changes** badge appears once
   you've made edits.
5. When you're done, click **Download data.json** (or **Copy JSON** to paste
   into the file directly in GitHub's web editor).
6. Replace the existing `data.json` in this folder, commit, push. Done.
7. **Discard local edits** lets you throw away your in-browser draft and
   reload the published `data.json` from scratch.

The admin URL is just security-through-obscurity — there's no real auth.
But: nothing you do in admin mode mutates the public data until you
commit the new `data.json` yourself. A curious viewer clicking around
in `?admin=1` mode only affects their own browser.

## Data format

`data.json` is a sparse map — only non-default slots are stored. The default
(everything else) is `available`.

```json
{
  "updated": "2026-05-15T00:00:00+09:00",
  "timezone": "Asia/Tokyo",
  "default_status": "available",
  "slots": {
    "2026-05-13T08:00": "booked",
    "2026-05-13T08:30": "booked"
  }
}
```

Status values: `available`, `booked`, `tentative`, `ooo`.

Slot keys: `YYYY-MM-DDTHH:MM` — date plus the **start time** of the 30-minute
slot, all in JST. The grid covers `08:00`, `08:30`, …, `18:30` (last slot
ends at 19:00).

## Customizing

Everything is in `index.html`:

- `START_HOUR` / `END_HOUR` constants change the daily time range.
- `DAYS_PER_WEEK` changes Mon–Fri to e.g. 7 if you want weekends.
- CSS custom properties at the top of `<style>` (`--available`, `--booked`,
  `--tentative`, `--ooo`) change the four status colors.
- The header text in `<header class="page">` and the footer note are plain
  HTML — edit in place.

## Carried-over bookings from the old xlsx

The following slots from `Availability Calendar_For Ichiyoshi.xlsx` are
preserved (company names dropped, as requested):

| Date         | Slot          | Status |
|--------------|---------------|--------|
| Fri May 8    | 09:00–10:00   | Booked |
| Tue May 12   | 12:00–13:00   | Booked |
| Wed May 13   | 08:00–09:00   | Booked |
| Thu May 21   | 08:00–09:00   | Booked |
| Fri May 22   | 09:00–10:00   | Booked |
| Wed Jun 10   | 17:00–18:00   | Booked |
