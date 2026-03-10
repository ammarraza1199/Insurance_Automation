# Insurance Verification & Authorization Platform – Task Checklist

## Phase 1: Backend – Core Infrastructure
- [ ] Restructure backend: create dedicated service files for each module
- [ ] Switch database from MongoDB to PostgreSQL (as per PDF spec)
- [ ] Create all DB tables: patients, insurance_cards, edi_transactions, benefits, financial_estimations, authorization_requests, denial_risk
- [ ] Set up SQLAlchemy ORM models and Alembic migrations
- [ ] Update requirements.txt with all new dependencies

## Phase 2: Backend – Module 1 & 2: Insurance Card Upload + OCR
- [ ] POST /upload-card – accept insurance card front/back images
- [ ] POST /extract-card-data – run OCR on uploaded card
- [ ] Enhance OCR to extract: member_name, member_id, group_number, policy_number, dob, payer_name, valid_thru
- [ ] Return structured JSON from OCR extraction

## Phase 3: Backend – Module 3 & 4: EDI 270/271
- [ ] POST /generate-270 – build EDI 270 eligibility request from extracted card data
- [ ] POST /simulate-271 – simulate payer EDI 271 response with coverage details (copay, deductible, coinsurance, out_of_pocket_max)

## Phase 4: Backend – Module 5: Benefits Interpretation Engine
- [ ] POST /benefits-analysis – parse EDI 271 segments into structured benefits JSON
- [ ] Store benefits in PostgreSQL

## Phase 5: Backend – Module 6: Financial Estimation Engine
- [ ] POST /estimate-cost – calculate patient pay = deductible_remaining + coinsurance% + copay
- [ ] Return patient_pay and insurance_pay estimates

## Phase 6: Backend – Module 7: Denial Risk Scoring Engine
- [ ] POST /denial-risk – rule-based scoring (inactive coverage +50, expired +40, out-of-network +20, high deductible +15)
- [ ] Return risk_score and risk_level (LOW/MEDIUM/HIGH)

## Phase 7: Backend – Module 8: CPT Authorization Engine (AI)
- [ ] POST /authorization/check – accept cpt_code, diagnosis_codes, medical_summary
- [ ] Use local LLM (Ollama) to reason medical necessity
- [ ] Return authorization_status (Approved/Denied/Manual Review), confidence_score, reason

## Phase 8: Backend – Report Generation
- [ ] POST /generate-report – compile full PDF report with all data
- [ ] Include: patient details, insurance details, eligibility, benefits, cost estimation, authorization decision, denial risk

## Phase 9: Frontend – Redesign to Match Insurance Verification Platform
- [ ] Page 1: Upload Insurance Card (drag-and-drop, front/back)
- [ ] Page 2: Extracted Data View (patient name, member ID, provider, policy)
- [ ] Page 3: Eligibility Verification Screen (animated progress steps)
- [ ] Page 4: Authorization Check Screen (CPT code, diagnosis, medical summary input)
- [ ] Page 5: Results Dashboard (coverage status, benefits summary, patient pay, authorization status, denial risk)
- [ ] Page 6: Download Report (PDF download button)
- [ ] Keep existing Overview Dashboard with updated KPIs
- [ ] Keep existing Patient Database / Records page

## Phase 10: Verification
- [ ] Test all API endpoints end-to-end
- [ ] Test full workflow from card upload to report generation
- [ ] Verify frontend pages render and connect to backend correctly
