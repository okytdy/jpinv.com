#!/usr/bin/env python3
"""
watchlist_alert.py -- Build the post-close 'new watched-name signal' digest.

Reads a watchlist_signals.json (live-fetched copy preferred; local fallback),
diffs every signal id against a local state file of already-alerted ids, and
writes the email parts for a Gmail draft. Snapshot-diff (not 'today only') so a
delayed run still catches everything since the last alert.

Usage:
  python tools/watchlist_alert.py [--src PATH] [--commit]
    --src PATH   watchlist_signals.json to read (default: compounders/feed/data/watchlist_signals.json)
    --commit     after building, record the new ids as alerted (call this only after the draft is created)

Outputs (always): prints  NEW=<n>
  tools/.alert_out_subject.txt   one-line subject
  tools/.alert_out_body.html     HTML body for create_draft(htmlBody=...)
  tools/.alert_out_body.txt      plaintext body for create_draft(body=...)
State: tools/.alert_state.json  {"alerted": [ids...], "seeded_at": iso, "last_run": iso}
First run with no state seeds silently (NEW=0) so you are not emailed the full backfill.
"""
import json, os, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
DEFAULT_SRC = os.path.join(ROOT, "compounders", "feed", "data", "watchlist_signals.json")
STATE = os.path.join(TOOLS, ".alert_state.json")
OUT_SUBJ = os.path.join(TOOLS, ".alert_out_subject.txt")
OUT_HTML = os.path.join(TOOLS, ".alert_out_body.html")
OUT_TXT  = os.path.join(TOOLS, ".alert_out_body.txt")
BASE = "https://jpinv.com"

def jst_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def load(path, default):
    try: return json.load(open(path, encoding="utf-8"))
    except Exception: return default

