"""
router.py — FastAPI router for Maternal Immunization Tracking.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

from .schemas import CreateImmunizationRecordRequest, PatientImmunizationStatusResponse
from .service import evaluate_patient_immunization_status
from .schedule import SCHEDULE_METADATA, VACCINE_DEFINITIONS
from app.mental_health import store

router = APIRouter(prefix="/immunization", tags=["immunization"])


@router.post("/records")
def record_vaccination(req: CreateImmunizationRecordRequest):
    patient = store.get_patient(req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient ID {req.patient_id} not found")
    
    payload = {
        "patient_id": req.patient_id,
        "visit_id": req.visit_id,
        "vaccine_name": req.vaccine_name,
        "dose_number": req.dose_number,
        "status": req.status,
        "administration_date": req.administration_date.isoformat() if req.administration_date else None,
        "confirmation_source": req.confirmation_source,
        "card_verified": req.card_verified,
        "next_due_date": req.next_due_date.isoformat() if req.next_due_date else None,
        "notes": req.notes,
    }
    record_id = store.save_immunization_record(payload)
    
    # Return updated status immediately
    status_eval = evaluate_patient_immunization_status(req.patient_id)
    return {
        "record_id": record_id,
        "message": f"Recorded {req.vaccine_name} dose {req.dose_number} ({req.status})",
        "current_status": status_eval
    }


@router.get("/patients/{patient_id}/status", response_model=PatientImmunizationStatusResponse)
def get_patient_immunization_status(patient_id: int):
    try:
        return evaluate_patient_immunization_status(patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/patients/{patient_id}/records")
def get_patient_immunization_records(patient_id: int):
    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient ID {patient_id} not found")
    records = store.get_immunization_records(patient_id)
    return {
        "patient_id": patient_id,
        "total_records": len(records),
        "records": records
    }


@router.get("/schedule")
def get_immunization_schedule():
    return {
        "metadata": SCHEDULE_METADATA,
        "vaccines": VACCINE_DEFINITIONS
    }
