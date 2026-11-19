# Carrier sourcing scorecard

**Demo page (sample output and eval results, no install):** https://pg2342-hub.github.io/carrier-sourcing-scorecard/

A small, runnable version of the shadow week in a four-week carrier sourcing pilot. An AI agent sources carriers for a broker's open loads while the reps keep booking as usual, and this scores the agent's options against what the reps actually booked on the same loads. The broker's written carrier rules are a hard gate, so a cheap quote from a carrier that should never be booked does not count as a saving.

Everything in `data/` is synthetic. The carriers, IDs, rates and times are invented, so the numbers below show how the scorecard works and say nothing about any real broker, carrier or vendor.

## Run it

```
python3 run.py              # score the sample week, writes reports/
python3 eval_gate.py        # 30 hand-labeled gate cases
python3 -m unittest         # 8 tests
python3 make_sample.py      # rebuild the sample week (fixed seed)
```

Python 3.9+ and the standard library only.

## What is in it

| Path | What it is |
|---|---|
| `scorecard/gate.py` | The written-rules gate. Each carrier on each load comes out **PASS** (a rep can approve the rate), **REVIEW** (a rep checks one named thing first), or **BLOCK** (never shown as bookable), with every reason listed |
| `scorecard/score.py` | Scores the week two ways, gated and naive, plus coverage, speed, and a go/no-go check |
| `rules/example_broker.json` | Example rules (minimum auto liability and cargo, authority status and age, safety rating, equipment, registered contact, do-not-use list, insurance dates). The values are common broker settings chosen for this demo; week 1 of a pilot replaces them with the rules a broker's reps actually apply |
| `data/loads.csv` | 40 dry van and reefer loads out of a hub in Irving, TX, with what the rep paid and how long it took to cover |
| `data/agent_options.csv` | The carrier options the agent found on each load, with quote and minutes after posting |
| `data/carriers.csv` | 15 synthetic carriers with the fields the gate reads |
| `data/gate_cases.csv` | 30 hand-labeled carrier-and-load cases, including the edges (exactly 90 days of authority, insurance ending on the pickup day) |
| `reports/` | `scorecard.md`, `scorecard.json`, and `rep_queue.csv` (every option a rep would see, cheapest passing first, with what to check) |

## Results on the sample week

| | |
|---|---|
| Loads covered by an option that passes the rules | 20 of 40 (50%) |
| Buy rate vs reps, naive (cheapest option on each load, rules ignored) | 7.1% lower |
| Buy rate vs reps, gated, on the loads it covered | 2.4% lower |
| Buy rate vs reps, gated, across all 40 loads | 1.1% lower |
| Loads where the cheapest option came from a blocked carrier | 16 of 30 |
| Median minutes on the 20 covered loads, rep to cover vs agent's first passing quote | 96.5 vs 37 |
| Gate eval | 30 of 30 cases match, 0 unsafe |

The minutes line compares different events (a rep's booking vs an agent's quote arriving), so it is a rough signal, not a time-to-cover result.

In this sample week, the naive readout would say the agent cut buy rates by 7.1%. Most of that came from carriers the rules block, so the gated figure is 2.4% on the loads the agent covered and 1.1% across the week, and coverage misses a 60% target. The sample was built to show that gap. A cheap quote from an inactive or underinsured carrier is a risk, not a saving.

## Choices worth knowing

- **Same-load comparison.** The agent's best passing quote is compared with what the rep paid on that same load, not with a market average that moves during the week.
- **Uncovered loads count.** The all-loads figure counts a load the agent could not cover as no saving, so a pilot cannot look better by only reporting the loads it handled.
- **REVIEW is not coverage.** A carrier that needs a rep check (new authority, conditional rating, contact not on the registry, insurance ending soon) goes in the rep queue with what to check, but the load is not counted as covered.
- **BLOCK wins.** If any rule blocks a carrier, it is blocked, and every reason is kept so the decision can be traced.
- **Insurance that ends on the pickup day blocks.** Policies typically lapse at 12:01 AM on the expiration date, so the carrier is not covered that day. Insurance ending within 15 days of pickup goes to a rep.
- **Equipment must match exactly.** A reefer-only carrier on a dry van load is blocked here. Many brokers do let reefers haul dry freight, so this is a rule choice a broker would set in week 1, not a fact about freight.
- **Unsafe means more lenient than the label.** The eval counts PASS where the label says REVIEW or BLOCK, and REVIEW where the label says BLOCK (a blocked carrier would reach a rep), as unsafe.
- **New authority is a setting.** Some brokers refuse carriers under a set age, others review them, so `new_authority_action` takes either.

## Limits

- Synthetic data. A real shadow week would read the broker's load export and the agent's call log.
- The gate reads fields a broker already has (registry status, certificate amounts, do-not-use list). It does not pull registry data itself or read the certificate.
- Thirty gate cases written by hand. A real version would replay the broker's past carrier decisions and compare.
