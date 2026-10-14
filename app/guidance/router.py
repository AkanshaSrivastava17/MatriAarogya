"""
router.py — FastAPI router for unified action recommendations and worker task tracking.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from .schemas import ActionRecommendationItem, UpdateActionStatusRequest, UnifiedActionPlanResponse
from .unified_engine import format_action_plan_response
from app.mental_health import store

router = APIRouter(prefix="/guidance", tags=["guidance"])


@router.get("/patients/{patient_id}/actions", response_model=UnifiedActionPlanResponse)
def get_patient_action_plan(patient_id: int):
    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient ID {patient_id} not found")
    existing = store.get_action_recommendations(patient_id)
    if not existing:
        from app.summary.summary_service import generate_comprehensive_summary
        try:
            generate_comprehensive_summary(patient_id)
        except Exception:
            pass
    return format_action_plan_response(patient_id)


@router.put("/actions/{action_id}/status")
def update_action_status(action_id: str, req: UpdateActionStatusRequest):
    updated = store.update_action_status(action_id, req.status, req.outcome_notes)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Action ID '{action_id}' not found")
    return {
        "action_id": action_id,
        "status": req.status,
        "outcome_notes": req.outcome_notes,
        "message": f"Action successfully marked as '{req.status}'"
    }
