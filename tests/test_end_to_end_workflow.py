"""
test_end_to_end_workflow.py

Comprehensive end-to-end integration tests for the SanRaksha Mental Health &
Longitudinal Monitoring System.

Verifies:
1. Patient registration, retrieval, and updating.
2. Prenatal visit 1 -> prenatal visit 2 -> postpartum follow-up visit 3 for the same patient.
3. Append-only persistence: visit 1 and visit 2 records are preserved and never overwritten.
4. Correct calculation of score deltas, risk deltas, historical statistics, and trend classification.
5. Deterministic PHQ-9 scoring + urgent suicidal ideation flag independent of overall score.
6. Contextual ML risk assessment with non-causal explanation and model versioning.
7. Explicit FutureRiskModel reporting unavailable postpartum prediction due to cross-sectional training data.
8. Standalone utility endpoints for screening and contextual risk evaluation.
9. Error handling on invalid/missing input fields.
"""
import sys
from datetime import date
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.mental_health import screening

client = TestClient(app)

SAMPLE_CONTEXT = {
    "Female Education": "Secondary",
    "Husband Education": "Secondary",
    "Working Status": "Housewife",
    "Previous Miscarriage": "No",
    "Sufficient Money for Basic Needs": "Yes",
    "Family System": "Nuclear",
    "Male Gender Preference": "No",
    "Relationship with Mother in-law": "Good",
    "Gravida": "Primigravida",
    "Physical Health ": "Good",
    "Current Appereance Acceptance": "Satisfied",
    "Gestational Age": 20,
    "Number of sons ": 0,
    "Number of daughters": 0,
    "Total Number of Children": 0,
}


def _make_phq9(suicide_val=0, default_val=1):
    scores = {item: default_val for item in screening.PHQ9_ITEMS}
    scores["phq_suicidal_ideation"] = suicide_val
    return scores


def test_patient_crud_lifecycle():
    # 1. Create Patient
    r = client.post("/mental-health/patients", json={
        "name": "Sunita Devi",
        "age": 26,
        "state": "Uttar Pradesh",
        "pregnancy_status": "pregnant",
        "notes": "Second trimester regular checkup"
    })
    assert r.status_code == 200
    data = r.json()
    patient_id = data["patient_id"]
    assert patient_id > 0
    assert data["name"] == "Sunita Devi"
    assert data["pregnancy_status"] == "pregnant"

    # 2. Get Patient
    r_get = client.get(f"/mental-health/patients/{patient_id}")
    assert r_get.status_code == 200
    p_info = r_get.json()
    assert p_info["patient_id"] == patient_id
    assert p_info["name"] == "Sunita Devi"
    assert p_info["state"] == "Uttar Pradesh"

    # 3. Update Patient Status
    r_up = client.put(f"/mental-health/patients/{patient_id}", json={
        "pregnancy_status": "postpartum",
        "delivery_date": "2026-08-15"
    })
    assert r_up.status_code == 200
    assert r_up.json()["updated"] is True

    r_verify = client.get(f"/mental-health/patients/{patient_id}")
    assert r_verify.json()["pregnancy_status"] == "postpartum"
    assert r_verify.json()["delivery_date"] == "2026-08-15"


