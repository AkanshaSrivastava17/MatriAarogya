"""
schemas.py — Pydantic schemas for unified action recommendations and worker task tracking.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ActionRecommendationItem(BaseModel):
    action_id: str
    patient_id: int
    visit_id: Optional[int] = None
    domain: str  # "physical_vitals", "mental_health", "nutrition", "immunization", "general"
    trigger_observation: str
    explanation: str
    action_text: str
    urgency: str  # "emergency", "urgent", "timely", "routine", "info"
    responsible_person: str  # "ASHA", "ANM", "PHC Doctor", "Hospital Specialist"
    timeframe: str  # "immediate", "within_24h", "within_7d", "routine_monthly"
    referral_required: bool = False
    status: str = "pending"  # "pending", "completed", "referred", "deferred"
    outcome_notes: Optional[str] = None
    completed_at: Optional[str] = None
    rule_source: str
    rule_version: str


class UpdateActionStatusRequest(BaseModel):
    status: str = Field(..., description="completed, referred, deferred, pending")
    outcome_notes: Optional[str] = None


class UnifiedActionPlanResponse(BaseModel):
    patient_id: int
    total_actions: int
    emergency_actions: List[ActionRecommendationItem]
    urgent_actions: List[ActionRecommendationItem]
    timely_actions: List[ActionRecommendationItem]
    routine_actions: List[ActionRecommendationItem]
    info_actions: List[ActionRecommendationItem]
    pending_count: int
    completed_count: int
