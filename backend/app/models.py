"""
Two roles in this system:
- "Issuer" (Company A / the previous employer) registers an ORIGINAL record
  for an employee once. This is the source of truth.
- "Verifier" (Company B / the company hiring now) uploads whatever document
  the candidate gave them, and the system diffs it against the original.

original_records are hash-chained (like the previous project) so that even
the issuing company can't quietly edit a record after the fact.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

DATABASE_URL = "sqlite:///./docverify.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class OriginalRecord(Base):
    """The ground-truth document, as issued by the original employer."""
    __tablename__ = "original_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String, nullable=False, index=True)
    employer_name = Column(String, nullable=False)
    document_type = Column(String, nullable=False)   # e.g. "Experience Letter", "Offer Letter"
    original_text = Column(Text, nullable=False)
    filename = Column(String, nullable=False)

    record_hash = Column(String, nullable=False, unique=True)
    previous_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class VerificationCheck(Base):
    """A log of every verification attempt (audit trail)."""
    __tablename__ = "verification_checks"

    id = Column(Integer, primary_key=True, index=True)
    original_record_id = Column(Integer, nullable=False)
    submitted_filename = Column(String, nullable=False)
    submitted_text = Column(Text, nullable=False)

    match_percentage = Column(Float, nullable=False)
    verdict = Column(String, nullable=False)          # "MATCH", "DISCREPANCY_FOUND"
    differences = Column(Text, nullable=False)          # JSON string of diffs

    checked_by = Column(String, nullable=False)         # e.g. "Company B - HR"
    checked_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
