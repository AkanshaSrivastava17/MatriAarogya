"""
router.py — Complete FastAPI router for the SanRaksha Mental Health & Longitudinal Monitoring Module.

Wired into app/main.py as an additional router (app.include_router(...)),
alongside the existing /predict endpoint, which is untouched.

Supports:
- Patient registration, retrieval, updating, and listing.
- Full unified visit submission (vitals + context + PHQ-9 + pregnancy/postpartum lifecycle).
- Clean separation of:
  1. Current Screening (deterministic PHQ-9 scoring + urgent suicidal ideation flag)
  2. Contextual Risk Assessment (scikit-learn Random Forest model on background features)
  3. Longitudinal Trend Tracking (visit-over-visit trajectory computation)
  4. Future/Postpartum Prediction (scientifically explicit unavailable status + interface)
"""
import logging
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query

from . import screening, context_model, longitudinal, store, trimester as trimester_mod
from .future_model import future_risk_evaluator
from .schemas import (
    CreatePatientRequest,
    UpdatePatientRequest,
    CreateVisitRequest,
    ScreeningScoreRequest,
    ContextRiskRequest,
)

logger = logging.getLogger("sanraksha.mental_health")
# Privacy: this logger must never be passed item-level PHQ-9 responses. Only patient_id/visit_id/outcomes.

router = APIRouter(prefix="/mental-health", tags=["mental-health"])

store.init_db()


# ── Patient Endpoints ──────────────────────────────────────────────────────────

@router.post("/patients")
def create_patient(req: CreatePatientRequest):
    patient_id = store.create_patient(
        name=req.name,
        age=req.age,
        state=req.state,
        pregnancy_status=req.pregnancy_status or "pregnant",
        delivery_date=req.delivery_date,
        notes=req.notes,
    )
    logger.info(f"Created patient_id={patient_id} name={req.name} status={req.pregnancy_status}")
    return {
        "patient_id": patient_id,
        "name": req.name,
        "age": req.age,
        "state": req.state,
        "pregnancy_status": req.pregnancy_status or "pregnant",
        "delivery_date": req.delivery_date.isoformat() if req.delivery_date else None,
    }


@router.get("/patients")
def list_patients():
    return {"patients": store.list_patients()}


@router.get("/patients/{patient_id}")
def get_patient(patient_id: int):
    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    history = store.get_patient_history(patient_id)
    return {
        **patient,
        "total_visits": len(history),
        "latest_assessment": history[-1] if history else None,
    }


