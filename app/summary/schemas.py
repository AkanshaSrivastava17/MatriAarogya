"""
schemas.py — Pydantic schemas for Comprehensive Maternal Health Summary.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.explainability.schemas import ModelExplanationResponse
from app.nutrition.schemas import NutritionEvaluationResponse
from app.immunization.schemas import PatientImmunizationStatusResponse
from app.guidance.schemas import ActionRecommendationItem


class PhysicalHealthSection(BaseModel):
    has_data: bool
    latest_vitals: Optional[Dict[str, Any]] = None
    prediction_label: Optional[str] = None
    risk_prediction: Optional[int] = None
    contributing_factors: List[str] = Field(default_factory=list)
    shap_explanation: Optional[ModelExplanationResponse] = None
    vitals_trajectory_summary: Optional[str] = None


class MentalHealthSection(BaseModel):
    has_data: bool
    total_score: Optional[int] = None
    severity: Optional[str] = None
    urgent_safety_flag: bool = False
    safety_message: Optional[str] = None
    contextual_probability: Optional[float] = None
    contextual_category: Optional[str] = None
    longitudinal_trend: Optional[str] = None
    score_change: Optional[int] = None
    previous_elevated_screenings: int = 0
    total_screenings: int = 0


class NutritionSection(BaseModel):
    has_data: bool
    dietary_pattern: Optional[str] = None
    current_bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    weight_gain_kg: Optional[float] = None
    weight_gain_status: Optional[str] = None
    gaps: List[str] = Field(default_factory=list)
    food_insecurity: bool = False
    evaluation: Optional[NutritionEvaluationResponse] = None


class ImmunizationSection(BaseModel):
    has_data: bool
    overall_compliance: str
    completed_doses: List[str] = Field(default_factory=list)
    due_doses: List[str] = Field(default_factory=list)
    overdue_doses: List[str] = Field(default_factory=list)
    details: Optional[PatientImmunizationStatusResponse] = None


class ComprehensiveMaternalHealthSummaryResponse(BaseModel):
    patient_id: int
    name: str
    age: Optional[int]
    state: str
    pregnancy_status: str
    gestational_age: Optional[int]
    trimester: str
    total_visits: int
    latest_visit_date: Optional[str]
    generated_at: str

    # Transparent Rule-Based Overall Health Status
    overall_health_status: str
    overall_status_explanation: str

    # 5 Assessed Clinical Domains
    physical_health: PhysicalHealthSection
    mental_health: MentalHealthSection
    nutrition: NutritionSection
    immunization: ImmunizationSection

    # Longitudinal Trajectory Summary
    trajectory_milestones: List[str]

    # Prioritized Consolidated Action Plan
    action_plan: List[ActionRecommendationItem]

    scientific_disclaimer: str
