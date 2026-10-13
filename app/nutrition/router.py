"""
router.py — FastAPI router for Maternal Nutrition Assessment.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from .schemas import CreateNutritionAssessmentRequest, NutritionEvaluationResponse
from .service import evaluate_nutrition_assessment
from .references import REFERENCE_METADATA, NUTRIENT_REFERENCES_BY_STAGE, WEIGHT_GAIN_GUIDELINES
from app.mental_health import store

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.post("/assessments", response_model=NutritionEvaluationResponse)
def submit_nutrition_assessment(req: CreateNutritionAssessmentRequest):
    patient = store.get_patient(req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient ID {req.patient_id} not found")
    try:
        return evaluate_nutrition_assessment(req, persist=True)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error processing nutrition assessment: {str(e)}")


@router.get("/patients/{patient_id}/assessments")
def get_patient_nutrition_history(patient_id: int):
    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient ID {patient_id} not found")
    history = store.get_nutrition_assessments(patient_id)
    return {
        "patient_id": patient_id,
        "total_assessments": len(history),
        "assessments": history
    }


@router.get("/patients/{patient_id}/latest")
def get_latest_patient_nutrition(patient_id: int):
    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient ID {patient_id} not found")
    latest = store.get_latest_nutrition_assessment(patient_id)
    if not latest:
        raise HTTPException(status_code=404, detail=f"No nutrition assessments found for patient {patient_id}")
    return latest


@router.get("/references")
def get_nutrition_reference_standards():
    return {
        "metadata": REFERENCE_METADATA,
        "nutrients_by_stage": NUTRIENT_REFERENCES_BY_STAGE,
        "gestational_weight_gain": WEIGHT_GAIN_GUIDELINES
    }
