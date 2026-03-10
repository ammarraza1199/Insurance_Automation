"""
Module 1 & 2: Insurance Card Upload + OCR Extraction Engine
Extracts structured data from insurance card images using EasyOCR + regex.
"""
import re # type: ignore
import easyocr # type: ignore
import torch # type: ignore
from datetime import datetime # type: ignore

# Lazy singleton — initialized on first use to avoid download at import time
_reader = None

def _get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
    return _reader


def extract_card_data(image_bytes: bytes) -> dict:
    """
    Run OCR on insurance card image and extract all insurance fields.
    Returns structured dict matching the PDF spec.
    """
    # --- OCR ---
    result = _get_reader().readtext(image_bytes, detail=0)
    raw_text = " ".join(result)
    lines = [r.strip() for r in result if r.strip()]

    # Build a helper lookup: map each label token to the token(s) that follow it.
    # This handles cases where EasyOCR splits a label and its value into separate
    # list items (e.g. ["Valid Thru", "12/31/2025"] as two separate detections).
    _token_pairs = {lines[i].lower(): lines[i + 1] for i in range(len(lines) - 1)}

    # --- Field Extractors ---
    member_name   = _extract_member_name(raw_text, lines, _token_pairs)
    member_id     = _extract_member_id(raw_text, _token_pairs)
    group_number  = _extract_group_number(raw_text, _token_pairs)
    policy_number = _extract_policy_number(raw_text, _token_pairs)
    dob           = _extract_dob(raw_text, _token_pairs)
    payer_name    = _extract_payer_name(raw_text, lines, _token_pairs)
    valid_thru    = _extract_valid_thru(raw_text, _token_pairs)

    return {
        "member_name":    member_name,
        "member_id":      member_id,
        "group_number":   group_number,
        "policy_number":  policy_number,
        "dob":            dob,
        "payer_name":     payer_name,
        "valid_thru":     valid_thru,
        "raw_text":       raw_text,
        "extracted_at":   datetime.utcnow().isoformat(),
    }


# ─── Private helpers ──────────────────────────────────────────────────────────

def _clean_name(raw: str) -> str:
    """
    Strip any trailing garbage that bleeds into a name due to OCR token joining.
    Truncates at the first known label keyword or ID-like string.
    Examples:
      'JOHN A SMITH Member ID BSC-123' → 'JOHN A SMITH'
      'MARIA GONZALEZ Group 12345'     → 'MARIA GONZALEZ'
    """
    # Truncate at common field labels that follow a name
    label_boundary = re.compile(
        r'\b(?:Member\s*ID|Subscriber\s*ID|Group|Plan|Policy|DOB|Date\s*of\s*Birth|'
        r'Payer|Insurance|Valid|Thru|Through|Copay|Deductible|ID\b)',
        re.IGNORECASE
    )
    m = label_boundary.search(raw)
    if m:
        raw = raw[:m.start()].strip()
    # Also strip trailing standalone alphanumeric codes that look like IDs (e.g. "BSC-")
    raw = re.sub(r'\s+[A-Z]{2,5}-?\s*$', '', raw).strip()
    return raw


