import easyocr # type: ignore
import re # type: ignore
import torch # type: ignore

# ── spaCy NER (en_core_web_sm) ────────────────────────────────────────────────
try:
    import spacy # type: ignore
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    # If spaCy or the model is not installed, fall back to regex-only mode
    nlp = None
    SPACY_AVAILABLE = False
    print("[WARNING] spaCy en_core_web_sm not found. Using regex fallback for NER.")
    print("          To enable NER: pip install spacy && python -m spacy download en_core_web_sm")

# ── EasyOCR ────────────────────────────────────────────────────────────────────
reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

# ── ICD-10 regex (e.g. E11.9, Z99.8, A00.0) ───────────────────────────────────
ICD10_PATTERN = re.compile(r'\b[A-TV-Z][0-9][0-9AB]\.?[0-9A-TV-Z]{0,4}\b')


def _extract_with_spacy(text: str) -> dict:
    """Use spaCy NER to extract PERSON and DATE entities."""
    doc = nlp(text) # type: ignore
    name, dob = "Unknown", "Unknown"

    for ent in doc.ents:
        if ent.label_ == "PERSON" and name == "Unknown":
            name = ent.text.strip()
        elif ent.label_ == "DATE" and dob == "Unknown":
            dob = ent.text.strip()

    return {"name": name, "dob": dob}


def _extract_with_regex(text: str) -> dict:
    """Fallback: look for labelled fields like 'Patient Name: John Doe'."""
    name, dob = "Unknown", "Unknown"

    name_match = re.search(
        r'(?:Patient\s*Name|Name)\s*[:\-]\s*([A-Za-z][A-Za-z\s\-\']{1,50})',
        text, re.IGNORECASE
    )
    if name_match:
        name = name_match.group(1).strip()

    dob_match = re.search(
        r'(?:DOB|Date of Birth|Birth Date)\s*[:\-]\s*([\d]{1,2}[/\-][\d]{1,2}[/\-][\d]{2,4})',
        text, re.IGNORECASE
    )
    if dob_match:
        dob = dob_match.group(1).strip()

    return {"name": name, "dob": dob}


def extract_info_from_image(image_bytes: bytes) -> dict:
    """Main function: OCR -> ICD-10 extraction -> NER for patient info."""
    # 1. Run EasyOCR
    result = reader.readtext(image_bytes, detail=0)
    raw_text = " ".join(result)

    # 2. Extract ICD-10 codes via regex (most reliable method – codes are structured)
    icd10_matches = list(set(ICD10_PATTERN.findall(raw_text)))

    # 3. Extract patient demographics: spaCy first, regex as fallback
    if SPACY_AVAILABLE:
        patient_info = _extract_with_spacy(raw_text)
        # If spaCy didn't find a name, try regex too (labelled documents)
        if patient_info["name"] == "Unknown":
            regex_info = _extract_with_regex(raw_text)
            if regex_info["name"] != "Unknown":
                patient_info["name"] = regex_info["name"]
        if patient_info["dob"] == "Unknown":
            regex_info = _extract_with_regex(raw_text)
            if regex_info["dob"] != "Unknown":
                patient_info["dob"] = regex_info["dob"]
    else:
        patient_info = _extract_with_regex(raw_text)

    return {
        "raw_text": raw_text,
        "icd10_codes": icd10_matches,
        "patient_info": patient_info,
        "ner_engine": "spaCy" if SPACY_AVAILABLE else "regex",
    }
