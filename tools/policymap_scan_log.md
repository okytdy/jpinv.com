# Policy Map — weekly milestone scan log

Each weekly run appends one dated block: sources scanned, new candidates staged, duplicates skipped, and any source that failed to load (logged visibly — never silently dropped). Candidates land in `compounders/policymap/data/milestones_inbox.json` with `notification_status: "pending"` and go live only after Teddy approves and runs `tools/policymap_promote_milestones.py`.

---
