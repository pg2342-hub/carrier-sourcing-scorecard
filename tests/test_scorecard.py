import json
import unittest

from scorecard.gate import BLOCK, PASS, REVIEW, check
from scorecard.score import score

RULES = json.load(open("rules/example_broker.json"))
GOOD = {"carrier_id": "G", "authority_status": "ACTIVE", "authority_granted": "2018-01-01",
        "auto_liability": "1000000", "cargo": "100000", "safety_rating": "None", "equipment": "V",
        "contact_matches_registry": "Y", "do_not_use": "N", "insurance_expires": "2027-06-30"}
BAD = {**GOOD, "carrier_id": "B", "authority_status": "INACTIVE"}
NEW = {**GOOD, "carrier_id": "N", "authority_granted": "2026-11-01"}
LOAD = {"load_id": "L1", "origin": "Irving, TX", "destination": "Houston, TX", "miles": "245",
        "equipment": "V", "pickup_date": "2026-11-10", "rep": "Rep A", "rep_buy_rate": "1000",
        "rep_minutes_to_cover": "120"}


def opt(load_id, carrier_id, quote, minutes=10):
    return {"load_id": load_id, "carrier_id": carrier_id, "quote": str(quote), "minutes_after_post": str(minutes)}


class GateTests(unittest.TestCase):
    def test_block_wins_over_review_and_keeps_all_reasons(self):
        c = {**GOOD, "authority_status": "INACTIVE", "safety_rating": "Conditional"}
        d, reasons = check(c, LOAD, RULES)
        self.assertEqual(d, BLOCK)
        self.assertEqual(set(reasons), {"authority_not_active", "safety_rating_conditional"})

    def test_new_authority_can_be_made_a_hard_block(self):
        self.assertEqual(check(NEW, LOAD, RULES)[0], REVIEW)
        self.assertEqual(check(NEW, LOAD, {**RULES, "new_authority_action": "BLOCK"})[0], BLOCK)

    def test_insurance_ending_on_pickup_day_blocks(self):
        d, reasons = check({**GOOD, "insurance_expires": "2026-11-10"}, LOAD, RULES)
        self.assertEqual((d, reasons), (BLOCK, ["insurance_lapsed_by_pickup"]))

    def test_clean_carrier_passes(self):
        self.assertEqual(check(GOOD, LOAD, RULES), (PASS, []))


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.carriers = {"G": GOOD, "B": BAD, "N": NEW}
        self.loads = [LOAD, {**LOAD, "load_id": "L2"}]

    def test_cheap_blocked_quote_does_not_count_as_saving(self):
        rows, s = score(self.loads, [opt("L1", "B", 800), opt("L1", "G", 980)], self.carriers, RULES)
        self.assertEqual(rows[0]["best_pass"]["carrier_id"], "G")
        self.assertEqual(s["naive_buy_rate_change_pct"], 20.0)
        self.assertEqual(s["gated_buy_rate_change_pct_covered_loads"], 2.0)
        self.assertEqual(s["loads_where_cheapest_option_is_blocked"], 1)

    def test_uncovered_load_counts_against_the_all_loads_number(self):
        _, s = score(self.loads, [opt("L1", "G", 980)], self.carriers, RULES)
        self.assertEqual(s["coverage_pct"], 50.0)
        self.assertEqual(s["gated_buy_rate_change_pct_all_loads"], 1.0)
        self.assertFalse(s["go_no_go"]["coverage_met"])

    def test_review_option_is_queued_but_not_counted_as_covered(self):
        rows, s = score(self.loads, [opt("L1", "N", 900)], self.carriers, RULES)
        self.assertEqual(s["loads_covered_by_passing_option"], 0)
        self.assertEqual([g["carrier_id"] for g in rows[0]["rep_queue"]], ["N"])

    def test_blocked_carrier_never_reaches_rep_queue(self):
        rows, s = score(self.loads, [opt("L1", "B", 500), opt("L2", "B", 500)], self.carriers, RULES)
        self.assertTrue(all(not r["rep_queue"] for r in rows))
        self.assertEqual(s["blocked_carriers_in_rep_queue"], 0)


if __name__ == "__main__":
    unittest.main()
