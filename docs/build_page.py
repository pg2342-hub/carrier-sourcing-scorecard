"""Builds docs/index.html (the GitHub Pages demo) from the scorecard's real output.

Usage: python3 docs/build_page.py   (then python3 scripts/demo_chrome.py docs/index.html --repo carrier-sourcing-scorecard)
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scorecard.gate import BLOCK, PASS, REVIEW, check  # noqa: E402
from scorecard.score import load_inputs, score  # noqa: E402

os.chdir(ROOT)
loads, options, carriers, rules = load_inputs("data", "rules/example_broker.json")
rows, s = score(loads, options, carriers, rules)


def status(r):
    if r["best_pass"]:
        return "covered"
    if r["n_review"]:
        return "review"
    if r["n_block"]:
        return "blocked"
    return "none"


out_rows = []
for r in rows:
    out_rows.append({"id": r["load_id"], "lane": r["lane"], "rep_buy": r["rep_buy"], "rep_minutes": r["rep_minutes"],
                     "n_options": r["n_options"], "n_pass": r["n_pass"], "n_review": r["n_review"],
                     "n_block": r["n_block"], "status": status(r),
                     "best": r["best_pass"]["quote"] if r["best_pass"] else None,
                     "first_pass_minutes": r["first_pass_minutes"]})

# Every option on each load, with the gate's decision, for the load detail.
by_load = {}
for o in options:
    ld = next(x for x in loads if x["load_id"] == o["load_id"])
    d, reasons = check(carriers[o["carrier_id"]], ld, rules)
    by_load.setdefault(o["load_id"], []).append(
        {"carrier": o["carrier_id"], "name": carriers[o["carrier_id"]]["name"], "quote": float(o["quote"]),
         "minutes": float(o["minutes_after_post"]), "decision": d, "reasons": reasons})
for r in out_rows:
    r["options"] = sorted(by_load.get(r["id"], []), key=lambda g: ({PASS: 0, REVIEW: 1, BLOCK: 2}[g["decision"]], g["quote"]))

# The 30 hand-labeled gate cases, scored the way eval_gate.py scores them.
rank = {PASS: 0, REVIEW: 1, BLOCK: 2}
cases = list(csv.DictReader(open("data/gate_cases.csv", newline="")))
ok = unsafe = 0
for c in cases:
    d, reasons = check(c, {"equipment": c["load_equipment"], "pickup_date": c["pickup_date"]}, rules)
    want = set(filter(None, c["expected_reasons"].split(";")))
    ok += d == c["expected_decision"] and set(reasons) == want
    unsafe += rank[d] < rank[c["expected_decision"]]

payload = {"summary": s, "loads": out_rows, "gate_eval": {"cases": len(cases), "match": ok, "unsafe": unsafe},
           "rules": {k: v for k, v in rules.items() if not k.startswith("_")}}
template = open(os.path.join(ROOT, "docs", "template.html"), encoding="utf-8").read()
out = template.replace("/*DATA*/null", json.dumps(payload))
open(os.path.join(ROOT, "docs", "index.html"), "w", encoding="utf-8").write(out)
print("wrote docs/index.html", len(out), "bytes")
