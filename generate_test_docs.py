"""
Test Document Generator — Comprehensive Edition
================================================
Generates PNG images simulating insurance cards, medical records, referral letters,
EOB forms, and authorization requests for full edge-case OCR testing.

Covers all 8 backend modules:
  - Module 1&2 : Insurance Card OCR
  - Module 3   : EDI 270 Generator
  - Module 4   : EDI 271 Simulator
  - Module 5   : Benefits Interpretation
  - Module 6   : Financial Estimation
  - Module 7   : Denial Risk Scoring
  - Module 8   : CPT Authorization (AI)

Requirements:
    pip install Pillow

Usage:
    python generate_test_docs.py

Output: Creates/updates `test_docs/` folder with 20 test PNG images.
"""

from PIL import Image, ImageDraw, ImageFont
import os, random

OUTPUT_DIR = "test_docs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_font(size=18, bold=False):
    candidates = [
        ("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        "C:/Windows/Fonts/cour.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Courier.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


HEADER_COLORS = {
    "insurance": "#003566",   # dark blue — insurance card
    "medical":   "#1B4332",   # dark green — medical record
    "referral":  "#6A0572",   # purple — referral letter
    "billing":   "#7D0000",   # dark red — billing / EOB
    "auth":      "#0B3D91",   # navy — authorization
    "edge":      "#4A4A4A",   # grey — edge/stress cases
}


def make_doc(
    filename: str,
    lines: list,
    title: str = "",
    doc_type: str = "medical",
    width: int = 820,
    line_height: int = 26,
    watermark: str = None,
):
    """Render a list of text lines onto a styled PNG."""
    font_title  = get_font(21, bold=True)
    font_body   = get_font(17)
    font_small  = get_font(13)
    font_wm     = get_font(48)

    padding   = 40
    height    = padding * 2 + (len(lines) + 4) * line_height + 70
    img       = Image.new("RGB", (width, height), color="#FAFAFA")
    draw      = ImageDraw.Draw(img)

    # Header bar
    color = HEADER_COLORS.get(doc_type, "#003566")
    draw.rectangle([0, 0, width, 64], fill=color)
    draw.text((padding, 20), title or filename, fill="white", font=font_title)

    # Subtle top-right label
    draw.text((width - 160, 22), doc_type.upper(), fill="rgba(255,255,255,128)", font=font_small)

    # Horizontal separator
    draw.rectangle([padding, 72, width - padding, 74], fill="#CCCCCC")

    # Body text
    y = 82
    for line in lines:
        color_txt = "#444444" if line.startswith("  ") else "#111111"
        if line.startswith("──") or line.startswith("=="):
            draw.rectangle([padding, y + 10, width - padding, y + 12], fill="#AAAAAA")
            y += line_height
            continue
        draw.text((padding, y), line, fill=color_txt, font=font_body)
        y += line_height

    # Footer
    draw.rectangle([0, height - 30, width, height], fill="#EEEEEE")
    draw.text((padding, height - 22), f"TEST DOCUMENT — {filename}", fill="#888888", font=font_small)

    # Optional watermark
    if watermark:
        wm_w = draw.textlength(watermark, font=font_wm)
        draw.text(
            ((width - wm_w) // 2, height // 2 - 30),
            watermark, fill=(220, 50, 50, 60), font=font_wm
        )

    path = os.path.join(OUTPUT_DIR, filename)
    img.save(path)
    print(f"  ✅ Created: {path}")


# ═════════════════════════════════════════════════════════════════════════════
# GROUP A — INSURANCE CARD OCR  (Modules 1 & 2)
# ═════════════════════════════════════════════════════════════════════════════

make_doc("01_insurance_card_standard.png",
    title="[A1] Insurance Card — Standard (Happy Path)",
    doc_type="insurance",
    lines=[
        "BLUE SHIELD OF CALIFORNIA",
        "──────────────────────────────────────────────────────",
        "Member Name   :  JOHN A. SMITH",
        "Member ID     :  BSC-4928173-01",
        "Group Number  :  GRP-00291",
        "Policy Number :  POL-2025-009812",
        "Plan Type     :  PPO",
        "Valid Thru    :  12/31/2025",
        "Date of Birth :  04/15/1978",
        "──────────────────────────────────────────────────────",
        "Copay         :  $25 (Primary Care) / $50 (Specialist)",
        "Deductible    :  $1,500 / year",
        "Out-of-Pocket :  $5,000 / year",
        "In-Network    :  YES",
    ]
)

make_doc("02_insurance_card_missing_fields.png",
    title="[A2] Insurance Card — Missing Fields (Edge Case)",
    doc_type="insurance",
    lines=[
        "UNITED HEALTHCARE",
        "──────────────────────────────────────────────────────",
        "Member Name   :  MARIA GONZALEZ",
        "Member ID     :  UHC-9982110",
        "Group Number  :  (NOT PROVIDED)",
        "Policy Number :  —",
        "Plan Type     :  HMO",
        "Valid Thru    :  UNKNOWN",
        "Date of Birth :  09/22/1965",
        "──────────────────────────────────────────────────────",
        "NOTE: Group and Policy numbers were not printed.",
        "Please verify with employer HR department.",
    ]
)

make_doc("03_insurance_card_expired.png",
    title="[A3] Insurance Card — Expired Coverage",
    doc_type="insurance",
    watermark="EXPIRED",
    lines=[
        "AETNA HEALTH INSURANCE",
        "──────────────────────────────────────────────────────",
        "Member Name   :  ROBERT ANDERSON",
        "Member ID     :  AET-0038821",
        "Group Number  :  GRP-7712",
        "Policy Number :  POL-2023-001199",
        "Plan Type     :  EPO",
        "Valid Thru    :  06/30/2023   ← EXPIRED",
        "Date of Birth :  03/03/1982",
        "──────────────────────────────────────────────────────",
        "Coverage Status: LAPSED — Renewal required.",
        "Contact: 1-800-AETNA-01 for reinstatement.",
    ]
)

make_doc("04_insurance_card_medicaid.png",
    title="[A4] Insurance Card — Medicaid / Low-Income Plan",
    doc_type="insurance",
    lines=[
        "STATE MEDICAID PROGRAM",
        "──────────────────────────────────────────────────────",
        "Recipient Name :  DIANA FOSTER",
        "Medicaid ID    :  MCD-CA-2025-774412",
        "Case Number    :  CAS-00198822",
        "Plan Type      :  Medicaid Managed Care",
        "Valid Thru     :  12/31/2025",
        "Date of Birth  :  07/04/2001",
        "──────────────────────────────────────────────────────",
        "Copay          :  $0 (Medicaid Exempt)",
        "Deductible     :  $0",
        "Out-of-Pocket  :  $0",
        "In-Network     :  YES (Statewide)",
    ]
)

make_doc("05_insurance_card_ocr_noise.png",
    title="[A5] Insurance Card — OCR Noise / Scan Artifacts",
    doc_type="edge",
    lines=[
        "BLU3 CR0SS BLU3 SH13LD  (OCR misread: O→0, E→3)",
        "──────────────────────────────────────────────────────",
        "M3mb3r Nam3   :  THOM4S WR1GHT",
        "M3mb3r 1D     :  BC-00 44-938    (space artifact)",
        "Gr0up Numb3r  :  GRP- O29I      (O vs 0, I vs 1)",
        "P0licy Numb3r :  POL-2O25-OO12  (misread digits)",
        "Plan Typ3     :  PP0",
        "Val1d Thru    :  I2/3I/2025     (I vs 1)",
        "──────────────────────────────────────────────────────",
        "Copay         :  $2S            (S vs 5)",
        "D3ductib13    :  $I,5OO",
        "NOTE: Scanned from faxed copy — quality degraded.",
    ]
)


# ═════════════════════════════════════════════════════════════════════════════
# GROUP B — MEDICAL RECORDS / DIAGNOSIS  (Modules 3, 5, 7, 8)
# ═════════════════════════════════════════════════════════════════════════════

make_doc("06_medical_record_standard.png",
    title="[B1] Medical Record — Standard Visit (Happy Path)",
    doc_type="medical",
    lines=[
        "LAKESIDE FAMILY CLINIC — Visit Summary",
        "──────────────────────────────────────────────────────",
        "Patient Name  :  Sarah Thompson",
        "Date of Birth :  11/20/1985",
        "Visit Date    :  02/10/2025",
        "Provider      :  Dr. Emily Chen, MD",
        "──────────────────────────────────────────────────────",
        "PRIMARY DIAGNOSIS",
        "  E11.9   — Type 2 Diabetes Mellitus, uncontrolled",
        "",
        "SECONDARY DIAGNOSES",
        "  I10     — Essential (Primary) Hypertension",
        "  E78.5   — Hyperlipidemia, unspecified",
        "",
        "PROCEDURES",
        "  99213   — Office or Other Outpatient Visit (Est.)",
        "  83036   — Hemoglobin A1C Level",
        "  93000   — Electrocardiogram",
        "",
        "MEDICAL SUMMARY",
        "  Patient presents with poorly controlled T2DM.",
        "  HbA1c elevated at 9.2%. BP: 145/92mmHg.",
        "  Medication adjusted; follow-up in 6 weeks.",
    ]
)

make_doc("07_medical_record_multiple_icd10.png",
    title="[B2] Medical Record — 6 Comorbid Diagnoses",
    doc_type="medical",
    lines=[
        "REGIONAL MEDICAL CENTER — Discharge Summary",
        "──────────────────────────────────────────────────────",
        "Patient       :  Carlos Mendez,  DOB: 06/15/1958",
        "Admission     :  01/28/2025      Discharge: 02/02/2025",
        "Attending     :  Dr. William Osei, MD",
        "──────────────────────────────────────────────────────",
        "DIAGNOSES (All Active)",
        "  1. J18.9   — Pneumonia, unspecified organism",
        "  2. E11.65  — T2DM with hyperglycemia",
        "  3. I50.9   — Heart failure, unspecified",
        "  4. N18.3   — Chronic Kidney Disease, Stage 3",
        "  5. J44.1   — COPD with acute exacerbation",
        "  6. F32.1   — Major Depressive Disorder, moderate",
        "──────────────────────────────────────────────────────",
        "PROCEDURES",
        "  99223   — Initial hospital care, high complexity",
        "  71046   — Chest X-ray, 2 views",
        "  93306   — Echo w/ doppler",
    ]
)

make_doc("08_medical_record_no_icd10.png",
    title="[B3] Medical Record — No ICD-10 Codes (Edge Case)",
    doc_type="medical",
    lines=[
        "WELLNESS CENTER — Annual Physical",
        "──────────────────────────────────────────────────────",
        "Patient Name  :  Susan Park",
        "Date of Birth :  07/30/1992",
        "Visit Date    :  03/01/2025",
        "Provider      :  Dr. James Okafor, MD",
        "──────────────────────────────────────────────────────",
        "PURPOSE: Annual preventive health examination.",
        "",
        "FINDINGS:",
        "  Patient is in excellent overall health.",
        "  BMI: 22.1  |  BP: 118/76  |  HR: 68 bpm",
        "  All labs within normal range.",
        "",
        "NOTE: No diagnosis codes applicable at this time.",
        "Routine preventive care only.",
        "",
        "CPT: 99395 — Preventive Care, established, 18-39 yrs",
    ]
)

make_doc("09_medical_record_pediatric.png",
    title="[B4] Medical Record — Pediatric Patient (Age 6)",
    doc_type="medical",
    lines=[
        "CHILDREN'S HEALTH CLINIC — Pediatric Visit",
        "──────────────────────────────────────────────────────",
        "Patient Name  :  Emma Johnson",
        "Date of Birth :  06/12/2018   (Age: 6)",
        "Parent/Guardian: Kate Johnson",
        "Insurance     :  Aetna Kids  #AET-2019-1122",
        "──────────────────────────────────────────────────────",
        "DIAGNOSES",
        "  J06.9   — Acute Upper Respiratory Infection",
        "  L20.9   — Atopic Dermatitis, unspecified",
        "  Z23     — Encounter for immunization",
        "",
        "PROCEDURES",
        "  99213   — Office Visit, established patient",
        "  90686   — Influenza vaccine, quadrivalent",
        "  96372   — Therapeutic injection",
    ]
)

make_doc("10_medical_record_emergency.png",
    title="[B5] Medical Record — Emergency / Unknown Patient",
    doc_type="medical",
    watermark="UNIDENTIFIED",
    lines=[
        "COUNTY GENERAL HOSPITAL — Emergency Department",
        "──────────────────────────────────────────────────────",
        "Reference #   :  ER-20250103-0042",
        "Admit Date    :  01/03/2025  02:47 AM",
        "Patient Name  :  UNKNOWN (refused identification)",
        "Date of Birth :  UNKNOWN",
        "Insurance     :  UNKNOWN — Self-pay assumed",
        "──────────────────────────────────────────────────────",
        "CHIEF COMPLAINT: Chest pain, shortness of breath.",
        "",
        "EMERGENCY DIAGNOSES",
        "  I21.9   — Acute Myocardial Infarction, unspecified",
        "  I10     — Hypertension (new finding)",
        "",
        "PROCEDURES",
        "  99285   — ED Visit, high complexity",
        "  93010   — ECG interpretation",
        "  71046   — Chest X-ray (2 views)",
    ]
)

make_doc("11_referral_freeform_letter.png",
    title="[B6] Referral Letter — Freeform Prose (tests NER)",
    doc_type="referral",
    lines=[
        "METROPOLITAN MEDICAL ASSOCIATES",
        "──────────────────────────────────────────────────────",
        "Date: February 15, 2025",
        "",
        "Dear Dr. Parker,",
        "",
        "I am referring my patient Robert Anderson, born on",
        "March 3rd, 1982, for further evaluation of his recently",
        "diagnosed Type 2 Diabetes (E11.9) and hypertension (I10).",
        "",
        "Robert has been under my care since January 2020 and",
        "has not responded adequately to metformin therapy.",
        "HbA1c remains at 10.1%. I believe an endocrinology",
        "consultation and possible insulin initiation (CPT 99245)",
        "would be appropriate at this time.",
        "",
        "Please arrange an appointment at your earliest convenience.",
        "",
        "Sincerely,",
        "Dr. Lisa Nguyen, MD — Internal Medicine",
        "License: CA-MD-298841",
    ]
)


# ═════════════════════════════════════════════════════════════════════════════
# GROUP C — BILLING / FINANCIAL / EOB  (Module 6)
# ═════════════════════════════════════════════════════════════════════════════

make_doc("12_eob_standard.png",
    title="[C1] Explanation of Benefits — Standard Claim",
    doc_type="billing",
    lines=[
        "BLUE SHIELD OF CALIFORNIA — Explanation of Benefits",
        "──────────────────────────────────────────────────────",
        "Claim #       :  CLM-2025-009812-01",
        "Patient       :  John A. Smith",
        "Member ID     :  BSC-4928173-01",
        "Date of Service: 01/20/2025",
        "──────────────────────────────────────────────────────",
        "SERVICE DETAIL",
        "  CPT 99213   Office Visit             $250.00",
        "  CPT 83036   HbA1c Lab Test           $85.00",
        "  CPT 93000   ECG                      $120.00",
        "                                   ──────────",
        "  Total Billed                         $455.00",
        "──────────────────────────────────────────────────────",
        "PAYMENT BREAKDOWN",
        "  Insurance Allowance                  $380.00",
        "  Deductible Applied                   $150.00",
        "  Coinsurance (20%)                    $46.00",
        "  Copay                                $25.00",
        "  Insurance Paid                       $159.00",
        "  Patient Responsibility               $221.00",
    ]
)

make_doc("13_eob_high_deductible.png",
    title="[C2] EOB — High Deductible Plan (HDHP)",
    doc_type="billing",
    lines=[
        "CIGNA HEALTH — Explanation of Benefits",
        "──────────────────────────────────────────────────────",
        "Claim #       :  CGN-2025-771200",
        "Patient       :  David Kim,  DOB: 11/05/1955",
        "Plan Type     :  HDHP / HSA-Compatible",
        "Deductible    :  $5,000 / year  (Remaining: $4,200)",
        "──────────────────────────────────────────────────────",
        "SERVICE DETAIL",
        "  CPT 27447   Total Knee Arthroplasty  $28,500.00",
        "  CPT 99232   Subsequent Hosp. Care    $180.00",
        "                                   ──────────",
        "  Total Billed                         $28,680.00",
        "──────────────────────────────────────────────────────",
        "PAYMENT BREAKDOWN",
        "  Deductible Applied (remaining)       $4,200.00",
        "  Coinsurance (20% of remainder)       $4,896.00",
        "  Insurance Paid                       $19,584.00",
        "  Patient Responsibility               $9,096.00",
        "  NOTE: Out-of-pocket maximum: $7,000",
    ]
)

make_doc("14_eob_out_of_network.png",
    title="[C3] EOB — Out-of-Network Provider (Higher Cost)",
    doc_type="billing",
    lines=[
        "AETNA HEALTH — Explanation of Benefits",
        "──────────────────────────────────────────────────────",
        "Claim #       :  AET-2025-OON-00931",
        "Patient       :  Maria Gonzalez",
        "Provider      :  Dr. Patrick Burns  (OUT-OF-NETWORK)",
        "Plan Type     :  EPO",
        "──────────────────────────────────────────────────────",
        "SERVICE DETAIL",
        "  CPT 45378   Colonoscopy             $3,200.00",
        "──────────────────────────────────────────────────────",
        "PAYMENT BREAKDOWN",
        "  Out-of-Network Penalty Applied:  YES",
        "  Allowed Amount (OON rate)        $1,400.00",
        "  Deductible Applied               $1,000.00",
        "  Coinsurance OON (40%)            $160.00",
        "  Insurance Paid                   $240.00",
        "  Patient Responsibility           $2,960.00",
        "  BALANCE BILLING by provider possible.",
    ]
)


# ═════════════════════════════════════════════════════════════════════════════
# GROUP D — AUTHORIZATION REQUESTS  (Module 8)
# ═════════════════════════════════════════════════════════════════════════════

make_doc("15_auth_request_approved.png",
    title="[D1] Prior Authorization — Likely Approved (CPT 27447)",
    doc_type="auth",
    lines=[
        "PRIOR AUTHORIZATION REQUEST",
        "──────────────────────────────────────────────────────",
        "Patient       :  James Walker,  DOB: 05/02/1950",
        "Insurance     :  Medicare Advantage  #MCR-44891",
        "Requesting MD :  Dr. Priya Patel, Orthopedic Surgery",
        "──────────────────────────────────────────────────────",
        "CPT CODE: 27447 — Total Knee Arthroplasty (TKA)",
        "",
        "DIAGNOSIS CODES",
        "  M17.11  — Primary Osteoarthritis, Right Knee",
        "  Z96.641 — Presence of right artificial knee joint",
        "",
        "MEDICAL JUSTIFICATION",
        "  Patient has failed 12 months of conservative therapy:",
        "  physical therapy, NSAIDs, corticosteroid injections.",
        "  X-ray shows bone-on-bone articulation (Grade IV).",
        "  Functional mobility severely limited. ADLs impaired.",
        "  Surgery is medically necessary per AMA guidelines.",
    ]
)

make_doc("16_auth_request_denied.png",
    title="[D2] Prior Authorization — Likely Denied (Cosmetic)",
    doc_type="auth",
    watermark="REVIEW",
    lines=[
        "PRIOR AUTHORIZATION REQUEST",
        "──────────────────────────────────────────────────────",
        "Patient       :  Amanda Ross,  DOB: 03/12/1988",
        "Insurance     :  Cigna PPO  #CGN-7721-00",
        "Requesting MD :  Dr. Kevin Hart, Plastic Surgery",
        "──────────────────────────────────────────────────────",
        "CPT CODE: 19318 — Breast Reduction Mammaplasty",
        "",
        "DIAGNOSIS CODES",
        "  N64.89  — Other specified disorders of breast",
        "",
        "MEDICAL JUSTIFICATION",
        "  Patient requests reduction for cosmetic reasons.",
        "  No documented back pain or functional impairment.",
        "  BMI: 21.4  |  Weight of tissue to remove: unknown.",
        "",
        "  NOTE: Insufficient documentation of medical necessity.",
        "  Insurer may classify as cosmetic — denial likely.",
    ]
)

make_doc("17_auth_request_experimental.png",
    title="[D3] Prior Authorization — Experimental Procedure",
    doc_type="auth",
    watermark="REVIEW",
    lines=[
        "PRIOR AUTHORIZATION REQUEST",
        "──────────────────────────────────────────────────────",
        "Patient       :  Thomas Green,  DOB: 09/18/1965",
        "Insurance     :  BlueCross PPO  #BC-998-77831",
        "Requesting MD :  Dr. Angela Moore, Oncology",
        "──────────────────────────────────────────────────────",
        "CPT CODE: 86849 — Unlisted Immunology Procedure",
        "         (CAR-T Cell Therapy, clinical trial)",
        "",
        "DIAGNOSIS CODES",
        "  C83.39  — Diffuse Large B-Cell Lymphoma (DLBCL)",
        "  Z79.899 — Long-term immunotherapy",
        "",
        "MEDICAL JUSTIFICATION",
        "  Patient enrolled in FDA Phase II clinical trial.",
        "  Standard chemotherapy failed (3 lines).",
        "  CAR-T is considered investigational by payer policy.",
        "",
        "  RISK: HIGH — Insurer may deny as experimental.",
    ]
)


# ═════════════════════════════════════════════════════════════════════════════
# GROUP E — DENIAL RISK / EDGE CASES  (Module 7)
# ═════════════════════════════════════════════════════════════════════════════

make_doc("18_denial_risk_high.png",
    title="[E1] High Denial Risk — Multiple Red Flags",
    doc_type="edge",
    watermark="HIGH RISK",
    lines=[
        "CLAIM REVIEW FILE — HIGH DENIAL RISK",
        "──────────────────────────────────────────────────────",
        "Patient       :  Unknown / Unidentified",
        "Insurance     :  LAPSED (Valid Thru: 01/2023)",
        "In-Network    :  NO  (Out-of-Network Provider)",
        "Deductible Rem:  $4,500 (nearly full year remaining)",
        "──────────────────────────────────────────────────────",
        "CPT CODE: 27447 — Total Knee Arthroplasty",
        "DIAGNOSIS   :  M79.3 — Panniculitis  (code mismatch!)",
        "",
        "RED FLAGS:",
        "  ✗ Coverage expired 2 years ago",
        "  ✗ Out-of-network provider, EPO plan",
        "  ✗ No prior authorization on file",
        "  ✗ Diagnosis code does not support CPT code",
        "  ✗ Deductible almost entirely unmet",
        "  ✗ No medical necessity documentation attached",
    ]
)

make_doc("19_icd10_without_dots.png",
    title="[E2] ICD-10 Codes Without Decimal Points (Format Edge Case)",
    doc_type="edge",
    lines=[
        "REGIONAL BILLING CENTER — Legacy System Export",
        "──────────────────────────────────────────────────────",
        "Patient       :  David Kim,  DOB: 11/05/1955",
        "System        :  Legacy ICD exporter v1.2 (no dots)",
        "──────────────────────────────────────────────────────",
        "BILLING CODES (no decimal format)",
        "",
        "  Primary   :  E119    (= E11.9  T2DM uncontrolled)",
        "  Secondary :  I10     (= I10    Hypertension)",
        "  Tertiary  :  J459    (= J45.9  Asthma)",
        "  Quaternary:  M545    (= M54.5  Low Back Pain)",
        "  Quinary   :  F321    (= F32.1  MDD, moderate)",
        "",
        "NOTE: All codes must be normalised to X##.X format",
        "before submission to modern payer portals.",
        "",
        "CPT: 99214 — Office Visit, moderate complexity",
        "CPT: 94640 — Nebulizer treatment",
    ]
)

make_doc("20_mixed_ocr_stress_test.png",
    title="[E3] Mixed OCR Noise + Missing Data (Full Stress Test)",
    doc_type="edge",
    lines=[
        "paTieNt nAme: Thom@s  Wri ght  [OCR garbling]",
        "──────────────────────────────────────────────────────",
        "dOb:  O3 / 21 / 1970   [O vs 0 typo]",
        "InsuranCe lD: BC-00 44-938   [space artifact]",
        "V@lid Thru: l2/3l/2025  [l vs 1 confusion]",
        "──────────────────────────────────────────────────────",
        "diaGnoSis coDe: E11.9  [mixed case — should parse OK]",
        "sEcondary: i10   [lowercase i instead of I]",
        "tertiary:  j459  [lowercase, no dot]",
        "",
        "cPT: 993 13   [space inserted inside code]",
        "Doctor: D r .  P e t  e  r  M o r r i s  [spaced out]",
        "──────────────────────────────────────────────────────",
        "Copay: $2S   [S misread as 5]",
        "Deductible: $I,5OO  [I→1, O→0]",
        "Coverage: INNETWORK  [missing hyphen]",
        "",
        "Expected: parser must handle all above variations.",
    ]
)


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"All 20 test documents created in: ./{OUTPUT_DIR}/")
print(f"{'='*60}\n")

groups = [
    ("GROUP A — Insurance Card OCR (Modules 1 & 2)", [
        "01 — Standard card (happy path)",
        "02 — Missing group & policy number",
        "03 — Expired coverage card",
        "04 — Medicaid / low-income plan",
        "05 — OCR noise / scan artifacts",
    ]),
    ("GROUP B — Medical Records & Referrals (Modules 3,5,7,8)", [
        "06 — Standard office visit with diagnoses",
        "07 — 6 comorbid ICD-10 codes",
        "08 — Annual exam — no ICD-10 codes",
        "09 — Pediatric patient (age 6)",
        "10 — Emergency / unknown patient",
        "11 — Freeform referral letter (tests spaCy NER)",
    ]),
    ("GROUP C — Billing / EOB (Module 6)", [
        "12 — Standard EOB claim",
        "13 — High deductible plan (HDHP)",
        "14 — Out-of-network penalty",
    ]),
    ("GROUP D — Authorization Requests (Module 8)", [
        "15 — Likely approved (TKA with full documentation)",
        "16 — Likely denied (cosmetic, no medical necessity)",
        "17 — Experimental procedure (CAR-T, clinical trial)",
    ]),
    ("GROUP E — Denial Risk & Edge Cases (Module 7)", [
        "18 — High denial risk (6 compounding red flags)",
        "19 — ICD-10 codes without decimal points",
        "20 — Full OCR stress test (noise + missing data)",
    ]),
]

for heading, items in groups:
    print(f"  {heading}")
    for item in items:
        print(f"    • {item}")
    print()