def main():
    args = sys.argv[1:]
    src = DEFAULT_SRC
    commit = "--commit" in args
    if "--src" in args:
        src = args[args.index("--src") + 1]

    payload = load(src, {"names": []})
    names = payload.get("names", [])

    # flatten every signal with its name context
    items = []
    for n in names:
        for s in n.get("signals", []):
            sid = s.get("id") or (n["ticker"] + "-" + (s.get("ts") or ""))
            items.append({
                "id": sid, "ticker": n["ticker"], "name_en": n["name_en"], "name_jp": n["name_jp"],
                "in_universe": n["in_universe"], "profile_exists": n["profile_exists"],
                "date": s.get("date", ""), "ts": s.get("ts", ""),
                "class_en": s.get("class_en", ""), "tag_en": s.get("tag_en", "") or s.get("tag_jp", ""),
                "doc_url": s.get("doc_url", ""),
            })

    state = load(STATE, None)
    if state is None:
        # First run: seed, do not email the whole backfill.
        seed = sorted({it["id"] for it in items})
        json.dump({"alerted": seed, "seeded_at": jst_now().isoformat(timespec="seconds"),
                   "last_run": jst_now().isoformat(timespec="seconds")},
                  open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        for p in (OUT_SUBJ, OUT_HTML, OUT_TXT):
            open(p, "w", encoding="utf-8").write("")
        print(f"NEW=0 (seeded {len(seed)} existing ids; no email on first run)")
        return

    alerted = set(state.get("alerted", []))
    new = [it for it in items if it["id"] not in alerted]
    # universe (the watchlist) first, then wider screen; newest first within each
    new.sort(key=lambda x: (not x["in_universe"], x["ts"]), reverse=False)
    new.sort(key=lambda x: x["ts"], reverse=True)
    new.sort(key=lambda x: not x["in_universe"])  # stable: universe block first

    today = jst_now().strftime("%Y-%m-%d")
    n_new = len(new)
    if n_new == 0:
        for p in (OUT_SUBJ, OUT_HTML, OUT_TXT):
            open(p, "w", encoding="utf-8").write("")
        # still record the run
        state["last_run"] = jst_now().isoformat(timespec="seconds")
        json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("NEW=0")
        return

    subj = f"JII signals · {n_new} new watched-name disclosure{'s' if n_new>1 else ''} · {today}"

    def row_html(it):
        sigpage = f"{BASE}/en/compounders/signals/{it['ticker']}/"
        tag = it["tag_en"] or it["class_en"]
        if tag.startswith(it["class_en"] + " - "): tag = tag[len(it["class_en"])+3:]
        badge = "Standing universe" if it["in_universe"] else "Wider screen"
        prof = f' &middot; <a href="{BASE}/en/compounders/{it["ticker"]}/initiation/">profile</a>' if it["profile_exists"] else ""
        doc = f' &middot; <a href="{it["doc_url"]}">TDnet</a>' if it["doc_url"] else ""
        return (f'<tr><td style="padding:8px 10px;border-bottom:1px solid #e8edf3;font:12px monospace;color:#7a8290;white-space:nowrap">{it["date"]}</td>'
                f'<td style="padding:8px 10px;border-bottom:1px solid #e8edf3"><b>{it["ticker"]}</b> {it["name_en"]}<br>'
                f'<span style="font:11px monospace;color:#9a7838;text-transform:uppercase;letter-spacing:.08em">{it["class_en"]}</span> '
                f'<span style="color:#4a5566">{tag}</span><br>'
                f'<span style="font:11px monospace;color:#7a8290">{badge}</span> &middot; '
                f'<a href="{sigpage}">signal log</a>{prof}{doc}</td></tr>')

    uni = [it for it in new if it["in_universe"]]
    scr = [it for it in new if not it["in_universe"]]
    body_html = [f'<div style="font-family:system-ui,Arial,sans-serif;max-width:640px">'
                 f'<p style="font-size:15px;color:#172641"><b>{n_new}</b> new capital-allocation signal{"s" if n_new>1 else ""} '
                 f'on names you watch (post-close {today} JST).</p>']
    if uni:
        body_html.append('<p style="font:11px monospace;letter-spacing:.12em;color:#9a7838;text-transform:uppercase;margin:18px 0 4px">Standing universe</p>')
        body_html.append('<table style="border-collapse:collapse;width:100%">' + "".join(row_html(it) for it in uni) + '</table>')
    if scr:
        body_html.append('<p style="font:11px monospace;letter-spacing:.12em;color:#7a8290;text-transform:uppercase;margin:18px 0 4px">Wider screen (200-name)</p>')
        body_html.append('<table style="border-collapse:collapse;width:100%">' + "".join(row_html(it) for it in scr) + '</table>')
    body_html.append(f'<p style="font-size:13px;color:#4a5566;margin-top:20px">Each name above is a candidate for the next JII Compounder post. '
                     f'Signal log index: <a href="{BASE}/en/compounders/signals/">{BASE}/en/compounders/signals/</a></p></div>')
    body_html = "\n".join(body_html)

    body_txt = [f"{n_new} new capital-allocation signal(s) on watched names (post-close {today} JST).", ""]
    for label, grp in (("STANDING UNIVERSE", uni), ("WIDER SCREEN", scr)):
        if not grp: continue
        body_txt.append(f"== {label} ==")
        for it in grp:
            body_txt.append(f"  {it['date']}  {it['ticker']}  {it['name_en']}")
            _t = it["tag_en"]
            if _t.startswith(it["class_en"]+" - "): _t = _t[len(it["class_en"])+3:]
            body_txt.append(f"            {it['class_en']} - {_t}")
            body_txt.append(f"            signal log: {BASE}/en/compounders/signals/{it['ticker']}/")
            if it["doc_url"]: body_txt.append(f"            TDnet: {it['doc_url']}")
        body_txt.append("")
    body_txt = "\n".join(body_txt)

    open(OUT_SUBJ, "w", encoding="utf-8").write(subj)
    open(OUT_HTML, "w", encoding="utf-8").write(body_html)
    open(OUT_TXT, "w", encoding="utf-8").write(body_txt)

    if commit:
        alerted |= {it["id"] for it in new}
        state["alerted"] = sorted(alerted)
        state["last_run"] = jst_now().isoformat(timespec="seconds")
        json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"NEW={n_new} (committed)")
    else:
        print(f"NEW={n_new}")

if __name__ == "__main__":
    main()
