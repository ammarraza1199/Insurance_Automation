from fastapi import FastAPI, UploadFile, File, Form, HTTPException # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import Response # type: ignore
from pydantic import BaseModel # type: ignore
from typing import Optional, List
import uuid, json

from database import init_db, close_db, get_db_session # type: ignore
from models import ( # type: ignore
    Patient, InsuranceCard, EdiTransaction, Benefit,
    FinancialEstimation, AuthorizationRequest, DenialRisk
)
from ocr_service import extract_info_from_image # type: ignore
from llm_service import get_cpt_details # type: ignore
from insurance_card_service import extract_card_data # type: ignore
from edi_service import generate_270, simulate_271 # type: ignore
from benefits_service import interpret_benefits # type: ignore
from financial_service import estimate_cost # type: ignore
from denial_risk_service import score_denial_risk # type: ignore
from authorization_service import check_authorization # type: ignore
from report_service import generate_pdf_report # type: ignore

app = FastAPI(title="Insurance Verification & Authorization Automation Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Lifespan ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db()

# ─── Health ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "Insurance Verification & Authorization Platform — Running (PostgreSQL)"}


# ══════════════════════════════════════════════════════════════════════════════
# LEGACY ENDPOINTS  (preserved for backward-compatibility)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Legacy OCR endpoint."""
    content = await file.read()
    try:
        data = extract_info_from_image(content)
        return {"message": "Extracted successfully", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cpt-description")
async def get_cpt_info(cpt_code: str):
    """Legacy CPT description endpoint."""
    try:
        description = get_cpt_details(cpt_code)
        return {"cpt_code": cpt_code, "description": description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Platform stats from PostgreSQL."""
    from sqlalchemy import select, func as sqlfunc # type: ignore
    async with get_db_session() as db:
        total_patients = (await db.execute(select(sqlfunc.count()).select_from(Patient))).scalar()
        active_benefits = (await db.execute(
            select(sqlfunc.count()).select_from(Benefit).where(Benefit.coverage_status == "Active")
        )).scalar()
        approved_auth = (await db.execute(
            select(sqlfunc.count()).select_from(AuthorizationRequest)
            .where(AuthorizationRequest.authorization_status == "Approved")
        )).scalar()
        total_auth = (await db.execute(select(sqlfunc.count()).select_from(AuthorizationRequest))).scalar()
        high_risk = (await db.execute(
            select(sqlfunc.count()).select_from(DenialRisk).where(DenialRisk.risk_level == "HIGH")
        )).scalar()

    return {
        "total_patients":   total_patients,
        "active_coverage":  active_benefits,
        "auth_approved":    approved_auth,
        "auth_total":       total_auth,
        "high_denial_risk": high_risk,
        "approval_rate":    round(approved_auth / total_auth * 100, 1) if total_auth else 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 1 & 2 — Insurance Card Upload + OCR
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/upload-card")
async def upload_card(file: UploadFile = File(...)):
    """
    Upload insurance card image.
    Creates a patient record in PostgreSQL.
    Returns session_id (= patient_id UUID).
    """
    content = await file.read()
    async with get_db_session() as db:
        patient = Patient(name="Unknown", dob="Unknown", gender="Unknown")
        db.add(patient)
        await db.flush()   # get patient.id before commit
        patient_id = patient.id
        await db.commit()

    # Store image bytes temporarily in memory (session cache)
    _card_image_cache[patient_id] = content
    return {
        "session_id": patient_id,
        "message":    "Card uploaded. Call /extract-card-data next.",
    }


# In-memory image cache (cleared after OCR)
_card_image_cache: dict = {}


@app.post("/extract-card-data")
async def extract_card_data_endpoint(session_id: str = Form(...)):
    """
    Run OCR on uploaded card image.
    Saves InsuranceCard row + updates Patient.name/dob in PostgreSQL.
    """
    image_bytes = _card_image_cache.pop(session_id, None)
    if image_bytes is None:
        raise HTTPException(status_code=400, detail="No card image for this session. Upload first.")

    try:
        card_data = extract_card_data(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    async with get_db_session() as db:
        # Update patient with real name/dob from OCR
        patient = await db.get(Patient, session_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient record not found.")
        patient.name = card_data.get("member_name", "Unknown")
        patient.dob  = card_data.get("dob", "Unknown")

        # Save insurance card row
        card_row = InsuranceCard(
            patient_id    = session_id,
            member_id     = card_data.get("member_id"),
            group_number  = card_data.get("group_number"),
            policy_number = card_data.get("policy_number"),
            payer_name    = card_data.get("payer_name"),
            valid_thru    = card_data.get("valid_thru"),
            raw_text      = card_data.get("raw_text"),
        )
        db.add(card_row)
        await db.commit()

    return {"session_id": session_id, "card_data": card_data}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — EDI 270 Generator
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/generate-270")
async def generate_270_endpoint(session_id: str = Form(...)):
    """Generate EDI 270 from card data. Stores in edi_transactions."""
    async with get_db_session() as db:
        patient = await db.get(Patient, session_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Session not found.")

        # Get latest InsuranceCard for this patient
        from sqlalchemy import select # type: ignore
        result = await db.execute(
            select(InsuranceCard)
            .where(InsuranceCard.patient_id == session_id)
            .order_by(InsuranceCard.created_at.desc())
        )
        card_row = result.scalars().first()
        card_data = {}
        if card_row:
            card_data = {
                "member_name":  patient.name,
                "member_id":    card_row.member_id,
                "group_number": card_row.group_number,
                "payer_name":   card_row.payer_name,
                "dob":          patient.dob,
            }

    edi_270 = generate_270(card_data)

    async with get_db_session() as db:
        # Upsert EDI transaction
        from sqlalchemy import select # type: ignore
        result = await db.execute(
            select(EdiTransaction).where(EdiTransaction.patient_id == session_id)
        )
        edi_row = result.scalars().first()
        if edi_row:
            edi_row.edi_270 = edi_270
        else:
            edi_row = EdiTransaction(patient_id=session_id, edi_270=edi_270)
            db.add(edi_row)
        await db.commit()

    return {"session_id": session_id, "edi_270": edi_270}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4 — EDI 271 Simulator
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/simulate-271")
async def simulate_271_endpoint(session_id: str = Form(...)):
    """Simulate payer EDI 271 response. Updates edi_transactions row."""
    async with get_db_session() as db:
        from sqlalchemy import select # type: ignore
        result = await db.execute(
            select(InsuranceCard).where(InsuranceCard.patient_id == session_id)
            .order_by(InsuranceCard.created_at.desc())
        )
        card_row = result.scalars().first()
        patient = await db.get(Patient, session_id)

    card_data = {}
    if card_row and patient:
        card_data = {
            "member_name": patient.name,
            "member_id":   card_row.member_id,
            "payer_name":  card_row.payer_name,
            "valid_thru":  card_row.valid_thru,
        }

    edi_response = simulate_271(card_data)

    async with get_db_session() as db:
        from sqlalchemy import select # type: ignore
        result = await db.execute(
            select(EdiTransaction).where(EdiTransaction.patient_id == session_id)
        )
        edi_row = result.scalars().first()
        if edi_row:
            edi_row.edi_271 = json.dumps(edi_response)
        else:
            edi_row = EdiTransaction(
                patient_id=session_id,
                edi_271=json.dumps(edi_response)
            )
            db.add(edi_row)
        await db.commit()

    return {"session_id": session_id, "edi_response": edi_response}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 5 — Benefits Interpretation Engine
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/benefits-analysis")
async def benefits_analysis(session_id: str = Form(...)):
    """Parse EDI 271 into structured benefits. Writes to benefits table."""
    async with get_db_session() as db:
        from sqlalchemy import select # type: ignore
        result = await db.execute(
            select(EdiTransaction).where(EdiTransaction.patient_id == session_id)
        )
        edi_row = result.scalars().first()

    if not edi_row or not edi_row.edi_271:
        raise HTTPException(status_code=400, detail="EDI 271 not found. Run /simulate-271 first.")

    edi_response = json.loads(edi_row.edi_271)
    benefits_data = interpret_benefits(edi_response)

    async with get_db_session() as db:
        b = Benefit(
            patient_id            = session_id,
            coverage_status       = benefits_data.get("coverage_status"),
            plan_type             = benefits_data.get("plan_type"),
            copay                 = benefits_data.get("copay", 0),
            deductible_total      = benefits_data.get("deductible_total", 0),
            deductible_remaining  = benefits_data.get("deductible_remaining", 0),
            coinsurance           = benefits_data.get("coinsurance", 0),
            out_of_pocket_max     = benefits_data.get("out_of_pocket_max", 0),
            in_network            = benefits_data.get("in_network", True),
            coverage_summary      = benefits_data.get("coverage_summary"),
        )
        db.add(b)
        await db.commit()

    return {"session_id": session_id, "benefits": benefits_data}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 6 — Financial Estimation Engine
# ══════════════════════════════════════════════════════════════════════════════

class CostEstimateRequest(BaseModel):
    session_id: str
    procedure_cost: float

@app.post("/estimate-cost")
async def estimate_cost_endpoint(req: CostEstimateRequest):
    """Calculate patient vs. insurance costs. Writes to financial_estimations."""
    async with get_db_session() as db:
        from sqlalchemy import select # type: ignore
        result = await db.execute(
            select(Benefit).where(Benefit.patient_id == req.session_id)
            .order_by(Benefit.id.desc())
        )
        benefit_row = result.scalars().first()

    if not benefit_row:
        raise HTTPException(status_code=400, detail="Benefits not found. Run /benefits-analysis first.")

    benefits_dict = {
        "coverage_status":      benefit_row.coverage_status,
        "copay":                float(benefit_row.copay or 0),
        "deductible_remaining": float(benefit_row.deductible_remaining or 0),
        "coinsurance":          float(benefit_row.coinsurance or 0),
        "out_of_pocket_max":    float(benefit_row.out_of_pocket_max or 0),
        "in_network":           benefit_row.in_network,
    }
    estimation = estimate_cost(req.procedure_cost, benefits_dict)

    async with get_db_session() as db:
        fe = FinancialEstimation(
            patient_id         = req.session_id,
            procedure_cost     = req.procedure_cost,
            patient_pay        = estimation.get("patient_pay", 0),
            insurance_pay      = estimation.get("insurance_pay", 0),
            deductible_applied = estimation.get("deductible_applied", 0),
            coinsurance_amount = estimation.get("coinsurance_amount", 0),
            copay_applied      = estimation.get("copay_applied", 0),
            coverage_pct       = estimation.get("coverage_pct", 0),
            note               = estimation.get("note"),
        )
        db.add(fe)
        await db.commit()

    return {"session_id": req.session_id, "financial_estimation": estimation}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 7 — Denial Risk Scoring Engine
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/denial-risk/{session_id}")
async def denial_risk_endpoint(session_id: str):
    """Compute denial risk score. Writes to denial_risk table."""
    async with get_db_session() as db:
        from sqlalchemy import select # type: ignore
        # Get benefits
        br = (await db.execute(
            select(Benefit).where(Benefit.patient_id == session_id).order_by(Benefit.id.desc())
        )).scalars().first()
        # Get insurance card
        cr = (await db.execute(
            select(InsuranceCard).where(InsuranceCard.patient_id == session_id)
            .order_by(InsuranceCard.created_at.desc())
        )).scalars().first()

    benefits_dict = {}
    if br:
        benefits_dict = {
            "coverage_status":     br.coverage_status,
            "in_network":          br.in_network,
            "deductible_remaining":float(br.deductible_remaining or 0),
        }
    card_dict = {}
    if cr:
        card_dict = {
            "member_id": cr.member_id,
            "valid_thru": cr.valid_thru,
        }

    risk = score_denial_risk(benefits_dict, card_dict)

    async with get_db_session() as db:
        dr = DenialRisk(
            patient_id      = session_id,
            risk_score      = risk.get("risk_score", 0),
            risk_level      = risk.get("risk_level"),
            summary         = risk.get("summary"),
            rules_triggered = json.dumps(risk.get("rules_triggered", [])),
        )
        db.add(dr)
        await db.commit()

    return {"session_id": session_id, "denial_risk": risk}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 8 — CPT Authorization Engine (AI)
# ══════════════════════════════════════════════════════════════════════════════

class AuthorizationRequestBody(BaseModel):
    cpt_code: str
    diagnosis_codes: List[str] = []
    medical_summary: str = ""
    session_id: Optional[str] = None

@app.post("/authorization/check")
async def authorization_check(req: AuthorizationRequestBody):
    """AI-powered CPT authorization via Ollama. Writes to authorization_requests."""
    try:
        result = check_authorization(req.cpt_code, req.diagnosis_codes, req.medical_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    async with get_db_session() as db:
        ar = AuthorizationRequest(
            patient_id           = req.session_id,
            cpt_code             = result.get("cpt_code", req.cpt_code),
            diagnosis_codes      = json.dumps(req.diagnosis_codes),
            medical_summary      = req.medical_summary,
            authorization_status = result.get("authorization_status"),
            confidence_score     = result.get("confidence_score", 0),
            reason               = result.get("reason"),
            source               = result.get("source", "AI"),
        )
        db.add(ar)
        await db.commit()

    return result


# ══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/generate-report")
async def generate_report(session_id: str = Form(...)):
    """Generate downloadable PDF report by assembling all tables for this patient."""
    async with get_db_session() as db:
        from sqlalchemy import select # type: ignore

        patient = await db.get(Patient, session_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found.")

        card_row = (await db.execute(
            select(InsuranceCard).where(InsuranceCard.patient_id == session_id)
            .order_by(InsuranceCard.created_at.desc())
        )).scalars().first()

        benefit_row = (await db.execute(
            select(Benefit).where(Benefit.patient_id == session_id).order_by(Benefit.id.desc())
        )).scalars().first()

        finance_row = (await db.execute(
            select(FinancialEstimation).where(FinancialEstimation.patient_id == session_id)
            .order_by(FinancialEstimation.created_at.desc())
        )).scalars().first()

        auth_row = (await db.execute(
            select(AuthorizationRequest).where(AuthorizationRequest.patient_id == session_id)
            .order_by(AuthorizationRequest.created_at.desc())
        )).scalars().first()

        risk_row = (await db.execute(
            select(DenialRisk).where(DenialRisk.patient_id == session_id)
            .order_by(DenialRisk.id.desc())
        )).scalars().first()

    # Auto-compute denial risk if missing
    if not risk_row:
        b = benefit_row
        c = card_row
        risk_data = score_denial_risk(
            {"coverage_status": b.coverage_status, "in_network": b.in_network,
             "deductible_remaining": float(b.deductible_remaining or 0)} if b else {},
            {"member_id": c.member_id, "valid_thru": c.valid_thru} if c else {}
        )
    else:
        risk_data = {
            "risk_score":      risk_row.risk_score,
            "risk_level":      risk_row.risk_level,
            "summary":         risk_row.summary,
            "rules_triggered": json.loads(risk_row.rules_triggered or "[]"),
        }

    # Build session dict for report_service (same shape as before)
    session_data = {
        "card_data": {
            "member_name":  patient.name,
            "dob":          patient.dob,
            "member_id":    card_row.member_id    if card_row else "",
            "group_number": card_row.group_number if card_row else "",
            "policy_number":card_row.policy_number if card_row else "",
            "payer_name":   card_row.payer_name   if card_row else "",
            "valid_thru":   card_row.valid_thru   if card_row else "",
        } if card_row else {},
        "benefits": {
            "coverage_status":      benefit_row.coverage_status,
            "plan_type":            benefit_row.plan_type,
            "in_network":           benefit_row.in_network,
            "copay":                float(benefit_row.copay or 0),
            "deductible_total":     float(benefit_row.deductible_total or 0),
            "deductible_remaining": float(benefit_row.deductible_remaining or 0),
            "coinsurance":          float(benefit_row.coinsurance or 0),
            "out_of_pocket_max":    float(benefit_row.out_of_pocket_max or 0),
        } if benefit_row else {},
        "financial_estimation": {
            "procedure_cost":    float(finance_row.procedure_cost or 0),
            "patient_pay":       float(finance_row.patient_pay or 0),
            "insurance_pay":     float(finance_row.insurance_pay or 0),
            "deductible_applied":float(finance_row.deductible_applied or 0),
            "coinsurance_amount":float(finance_row.coinsurance_amount or 0),
            "copay_applied":     float(finance_row.copay_applied or 0),
            "coverage_pct":      float(finance_row.coverage_pct or 0),
            "note":              finance_row.note,
        } if finance_row else {},
        "authorization": {
            "cpt_code":             auth_row.cpt_code,
            "authorization_status": auth_row.authorization_status,
            "confidence_score":     float(auth_row.confidence_score or 0),
            "reason":               auth_row.reason,
            "source":               auth_row.source,
        } if auth_row else {},
        "denial_risk": risk_data,
    }

    pdf_bytes = generate_pdf_report(session_data)
    # Get the first 8 characters from session_id
    short_id = session_id[0:8] if session_id else "unknown" # type: ignore
    headers = {
        "Content-Disposition": f'attachment; filename="insurance_report_{short_id}.pdf"'
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


# ══════════════════════════════════════════════════════════════════════════════
# SESSIONS / PATIENT LISTING
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/sessions")
async def get_all_sessions():
    """List all patients with their latest benefits & authorization status."""
    from sqlalchemy import select, outerjoin # type: ignore
    async with get_db_session() as db:
        patients = (await db.execute(select(Patient).order_by(Patient.created_at.desc()))).scalars().all()
        result = []
        for p in patients:
            br = (await db.execute(
                select(Benefit).where(Benefit.patient_id == p.id).order_by(Benefit.id.desc())
            )).scalars().first()
            ar = (await db.execute(
                select(AuthorizationRequest).where(AuthorizationRequest.patient_id == p.id)
                .order_by(AuthorizationRequest.created_at.desc())
            )).scalars().first()
            dr = (await db.execute(
                select(DenialRisk).where(DenialRisk.patient_id == p.id).order_by(DenialRisk.id.desc())
            )).scalars().first()
            cr = (await db.execute(
                select(InsuranceCard).where(InsuranceCard.patient_id == p.id)
                .order_by(InsuranceCard.created_at.desc())
            )).scalars().first()

            result.append({
                "_id": p.id,
                "card_data": {
                    "member_name": p.name,
                    "member_id":   cr.member_id   if cr else None,
                    "payer_name":  cr.payer_name  if cr else None,
                    "valid_thru":  cr.valid_thru  if cr else None,
                },
                "benefits": {
                    "coverage_status": br.coverage_status if br else None,
                    "copay":           float(br.copay or 0) if br else None,
                    "deductible_remaining": float(br.deductible_remaining or 0) if br else None,
                    "coinsurance":     float(br.coinsurance or 0) if br else None,
                    "out_of_pocket_max": float(br.out_of_pocket_max or 0) if br else None,
                    "in_network":      br.in_network if br else None,
                    "plan_type":       br.plan_type if br else None,
                } if br else None,
                "authorization": {
                    "authorization_status": ar.authorization_status,
                    "confidence_score":     float(ar.confidence_score or 0),
                    "reason":               ar.reason,
                } if ar else None,
                "denial_risk": {
                    "risk_score": dr.risk_score,
                    "risk_level": dr.risk_level,
                    "summary":    dr.summary,
                    "rules_triggered": json.loads(dr.rules_triggered or "[]"),
                } if dr else None,
            })
    return result


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full patient record by session_id."""
    result_list = await get_all_sessions()
    for item in result_list:
        if item["_id"] == session_id:
            return item
    raise HTTPException(status_code=404, detail="Session not found.")


# ══════════════════════════════════════════════════════════════════════════════
# CPT LOGS — Authorization request history
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/cpt-logs")
async def get_cpt_logs(session_id: Optional[str] = None, limit: int = 50):
    """
    Return CPT authorization request history.
    Optionally filter by session_id (patient).
    """
    from sqlalchemy import select  # type: ignore
    async with get_db_session() as db:
        q = select(AuthorizationRequest).order_by(AuthorizationRequest.created_at.desc())
        if session_id:
            q = q.where(AuthorizationRequest.patient_id == session_id)
        q = q.limit(limit)
        rows = (await db.execute(q)).scalars().all()

    return [
        {
            "id":                   str(row.id),
            "session_id":           row.patient_id,
            "cpt_code":             row.cpt_code,
            "diagnosis_codes":      json.loads(row.diagnosis_codes or "[]"),
            "medical_summary":      row.medical_summary,
            "authorization_status": row.authorization_status,
            "confidence_score":     float(row.confidence_score or 0),
            "reason":               row.reason,
            "source":               row.source,
            "created_at":           row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


# ══════════════════════════════════════════════════════════════════════════════
# BACKFILL — Compute missing risk & authorization for existing patients
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/backfill-risk-auth")
async def backfill_risk_auth():
    """
    Iterate all patients that are missing DenialRisk or AuthorizationRequest
    records, and compute them using rule-based logic.
    Safe to call multiple times (skips already-computed records).
    Returns a summary of how many records were backfilled.
    """
    from sqlalchemy import select  # type: ignore

    filled_risk = 0
    filled_auth = 0

    async with get_db_session() as db:
        patients = (await db.execute(select(Patient))).scalars().all()

    for p in patients:
        async with get_db_session() as db:
            # Check existing risk record
            existing_risk = (await db.execute(
                select(DenialRisk).where(DenialRisk.patient_id == p.id)
            )).scalars().first()

            existing_auth = (await db.execute(
                select(AuthorizationRequest).where(AuthorizationRequest.patient_id == p.id)
            )).scalars().first()

            # Get related benefit + card data
            br = (await db.execute(
                select(Benefit).where(Benefit.patient_id == p.id).order_by(Benefit.id.desc())
            )).scalars().first()

            cr = (await db.execute(
                select(InsuranceCard).where(InsuranceCard.patient_id == p.id)
                .order_by(InsuranceCard.created_at.desc())
            )).scalars().first()

        # ── Backfill Denial Risk ──────────────────────────────────────────────
        if not existing_risk:
            benefits_dict = {}
            card_dict = {}
            if br:
                benefits_dict = {
                    "coverage_status":      br.coverage_status,
                    "in_network":           br.in_network,
                    "deductible_remaining": float(br.deductible_remaining or 0),
                }
            if cr:
                card_dict = {
                    "member_id":  cr.member_id,
                    "valid_thru": cr.valid_thru,
                }

            risk = score_denial_risk(benefits_dict, card_dict)
            async with get_db_session() as db:
                dr = DenialRisk(
                    patient_id      = p.id,
                    risk_score      = risk.get("risk_score", 0),
                    risk_level      = risk.get("risk_level", "UNKNOWN"),
                    summary         = risk.get("summary", ""),
                    rules_triggered = json.dumps(risk.get("rules_triggered", [])),
                )
                db.add(dr)
                await db.commit()
            filled_risk += 1

        # ── Backfill Authorization (rule-based, not LLM) ──────────────────────
        if not existing_auth:
            # Use a minimal rule-based check — avoids slow LLM calls during backfill
            coverage = br.coverage_status if br else "Unknown"
            if coverage == "Active":
                auth_status = "Approved"
                confidence  = 0.65
                reason      = "Coverage is active; auto-approved via backfill rule."
            elif coverage == "Inactive":
                auth_status = "Denied"
                confidence  = 0.70
                reason      = "Coverage is inactive; auto-denied via backfill rule."
            else:
                auth_status = "Manual Review"
                confidence  = 0.50
                reason      = "Coverage status unknown; manual review required."

            async with get_db_session() as db:
                ar = AuthorizationRequest(
                    patient_id           = p.id,
                    cpt_code             = "N/A",
                    diagnosis_codes      = "[]",
                    medical_summary      = "Backfilled automatically.",
                    authorization_status = auth_status,
                    confidence_score     = confidence,
                    reason               = reason,
                    source               = "Rule-based backfill",
                )
                db.add(ar)
                await db.commit()
            filled_auth += 1

    return {
        "message":      "Backfill complete.",
        "risk_filled":  filled_risk,
        "auth_filled":  filled_auth,
    }


