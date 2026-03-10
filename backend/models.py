"""
SQLAlchemy ORM Models — matches the PostgreSQL schema from the PDF spec exactly.
Tables: patients, insurance_cards, edi_transactions, benefits,
        financial_estimations, authorization_requests, denial_risk
"""
import uuid # type: ignore
from datetime import datetime # type: ignore
from sqlalchemy import ( # type: ignore
    Column, String, Numeric, Boolean, Integer, Text,
    ForeignKey, DateTime, func
)
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from database import Base # type: ignore


def _uuid():
    return str(uuid.uuid4())


# ── Table 1: patients ─────────────────────────────────────────────────────────
class Patient(Base):
    __tablename__ = "patients"

    id         = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name       = Column(String(200))
    dob        = Column(String(50))
    gender     = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    insurance_cards        = relationship("InsuranceCard",      back_populates="patient", cascade="all, delete-orphan")
    edi_transactions       = relationship("EdiTransaction",     back_populates="patient", cascade="all, delete-orphan")
    benefits               = relationship("Benefit",            back_populates="patient", cascade="all, delete-orphan")
    financial_estimations  = relationship("FinancialEstimation",back_populates="patient", cascade="all, delete-orphan")
    authorization_requests = relationship("AuthorizationRequest",back_populates="patient",cascade="all, delete-orphan")
    denial_risks           = relationship("DenialRisk",         back_populates="patient", cascade="all, delete-orphan")


# ── Table 2: insurance_cards ──────────────────────────────────────────────────
class InsuranceCard(Base):
    __tablename__ = "insurance_cards"

    id             = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    patient_id     = Column(UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False)
    member_id      = Column(String(100))
    group_number   = Column(String(100))
    policy_number  = Column(String(100))
    payer_name     = Column(String(200))
    valid_thru     = Column(String(50))
    raw_text       = Column(Text)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="insurance_cards")


# ── Table 3: edi_transactions ─────────────────────────────────────────────────
class EdiTransaction(Base):
    __tablename__ = "edi_transactions"

    id         = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    patient_id = Column(UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False)
    edi_270    = Column(Text)
    edi_271    = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="edi_transactions")


# ── Table 4: benefits ─────────────────────────────────────────────────────────
class Benefit(Base):
    __tablename__ = "benefits"

    id                    = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    patient_id            = Column(UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False)
    coverage_status       = Column(String(50))
    plan_type             = Column(String(100))
    copay                 = Column(Numeric(12, 2), default=0)
    deductible_total      = Column(Numeric(12, 2), default=0)
    deductible_remaining  = Column(Numeric(12, 2), default=0)
    coinsurance           = Column(Numeric(5, 2),  default=0)  # %
    out_of_pocket_max     = Column(Numeric(12, 2), default=0)
    in_network            = Column(Boolean, default=True)
    coverage_summary      = Column(Text)

    patient = relationship("Patient", back_populates="benefits")


# ── Table 5: financial_estimations ────────────────────────────────────────────
class FinancialEstimation(Base):
    __tablename__ = "financial_estimations"

    id                = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    patient_id        = Column(UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False)
    procedure_cost    = Column(Numeric(12, 2), default=0)
    patient_pay       = Column(Numeric(12, 2), default=0)
    insurance_pay     = Column(Numeric(12, 2), default=0)
    deductible_applied = Column(Numeric(12, 2), default=0)
    coinsurance_amount = Column(Numeric(12, 2), default=0)
    copay_applied     = Column(Numeric(12, 2), default=0)
    coverage_pct      = Column(Numeric(5, 2),  default=0)
    note              = Column(Text)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="financial_estimations")


# ── Table 6: authorization_requests ──────────────────────────────────────────
class AuthorizationRequest(Base):
    __tablename__ = "authorization_requests"

    id                    = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    patient_id            = Column(UUID(as_uuid=False), ForeignKey("patients.id"), nullable=True)
    cpt_code              = Column(String(20))
    diagnosis_codes       = Column(Text)            # JSON-encoded list
    medical_summary       = Column(Text)
    authorization_status  = Column(String(50))      # Approved / Denied / Manual Review
    confidence_score      = Column(Numeric(4, 3))   # 0.000 – 1.000
    reason                = Column(Text)
    source                = Column(String(50))      # LLM / Rule-Based
    created_at            = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="authorization_requests")


# ── Table 7: denial_risk ──────────────────────────────────────────────────────
class DenialRisk(Base):
    __tablename__ = "denial_risk"

    id             = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    patient_id     = Column(UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False)
    risk_score     = Column(Integer, default=0)    # 0–100
    risk_level     = Column(String(20))            # LOW / MEDIUM / HIGH
    summary        = Column(Text)
    rules_triggered = Column(Text)                 # JSON-encoded list

    patient = relationship("Patient", back_populates="denial_risks")
