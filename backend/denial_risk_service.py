"""
Module 7: Denial Risk Scoring Engine
Rule-based system that predicts the likelihood of an insurance claim denial.
Scores 0-100     → LOW (<30) | MEDIUM (30-60) | HIGH (>60)
"""


def score_denial_risk(benefits: dict, card_data: dict) -> dict:
    """
    Evaluate denial risk based on coverage attributes.
    Returns a risk_score, risk_level, and list of triggered rules.
    """
    score  = 0
    rules  = []

    # ── Rule 1: Coverage Inactive (+50) ──────────────────────────────────────
    if benefits.get("coverage_status", "Active") != "Active":
        score += 50
        rules.append({
            "rule":   "Coverage Inactive",
            "points": 50,
            "detail": "Patient's insurance coverage is not active."
        })

    # ── Rule 2: Policy Expired (+40) ─────────────────────────────────────────
    valid_thru = card_data.get("valid_thru", "Unknown")
    if _is_expired(valid_thru):
        score += 40
        rules.append({
            "rule":   "Policy Expired",
            "points": 40,
            "detail": f"Insurance valid_thru date ({valid_thru}) has passed."
        })

    # ── Rule 3: Out of Network (+20) ─────────────────────────────────────────
    if not benefits.get("in_network", True):
        score += 20
        rules.append({
            "rule":   "Out of Network",
            "points": 20,
            "detail": "Service provider is not in the patient's insurance network."
        })

    # ── Rule 4: High Remaining Deductible (+15) ───────────────────────────────
    deductible_remaining = benefits.get("deductible_remaining", 0)
    deductible_total     = benefits.get("deductible_total", 1)
    if deductible_total > 0 and (deductible_remaining / deductible_total) > 0.75:
        score += 15
        rules.append({
            "rule":   "High Deductible Remaining",
            "points": 15,
            "detail": f"More than 75% of deductible (₹{deductible_remaining:,}) still unpaid."
        })

    # ── Rule 5: Unknown Member ID (+10) ──────────────────────────────────────
    if card_data.get("member_id", "Unknown") == "Unknown":
        score += 10
        rules.append({
            "rule":   "Missing Member ID",
            "points": 10,
            "detail": "Member ID could not be extracted from the insurance card."
        })

    # Cap at 100
    score = min(score, 100)

    # Determine level
    if score >= 60:
        level = "HIGH"
        badge = "danger"
    elif score >= 30:
        level = "MEDIUM"
        badge = "warning"
    else:
        level = "LOW"
        badge = "success"

    return {
        "risk_score":   score,
        "risk_level":   level,
        "badge_variant": badge,
        "rules_triggered": rules,
        "summary":      _build_summary(score, level, rules),
    }


def _is_expired(valid_thru: str) -> bool:
    """Return True if valid_thru date is in the past."""
    import re
    from datetime import date
    if not valid_thru or valid_thru == "Unknown":
        return False
    today = date.today()

    m = re.match(r'(\d{1,2})[/\-\.](\d{4})$', valid_thru)
    if m:
        mo, yr = int(m.group(1)), int(m.group(2))
        return (yr, mo) < (today.year, today.month)

    m = re.match(r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})$', valid_thru)
    if m:
        mo, dd, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(yr, mo, dd) < today
        except ValueError:
            pass
    return False


def _build_summary(score: int, level: str, rules: list) -> str:
    if not rules:
        return f"No denial risk factors identified. Risk Score: {score}/100 ({level})"
    top = rules[0]["rule"]
    return f"Primary risk: {top}. Overall Risk Score: {score}/100 — {level} risk of claim denial."
