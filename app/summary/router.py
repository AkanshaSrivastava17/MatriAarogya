"""
router.py — FastAPI router for Comprehensive Maternal Health Summary.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from .schemas import ComprehensiveMaternalHealthSummaryResponse
from .summary_service import generate_comprehensive_summary

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/patients/{patient_id}", response_model=ComprehensiveMaternalHealthSummaryResponse)
def get_patient_comprehensive_summary(patient_id: int):
    try:
        return generate_comprehensive_summary(patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating comprehensive summary: {str(e)}")
