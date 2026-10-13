"""
schemas.py — Pydantic schemas for maternal diet and nutrition assessment.
"""
from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field


class NutrientIntakeInput(BaseModel):
    energy_kcal: Optional[float] = Field(None, ge=500.0, le=5000.0, description="Daily energy intake in kcal")
    protein_g: Optional[float] = Field(None, ge=5.0, le=250.0, description="Daily protein intake in grams")
    carbohydrates_g: Optional[float] = Field(None, ge=20.0, le=600.0, description="Daily carbohydrate intake in grams")
    fat_g: Optional[float] = Field(None, ge=5.0, le=200.0, description="Daily fat intake in grams")
    fibre_g: Optional[float] = Field(None, ge=0.0, le=100.0, description="Daily fibre intake in grams")
    iron_mg: Optional[float] = Field(None, ge=0.0, le=100.0, description="Daily iron intake in mg")
    folate_mcg: Optional[float] = Field(None, ge=0.0, le=2000.0, description="Daily folate intake in mcg")
    calcium_mg: Optional[float] = Field(None, ge=0.0, le=3000.0, description="Daily calcium intake in mg")
    vitamin_d_iu: Optional[float] = Field(None, ge=0.0, le=4000.0, description="Daily vitamin D in IU")
    vitamin_b12_mcg: Optional[float] = Field(None, ge=0.0, le=50.0, description="Daily vitamin B12 in mcg")


class CreateNutritionAssessmentRequest(BaseModel):
    patient_id: int
    visit_id: Optional[int] = None
    assessment_date: Optional[date] = None
    gestational_age: Optional[int] = Field(None, ge=1, le=45, description="Gestational age in weeks")
    trimester: Optional[str] = None  # "Trimester 1", "Trimester 2", "Trimester 3", "Postpartum"
    
    # Anthropometrics
    height_cm: Optional[float] = Field(None, ge=100.0, le=220.0, description="Height in centimetres")
    current_weight_kg: Optional[float] = Field(None, ge=30.0, le=180.0, description="Current weight in kg")
    pre_pregnancy_weight_kg: Optional[float] = Field(None, ge=30.0, le=180.0, description="Pre-pregnancy weight in kg")
    
    # Dietary intake
    intake: NutrientIntakeInput
    
    # Contextual & Household factors
    dietary_pattern: str = Field("vegetarian", description="vegetarian, non_vegetarian, eggetarian, vegan")
    food_restrictions: Optional[str] = None
    appetite_difficulty: Optional[str] = Field("normal", description="normal, reduced, nausea_vomiting, poor")
    food_insecurity: bool = Field(False, description="Affordability or household food access difficulty")
    supplements_taken: List[str] = Field(default_factory=list, description="e.g. ['IFA tablet', 'Calcium tablet']")
    
    assessment_completeness: str = Field("partial", description="full, partial, minimal")
    data_source: str = Field("24h_dietary_recall", description="24h_dietary_recall, food_frequency, verbal_estimate")
    notes: Optional[str] = None


class NutrientComparisonResult(BaseModel):
    nutrient: str
    label: str
    reported_value: Optional[float]
    reference_value: float
    unit: str
    reference_type: str  # "RDA", "EAR", "AI"
    status: str  # "severely_below", "moderately_below", "adequate", "above", "not_assessed"
    percent_of_reference: Optional[float]
    difference: Optional[float]
    explanation: str


class WeightProgressionResult(BaseModel):
    height_cm: Optional[float]
    current_weight_kg: Optional[float]
    current_bmi: Optional[float]
    current_bmi_category: Optional[str]
    pre_pregnancy_weight_kg: Optional[float]
    pre_pregnancy_bmi: Optional[float]
    pre_pregnancy_bmi_category: Optional[str]
    gestational_weight_gain_kg: Optional[float]
    recommended_gain_range: Optional[str]
    weight_trend_status: str  # "on_track", "low_gain", "excessive_gain", "insufficient_data"
    guidance: str


class NutritionEvaluationResponse(BaseModel):
    assessment_id: Optional[int] = None
    patient_id: int
    visit_id: Optional[int]
    assessment_date: str
    trimester: str
    gestational_age: Optional[int]
    completeness: str
    
    # Anthropometrics
    weight_progression: WeightProgressionResult
    
    # Nutrient Comparison
    nutrient_comparisons: List[NutrientComparisonResult]
    
    # Identified Gaps & Culturally Appropriate Action Recommendations
    gaps: List[str]
    recommendations: List[str]
    unassessed_nutrients: List[str]
    food_security_flag: bool
    
    # Metadata & Provenance
    reference_source: str
    reference_version: str
    scientific_disclaimer: str
