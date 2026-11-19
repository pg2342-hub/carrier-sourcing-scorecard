# Shadow week scorecard

Synthetic data. These numbers show how the scorecard works and say nothing about any real broker or vendor.

| Metric | Value |
|---|---|
| Loads in the week | 40 |
| Loads with at least one agent option | 30 |
| Loads covered by an option that passes the written rules | 20 (50.0%) |
| Buy rate vs reps, naive (cheapest option, rules ignored, loads with any option) | 7.1% lower |
| Buy rate vs reps, gated, on loads with a passing option | 2.4% lower |
| Buy rate vs reps, gated, across every load (uncovered loads count as no saving) | 1.1% lower |
| Loads where the cheapest option came from a blocked carrier | 16 |
| Loads where the cheapest option needs a rep check first | 6 |
| Median minutes on covered loads, rep to cover vs agent's first passing quote (different events, see README) | 96.5 vs 37 |

## Go / no-go

- Coverage at least 60% of loads: NOT met
- Buy rate no worse than reps on the same loads: met
- Zero blocked carriers in the rep queue (guaranteed by construction, kept as a regression check): met
- Decision: **NO-GO, see which line failed**
