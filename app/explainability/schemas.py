"""
schemas.py — Pydantic schemas for genuine SHAP model explanations.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FeatureContribution(BaseModel):
    feature_name: str
    feature_label: str
    observed_value: Any
    unit: str
    shap_value: float
    direction: str  # "increases_risk", "decreases_risk", "neutral"
    clinical_interpretation: str


class ModelExplanationResponse(BaseModel):
    model_name: str
    model_version: str
    prediction_class: str
    prediction_score: float  # Model probability
    base_value: float        # Expected/baseline probability
    contributions_sum: float # Sum of SHAP values
    feature_contributions: List[FeatureContribution]
    top_risk_drivers: List[str]
    top_protective_factors: List[str]
    disclaimer: str
    provenance: str
