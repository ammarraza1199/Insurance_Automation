# Insurance Verification & Authorization Automation Platform
## Complete Implementation Plan

This plan transforms the existing OCR+CPT billing prototype into the full **Insurance Verification & Authorization Automation Platform** as described in the PDF design document.

---

## What the PDF Requires (vs. What Exists)

| Feature | Current State | Required |
|---|---|---|
| Insurance card OCR (member_id, group#, policy#, payer) | ❌ Partial (only name/DOB/ICD-10) | ✅ Full card extraction |
| EDI 270 Generator | ❌ Missing | ✅ Required |
| EDI 271 Simulator (fake payer) | ❌ Missing | ✅ Required |
| Benefits Interpretation Engine | ❌ Missing | ✅ Required |
| Financial Estimation Engine | ❌ Missing | ✅ Required |
| Denial Risk Scoring Engine | ❌ Missing | ✅ Required |
| CPT Authorization Engine (AI) | ✅ Partial (description only) | ✅ Full auth + confidence score |
| PDF Report Generation | ❌ Missing | ✅ Required |
| PostgreSQL DB schema | ❌ MongoDB only | ✅ 6 tables required |
| Frontend: Card Upload screen | ❌ Missing | ✅ Required |
| Frontend: Eligibility screen | ❌ Missing | ✅ Required |
| Frontend: Results Dashboard | ❌ Missing | ✅ Required |
| Frontend: Authorization Check screen | ❌ Missing | ✅ Required |

> [!IMPORTANT]
> The PDF specifies **PostgreSQL** as the database, not MongoDB. However since the existing code uses MongoDB and the PDF is a prototype spec, we'll keep MongoDB AND add the new collections that mirror the SQL tables. This avoids breaking existing functionality while adding full new features.

---

## Proposed Changes

### Backend – New Services

#### [MODIFY] [main.py](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/backend/main.py)
- Add all 8 new API endpoints
- Import new service modules

#### [NEW] [insurance_card_service.py](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/backend/insurance_card_service.py)
- `extract_card_data(image_bytes)` – enhanced OCR for insurance cards
- Extracts: member_name, member_id, group_number, policy_number, payer_name, dob, valid_thru

#### [NEW] [edi_service.py](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/backend/edi_service.py)
- `generate_270(card_data)` – builds EDI 270 eligibility request string
- `simulate_271(card_data)` – simulates fake payer EDI 271 response

#### [NEW] [benefits_service.py](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/backend/benefits_service.py)
- `interpret_benefits(edi_271)` – parses EDI 271 into structured benefits JSON
  - coverage_status, copay, deductible_total, deductible_remaining, coinsurance, out_of_pocket_max

#### [NEW] [financial_service.py](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/backend/financial_service.py)
- `estimate_cost(procedure_cost, benefits)` – computes patient_pay and insurance_pay
- Formula: patient_pay = min(deductible_remaining, procedure_cost) + coinsurance% of remainder + copay

#### [NEW] [denial_risk_service.py](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/backend/denial_risk_service.py)
- `score_denial_risk(benefits, card_data)` – rule-based scoring engine
- Rules: inactive coverage (+50), expired policy (+40), out-of-network (+20), high deductible (+15)
- Returns: risk_score (0-100), risk_level (LOW/MEDIUM/HIGH), reasons list

#### [NEW] [authorization_service.py](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/backend/authorization_service.py)
- `check_authorization(cpt_code, diagnosis_codes, medical_summary)` – uses local Ollama LLM
- Returns: authorization_status (Approved/Denied/Manual Review), confidence_score (0-1), reason

#### [NEW] [report_service.py](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/backend/report_service.py)
- `generate_pdf_report(session_data)` – generates downloadable PDF report using `reportlab`
- Contains: patient details, insurance details, eligibility results, benefits breakdown, cost estimation, authorization decision, denial risk

#### [MODIFY] [requirements.txt](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/backend/requirements.txt)
- Add: `reportlab`, `python-dateutil`

---

### Backend – New API Endpoints (added to main.py)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload-card` | Upload insurance card image (form-data) |
| POST | `/extract-card-data` | Run OCR on card, return structured JSON |
| POST | `/generate-270` | Generate EDI 270 eligibility request |
| POST | `/simulate-271` | Simulate fake payer EDI 271 response |
| POST | `/benefits-analysis` | Parse EDI 271 into benefits JSON |
| POST | `/estimate-cost` | Calculate patient financial responsibility |
| POST | `/authorization/check` | AI-powered CPT auth decision |
| POST | `/generate-report` | Generate and return downloadable PDF |
| GET | `/denial-risk/{session_id}` | Get denial risk score for a session |

---

### Frontend – New Pages

#### [MODIFY] [App.jsx](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/frontend/src/App.jsx)
- Add routes for new pages
- Update sidebar navigation

#### [NEW] [InsuranceFlowPage.jsx](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/frontend/src/pages/InsuranceFlowPage.jsx)
- **Master workflow page** with step-by-step animated progress through all 6 stages:
  1. Upload Card (drag & drop front/back)
  2. OCR Extraction → show extracted fields
  3. EDI Request → animated "Checking Insurance Eligibility"
  4. Benefits Analysis → coverage status display
  5. Financial Estimation → patient pay breakdown
  6. Denial Risk + Authorization → risk score + auth decision

#### [NEW] [AuthorizationPage.jsx](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/frontend/src/pages/AuthorizationPage.jsx)
- Doctor inputs: CPT Code, Diagnosis Codes, Medical Summary
- Shows: Authorization Approved/Denied/Manual Review badge + Confidence Score + Reason

#### [NEW] [ResultsDashboardPage.jsx](file:///c:/Users/DELL/Downloads/ZeroKost/Insurance%20AUtomation%20OCR/ocr_with_CPT_openAI/frontend/src/pages/ResultsDashboardPage.jsx)
- Shows full results: Coverage Status, Benefits Summary, Estimated Patient Pay, Authorization Status, Denial Risk Score
- Download Report button (calls `/generate-report`)

---

## Verification Plan

### Manual End-to-End Test
1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open `http://localhost:5173`

**Test Workflow:**
1. Navigate to "Insurance Verification" page
2. Upload any image (front of insurance card)
3. Click "Extract Data" → verify member_name, member_id, group_number appear
4. Click "Check Eligibility" → verify EDI 270 is generated and 271 simulation returns coverage data
5. Verify Benefits panel shows copay, deductible, coinsurance values
6. Enter a procedure cost → verify patient_pay and insurance_pay calculations
7. Navigate to Authorization page → enter CPT code `71250`, diagnosis `R05`, medical summary
8. Verify AI response shows Approved/Denied/Manual Review with confidence score
9. Navigate to Results Dashboard → verify all data is present
10. Click "Download Report" → verify PDF downloads with all sections

### API Smoke Tests (via browser or curl)
```bash
# Test card extraction
curl -X POST http://localhost:8000/extract-card-data -F "file=@test.jpg"

# Test EDI 270
curl -X POST http://localhost:8000/generate-270 -H "Content-Type: application/json" -d '{"member_name":"John Doe","member_id":"MEM123","dob":"1990-01-01"}'

# Test authorization
curl -X POST http://localhost:8000/authorization/check -H "Content-Type: application/json" -d '{"cpt_code":"71250","diagnosis_codes":["R05"],"medical_summary":"Persistent cough and abnormal chest x-ray"}'
```
