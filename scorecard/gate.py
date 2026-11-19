"""The written-rules gate. Every carrier option passes through here before a rep sees it.

Outcomes:
  PASS   - meets every written rule; a rep can approve the rate
  REVIEW - a rep must check one named thing before approving
  BLOCK  - never shown as bookable, whatever the price
Any BLOCK reason wins over REVIEW reasons. Every reason is returned so the decision can be traced.
"""
from datetime import date

PASS, REVIEW, BLOCK = "PASS", "REVIEW", "BLOCK"


def _d(s):
    return date.fromisoformat(s) if s else None


def check(carrier, load, rules):
    """Return (decision, [reason codes]) for one carrier on one load."""
    block, review = [], []
    pickup = _d(load["pickup_date"])

    if carrier.get("do_not_use") == "Y":
        block.append("on_do_not_use_list")
    if carrier.get("authority_status") != "ACTIVE":
        block.append("authority_not_active")
    if carrier.get("safety_rating") in rules["blocked_safety_ratings"]:
        block.append("safety_rating_blocked")
    if float(carrier.get("auto_liability") or 0) < rules["min_auto_liability"]:
        block.append("auto_liability_below_min")
    if float(carrier.get("cargo") or 0) < rules["min_cargo"]:
        block.append("cargo_below_min")
    equipment = set((carrier.get("equipment") or "").split("|"))
    if load["equipment"] not in equipment:
        block.append("equipment_mismatch")
    expires = _d(carrier.get("insurance_expires"))
    if expires is None or expires <= pickup:  # policies lapse at 12:01 AM on the expiration date
        block.append("insurance_lapsed_by_pickup")
    elif (expires - pickup).days < rules["insurance_buffer_days"]:
        review.append("insurance_expires_soon")

    granted = _d(carrier.get("authority_granted"))
    if granted is None:
        review.append("authority_age_unknown")
    elif (pickup - granted).days < rules["min_authority_age_days"]:
        (block if rules["new_authority_action"] == BLOCK else review).append("authority_too_new")
    if carrier.get("safety_rating") in rules["review_safety_ratings"]:
        review.append("safety_rating_conditional")
    if carrier.get("contact_matches_registry") != "Y":
        review.append("contact_not_on_registry")

    if block:
        return BLOCK, block + review
    if review:
        return REVIEW, review
    return PASS, []
