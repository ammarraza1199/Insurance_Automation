"""
Module 3 & 4: EDI 270 Generator + Fake EDI 271 Response Simulator
Generates ANSI X12 EDI 270 eligibility requests and simulates 271 responses.
"""
import random
from datetime import datetime


def generate_270(card_data: dict) -> str:
    """
    Build a simplified EDI 270 eligibility inquiry transaction exactly as specified in the PDF.
    """
    member_id = (card_data.get("member_id") or "SHI2026MH458921").upper().replace(" ", "")
    dob_raw = card_data.get("dob") or "1995-08-15"
    dob_formatted = _format_dob_edi(dob_raw)
    
    # Using the exact name from the PDF if available, otherwise fallback
    name = (card_data.get("member_name") or "SAGAR A").upper()
    name_parts = name.split()
    first = name_parts[0] if len(name_parts) > 0 else "SAGAR"
    last = name_parts[-1] if len(name_parts) > 1 else "A"
    
    # Exact structure from PDF Module 3
    edi = (
        f"ST*270*0001~\n"
        f"NM1*IL*1*{first}*{last}****MI*{member_id}~\n"
        f"DMG*D8*{dob_formatted}*M~\n"
        f"EQ*30~\n"
    )
    return edi


def simulate_271(card_data: dict) -> dict:
    """
    Simulate a fake payer EDI 271 eligibility response.
    It returns the EXACT format from the PDF but varying (randomized) values to test edge cases.
    Returns both the raw EDI string and parsed benefits dict.
    """
    # Determine coverage based on card validity extracted via OCR
    valid_thru = card_data.get("valid_thru", "Unknown")
    coverage_active = _check_coverage_active(valid_thru)

    # Generate realistic-looking random benefit values to test edge cases
    copay                = random.choice([0, 20, 50, 100, 250, 500])
    deductible_total     = random.choice([2500, 5000, 10000, 15000, 20000, 50000])
    deductible_remaining = random.randint(0, deductible_total)
    coinsurance          = random.choice([0, 10, 20, 30])         # percent
    out_of_pocket_max    = random.choice([50000, 100000, 200000, 300000, 500000])

    status_code = "1" if coverage_active else "6"
    status_label = "ACTIVE COVERAGE" if coverage_active else "INACTIVE"
    
    # Exact structure from PDF Module 4 (but with randomized data points)
    edi_271 = (
        f"EB*{status_code}**30**{status_label}~\n"
        f"EB*B**98**{copay}~\n"
        f"EB*C**29**{deductible_total}~\n"
        f"EB*G**29**{deductible_remaining}~\n"
        f"EB*A**30**{coinsurance}~\n"
        f"EB*F**30**{out_of_pocket_max}~\n"
    )

    return {
        "edi_270":      "",  # Will be filled by caller
        "edi_271":      edi_271,
        "coverage_active": coverage_active,
        "copay":              copay,
        "deductible_total":   deductible_total,
        "deductible_remaining": deductible_remaining,
        "coinsurance":        coinsurance,
        "out_of_pocket_max":  out_of_pocket_max,
        "status_label":       status_label,
    }


def _check_coverage_active(valid_thru: str) -> bool:
    """Try to parse valid_thru date and compare to today."""
    if not valid_thru or valid_thru == "Unknown":
        return True   # Default to active if unknown

    import re
    from datetime import date
    today = date.today()

    # Try MM/YYYY
    m = re.match(r'(\d{1,2})[/\-\.](\d{4})$', valid_thru)
    if m:
        mo, yr = int(m.group(1)), int(m.group(2))
        return (yr, mo) >= (today.year, today.month)

    # Try MM/DD/YYYY or MM-DD-YYYY
    m = re.match(r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})$', valid_thru)
    if m:
        mo, dd, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            exp = date(yr, mo, dd)
            return exp >= today
        except ValueError:
            pass

    return True


def _format_dob_edi(dob: str) -> str:
    """Convert DOB to YYYYMMDD for EDI."""
    import re
    if not dob or dob == "Unknown":
        return "19900101"
    m = re.match(r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})$', dob)
    if m:
        mm, dd, yyyy = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
        return f"{yyyy}{mm}{dd}"
    return "19900101"
