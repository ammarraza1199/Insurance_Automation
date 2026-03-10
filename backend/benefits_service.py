"""
Module 5: Benefits Interpretation Engine
Converts raw EDI 271 response data into human-readable benefits JSON.
"""


def interpret_benefits(edi_response: dict) -> dict:
    """
    Convert the EDI 271 simulation output into a structured benefits object.
    This is the canonical benefits model used across the platform.
    """
    coverage_active = edi_response.get("coverage_active", True)

    benefits = {
        "coverage_status":        "Active" if coverage_active else "Inactive",
        "copay":                  edi_response.get("copay", 0),
        "deductible_total":       edi_response.get("deductible_total", 0),
        "deductible_remaining":   edi_response.get("deductible_remaining", 0),
        "deductible_met":         edi_response.get("deductible_total", 0) - edi_response.get("deductible_remaining", 0),
        "coinsurance":            edi_response.get("coinsurance", 20),   # percent
        "out_of_pocket_max":      edi_response.get("out_of_pocket_max", 0),
        "in_network":             True,   # Default assumption for prototype
        "plan_type":              _determine_plan_type(edi_response),
        "coverage_summary":       _build_coverage_summary(edi_response, coverage_active),
    }
    return benefits


def _determine_plan_type(edi: dict) -> str:
    """Guess plan type based on copay / deductible patterns."""
    copay      = edi.get("copay", 0)
    deductible = edi.get("deductible_total", 0)
    if copay == 0 and deductible > 20000:
        return "HDHP"         # High Deductible Health Plan
    elif copay > 0 and deductible < 10000:
        return "HMO/PPO"
    elif deductible == 0:
        return "Co-pay Only"
    return "PPO"


def _build_coverage_summary(edi: dict, active: bool) -> str:
    """Build a human-readable one-line coverage summary."""
    if not active:
        return "⚠️ Coverage is INACTIVE. Patient may not have valid insurance."
    copay    = edi.get("copay", 0)
    deduct   = edi.get("deductible_remaining", 0)
    coins    = edi.get("coinsurance", 20)
    return (
        f"Coverage ACTIVE. Copay: ₹{copay:,} | "
        f"Remaining Deductible: ₹{deduct:,} | "
        f"Coinsurance: {coins}%"
    )
