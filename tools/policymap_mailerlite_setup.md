# Policy Map milestone alerts — MailerLite setup (≈15 min, one time)

Goal: collect subscribers in MailerLite and send milestone alerts **as info@jpinv.com**, with no backend and no per-signup manual work.

## Steps

1. **Create a free MailerLite account** at mailerlite.com (the free tier covers a list this size).
2. **Verify your sending domain** so emails go out as info@jpinv.com: MailerLite → *Settings → Domains* → add `jpinv.com` and complete the DNS (SPF/DKIM) records with your domain registrar. This is what makes alerts arrive *from* info@jpinv.com rather than a MailerLite address.
3. **Create a group** named `Policy Map milestones` (Subscribers → Groups). This is your alert list.
4. **Create a form** (Forms → *Embedded form* or *Landing page*) and connect it to that group. Give it the promise text "Japan Policy Map — policy milestone alerts. No marketing, no investment advice."
5. **Copy the form's public URL** (Forms → your form → *Share* → copy the link; it looks like `https://your-handle.mailerlite.com/xxxxxxxxx`).
6. **Paste that URL** into `formUrl` in BOTH config files (keep them identical):
   - `en/compounders/policymap/data/notify_config.js`
   - `compounders/policymap/data/notify_config.js`
   Then commit + push. The "Notify me" button now opens your MailerLite form. (Until you do this, the button safely falls back to an email to info@jpinv.com.)

## How alerts get sent

- **Manual (default):** when you promote a new milestone, send a one-off campaign in MailerLite to the `Policy Map milestones` group. One broadcast reaches everyone — no per-subscriber drafting.
- **Fully automatic (optional):** create a MailerLite **API token** (Integrations → API) and send it to me. I'll wire the milestone *promote* step (`tools/policymap_promote_milestones.py`) and/or the weekly scan to POST a campaign to the group automatically whenever a milestone goes live — then it's hands-off.

## Why not auto-draft into Outlook?

That path needs Microsoft Power Automate (a "new signup → draft email" flow) and still leaves you hitting send on each one. MailerLite removes the manual step entirely while still sending from your info@jpinv.com address, so it's the lower-effort choice you picked.
