"""
Same hash-chain principle as before, applied to original employment records
instead of plagiarism reports. Ensures the ISSUING company itself can't
quietly edit a record after issuing it (e.g. under pressure from the
employee to "fix" a mistake retroactively without a trace).
"""

import hashlib
import json

GENESIS_HASH = "0" * 64


def compute_record_hash(content: dict, previous_hash: str, timestamp: str) -> str:
    payload = {"content": content, "previous_hash": previous_hash, "timestamp": timestamp}
    serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def get_latest_hash(db_session, OriginalRecord) -> str:
    latest = db_session.query(OriginalRecord).order_by(OriginalRecord.id.desc()).first()
    return latest.record_hash if latest else GENESIS_HASH


def verify_record(record) -> dict:
    content = {
        "employee_name": record.employee_name,
        "employer_name": record.employer_name,
        "document_type": record.document_type,
        "original_text": record.original_text,
        "filename": record.filename,
    }
    recomputed = compute_record_hash(content, record.previous_hash, record.created_at.isoformat())
    return {
        "valid": recomputed == record.record_hash,
        "stored_hash": record.record_hash,
        "recomputed_hash": recomputed,
    }


def verify_chain(db_session, OriginalRecord) -> dict:
    records = db_session.query(OriginalRecord).order_by(OriginalRecord.id.asc()).all()
    expected_previous = GENESIS_HASH
    for r in records:
        content = {
            "employee_name": r.employee_name,
            "employer_name": r.employer_name,
            "document_type": r.document_type,
            "original_text": r.original_text,
            "filename": r.filename,
        }
        recomputed = compute_record_hash(content, expected_previous, r.created_at.isoformat())

        if r.previous_hash != expected_previous:
            return {"valid": False, "broken_at_record_id": r.id, "reason": "previous_hash pointer mismatch"}
        if recomputed != r.record_hash:
            return {"valid": False, "broken_at_record_id": r.id, "reason": "record content does not match its hash — was edited after issuing"}

        expected_previous = r.record_hash

    return {"valid": True, "records_checked": len(records)}