def _extract_member_name(text: str, lines: list, token_pairs: dict = None) -> str:  # type: ignore
    """Extract member/patient name from card text."""
    if token_pairs is not None:
        for label_key in ["member name", "patient name", "insured name", "subscriber name", "name", "name:"]:
            if label_key in token_pairs:
                val = token_pairs[label_key].strip()
                if len(val) >= 4 and not bool(re.search(r'\d', val)):
                    return _clean_name(val)

    # Label-based extraction
    for pat in [
        r'(?:Member|Patient|Insured|Subscriber)\s*Name\s*[:\-]?\s*([A-Z][A-Za-z\s\-\']{2,40})',
        r'Name\s*[:\-]\s*([A-Z][A-Za-z\s\-\']{2,40})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return _clean_name(m.group(1).strip())

    # Fallback: look for "LAST, FIRST" pattern (pure alpha only)
    m = re.search(r'([A-Z]{2,20}),\s*([A-Z][A-Za-z]{1,20})(?=\s|$)', text)
    if m:
        return _clean_name(f"{m.group(2)} {m.group(1).title()}")

    return "Unknown"



def _extract_member_id(text: str, token_pairs: dict = None) -> str:  # type: ignore
    """Extract member/subscriber ID — allows hyphens in ID values."""
    if token_pairs is not None:
        for label_key in ["member id", "subscriber id", "id number", "member id:"]:
            if label_key in token_pairs:
                val = token_pairs[label_key].strip()
                if re.match(r'[A-Z0-9][A-Z0-9\-]{4,}', val, re.IGNORECASE):
                    return val

    for pat in [
        r'(?:Member|Subscriber)\s*ID\s*[:\-#]?\s*([A-Z0-9][A-Z0-9\-]{4,20})',
        r'\bID\s*[#:\s]+([A-Z0-9][A-Z0-9\-]{4,20})',
        r'\bID\b[^\n]{0,5}([A-Z]{2,4}-[\d\-]{4,18})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    m = re.search(r'\b([A-Z]{2,4}[\-]?\d{4,15}(?:[\-]\d{1,5})?)\b', text)
    if m:
        return m.group(1)
    return "Unknown"


def _extract_group_number(text: str, token_pairs: dict = None) -> str:  # type: ignore
    """Extract group number."""
    if token_pairs is not None:
        for label_key in ["group number", "group no", "group #", "grp", "grp number"]:
            if label_key in token_pairs:
                val = token_pairs[label_key].strip()
                if re.match(r'[A-Z0-9\-]{4,}', val, re.IGNORECASE):
                    return val

    for pat in [
        r'(?:Group|Grp)[\s#\-]*(?:No|Num|Number|#)?\s*[:\-]?\s*([A-Z0-9\-]{4,20})',
        r'GRP[:\-\s]+([A-Z0-9\-]{4,20})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Unknown"


def _extract_policy_number(text: str, token_pairs: dict = None) -> str:  # type: ignore
    """Extract policy number."""
    if token_pairs is not None:
        for label_key in ["policy number", "policy no", "policy #", "plan number", "contract number", "pol"]:
            if label_key in token_pairs:
                val = token_pairs[label_key].strip()
                if re.match(r'[A-Z0-9\-]{4,}', val, re.IGNORECASE):
                    return val

    for pat in [
        r'(?:Policy|Plan|Contract)\s*(?:No|Num|Number|#)?\s*[:\-]?\s*([A-Z0-9\-]{6,20})',
        r'POL[:\-\s]+([A-Z0-9\-]{6,20})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Unknown"


def _extract_dob(text: str, token_pairs: dict = None) -> str:  # type: ignore
    """Extract date of birth."""
    if token_pairs is not None:
        for label_key in ["dob", "date of birth", "birth date", "birth"]:
            if label_key in token_pairs:
                val = token_pairs[label_key].strip()
                if re.match(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', val) or re.match(r'\d{8}', val):
                    return val

    for pat in [
        r'(?:DOB|Date\s*of\s*Birth|Birth\s*Date)\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        r'(?:DOB|Birth)\s*[:\-]?\s*(\d{8})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Unknown"


def _extract_payer_name(text: str, lines: list, token_pairs: dict = None) -> str:  # type: ignore
    """Extract insurance provider/payer name."""
    # Strict matching based on common known payers (best approach for headers)
    known_payers = [
        "Aetna", "UnitedHealth", "Cigna", "Humana", "Anthem", "BlueCross",
        "Blue Cross", "Blue Shield", "Kaiser", "Molina", "Centene", "CVS",
        "Star Health", "Max Bupa", "HDFC Ergo", "SBI General", "United",
        "Medicare", "Medicaid", "Tricare"
    ]
    for payer in known_payers:
        if payer.lower() in text.lower():
            # Special case for split "Blue Shield" / "Blue Cross" OCR failures
            if payer == "Blue Shield" and "Cross" in text: return "Blue Cross Blue Shield"
            return payer

    if token_pairs is not None:
        for label_key in ["payer", "insurer", "insurance provider", "plan", "insurance"]:
            if label_key in token_pairs:
                val = token_pairs[label_key].strip()
                if len(val) >= 3 and not bool(re.search(r'\d', val)):
                    return val

    m = re.search(r'(?:Insurance|Payer|Provider|Plan|Carrier)\s*[:\-]?\s*([A-Z][A-Za-z\s]{2,40})', text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    if lines:
        return lines[0].strip()

    return "Unknown"


def _extract_valid_thru(text: str, token_pairs: dict = None) -> str:  # type: ignore
    """Extract policy valid/expiry date."""
    # Check adjacent OCR token lookup first
    if token_pairs:
        for label_key in ["valid thru", "valid through", "valid until", "exp date",
                          "expiry", "expiry date", "effective thru", "expires",
                          "member since", "valid:", "thru"]:
            if label_key in token_pairs:
                val = token_pairs[label_key].strip()
                # Accept common date formats: MM/DD/YYYY, MM-DD-YYYY, MM/YYYY
                if re.match(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', val) or \
                   re.match(r'\d{2}[/\-]\d{4}', val):
                    return val

    # Extended regex on joined text — covers 'Valid Thru', 'Valid Through', 'Effective'
    for pat in [
        r'(?:Valid|Expiry|Exp(?:iry|ires)?|Effective)\s*(?:Date|Thru|Through|Until)?\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        r'(?:Valid|Exp)\s*[:\-]?\s*(\d{2}[/\-]\d{4})',
        r'(?:Thru|Through|Until)\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        # Bare date that follows any expiry keyword within 60 characters
        r'(?:Valid|Expir|Thru|Effective).{1,60}?(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Unknown"
