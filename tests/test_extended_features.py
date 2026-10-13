"""
test_extended_features.py — Comprehensive tests for SanRaksha extensions:
1. Maternal Diet & Nutrition Assessment (ICMR-NIN 2020 RDA comparisons)
2. Maternal Vaccination & Immunization Tracking (MoHFW UIP Td schedule)
3. Genuine SHAP Explanations (Keras KernelExplainer & Random Forest TreeExplainer)
4. Unified, Prioritized Action Recommendations & Task Tracking
5. Real-World Comparative Benchmarks (NFHS-5)
6. Comprehensive Maternal Health Summary
"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.mental_health import store
from app.nutrition.service import evaluate_nutrition_assessment, compute_bmi, categorize_bmi, evaluate_weight_progression
from app.nutrition.schemas import CreateNutritionAssessmentRequest, NutrientIntakeInput
from app.immunization.service import evaluate_patient_immunization_status
from app.explainability.shap_service import explain_physical_vitals_prediction, explain_contextual_mental_health_prediction
from app.guidance.unified_engine import generate_unified_action_plan, format_action_plan_response
from app.summary.summary_service import generate_comprehensive_summary

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    store.init_db()


def test_nutrition_bmi_and_weight_progression():
    bmi = compute_bmi(weight_kg=55.0, height_cm=155.0)
    assert bmi == 22.9
    assert categorize_bmi(bmi) == "normal"

    under_bmi = compute_bmi(weight_kg=40.0, height_cm=155.0)
    assert categorize_bmi(under_bmi) == "underweight"

    prog = evaluate_weight_progression(
        height_cm=155.0,
        current_weight_kg=58.0,
        pre_pregnancy_weight_kg=55.0,
        gestational_age=24,
        trimester="Trimester 2"
    )
    assert prog.gestational_weight_gain_kg == 3.0
    assert prog.current_bmi_category == "normal"
    assert "kg" in prog.recommended_gain_range


def test_nutrition_intake_evaluation_and_icmr_gaps():
    # Patient with low protein and low iron intake
    req = CreateNutritionAssessmentRequest(
        patient_id=1,
        gestational_age=20,
        trimester="Trimester 2",
        height_cm=155.0,
        current_weight_kg=52.0,
        pre_pregnancy_weight_kg=50.0,
        intake=NutrientIntakeInput(
            energy_kcal=1400.0,  # Below 2010 RDA
            protein_g=30.0,      # Below 55.5 RDA
            iron_mg=12.0,        # Below 27.0 RDA
            calcium_mg=950.0,    # Close to 1000 RDA
        ),
        dietary_pattern="vegetarian",
        food_insecurity=True
    )
    res = evaluate_nutrition_assessment(req, persist=False)
    assert res.trimester == "Trimester 2"
    assert len(res.gaps) > 0
    assert any("Protein" in g for g in res.gaps)
    assert any("Iron" in g for g in res.gaps)
    assert res.food_security_flag is True
    assert any("Anganwadi Support" in r for r in res.recommendations)
    assert "ICMR-NIN" in res.reference_source


def test_nutrition_api_endpoints():
    # Register patient first
    p_res = client.post("/mental-health/patients", json={"name": "Pooja Devi", "age": 24, "state": "Uttar Pradesh"})
    assert p_res.status_code == 200
    pid = p_res.json()["patient_id"]

    nutr_payload = {
        "patient_id": pid,
        "gestational_age": 16,
        "trimester": "Trimester 2",
        "height_cm": 158.0,
        "current_weight_kg": 54.0,
        "pre_pregnancy_weight_kg": 51.0,
        "intake": {
            "energy_kcal": 1850.0,
            "protein_g": 50.0,
            "iron_mg": 22.0,
            "calcium_mg": 900.0,
        },
        "dietary_pattern": "vegetarian",
        "food_insecurity": False,
    }
    post_res = client.post("/nutrition/assessments", json=nutr_payload)
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["patient_id"] == pid
    assert data["assessment_id"] is not None

    get_res = client.get(f"/nutrition/patients/{pid}/latest")
    assert get_res.status_code == 200
    assert get_res.json()["patient_id"] == pid

    ref_res = client.get("/nutrition/references")
    assert ref_res.status_code == 200
    assert "ICMR-NIN" in ref_res.json()["metadata"]["source"]


def test_immunization_tracking_and_status_calculation():
    p_res = client.post("/mental-health/patients", json={"name": "Sunita Sharma", "age": 26, "state": "Madhya Pradesh"})
    pid = p_res.json()["patient_id"]

    # Initial status: no doses recorded yet -> Td-1 should be due or overdue
    st1 = client.get(f"/immunization/patients/{pid}/status")
    assert st1.status_code == 200
    doses1 = st1.json()["doses"]
    td1 = next(d for d in doses1 if d["vaccine_name"] == "Td-1")
    assert td1["status"] in ["due", "overdue"]

    # Record Td-1
    rec_payload = {
        "patient_id": pid,
        "vaccine_name": "Td-1",
        "dose_number": 1,
        "status": "completed",
        "administration_date": date.today().isoformat(),
        "confirmation_source": "mcp_card",
        "card_verified": True
    }
    post_res = client.post("/immunization/records", json=rec_payload)
    assert post_res.status_code == 200

    # Now check status: Td-1 completed, Td-2 due in future
    st2 = client.get(f"/immunization/patients/{pid}/status")
    assert st2.status_code == 200
    doses2 = st2.json()["doses"]
    td1_after = next(d for d in doses2 if d["vaccine_name"] == "Td-1")
    td2_after = next(d for d in doses2 if d["vaccine_name"] == "Td-2")
    assert td1_after["status"] == "completed"
    assert td2_after["status"] == "due"


def test_genuine_shap_physical_vitals_explanation():
    sample_vitals = {
        "Age": 32,
        "Systolic_BP": 165.0,  # Markedly high
        "Diastolic": 105.0,
        "BS": 9.5,
        "BMI": 31.0,
        "Previous_Complications": 1,
        "Preexisting_Diabetes": 1,
        "Gestational_Diabetes": 0,
        "Mental_Health": 0,
        "Heart_Rate": 95.0
    }
    expl = explain_physical_vitals_prediction(sample_vitals, pred=1, prob=0.92)
    assert expl.model_name == "Improved Keras Maternal Risk Classifier"
    assert expl.prediction_class == "High Risk"
    assert len(expl.feature_contributions) == 10
    # Systolic_BP or Diastolic or BS should be top risk drivers
    assert any("Blood Pressure" in d or "Blood Sugar" in d for d in expl.top_risk_drivers)
    # Check that contributions sum matches prediction delta within reasonable tolerance
    assert abs(expl.prediction_score - (expl.base_value + expl.contributions_sum)) < 0.25
    assert "disclaimer" in expl.model_dump()


def test_genuine_shap_contextual_rf_explanation():
    context_values = {
        "Female Education": "Illiterate",
        "Husband Education": "Primary",
        "Working Status": "Housewife",
        "Previous Miscarriage": "Yes",
        "Sufficient Money for Basic Needs": "No",
        "Family System": "Joint",
        "Male Gender Preference": "Yes",
        "Relationship with Mother in-law": "Bad",
        "Gravida": "Multigravida",
        "Physical Health ": "Bad",
        "Current Appereance Acceptance": "Dissatisfied",
        "Gestational Age": 22,
        "Number of sons ": 0,
        "Number of daughters": 2,
        "Total Number of Children": 2,
    }
    expl = explain_contextual_mental_health_prediction(context_values, age=28.0, prob=0.72)
    assert "Random Forest" in expl.model_name
    assert "Vulnerability" in expl.prediction_class
    assert len(expl.feature_contributions) > 10
    assert len(expl.top_risk_drivers) > 0
    assert "disclaimer" in expl.model_dump()


def test_unified_prioritized_action_plan_and_status():
    p_res = client.post("/mental-health/patients", json={"name": "Rekha Kumari", "age": 28, "state": "Bihar"})
    pid = p_res.json()["patient_id"]

    # Generate plan with suicidal ideation emergency and high BP
    actions = generate_unified_action_plan(
        patient_id=pid,
        vitals={"Systolic_BP": 165.0, "Diastolic": 110.0, "BS": 5.0},
        physical_pred=1,
        screening_result={"total_score": 18, "urgent_safety_flag": True},
        nutrition_eval={"food_security_flag": True, "gaps": ["Low protein"]},
        immunization_status={"doses": [{"vaccine_name": "Td-1", "status": "overdue"}]},
        persist=True
    )
    assert len(actions) >= 4
    # Highest priority should be emergency
    urgencies = [a.urgency for a in actions]
    assert "emergency" in urgencies
    assert "urgent" in urgencies
    assert "timely" in urgencies

    # Check API response
    res = client.get(f"/guidance/patients/{pid}/actions")
    assert res.status_code == 200
    plan = res.json()
    assert plan["pending_count"] > 0
    assert len(plan["emergency_actions"]) >= 1

    # Update one action status
    act_id = actions[0].action_id
    put_res = client.put(f"/guidance/actions/{act_id}/status", json={"status": "completed", "outcome_notes": "Referred to CHC via 108"})
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "completed"


def test_comprehensive_maternal_health_summary():
    # Register patient, submit a visit, submit nutrition, submit immunization
    p_res = client.post("/mental-health/patients", json={"name": "Kavita Singh", "age": 25, "state": "Rajasthan"})
    pid = p_res.json()["patient_id"]

    # Submit physical & mental health visit
    visit_payload = {
        "visit_date": date.today().isoformat(),
        "gestational_age": 22,
        "vitals": {
            "systolic_bp": 145.0,
            "diastolic_bp": 92.0,
            "blood_sugar": 6.0,
            "bmi": 23.5,
            "heart_rate": 80.0
        },
        "phq9_item_scores": {
            "phq_anhedonia": 1,
            "phq_depressed_mood": 1,
            "phq_sleep": 1,
            "phq_fatigue": 1,
            "phq_appetite": 1,
            "phq_worthlessness": 1,
            "phq_concentration": 1,
            "phq_psychomotor": 1,
            "phq_suicidal_ideation": 0
        },
    }
    client.post(f"/mental-health/patients/{pid}/visits", json=visit_payload)

    # Submit nutrition
    client.post("/nutrition/assessments", json={
        "patient_id": pid,
        "gestational_age": 22,
        "intake": {"energy_kcal": 1900.0, "protein_g": 52.0, "iron_mg": 24.0, "calcium_mg": 950.0},
        "dietary_pattern": "vegetarian"
    })

    # Submit immunization dose
    client.post("/immunization/records", json={
        "patient_id": pid,
        "vaccine_name": "Td-1",
        "dose_number": 1,
        "status": "completed",
        "administration_date": date.today().isoformat(),
        "card_verified": True
    })

    # Fetch Comprehensive Summary
    sum_res = client.get(f"/summary/patients/{pid}")
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["patient_id"] == pid
    assert summary["physical_health"]["has_data"] is True
    assert summary["mental_health"]["has_data"] is True
    assert summary["nutrition"]["has_data"] is True
    assert summary["immunization"]["has_data"] is True
    assert summary["overall_health_status"] in ["Follow-up Required", "Routine Care with Monitoring", "Urgent Clinical Review Required"]
    assert len(summary["action_plan"]) > 0
    assert len(summary["trajectory_milestones"]) > 0


def test_reference_analytics_endpoint():
    res = client.get("/analytics/benchmarks?state=Uttar%20Pradesh")
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "Uttar Pradesh"
    assert "td_coverage_pct" in data["indicators"]
    assert "NFHS-5" in data["provenance"]["title"]
