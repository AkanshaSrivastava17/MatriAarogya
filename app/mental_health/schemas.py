from datetime import date
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field


class CreatePatientRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    state: Optional[str] = None
    pregnancy_status: Optional[str] = "pregnant"  # 'pregnant', 'postpartum', 'completed'
    delivery_date: Optional[date] = None
    notes: Optional[str] = None


class UpdatePatientRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    state: Optional[str] = None
    pregnancy_status: Optional[str] = None
    delivery_date: Optional[date] = None
    notes: Optional[str] = None


class VitalsIn(BaseModel):
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    blood_sugar: Optional[float] = None
    bmi: Optional[float] = None
    heart_rate: Optional[float] = None
    body_temp: Optional[float] = None
    previous_complications: Optional[int] = 0
    preexisting_diabetes: Optional[int] = 0
    gestational_diabetes: Optional[int] = 0


class ContextIn(BaseModel):
    # Dict of categorical + numeric background features matching context_model.py
    values: Dict[str, Any]
    age: float


class CreateVisitRequest(BaseModel):
    visit_date: date
    gestational_age: Optional[int] = None
    delivery_date: Optional[date] = None
    visit_type: Optional[str] = "prenatal"  # 'prenatal', 'postpartum_followup', 'routine'
    vitals: Optional[VitalsIn] = None
    phq9_item_scores: Dict[str, int]  # keys: screening.PHQ9_ITEMS
    context: Optional[ContextIn] = None
    notes: Optional[str] = None


class ScreeningScoreRequest(BaseModel):
    screening_type: Optional[str] = "PHQ-9"
    item_scores: Dict[str, int]


class ContextRiskRequest(BaseModel):
    values: Dict[str, Any]
    age: float
