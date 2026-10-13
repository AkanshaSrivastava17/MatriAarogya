"""
router.py — FastAPI router for genuine SHAP model explanations.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel

from .schemas import ModelExplanationResponse
from .shap_service import explain_physical_vitals_prediction, explain_contextual_mental_health_prediction
from app.mental_health import store

router = APIRouter(prefix="/explainability", tags=["explainability"])


class ExplainPhysicalRequest(BaseModel):
    patient_id: Optional[int] = None
    visit_id: Optional[int] = None
    vitals: Dict[str, Any]
    prediction: Optional[int] = None
    probability: Optional[float] = None


class ExplainContextRequest(BaseModel):
    patient_id: Optional[int] = None
    visit_id: Optional[int] = None
    context_values: Dict[str, Any]
    age: float
    probability: Optional[float] = None


@router.post("/physical-risk", response_model=ModelExplanationResponse)
def explain_physical_risk(req: ExplainPhysicalRequest):
    try:
        from app.main import keras_model, scaler
        raw_vals = [
            req.vitals.get("Age", 25),
            req.vitals.get("Systolic_BP", 120.0) if req.vitals.get("Systolic_BP") is not None else 120.0,
            req.vitals.get("Diastolic", 80.0) if req.vitals.get("Diastolic") is not None else 80.0,
            req.vitals.get("BS", 5.0) if req.vitals.get("BS") is not None else 5.0,
            req.vitals.get("BMI", 22.0) if req.vitals.get("BMI") is not None else 22.0,
            req.vitals.get("Previous_Complications", 0) or 0,
            req.vitals.get("Preexisting_Diabetes", 0) or 0,
            req.vitals.get("Gestational_Diabetes", 0) or 0,
            req.vitals.get("Mental_Health", 0) or 0,
            req.vitals.get("Heart_Rate", 75.0) if req.vitals.get("Heart_Rate") is not None else 75.0,
        ]
        import numpy as np
        scaled = scaler.transform(np.array([raw_vals]))
        prob = float(keras_model.predict(scaled, verbose=0)[0, 0])
        pred = 1 if prob > 0.5 else 0

        explanation = explain_physical_vitals_prediction(req.vitals, pred, prob)

        if req.patient_id:
            store.save_prediction_explanation({
                "patient_id": req.patient_id,
                "visit_id": req.visit_id,
                "model_name": explanation.model_name,
                "model_version": explanation.model_version,
                "prediction_class": explanation.prediction_class,
                "prediction_score": explanation.prediction_score,
                "base_value": explanation.base_value,
                "shap_values": {c.feature_name: c.shap_value for c in explanation.feature_contributions},
                "top_features": explanation.top_risk_drivers,
                "limitations_disclaimer": explanation.disclaimer,
            })

        return explanation
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error generating physical risk SHAP explanation: {str(e)}")


@router.post("/contextual-risk", response_model=ModelExplanationResponse)
def explain_contextual_risk(req: ExplainContextRequest):
    try:
        from app.mental_health.context_model import predict_context_risk
        res = predict_context_risk(req.context_values, req.age)
        prob = res["risk_probability"]

        explanation = explain_contextual_mental_health_prediction(req.context_values, req.age, prob)

        if req.patient_id:
            store.save_prediction_explanation({
                "patient_id": req.patient_id,
                "visit_id": req.visit_id,
                "model_name": explanation.model_name,
                "model_version": explanation.model_version,
                "prediction_class": explanation.prediction_class,
                "prediction_score": explanation.prediction_score,
                "base_value": explanation.base_value,
                "shap_values": {c.feature_name: c.shap_value for c in explanation.feature_contributions},
                "top_features": explanation.top_risk_drivers,
                "limitations_disclaimer": explanation.disclaimer,
            })

        return explanation
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error generating contextual risk SHAP explanation: {str(e)}")


@router.get("/patients/{patient_id}/explanations")
def get_patient_explanations(patient_id: int):
    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient ID {patient_id} not found")
    return {
        "patient_id": patient_id,
        "explanations": store.get_prediction_explanations(patient_id)
    }
