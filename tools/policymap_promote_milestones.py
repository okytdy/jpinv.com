# -*- coding: utf-8 -*-
"""
Promote approved Policy Map milestone candidates from the review-staging inbox
into the LIVE milestones array, in both locales, and rebuild policymap_data.js.

Pipeline (review-staged, history-safe):
  weekly scan  -> appends candidates to compounders/policymap/data/milestones_inbox.json
                  (notification_status = "pending")
  Teddy review -> set a candidate's notification_status to "approved" or "rejected"
  this script  -> merges "approved" into the live milestones array (both en/ + ja),
                  rebuilds the .js, dedupes by id, sorts newest-first, and clears
                  promoted/rejected items out of the inbox. It NEVER overwrites or
                  deletes an existing live milestone.

Run from the repo root:
    python tools/policymap_promote_milestones.py
"""
import json, os, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(ROOT, "compounders", "policymap", "data", "milestones_inbox.json")
DATA_DIRS = [
    os.path.join(ROOT, "en", "compounders", "policymap", "data"),
    os.path.join(ROOT, "compounders", "policymap", "data"),
]
SCHEMA = ["id","date","domain","subtheme","event_type","agency_en","agency_ja",
          "title_en","title_ja","summary_en","summary_ja","source_id","source_url",
          "source_title_en","source_primary","last_checked","notification_status"]

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def write_data(d, base):
    with open(os.path.join(base, "policymap_data.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    body = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(base, "policymap_data.js"), "w", encoding="utf-8") as f:
        f.write("window.PM_DATA=" + body + ";\n")

def main():
    inbox = load(INBOX)
    cands = inbox.get("candidates", [])
    approved = [c for c in cands if c.get("notification_status") == "approved"]
    rejected = [c for c in cands if c.get("notification_status") == "rejected"]
    if not approved and not rejected:
        print("Nothing to promote or reject. Set a candidate's notification_status to "
              "'approved' or 'rejected' first.")
        return

    today = datetime.date.today().isoformat()
    promoted_ids = []
    for base in DATA_DIRS:
        d = load(os.path.join(base, "policymap_data.json"))
        live = d.get("milestones", [])
        have = {m["id"] for m in live}
        for c in approved:
            if c["id"] in have:
                continue  # never overwrite history
            m = {k: c.get(k, "") for k in SCHEMA}
            m["notification_status"] = "published"
            if not m.get("last_checked"):
                m["last_checked"] = today
            live.append(m)
            have.add(c["id"])
            if c["id"] not in promoted_ids:
                promoted_ids.append(c["id"])
        live.sort(key=lambda m: (m.get("date") or ""), reverse=True)
        d["milestones"] = live
        d.setdefault("meta", {})
        d["meta"]["milestones_count"] = len(live)
        d["meta"]["milestones_last_scan"] = today
        write_data(d, base)

    # Clear promoted + rejected out of the inbox; keep still-pending ones.
    remaining = [c for c in cands if c.get("notification_status") == "pending"]
    inbox["candidates"] = remaining
    with open(INBOX, "w", encoding="utf-8") as f:
        json.dump(inbox, f, ensure_ascii=False, indent=1)

    print(f"Promoted {len(promoted_ids)} milestone(s): {promoted_ids}")
    print(f"Rejected {len(rejected)} candidate(s).")
    print(f"{len(remaining)} candidate(s) still pending in the inbox.")

if __name__ == "__main__":
    main()
