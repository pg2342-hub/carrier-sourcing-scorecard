"""Shadow-week scorecard: agent-sourced options vs what the reps booked on the same loads.

Two ways to score the same week:
  gated - only options that PASS the written rules count, every load counts
          (a load the agent could not cover is a miss, not a skipped row)
  naive - cheapest option on each load, rules ignored, averaged only over loads that got any option
The gap between the two is how much a quick readout would overstate the pilot.
"""
import csv
import json
from statistics import median

from .gate import BLOCK, PASS, REVIEW, check


def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def load_inputs(data_dir, rules_path):
    loads = load_csv(f"{data_dir}/loads.csv")
    options = load_csv(f"{data_dir}/agent_options.csv")
    carriers = {c["carrier_id"]: c for c in load_csv(f"{data_dir}/carriers.csv")}
    with open(rules_path) as f:
        rules = json.load(f)
    return loads, options, carriers, rules


def score(loads, options, carriers, rules):
    by_load = {}
    for o in options:
        by_load.setdefault(o["load_id"], []).append(o)

    rows = []
    for ld in loads:
        rep_buy = float(ld["rep_buy_rate"])
        graded = []
        for o in by_load.get(ld["load_id"], []):
            decision, reasons = check(carriers[o["carrier_id"]], ld, rules)
            graded.append({**o, "quote": float(o["quote"]), "minutes": float(o["minutes_after_post"]),
                           "decision": decision, "reasons": reasons})
        passing = sorted((g for g in graded if g["decision"] == PASS), key=lambda g: g["quote"])
        cheapest_any = min(graded, key=lambda g: g["quote"]) if graded else None
        best = passing[0] if passing else None
        rows.append({
            "load_id": ld["load_id"],
            "lane": f'{ld["origin"]} to {ld["destination"]}',
            "miles": float(ld["miles"]),
            "rep_buy": rep_buy,
            "rep_minutes": float(ld["rep_minutes_to_cover"]),
            "n_options": len(graded),
            "n_pass": len(passing),
            "n_review": sum(g["decision"] == REVIEW for g in graded),
            "n_block": sum(g["decision"] == BLOCK for g in graded),
            "best_pass": best,
            "cheapest_any": cheapest_any,
            "rep_queue": [g for g in graded if g["decision"] != BLOCK],
        })
    return rows, summarize(rows, rules)


def _pct(a, b):
    return round(100.0 * a / b, 1) if b else 0.0


def summarize(rows, rules):
    n = len(rows)
    covered = [r for r in rows if r["best_pass"]]
    rep_total_all = sum(r["rep_buy"] for r in rows)
    gated_saving = sum(r["rep_buy"] - r["best_pass"]["quote"] for r in covered)

    with_any = [r for r in rows if r["cheapest_any"]]
    naive_saving = sum(r["rep_buy"] - r["cheapest_any"]["quote"] for r in with_any)
    naive_base = sum(r["rep_buy"] for r in with_any)
    cheapest_fails = [r for r in with_any if r["cheapest_any"]["decision"] == BLOCK]
    cheapest_review = [r for r in with_any if r["cheapest_any"]["decision"] == REVIEW]

    beat = [r for r in covered if r["best_pass"]["quote"] < r["rep_buy"]]
    faster = [r for r in covered if r["best_pass"]["minutes"] < r["rep_minutes"]]
    blocked_in_queue = sum(1 for r in rows for g in r["rep_queue"] if g["decision"] == BLOCK)

    s = {
        "loads": n,
        "loads_with_any_option": len(with_any),
        "loads_covered_by_passing_option": len(covered),
        "coverage_pct": _pct(len(covered), n),
        "gated_buy_rate_change_pct_all_loads": _pct(gated_saving, rep_total_all),
        "gated_buy_rate_change_pct_covered_loads": _pct(gated_saving, sum(r["rep_buy"] for r in covered)),
        "naive_buy_rate_change_pct": _pct(naive_saving, naive_base),
        "loads_where_cheapest_option_is_blocked": len(cheapest_fails),
        "loads_where_cheapest_option_needs_review": len(cheapest_review),
        "covered_loads_agent_beat_rep_rate": len(beat),
        "covered_loads_agent_faster": len(faster),
        "median_minutes_rep": median(r["rep_minutes"] for r in rows),
        "median_minutes_first_pass_option": median(r["best_pass"]["minutes"] for r in covered) if covered else None,
        "blocked_carriers_in_rep_queue": blocked_in_queue,
    }
    g = rules.get("go_no_go", {})
    s["go_no_go"] = {
        "coverage_target_pct": g.get("coverage_target_pct", 60),
        "coverage_met": s["coverage_pct"] >= g.get("coverage_target_pct", 60),
        "buy_rate_not_worse_met": s["gated_buy_rate_change_pct_covered_loads"] >= 0,
        "zero_blocked_in_queue_met": blocked_in_queue == 0,
    }
    s["go_no_go"]["go"] = all(v for k, v in s["go_no_go"].items() if k.endswith("_met"))
    return s
