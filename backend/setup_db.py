"""
One-time PostgreSQL database setup script.
Uses psycopg2 directly — does NOT require the psql CLI to be installed.

Run this AFTER starting PostgreSQL to:
  1. Create the 'insurance_platform' database (if it doesn't exist)
  2. Create all 7 tables

Usage:
    python setup_db.py

NOTE: If you started PostgreSQL via Docker with:
    -e POSTGRES_DB=insurance_platform
  then the database already exists and you can skip this script.
  The FastAPI app creates all tables automatically on startup.
"""
import os # type: ignore
import psycopg2 # type: ignore
from psycopg2 import sql # type: ignore
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT # type: ignore

PG_USER     = os.environ.get("PGUSER",     "postgres")
PG_PASSWORD = os.environ.get("PGPASSWORD", "postgres")
PG_HOST     = os.environ.get("PGHOST",     "localhost")
PG_PORT     = int(os.environ.get("PGPORT", "5432"))
DB_NAME     = "insurance_platform"


CREATE_TABLES_SQL = """
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS patients (
    id         VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name       VARCHAR(200),
    dob        VARCHAR(50),
    gender     VARCHAR(20),
    created_at TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS insurance_cards (
    id             VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::text,
    patient_id     VARCHAR(36)  NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    member_id      VARCHAR(100),
    group_number   VARCHAR(100),
    policy_number  VARCHAR(100),
    payer_name     VARCHAR(200),
    valid_thru     VARCHAR(50),
    raw_text       TEXT,
    created_at     TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS edi_transactions (
    id         VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    patient_id VARCHAR(36) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    edi_270    TEXT,
    edi_271    TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS benefits (
    id                    VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    patient_id            VARCHAR(36) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    coverage_status       VARCHAR(50),
    plan_type             VARCHAR(100),
    copay                 NUMERIC(12,2) DEFAULT 0,
    deductible_total      NUMERIC(12,2) DEFAULT 0,
    deductible_remaining  NUMERIC(12,2) DEFAULT 0,
    coinsurance           NUMERIC(5,2)  DEFAULT 0,
    out_of_pocket_max     NUMERIC(12,2) DEFAULT 0,
    in_network            BOOLEAN       DEFAULT TRUE,
    coverage_summary      TEXT
);

CREATE TABLE IF NOT EXISTS financial_estimations (
    id                 VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    patient_id         VARCHAR(36) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    procedure_cost     NUMERIC(12,2) DEFAULT 0,
    patient_pay        NUMERIC(12,2) DEFAULT 0,
    insurance_pay      NUMERIC(12,2) DEFAULT 0,
    deductible_applied NUMERIC(12,2) DEFAULT 0,
    coinsurance_amount NUMERIC(12,2) DEFAULT 0,
    copay_applied      NUMERIC(12,2) DEFAULT 0,
    coverage_pct       NUMERIC(5,2)  DEFAULT 0,
    note               TEXT,
    created_at         TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS authorization_requests (
    id                    VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    patient_id            VARCHAR(36) REFERENCES patients(id) ON DELETE SET NULL,
    cpt_code              VARCHAR(20),
    diagnosis_codes       TEXT,
    medical_summary       TEXT,
    authorization_status  VARCHAR(50),
    confidence_score      NUMERIC(4,3) DEFAULT 0,
    reason                TEXT,
    source                VARCHAR(50),
    created_at            TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS denial_risk (
    id              VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    patient_id      VARCHAR(36) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    risk_score      INTEGER     DEFAULT 0,
    risk_level      VARCHAR(20),
    summary         TEXT,
    rules_triggered TEXT
);
"""


def create_database():
    """Create the insurance_platform database if it doesn't exist."""
    print(f"🔌 Connecting to PostgreSQL at {PG_HOST}:{PG_PORT} as {PG_USER}...")
    try:
        # Connect to default 'postgres' db to create our database
        conn = psycopg2.connect(
            user=PG_USER, password=PG_PASSWORD,
            host=PG_HOST, port=PG_PORT, dbname="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if database already exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        if cur.fetchone():
            print(f"✅ Database '{DB_NAME}' already exists — skipping creation.")
        else:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
            print(f"✅ Database '{DB_NAME}' created.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to connect/create database: {e}")
        raise


def create_tables():
    """Create all 7 tables inside insurance_platform."""
    print(f"\n📋 Creating tables in '{DB_NAME}'...")
    try:
        conn = psycopg2.connect(
            user=PG_USER, password=PG_PASSWORD,
            host=PG_HOST, port=PG_PORT, dbname=DB_NAME
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Run each statement separately
        for stmt in CREATE_TABLES_SQL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    cur.execute(stmt)
                    print(f"  ✅ OK")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"  ⚠️  Already exists — skipped")
                    else:
                        print(f"  ❌ Error: {e}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        raise


if __name__ == "__main__":
    create_database()
    create_tables()
    print("\n🎉 Database setup complete! Tables created:")
    print("   patients, insurance_cards, edi_transactions, benefits,")
    print("   financial_estimations, authorization_requests, denial_risk")
    print(f"\nConnection string: postgresql+asyncpg://postgres:postgres@localhost:5432/{DB_NAME}")