@router.put("/patients/{patient_id}")
def update_patient(patient_id: int, req: UpdatePatientRequest):
    existing = store.get_patient(patient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")

    updated = store.update_patient(
        patient_id=patient_id,
        name=req.name,
        age=req.age,
        state=req.state,
        pregnancy_status=req.pregnancy_status,
        delivery_date=req.delivery_date,
        notes=req.notes,
    )
    return {"patient_id": patient_id, "updated": updated}


# ── Visit & Assessment Endpoints ──────────────────────────────────────────────

@router.post("/patients/{patient_id}/visits")
def create_visit(patient_id: int, req: CreateVisitRequest):
    # 1. Deterministic Current Mental Health Screening (Task A)
    try:
        screening_result = screening.score_phq9(req.phq9_item_scores)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 2. Contextual ML Risk Assessment (Task B)
    context_result = None
    if req.context is not None:
        try:
            context_result = context_model.predict_context_risk(req.context.values, req.context.age)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"Invalid context fields: {e}")

    # 3. Trimester & Pregnancy Lifecycle Classification
    try:
        trimester = trimester_mod.trimester_from_gestational_age(req.gestational_age, req.delivery_date)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Trimester error: {e}")

    visit_type = req.visit_type or ("postpartum_followup" if trimester == "Postpartum" else "prenatal")

    # 4. Longitudinal Feature Generation (Trajectory Engine)
    previous_visits = store.get_previous_visits(patient_id)
    current_summary = {
        "visit_date": req.visit_date,
        "gestational_age": req.gestational_age,
        "phq9_total_score": screening_result["total_score"],
        "phq9_at_risk": screening_result["at_risk"],
        "vitals": req.vitals.model_dump() if req.vitals else {},
    }
    if context_result:
        current_summary["context_risk_probability"] = context_result["risk_probability"]

    longitudinal_result = longitudinal.build_longitudinal_features(previous_visits, current_summary)

    # 5. Scientific Future/Postpartum Prediction Evaluation
    future_prediction = future_risk_evaluator.predict_future_risk(
        patient_id=patient_id,
        current_gestational_age=req.gestational_age,
        delivery_date=req.delivery_date,
        longitudinal_history=previous_visits,
        current_vitals=req.vitals.model_dump() if req.vitals else None,
        current_context=req.context.values if req.context else None,
    )

    # 6. Append-Only Persistence (Historical Visits Never Overwritten)
    visit_id = store.save_visit(
        patient_id=patient_id,
        visit_date=req.visit_date,
        trimester=trimester,
        visit_type=visit_type,
        screening_result=screening_result,
        context_result=context_result,
        longitudinal_result=longitudinal_result,
        gestational_age=req.gestational_age,
        delivery_date=req.delivery_date,
        vitals=req.vitals.model_dump() if req.vitals else None,
        item_scores=req.phq9_item_scores,
        context_inputs=req.context.values if req.context else None,
        notes=req.notes,
    )

    logger.info(
        f"visit_id={visit_id} patient_id={patient_id} at_risk={screening_result['at_risk']} "
        f"urgent_safety_flag={screening_result['urgent_safety_flag']} trend={longitudinal_result['trend']}"
    )

    # 7. Formatted Structured Response Matching Section 9 Specification
    return {
        "patient_id": patient_id,
        "visit_id": visit_id,
        "visit_date": req.visit_date.isoformat(),
        "trimester": trimester,
        "visit_type": visit_type,
        "current_screening": {
            "screening_type": screening_result["screening_type"],
            "phq9_score": screening_result["total_score"],
            "total_score": screening_result["total_score"],  # Backwards-compatible
            "severity": screening_result["severity"],
            "screen_positive": screening_result["at_risk"],
            "at_risk": screening_result["at_risk"],          # Backwards-compatible
            "urgent_flag": screening_result["urgent_safety_flag"],
            "urgent_safety_flag": screening_result["urgent_safety_flag"],
            "safety_message": screening_result["safety_message"],
        },
        "contextual_risk": {
            "model_name": context_result["model_name"],
            "model_version": context_result["model_version"],
            "probability": context_result["risk_probability"],
            "risk_probability": context_result["risk_probability"],  # Backwards-compatible
            "category": context_result["risk_category"],
            "risk_category": context_result["risk_category"],        # Backwards-compatible
            "top_contributing_factors": context_result["top_contributing_factors"],
            "explanation": context_result["explanation"],
        } if context_result else None,
        "longitudinal": {
            "previous_phq9": longitudinal_result["previous_phq9"],
            "phq9_change": longitudinal_result["phq9_change"],
            "score_change": longitudinal_result["score_change"],     # Backwards-compatible
            "previous_risk": longitudinal_result["previous_risk"],
            "risk_change": longitudinal_result["risk_change"],
            "risk_probability_change": longitudinal_result["risk_probability_change"], # Backwards-compatible
            "previous_elevated_screenings": longitudinal_result["previous_elevated_screenings"],
            "num_previous_elevated_screenings": longitudinal_result["num_previous_elevated_screenings"],
            "max_previous_score": longitudinal_result["max_previous_score"],
            "avg_previous_score": longitudinal_result["avg_previous_score"],
            "visit_count": longitudinal_result["visit_count"],
            "trend": longitudinal_result["trend"],
            "days_since_last_visit": longitudinal_result["days_since_last_visit"],
            "gestational_age_progression": longitudinal_result["gestational_age_progression"],
            "vitals_changes": longitudinal_result["vitals_changes"],
        },
        "postpartum_prediction": future_prediction,
        # Safety surfaced directly at top-level so it cannot be missed or suppressed
        "safety_flag": screening_result["urgent_safety_flag"],
        "urgent_message": screening_result.get("urgent_message"),
    }


@router.get("/patients/{patient_id}/history")
def get_history(patient_id: int):
    history = store.get_patient_history(patient_id)
    if not history:
        raise HTTPException(status_code=404, detail="No visits found for this patient_id")
    return {"patient_id": patient_id, "visits": history}


@router.get("/patients/{patient_id}/latest")
def get_latest(patient_id: int):
    latest = store.get_latest_visit(patient_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No assessments found for this patient_id")
    return {"patient_id": patient_id, "latest_visit": latest}


# ── Standalone Utility Endpoints ──────────────────────────────────────────────

@router.post("/screening/score")
def calculate_screening_score(req: ScreeningScoreRequest):
    """Computes deterministic PHQ-9 or EPDS score without persisting."""
    try:
        if (req.screening_type or "").upper() == "EPDS":
            return screening.score_epds(req.item_scores)
        return screening.score_phq9(req.item_scores)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/context/predict")
def predict_context(req: ContextRiskRequest):
    """Computes contextual risk prediction without persisting."""
    try:
        return context_model.predict_context_risk(req.values, req.age)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
