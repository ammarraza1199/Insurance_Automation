"""
Module 6: Financial Estimation Engine
Estimates patient vs. insurance financial responsibility for a given procedure cost.

Real-world US insurance billing order:
  1. If procedure_cost <= copay → patient pays copay (flat fee), insurance pays 0
     (copay is the floor — the guaranteed minimum patient contribution)
  2. Otherwise:
     a. Patient pays toward remaining deductible first
     b. After deductible is met, patient pays coinsurance % on residual
     c. Copay is charged as a flat per-visit fee IN ADDITION only if it's
        an office visit type (for simplicity we add it as the minimum floor)
  3. Total patient_pay is capped at out_of_pocket_max
"""


def estimate_cost(procedure_cost: float, benefits: dict) -> dict:
    """
    Calculate patient_pay and insurance_pay based on real RCM billing logic.
    """
    deductible_remaining = float(benefits.get("deductible_remaining", 0))
    coinsurance_pct      = float(benefits.get("coinsurance", 20)) / 100.0
    copay                = float(benefits.get("copay", 0))
    oop_max              = float(benefits.get("out_of_pocket_max", 0)) or float("inf")
    coverage_active      = benefits.get("coverage_status", "Active") == "Active"

    if not coverage_active:
        return {
            "procedure_cost":     round(procedure_cost, 2),
            "patient_pay":        round(procedure_cost, 2),
            "insurance_pay":      0.0,
            "deductible_applied": 0.0,
            "coinsurance_amount": 0.0,
            "copay_applied":      0.0,
            "coverage_pct":       0.0,
            "note": "Coverage is inactive — patient responsible for full cost.",
        }

    # ── Step 1: Deductible ───────────────────────────────────────────────────
    deductible_applied = min(deductible_remaining, procedure_cost)
    cost_after_ded     = procedure_cost - deductible_applied

    # ── Step 2: Coinsurance on cost after deductible ─────────────────────────
    coinsurance_amount = round(cost_after_ded * coinsurance_pct, 2)

    # ── Step 3: Copay logic ───────────────────────────────────────────────────
    # Copay is a flat per-visit fee. In real billing:
    # - If the entire procedure is covered by the copay (procedure_cost <= copay),
    #   the patient just pays the copay and insurance pays nothing.
    # - Otherwise, copay is applied as a minimum per-visit contribution
    #   (which may overlap with deductible+coinsurance calculations).
    # Simplified: patient pays MAX of (copay) vs (deductible + coinsurance).
    # This model: patient pays deductible + coinsurance, floored to copay minimum.
    calc_patient = deductible_applied + coinsurance_amount
    patient_responsibility = max(calc_patient, copay)
    copay_applied = copay if patient_responsibility == copay else 0.0

    # ── Step 4: Cap at out-of-pocket max ────────────────────────────────────
    patient_pay   = round(min(patient_responsibility, oop_max), 2)
    insurance_pay = round(max(procedure_cost - patient_pay, 0.0), 2)
    coverage_pct  = round((insurance_pay / procedure_cost * 100) if procedure_cost > 0 else 0.0, 1)

    return {
        "procedure_cost":     round(procedure_cost, 2),
        "patient_pay":        patient_pay,
        "insurance_pay":      insurance_pay,
        "deductible_applied": round(deductible_applied, 2),
        "coinsurance_amount": coinsurance_amount,
        "copay_applied":      copay_applied,
        "coverage_pct":       coverage_pct,
        "note":               _build_note(patient_pay, insurance_pay, procedure_cost, deductible_applied, coinsurance_amount, copay),
    }


def _build_note(patient_pay: float, insurance_pay: float, total: float,
                ded: float, coins: float, copay: float) -> str:
    if total == 0:
        return "No cost entered."
    pct = round(insurance_pay / total * 100, 1) if total > 0 else 0
    parts = []
    if ded > 0:
        parts.append(f"₹{ded:,.0f} toward deductible")
    if coins > 0:
        parts.append(f"₹{coins:,.0f} coinsurance ({int(coins/max(total-ded,1)*100)}% of post-deductible cost)")
    if copay > 0 and not parts:
        parts.append(f"₹{copay:,.0f} copay")
    breakdown = "; ".join(parts) if parts else "copay applied"
    return f"Insurance covers {pct}% of the total procedure cost. Patient breakdown: {breakdown}."