def test_end_to_end_longitudinal_visit_progression():
    # Create fresh patient
    r_p = client.post("/mental-health/patients", json={
        "name": "Pooja Sharma",
        "age": 24,
        "state": "Bihar",
        "pregnancy_status": "pregnant"
    })
    patient_id = r_p.json()["patient_id"]

    # ── VISIT 1 (Prenatal, Week 16, Second trimester, Low PHQ-9) ───────────────────
    v1_scores = _make_phq9(suicide_val=0, default_val=0)  # total score = 0
    r_v1 = client.post(f"/mental-health/patients/{patient_id}/visits", json={
        "visit_date": "2026-03-01",
        "gestational_age": 16,
        "visit_type": "prenatal",
        "phq9_item_scores": v1_scores,
        "context": {"values": SAMPLE_CONTEXT, "age": 24},
        "vitals": {"systolic_bp": 115.0, "diastolic_bp": 75.0, "bmi": 22.5, "heart_rate": 76.0}
    })
    assert r_v1.status_code == 200
    v1_data = r_v1.json()

    assert v1_data["patient_id"] == patient_id
    assert v1_data["trimester"] == "Second trimester"
    assert v1_data["current_screening"]["phq9_score"] == 0
    assert v1_data["current_screening"]["severity"] == "Minimal"
    assert v1_data["current_screening"]["screen_positive"] is False
    assert v1_data["safety_flag"] is False
    assert v1_data["contextual_risk"]["model_name"] == "ContextualRandomForest"
    assert 0.0 <= v1_data["contextual_risk"]["probability"] <= 1.0
    assert "explanation" in v1_data["contextual_risk"]

    # Longitudinal on Visit 1 (First visit)
    assert v1_data["longitudinal"]["visit_count"] == 1
    assert v1_data["longitudinal"]["previous_phq9"] is None
    assert v1_data["longitudinal"]["phq9_change"] is None
    assert v1_data["longitudinal"]["trend"] == "insufficient_data"

    # Scientific Postpartum Interface check
    assert v1_data["postpartum_prediction"]["available"] is False
    assert "cross-sectional" in v1_data["postpartum_prediction"]["reason"].lower()

    # Actionable Guidance for ASHA workers
    assert "actionable_guidance" in v1_data
    assert isinstance(v1_data["actionable_guidance"], list)
    assert len(v1_data["actionable_guidance"]) > 0

    # ── VISIT 2 (Prenatal, Week 24, Second trimester, Elevated PHQ-9) ───────────────
    v2_scores = _make_phq9(suicide_val=0, default_val=1)
    v2_scores["phq_depressed_mood"] = 3
    v2_scores["phq_anhedonia"] = 3  # total score = 8 + 4 = 12 (Moderate, >=10 cutoff)
    r_v2 = client.post(f"/mental-health/patients/{patient_id}/visits", json={
        "visit_date": "2026-05-01",
        "gestational_age": 24,
        "visit_type": "prenatal",
        "phq9_item_scores": v2_scores,
        "context": {"values": SAMPLE_CONTEXT, "age": 24},
        "vitals": {"systolic_bp": 125.0, "diastolic_bp": 82.0, "bmi": 23.8, "heart_rate": 84.0}
    })
    assert r_v2.status_code == 200
    v2_data = r_v2.json()

    assert v2_data["current_screening"]["phq9_score"] == 12
    assert v2_data["current_screening"]["severity"] == "Moderate"
    assert v2_data["current_screening"]["screen_positive"] is True

    # Longitudinal progression: 0 -> 12 (+12 change)
    assert v2_data["longitudinal"]["visit_count"] == 2
    assert v2_data["longitudinal"]["previous_phq9"] == 0
    assert v2_data["longitudinal"]["phq9_change"] == 12
    assert v2_data["longitudinal"]["trend"] == "increasing"
    assert v2_data["longitudinal"]["gestational_age_progression"] == 8

    # ── VISIT 3 (Postpartum Follow-up Screening with Delivery Date) ─────────────────
    v3_scores = _make_phq9(suicide_val=0, default_val=1)  # total score = 8
    r_v3 = client.post(f"/mental-health/patients/{patient_id}/visits", json={
        "visit_date": "2026-09-01",
        "delivery_date": "2026-08-15",
        "visit_type": "postpartum_followup",
        "phq9_item_scores": v3_scores,
        "context": {"values": SAMPLE_CONTEXT, "age": 24},
        "vitals": {"systolic_bp": 118.0, "diastolic_bp": 78.0, "bmi": 23.0, "heart_rate": 78.0}
    })
    assert r_v3.status_code == 200
    v3_data = r_v3.json()

    assert v3_data["trimester"] == "Postpartum"
    assert v3_data["visit_type"] == "postpartum_followup"
    assert v3_data["longitudinal"]["visit_count"] == 3
    assert v3_data["longitudinal"]["previous_phq9"] == 12
    assert v3_data["longitudinal"]["phq9_change"] == -4  # 8 - 12 = -4
    assert v3_data["longitudinal"]["trend"] == "decreasing"
    assert v3_data["longitudinal"]["num_previous_elevated_screenings"] == 1
    assert v3_data["longitudinal"]["max_previous_score"] == 12

    # ── Verify Append-Only History Retrieval ────────────────────────────────────────
    r_hist = client.get(f"/mental-health/patients/{patient_id}/history")
    assert r_hist.status_code == 200
    visits = r_hist.json()["visits"]
    assert len(visits) == 3

    # Visit 1 was untouched by subsequent writes
    assert visits[0]["total_score"] == 0
    assert visits[0]["gestational_age"] == 16
    assert visits[0]["trimester"] == "Second trimester"

    # Visit 2 preserved
    assert visits[1]["total_score"] == 12
    assert visits[1]["at_risk"] == 1

    # Visit 3 preserved
    assert visits[2]["total_score"] == 8
    assert visits[2]["trimester"] == "Postpartum"


def test_safety_flag_priority_over_score():
    """Item 9 > 0 must trigger urgent_flag=true even if total score is minimal (1/27)."""
    r_p = client.post("/mental-health/patients", json={"name": "Safety Test Patient"})
    patient_id = r_p.json()["patient_id"]

    scores = _make_phq9(suicide_val=1, default_val=0)  # total score is only 1!
    r = client.post(f"/mental-health/patients/{patient_id}/visits", json={
        "visit_date": "2026-06-01",
        "gestational_age": 28,
        "phq9_item_scores": scores
    })
    assert r.status_code == 200
    res = r.json()

    assert res["current_screening"]["phq9_score"] == 1
    assert res["current_screening"]["severity"] == "Minimal"
    assert res["current_screening"]["screen_positive"] is False
    # Urgent safety flag MUST be True and safety message must be prominent
    assert res["safety_flag"] is True
    assert res["current_screening"]["urgent_flag"] is True
    assert "URGENT" in res["urgent_message"]


def test_standalone_utility_endpoints():
    # 1. Screening Score Calculator
    scores = _make_phq9(suicide_val=0, default_val=2)  # total = 16 (Moderately Severe)
    r_calc = client.post("/mental-health/screening/score", json={
        "screening_type": "PHQ-9",
        "item_scores": scores
    })
    assert r_calc.status_code == 200
    assert r_calc.json()["total_score"] == 16
    assert r_calc.json()["severity"] == "Moderately Severe"
    assert r_calc.json()["at_risk"] is True

    # 2. Context Predictor
    r_ctx = client.post("/mental-health/context/predict", json={
        "values": SAMPLE_CONTEXT,
        "age": 25.0
    })
    assert r_ctx.status_code == 200
    c_res = r_ctx.json()
    assert "risk_probability" in c_res
    assert "risk_category" in c_res
    assert len(c_res["top_contributing_factors"]) > 0


def test_error_handling():
    # Incomplete PHQ-9 (missing items)
    r = client.post("/mental-health/patients/1/visits", json={
        "visit_date": "2026-06-01",
        "gestational_age": 20,
        "phq9_item_scores": {"phq_anhedonia": 1}  # Missing 8 items
    })
    assert r.status_code == 422
    assert "Missing required PHQ-9 item" in r.json()["detail"]

    # Invalid patient history query
    r_bad = client.get("/mental-health/patients/999999/history")
    assert r_bad.status_code == 404
