"""
Run with: uvicorn app.main:app --reload   (from the backend/ folder)
"""

import json
import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.models import init_db, SessionLocal, OriginalRecord, VerificationCheck
from app.extract import extract_text
from app.diff_engine import compare_documents
from app import hashchain

app = FastAPI(title="Document Verification System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Company A side: register an original record ----------

@app.post("/records/register")
def register_original_record(
    employee_name: str = Form(...),
    employer_name: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    raw = file.file.read()
    try:
        text = extract_text(file.filename, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from this file.")

    previous_hash = hashchain.get_latest_hash(db, OriginalRecord)
    timestamp = datetime.datetime.utcnow()

    content = {
        "employee_name": employee_name,
        "employer_name": employer_name,
        "document_type": document_type,
        "original_text": text,
        "filename": file.filename,
    }
    record_hash = hashchain.compute_record_hash(content, previous_hash, timestamp.isoformat())

    record = OriginalRecord(
        employee_name=employee_name,
        employer_name=employer_name,
        document_type=document_type,
        original_text=text,
        filename=file.filename,
        record_hash=record_hash,
        previous_hash=previous_hash,
        created_at=timestamp,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "record_id": record.id,
        "employee_name": employee_name,
        "employer_name": employer_name,
        "document_type": document_type,
        "record_hash": record_hash,
        "message": "Original record registered and locked into the hash chain.",
    }


@app.get("/records/search")
def search_records(employee_name: str, db: Session = Depends(get_db)):
    """Company B searches for a candidate's original records by name."""
    records = (
        db.query(OriginalRecord)
        .filter(OriginalRecord.employee_name.ilike(f"%{employee_name}%"))
        .all()
    )
    return [
        {
            "record_id": r.id,
            "employee_name": r.employee_name,
            "employer_name": r.employer_name,
            "document_type": r.document_type,
            "filename": r.filename,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


# ---------- Company B side: verify a submitted document ----------

@app.post("/verify")
def verify_document(
    record_id: int = Form(...),
    checked_by: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    record = db.query(OriginalRecord).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Original record not found.")

    raw = file.file.read()
    try:
        submitted_text = extract_text(file.filename, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    match_percentage, differences, verdict = compare_documents(
        record.original_text, submitted_text
    )

    check = VerificationCheck(
        original_record_id=record.id,
        submitted_filename=file.filename,
        submitted_text=submitted_text,
        match_percentage=match_percentage,
        verdict=verdict,
        differences=json.dumps(differences),
        checked_by=checked_by,
    )
    db.add(check)
    db.commit()
    db.refresh(check)

    return {
        "check_id": check.id,
        "employee_name": record.employee_name,
        "employer_name": record.employer_name,
        "document_type": record.document_type,
        "match_percentage": match_percentage,
        "verdict": verdict,
        "differences": differences,
        "original_record_hash": record.record_hash,
    }


@app.get("/verify/history")
def verification_history(db: Session = Depends(get_db)):
    checks = db.query(VerificationCheck).order_by(VerificationCheck.id.desc()).all()
    result = []
    for c in checks:
        record = db.query(OriginalRecord).get(c.original_record_id)
        result.append({
            "check_id": c.id,
            "employee_name": record.employee_name if record else "unknown",
            "submitted_filename": c.submitted_filename,
            "match_percentage": c.match_percentage,
            "verdict": c.verdict,
            "checked_by": c.checked_by,
            "checked_at": c.checked_at.isoformat(),
        })
    return result


# ---------- Integrity of the original records themselves ----------

@app.get("/records/verify-chain")
def verify_records_chain(db: Session = Depends(get_db)):
    return hashchain.verify_chain(db, OriginalRecord)


@app.get("/records/verify/{record_id}")
def verify_single_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(OriginalRecord).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    return hashchain.verify_record(record)


# ---------- DEMO ONLY: simulate a rogue edit to an original record ----------

@app.post("/demo/tamper-record/{record_id}")
def tamper_record(record_id: int, new_document_type: str, db: Session = Depends(get_db)):
    record = db.query(OriginalRecord).get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    record.document_type = new_document_type  # direct edit, bypassing the hash update
    db.commit()
    return {"message": f"Record {record_id} edited directly in the database. Call /records/verify-chain to see it get caught."}
