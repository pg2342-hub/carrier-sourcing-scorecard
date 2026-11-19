"""Score a shadow week.  python3 run.py [--data data] [--rules rules/example_broker.json]

Writes reports/scorecard.md, reports/scorecard.json and reports/rep_queue.csv.
"""
import argparse
import csv
import json
import os

from scorecard.score import load_inputs, score


def write_reports(rows, s, out):
    os.makedirs(out, exist_ok=True)
    with open(f"{out}/scorecard.json", "w") as f:
        json.dump(s, f, indent=2)
    with open(f"{out}/rep_queue.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["load_id", "lane", "rep_buy_rate", "carrier_id", "quote", "decision", "check_first"])
        for r in rows:
            for g in sorted(r["rep_queue"], key=lambda g: (g["decision"] != "PASS", g["quote"])):
                w.writerow([r["load_id"], r["lane"], r["rep_buy"], g["carrier_id"], g["quote"], g["decision"],
                            "; ".join(g["reasons"])])
    gng = s["go_no_go"]
    lines = [
        "# Shadow week scorecard", "",
        "Synthetic data. These numbers show how the scorecard works and say nothing about any real broker or vendor.", "",
        "| Metric | Value |", "|---|---|",
        f"| Loads in the week | {s['loads']} |",
        f"| Loads with at least one agent option | {s['loads_with_any_option']} |",
        f"| Loads covered by an option that passes the written rules | {s['loads_covered_by_passing_option']} ({s['coverage_pct']}%) |",
        f"| Buy rate vs reps, naive (cheapest option, rules ignored, loads with any option) | {s['naive_buy_rate_change_pct']}% lower |",
        f"| Buy rate vs reps, gated, on loads with a passing option | {s['gated_buy_rate_change_pct_covered_loads']}% lower |",
        f"| Buy rate vs reps, gated, across every load (uncovered loads count as no saving) | {s['gated_buy_rate_change_pct_all_loads']}% lower |",
        f"| Loads where the cheapest option came from a blocked carrier | {s['loads_where_cheapest_option_is_blocked']} |",
        f"| Loads where the cheapest option needs a rep check first | {s['loads_where_cheapest_option_needs_review']} |",
        f"| Median minutes on covered loads, rep to cover vs agent's first passing quote (different events, see README) | {s['median_minutes_rep_covered_loads']:g} vs {s['median_minutes_first_passing_option']:g} |",
        "", "## Go / no-go", "",
        f"- Coverage at least {gng['coverage_target_pct']}% of loads: {'met' if gng['coverage_met'] else 'NOT met'}",
        f"- Buy rate no worse than reps on the same loads: {'met' if gng['buy_rate_not_worse_met'] else 'NOT met'}",
        f"- Zero blocked carriers in the rep queue (guaranteed by construction, kept as a regression check): {'met' if gng['zero_blocked_in_queue_met'] else 'NOT met'}",
        f"- Decision: **{'GO' if gng['go'] else 'NO-GO, see which line failed'}**", "",
    ]
    with open(f"{out}/scorecard.md", "w") as f:
        f.write("\n".join(lines))
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data")
    p.add_argument("--rules", default="rules/example_broker.json")
    p.add_argument("--out", default="reports")
    a = p.parse_args()
    rows, s = score(*load_inputs(a.data, a.rules))
    print(write_reports(rows, s, a.out))


if __name__ == "__main__":
    main()
