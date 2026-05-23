import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from .database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class Submission(Base):
    __tablename__ = "submissions"

    id           = Column(String, primary_key=True, default=new_id)
    email        = Column(String, nullable=False, index=True)
    name         = Column(String, nullable=False)
    country      = Column(String, nullable=False)
    accounts     = Column(JSON, nullable=False)   # [{platform, handle}]
    reason       = Column(String, nullable=False)
    timeline     = Column(String, nullable=False)
    tier         = Column(String, default="free")          # free|standard|attorney|monitor
    # Lead status — update manually in Supabase dashboard
    # Values: new | scan_done | paid | refunded | churned | no_show
    lead_status  = Column(String, default="new", index=True)
    notes        = Column(Text, nullable=True)             # internal notes field
    created_at   = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id            = Column(String, primary_key=True, default=new_id)
    submission_id = Column(String, nullable=False, index=True)
    status        = Column(String, default="queued")   # queued|processing|done|failed
    report_json   = Column(JSON, nullable=True)
    pdf_path      = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FreeIPUsage(Base):
    __tablename__ = "free_ip_usage"

    id         = Column(String, primary_key=True, default=new_id)
    ip_address = Column(String, nullable=False, unique=True, index=True)
    used_at    = Column(DateTime, default=datetime.utcnow)


class PaidOrder(Base):
    __tablename__ = "paid_orders"

    id                = Column(String, primary_key=True, default=new_id)
    stripe_session_id = Column(String, unique=True, nullable=False, index=True)
    email             = Column(String, nullable=True, index=True)
    tier              = Column(String, nullable=False)   # standard|attorney|monitor
    paid              = Column(Boolean, default=False)
    created_at        = Column(DateTime, default=datetime.utcnow)
