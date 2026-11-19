"""Runs the 30 hand-labeled gate cases.  python3 eval_gate.py [--rules rules/example_broker.json]

A case passes when the decision AND the set of reasons match the label.
Unsafe = the gate is more lenient than the label: PASS where the label says REVIEW or BLOCK (a rep would book
unchecked), or REVIEW where the label says BLOCK (a blocked carrier would reach a rep).
"""
import argparse
import csv
import json

from scorecard.gate import PASS, check


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rules", default="rules/example_broker.json")
    p.add_argument("--cases", default="data/gate_cases.csv")
    a = p.parse_args()
    rules = json.load(open(a.rules))
    ok = unsafe = 0
    misses = []
    rows = list(csv.DictReader(open(a.cases, newline="")))
    for c in rows:
        load = {"equipment": c["load_equipment"], "pickup_date": c["pickup_date"]}
        decision, reasons = check(c, load, rules)
        want = set(filter(None, c["expected_reasons"].split(";")))
        if decision == c["expected_decision"] and set(reasons) == want:
            ok += 1
        else:
            misses.append(f'{c["case_id"]} {c["what_it_tests"]}: got {decision} {reasons}, '
                          f'expected {c["expected_decision"]} {sorted(want)}')
        rank = {"PASS": 0, "REVIEW": 1, "BLOCK": 2}
        if rank[decision] < rank[c["expected_decision"]]:
            unsafe += 1
    print(f"{ok} of {len(rows)} cases match, {unsafe} unsafe")
    for m in misses:
        print("  MISS", m)


if __name__ == "__main__":
    main()
