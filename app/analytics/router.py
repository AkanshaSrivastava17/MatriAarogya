"""
router.py — FastAPI router for real-world reference data and population analytics.
"""
from fastapi import APIRouter, Query
from typing import Dict, Any

from .reference_data import get_real_world_benchmarks, NFHS5_MATERNAL_INDICATORS, REFERENCE_PROVENANCE

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/benchmarks")
def get_benchmarks(state: str = Query("All India")):
    return get_real_world_benchmarks(state)


@router.get("/states")
def list_available_states():
    return {
        "states": list(NFHS5_MATERNAL_INDICATORS.keys()),
        "provenance": REFERENCE_PROVENANCE["NFHS-5"]
    }
