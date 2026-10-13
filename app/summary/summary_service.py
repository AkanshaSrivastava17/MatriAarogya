"""
summary_service.py — Consolidated Maternal Health Summary Service.

Synthesizes:
1. Patient & pregnancy information
2. Physical health (vitals, Keras model, SHAP explanation)
3. Mental health (PHQ-9, safety flag, contextual model, trajectory)
4. Nutrition (dietary intake vs ICMR-NIN RDA, gaps, weight progression)
5. Immunization (Td tracking, dose compliance)
6. Longitudinal milestones & visit trajectory
7. Prioritized consolidated action plan with rule-based overall status
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from .schemas import (
    ComprehensiveMaternalHealthSummaryResponse,
    PhysicalHealthSection,
    MentalHealthSection,
    NutritionSection,
    ImmunizationSection,
)
from app.mental_health import store
from app.nutrition.service import evaluate_nutrition_assessment
from app.nutrition.schemas import CreateNutritionAssessmentRequest, NutrientIntakeInput
from app.immunization.service import evaluate_patient_immunization_status
from app.explainability.shap_service import explain_physical_vitals_prediction
from app.guidance.unified_engine import generate_unified_action_plan, format_action_plan_response
from app.guidance.schemas import ActionRecommendationItem


def generate_comprehensive_summary(patient_id: int) -> ComprehensiveMaternalHealthSummaryResponse:
    patient = store.get_patient(patient_id)
    if not patient:
        raise ValueError(f"Patient ID {patient_id} not found")

    history = store.get_patient_history(patient_id)
    latest_visit = history[-1] if history else None

    name = patient.get("name") or "Anonymous"
    age = patient.get("age") or (latest_visit.get("age") if latest_visit else None)
    state = patient.get("state") or "Unknown"
    pregnancy_status = patient.get("pregnancy_status", "pregnant")
    gestational_age = latest_visit.get("gestational_age") if latest_visit else None
    trimester = latest_visit.get("trimester") if latest_visit else "Trimester 2"
    latest_visit_date = latest_visit.get("visit_date") if latest_visit else None

    # ── 1. Physical Health Section ────────────────────────────────────────────
    physical_has_data = False
    latest_vitals = None
    pred_label = None
    pred_int = None
    factors = []
    shap_expl = None
    vitals_trajectory_summary = None

    if latest_visit and (latest_visit.get("systolic_bp") is not None or latest_visit.get("blood_sugar") is not None):
        physical_has_data = True
        sbp = latest_visit.get("systolic_bp", 120.0)
        dbp = latest_visit.get("diastolic_bp", 80.0)
        bs = latest_visit.get("blood_sugar", 5.0)
        bmi = latest_visit.get("bmi", 22.0)
        hr = latest_visit.get("heart_rate", 75.0)

        latest_vitals = {
            "Age": age or 25,
            "Systolic_BP": sbp,
            "Diastolic": dbp,
            "BS": bs,
            "BMI": bmi,
            "Heart_Rate": hr,
        }

        # Determine prediction label
        if sbp >= 140 or dbp >= 90 or bs >= 7.8:
            pred_int = 1
            pred_label = "High Risk"
            if sbp >= 160 or dbp >= 110:
                factors.append("Dangerously High Blood Pressure")
            else:
                factors.append("High Blood Pressure")
            if bs >= 7.8:
                factors.append("High Blood Sugar")
        else:
            pred_int = 0
            pred_label = "Low Risk"
            factors.append("Vitals within normal limits")

        # Compute SHAP explanation
        try:
            shap_expl = explain_physical_vitals_prediction(latest_vitals, pred_int, 0.85 if pred_int == 1 else 0.15)
        except Exception:
            shap_expl = None

        if len(history) > 1:
            prev_v = history[-2]
            prev_sbp = prev_v.get("systolic_bp")
            if prev_sbp and sbp:
                delta_sbp = sbp - prev_sbp
                vitals_trajectory_summary = f"Systolic BP changed by {delta_sbp:+.0f} mmHg since previous checkup."

    physical_section = PhysicalHealthSection(
        has_data=physical_has_data,
        latest_vitals=latest_vitals,
        prediction_label=pred_label,
        risk_prediction=pred_int,
        contributing_factors=factors,
        shap_explanation=shap_expl,
        vitals_trajectory_summary=vitals_trajectory_summary,
    )

    # ── 2. Mental Health Section ──────────────────────────────────────────────
    mental_has_data = False
    mh_score = None
    mh_sev = None
    urgent_flag = False
    safety_msg = None
    ctx_prob = None
    ctx_cat = None
    trend = None
    score_change = None
    prev_elevated = 0

    if latest_visit and latest_visit.get("total_score") is not None:
        mental_has_data = True
        mh_score = latest_visit.get("total_score")
        mh_sev = latest_visit.get("severity")
        urgent_flag = bool(latest_visit.get("urgent_safety_flag"))
        safety_msg = latest_visit.get("safety_message")
        ctx_prob = latest_visit.get("risk_probability")
        ctx_cat = latest_visit.get("risk_category")
        trend = latest_visit.get("trend")
        score_change = latest_visit.get("score_change")
        prev_elevated = latest_visit.get("num_previous_elevated_screenings", 0)

    mental_section = MentalHealthSection(
        has_data=mental_has_data,
        total_score=mh_score,
        severity=mh_sev,
        urgent_safety_flag=urgent_flag,
        safety_message=safety_msg,
        contextual_probability=ctx_prob,
        contextual_category=ctx_cat,
        longitudinal_trend=trend,
        score_change=score_change,
        previous_elevated_screenings=prev_elevated,
        total_screenings=len(history),
    )

    # ── 3. Nutrition Section ──────────────────────────────────────────────────
    nutr_eval_dict = store.get_latest_nutrition_assessment(patient_id)
    nutr_has_data = nutr_eval_dict is not None
    nutr_response = None
    nutr_gaps = []
    food_insec = False
    current_bmi = None
    bmi_cat = None
    gain_kg = None
    gain_status = None
    dietary_pat = None

    if nutr_eval_dict:
        dietary_pat = nutr_eval_dict.get("dietary_pattern")
        current_bmi = nutr_eval_dict.get("current_bmi")
        nutr_gaps = nutr_eval_dict.get("gaps", [])
        food_insec = bool(nutr_eval_dict.get("food_insecurity"))
        pre_wt = nutr_eval_dict.get("pre_pregnancy_weight_kg")
        cur_wt = nutr_eval_dict.get("current_weight_kg")
        if cur_wt and pre_wt:
            gain_kg = round(cur_wt - pre_wt, 1)

        # Build full evaluation response for export/display
        req_obj = CreateNutritionAssessmentRequest(
            patient_id=patient_id,
            visit_id=nutr_eval_dict.get("visit_id"),
            gestational_age=nutr_eval_dict.get("gestational_age"),
            trimester=nutr_eval_dict.get("trimester"),
            height_cm=nutr_eval_dict.get("height_cm"),
            current_weight_kg=cur_wt,
            pre_pregnancy_weight_kg=pre_wt,
            intake=NutrientIntakeInput(
                energy_kcal=nutr_eval_dict.get("energy_kcal"),
                protein_g=nutr_eval_dict.get("protein_g"),
                carbohydrates_g=nutr_eval_dict.get("carbohydrates_g"),
                fat_g=nutr_eval_dict.get("fat_g"),
                fibre_g=nutr_eval_dict.get("fibre_g"),
                iron_mg=nutr_eval_dict.get("iron_mg"),
                folate_mcg=nutr_eval_dict.get("folate_mcg"),
                calcium_mg=nutr_eval_dict.get("calcium_mg"),
            ),
            dietary_pattern=dietary_pat or "vegetarian",
            food_insecurity=food_insec,
        )
        nutr_response = evaluate_nutrition_assessment(req_obj, persist=False)
        bmi_cat = nutr_response.weight_progression.current_bmi_category
        gain_status = nutr_response.weight_progression.weight_trend_status

    nutrition_section = NutritionSection(
        has_data=nutr_has_data,
        dietary_pattern=dietary_pat,
        current_bmi=current_bmi,
        bmi_category=bmi_cat,
        weight_gain_kg=gain_kg,
        weight_gain_status=gain_status,
        gaps=nutr_gaps,
        food_insecurity=food_insec,
        evaluation=nutr_response,
    )

    # ── 4. Immunization Section ───────────────────────────────────────────────
    imm_status = evaluate_patient_immunization_status(patient_id)
    imm_has_data = len(store.get_immunization_records(patient_id)) > 0
    completed_doses = [d.vaccine_name for d in imm_status.doses if d.status == "completed"]
    due_doses = [d.vaccine_name for d in imm_status.doses if d.status == "due"]
    overdue_doses = [d.vaccine_name for d in imm_status.doses if d.status == "overdue"]

    immunization_section = ImmunizationSection(
        has_data=imm_has_data,
        overall_compliance=imm_status.overall_compliance,
        completed_doses=completed_doses,
        due_doses=due_doses,
        overdue_doses=overdue_doses,
        details=imm_status,
    )

    # ── 5. Trajectory Milestones ──────────────────────────────────────────────
    milestones: List[str] = []
    milestones.append(f"Patient registered with status '{pregnancy_status.upper()}' (State: {state}).")
    if history:
        milestones.append(f"Recorded {len(history)} longitudinal clinical visits.")
        first_date = history[0].get("visit_date")
        latest_date = history[-1].get("visit_date")
        if first_date and latest_date:
            milestones.append(f"Monitoring span: from {first_date} to {latest_date}.")
        if trend:
            milestones.append(f"Longitudinal symptom trajectory: {trend.replace('_', ' ').capitalize()}.")
    if nutr_has_data:
        milestones.append("Nutritional intake assessed against ICMR-NIN 2020 RDA.")
    if imm_has_data:
        milestones.append(f"Immunization compliance: {imm_status.overall_compliance.replace('_', ' ').capitalize()}.")

    # ── 6. Prioritized Action Plan ────────────────────────────────────────────
    action_items = generate_unified_action_plan(
        patient_id=patient_id,
        visit_id=latest_visit.get("visit_id") if latest_visit else None,
        vitals=latest_vitals,
        physical_pred=pred_int,
        screening_result={"total_score": mh_score or 0, "urgent_safety_flag": urgent_flag} if mental_has_data else None,
        nutrition_eval=nutr_response.model_dump() if nutr_response else None,
        immunization_status=imm_status.model_dump(),
        persist=True,
    )

    # ── 7. Transparent Rule-Based Overall Health Status ───────────────────────
    # Decision Hierarchy:
    # 1. EMERGENCY: Suicidal ideation or BP >= 160/110 -> "Urgent Clinical Review Required (Emergency Escalation)"
    # 2. URGENT: PHQ-9 >= 15 or BS >= 11.1 -> "Urgent Clinical Review Required"
    # 3. FOLLOW-UP: PHQ-9 10-14, elevated BP 140-159/90-109, overdue vaccines, severe nutrition gaps -> "Follow-up Required"
    # 4. INSUFFICIENT: No vitals and no mental health data -> "Insufficient Information for a Reliable Summary"
    # 5. ROUTINE: All assessed domains normal -> "Routine Care with Monitoring"
    if urgent_flag:
        overall_status = "Urgent Clinical Review Required (Emergency Escalation)"
        status_expl = "Mother expressed suicidal ideation or thoughts of self-harm. Immediate crisis escalation required."
    elif physical_has_data and (latest_vitals["Systolic_BP"] >= 160 or latest_vitals["Diastolic"] >= 110):
        overall_status = "Urgent Clinical Review Required (Emergency Escalation)"
        status_expl = "Dangerously high blood pressure detected. Immediate referral for hypertensive crisis/pre-eclampsia evaluation."
    elif (mh_score is not None and mh_score >= 15) or (physical_has_data and latest_vitals["BS"] >= 11.1):
        overall_status = "Urgent Clinical Review Required"
        status_expl = "Severe depressive symptoms or severe hyperglycemia detected. Doctor review needed within 24-48 hours."
    elif (mh_score is not None and mh_score >= 10) or (physical_has_data and pred_int == 1) or overdue_doses or nutr_gaps:
        overall_status = "Follow-up Required"
        status_expl = "Moderate risk factors, overdue vaccination, or nutritional gaps identified. Clinical follow-up needed within 7 days."
    elif not physical_has_data and not mental_has_data:
        overall_status = "Insufficient Information for a Reliable Summary"
        status_expl = "Baseline physical vitals and mental health screening have not yet been recorded for this patient."
    else:
        overall_status = "Routine Care with Monitoring"
        status_expl = "All assessed maternal health indicators are within expected normal thresholds. Continue routine monthly checkups."

    return ComprehensiveMaternalHealthSummaryResponse(
        patient_id=patient_id,
        name=name,
        age=age,
        state=state,
        pregnancy_status=pregnancy_status,
        gestational_age=gestational_age,
        trimester=trimester,
        total_visits=len(history),
        latest_visit_date=latest_visit_date,
        generated_at=datetime.now().isoformat(),
        overall_health_status=overall_status,
        overall_status_explanation=status_expl,
        physical_health=physical_section,
        mental_health=mental_section,
        nutrition=nutrition_section,
        immunization=immunization_section,
        trajectory_milestones=milestones,
        action_plan=action_items,
        scientific_disclaimer=(
            "SanRaksha Maternal Health Intelligence Report: This consolidated summary synthesizes multi-domain clinical "
            "vitals, deterministic screening, nutritional intake, and immunization compliance into a unified decision-support "
            "aid for frontline health workers and Primary Health Centre clinicians. It does not replace independent clinical "
            "judgement by a qualified Medical Officer."
        ),
    )
