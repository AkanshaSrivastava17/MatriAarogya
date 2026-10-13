"""
schemas.py — Pydantic schemas for maternal vaccination and immunization tracking.
"""
from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field


class CreateImmunizationRecordRequest(BaseModel):
    patient_id: int
    visit_id: Optional[int] = None
    vaccine_name: str = Field(..., description="Td-1, Td-2, or Td-Booster")
    dose_number: int = Field(1, ge=1, le=5)
    status: str = Field("completed", description="completed, due, overdue, not_indicated, declined, unknown")
    administration_date: Optional[date] = None
    confirmation_source: str = Field("mcp_card", description="mcp_card, facility_register, verbal_recall, unverified")
    card_verified: bool = Field(True, description="Physical Mother & Child Protection (MCP) card verified")
    next_due_date: Optional[date] = None
    notes: Optional[str] = None


class VaccineDoseStatus(BaseModel):
    vaccine_name: str
    dose_number: int
    status: str  # "completed", "due", "overdue", "not_indicated", "unknown"
    administration_date: Optional[str] = None
    confirmation_source: Optional[str] = None
    card_verified: bool = False
    next_due_date: Optional[str] = None
    status_label: str
    action_required: Optional[str] = None


class PatientImmunizationStatusResponse(BaseModel):
    patient_id: int
    gestational_age_weeks: Optional[int]
    pregnancy_status: str
    schedule_version: str
    overall_compliance: str  # "fully_protected", "partially_protected", "action_needed", "history_unknown"
    doses: List[VaccineDoseStatus]
    asha_action_checklist: List[str]
    disclaimer: str
