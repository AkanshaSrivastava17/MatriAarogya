"""
unified_engine.py — Cross-domain clinical action prioritization and worker task engine.

Prioritization Tiers:
1. EMERGENCY: Immediate life-safety escalation (Tele-MANAS suicide alert, BP >= 160/110 hypertensive crisis)
2. URGENT: Action within 24-48 hours (PHQ-9 >= 15, Blood sugar >= 11.1 mmol/L)
3. TIMELY: Action within 7 days (PHQ-9 10-14, elevated BP 140-159/90-109, severe nutrition gap, Td overdue)
4. ROUTINE: Preventive care and monthly monitoring (IFA/calcium, routine ANC, scheduled vaccine)
5. INFO: Contextual background cues, non-clinical explanations
"""
from typing import List, Dict, Any, Optional
import hashlib
from datetime import datetime

from .schemas import ActionRecommendationItem, UnifiedActionPlanResponse
from app.mental_health import store


def _make_action_id(patient_id: int, domain: str, trigger: str) -> str:
    h = hashlib.md5(f"{patient_id}-{domain}-{trigger}".encode()).hexdigest()[:8]
    return f"ACT-{patient_id}-{domain[:3].upper()}-{h}"


def generate_unified_action_plan(
    patient_id: int,
    visit_id: Optional[int] = None,
    vitals: Optional[Dict[str, Any]] = None,
    physical_pred: Optional[int] = None,
    screening_result: Optional[Dict[str, Any]] = None,
    nutrition_eval: Optional[Dict[str, Any]] = None,
    immunization_status: Optional[Dict[str, Any]] = None,
    persist: bool = True
) -> List[ActionRecommendationItem]:
    actions: List[ActionRecommendationItem] = []

    # ── 1. MENTAL HEALTH ACTIONS ──────────────────────────────────────────────
    if screening_result:
        # Suicidal ideation item 9 (EMERGENCY)
        if screening_result.get("urgent_safety_flag") or screening_result.get("urgent_flag"):
            actions.append(
                ActionRecommendationItem(
                    action_id=_make_action_id(patient_id, "mental_health", "suicidal_ideation"),
                    patient_id=patient_id,
                    visit_id=visit_id,
                    domain="mental_health",
                    trigger_observation="Mother reports thoughts of self-harm or feeling hopeless (PHQ-9 Question 9)",
                    explanation="Urgent safety risk. Mother is experiencing acute emotional crisis or thoughts of giving up.",
                    action_text="🚨 DO NOT LEAVE MOTHER ALONE. Call the free Tele-MANAS helpline (14416) or take her to the nearest hospital immediately.",
                    urgency="emergency",
                    responsible_person="ASHA & Family",
                    timeframe="immediate",
                    referral_required=True,
                    rule_source="National Tele-MANAS Mental Health Escalation Protocol",
                    rule_version="v2.0"
                )
            )

        score = screening_result.get("total_score") or screening_result.get("phq9_score") or 0
        if score >= 15:
            actions.append(
                ActionRecommendationItem(
                    action_id=_make_action_id(patient_id, "mental_health", "phq9_severe"),
                    patient_id=patient_id,
                    visit_id=visit_id,
                    domain="mental_health",
                    trigger_observation=f"High Depression Score ({score}/27)",
                    explanation="Severe depressive distress affecting maternal daily functioning and well-being.",
                    action_text="Take mother to the PHC doctor or psychiatrist within 24 to 48 hours for medical evaluation.",
                    urgency="urgent",
                    responsible_person="ASHA & PHC Doctor",
                    timeframe="within_24h",
                    referral_required=True,
                    rule_source="MoHFW Perinatal Mental Health Screening Protocol",
                    rule_version="v2.0"
                )
            )
        elif score >= 10:
            actions.append(
                ActionRecommendationItem(
                    action_id=_make_action_id(patient_id, "mental_health", "phq9_moderate"),
                    patient_id=patient_id,
                    visit_id=visit_id,
                    domain="mental_health",
                    trigger_observation=f"Moderate Sadness / Anxiety Score ({score}/27)",
                    explanation="Elevated mood symptoms during pregnancy. Early medical and emotional support prevents deterioration.",
                    action_text="Arrange appointment with the PHC doctor or ANM within 7 days. Explain to husband that sadness during pregnancy is treatable.",
                    urgency="timely",
                    responsible_person="ASHA & ANM",
                    timeframe="within_7d",
                    referral_required=True,
                    rule_source="MoHFW Perinatal Mental Health Screening Protocol",
                    rule_version="v2.0"
                )
            )

    # ── 2. PHYSICAL VITALS ACTIONS ────────────────────────────────────────────
    if vitals:
        sbp = vitals.get("Systolic_BP") or vitals.get("systolic_bp") or 120.0
        dbp = vitals.get("Diastolic") or vitals.get("diastolic_bp") or 80.0
        bs = vitals.get("BS") or vitals.get("blood_sugar") or 5.0
        bmi = vitals.get("BMI") or vitals.get("bmi") or 22.0

        # Hypertensive Crisis / Severe Pre-eclampsia Risk (EMERGENCY)
        if sbp >= 160 or dbp >= 110:
            actions.append(
                ActionRecommendationItem(
                    action_id=_make_action_id(patient_id, "physical_vitals", "bp_crisis"),
                    patient_id=patient_id,
                    visit_id=visit_id,
                    domain="physical_vitals",
                    trigger_observation=f"Dangerously High Blood Pressure ({int(sbp)}/{int(dbp)} mmHg)",
                    explanation="Severe hypertension with risk of eclampsia fits, placental complications, or stroke.",
                    action_text="🚨 Take mother to the District Hospital or CHC immediately. Check urine for protein. Save 108 ambulance number.",
                    urgency="emergency",
                    responsible_person="ASHA & Emergency Services",
                    timeframe="immediate",
                    referral_required=True,
                    rule_source="MoHFW Hypertensive Disorders of Pregnancy Guidelines",
                    rule_version="v2.0"
                )
            )
        elif sbp >= 140 or dbp >= 90:
            actions.append(
                ActionRecommendationItem(
                    action_id=_make_action_id(patient_id, "physical_vitals", "bp_elevated"),
                    patient_id=patient_id,
                    visit_id=visit_id,
                    domain="physical_vitals",
                    trigger_observation=f"High Blood Pressure ({int(sbp)}/{int(dbp)} mmHg)",
                    explanation="Stage 1 / Gestational hypertension requiring medical workup and dietary adjustment.",
                    action_text="Refer mother to the PHC doctor on the upcoming PMSMA day (9th of month) or within 48 hours. Advise low salt and left-sided rest.",
                    urgency="timely",
                    responsible_person="ASHA & ANM",
                    timeframe="within_7d",
                    referral_required=True,
                    rule_source="Pradhan Mantri Surakshit Matritva Abhiyan (PMSMA)",
                    rule_version="v2.0"
                )
            )

        # Blood Sugar / Gestational Diabetes
        if bs >= 11.1:
            actions.append(
                ActionRecommendationItem(
                    action_id=_make_action_id(patient_id, "physical_vitals", "sugar_severe"),
                    patient_id=patient_id,
                    visit_id=visit_id,
                    domain="physical_vitals",
                    trigger_observation=f"Very High Blood Sugar ({bs:.1f} mmol/L)",
                    explanation="Severe hyperglycemia with high risk of fetal macrosomia and birth complications.",
                    action_text="Urgent: Escort mother to the PHC / hospital doctor within 24-48 hours for insulin/medication review.",
                    urgency="urgent",
                    responsible_person="ASHA & PHC Doctor",
                    timeframe="within_24h",
                    referral_required=True,
                    rule_source="National Guidelines for Gestational Diabetes Mellitus (GDM)",
                    rule_version="v2.0"
                )
            )
        elif bs >= 7.8:
            actions.append(
                ActionRecommendationItem(
                    action_id=_make_action_id(patient_id, "physical_vitals", "sugar_moderate"),
                    patient_id=patient_id,
                    visit_id=visit_id,
                    domain="physical_vitals",
                    trigger_observation=f"Elevated Blood Sugar ({bs:.1f} mmol/L)",
                    explanation="Suspected gestational diabetes. Fasting Oral Glucose Tolerance Test (OGTT) required.",
                    action_text="Take mother to the PHC lab in the morning without breakfast for an OGTT test. Advise eliminating sweets and sugary tea.",
                    urgency="timely",
                    responsible_person="ASHA & Laboratory",
                    timeframe="within_7d",
                    referral_required=True,
                    rule_source="National Guidelines for Gestational Diabetes Mellitus (GDM)",
                    rule_version="v2.0"
                )
            )

    # ── 3. NUTRITION ACTIONS ──────────────────────────────────────────────────
    if nutrition_eval:
        gaps = nutrition_eval.get("gaps", [])
        recs = nutrition_eval.get("recommendations", [])
        food_insecurity = nutrition_eval.get("food_security_flag", False)

        if food_insecurity:
            actions.append(
                ActionRecommendationItem(
                    action_id=_make_action_id(patient_id, "nutrition", "food_insecurity"),
                    patient_id=patient_id,
                    visit_id=visit_id,
                    domain="nutrition",
                    trigger_observation="Household Food Insecurity / Affordability Concern",
                    explanation="Mother's family struggles with affordability or access to basic nutritious foods.",
                    action_text="Register family immediately at Anganwadi for Take-Home Ration (Poshahar) and assist in applying for PMMVY cash benefit.",
                    urgency="timely",
                    responsible_person="ASHA & Anganwadi Worker",
                    timeframe="within_7d",
                    referral_required=False,
                    rule_source="POSHAN Abhiyaan & PMMVY Guidelines",
                    rule_version="v2.0"
                )
            )

        if gaps:
            gap_summary = "; ".join(gaps[:2])
            actions.append(
                ActionRecommendationItem(
                    action_id=_make_action_id(patient_id, "nutrition", "dietary_gap"),
                    patient_id=patient_id,
                    visit_id=visit_id,
                    domain="nutrition",
                    trigger_observation=f"Nutritional Gaps: {gap_summary}",
                    explanation="Reported dietary intake is below ICMR-NIN recommended pregnancy standards.",
                    action_text="Counsel family on affordable local protein (dal, chana, peanuts, eggs) and ensure daily red iron (IFA) and calcium tablets.",
                    urgency="routine",
                    responsible_person="ASHA Worker",
                    timeframe="routine_monthly",
                    referral_required=False,
                    rule_source="ICMR-NIN Dietary Guidelines for Indians (2020)",
                    rule_version="v1.0"
                )
            )

    # ── 4. IMMUNIZATION ACTIONS ───────────────────────────────────────────────
    if immunization_status:
        doses = immunization_status.get("doses", [])
        for d in doses:
            status = d.get("status")
            v_name = d.get("vaccine_name")
            if status == "overdue":
                actions.append(
                    ActionRecommendationItem(
                        action_id=_make_action_id(patient_id, "immunization", f"{v_name}_overdue"),
                        patient_id=patient_id,
                        visit_id=visit_id,
                        domain="immunization",
                        trigger_observation=f"{v_name} Vaccination Overdue",
                        explanation="Maternal tetanus and diphtheria immunization is past the scheduled window.",
                        action_text=f"Urgent: Mobilize mother to receive {v_name} from the ANM at the next Village Health and Nutrition Day (VHND).",
                        urgency="timely",
                        responsible_person="ASHA & ANM",
                        timeframe="within_7d",
                        referral_required=True,
                        rule_source="Universal Immunization Programme (UIP) India",
                        rule_version="v2.0"
                    )
                )
            elif status == "due":
                actions.append(
                    ActionRecommendationItem(
                        action_id=_make_action_id(patient_id, "immunization", f"{v_name}_due"),
                        patient_id=patient_id,
                        visit_id=visit_id,
                        domain="immunization",
                        trigger_observation=f"{v_name} Vaccination Due",
                        explanation="Mother is eligible for next scheduled tetanus-diphtheria immunization dose.",
                        action_text=f"Schedule and escort mother for {v_name} vaccination at upcoming VHND or clinic session.",
                        urgency="routine",
                        responsible_person="ASHA Worker",
                        timeframe="routine_monthly",
                        referral_required=False,
                        rule_source="Universal Immunization Programme (UIP) India",
                        rule_version="v2.0"
                    )
                )

    # If no actions created, provide baseline routine antenatal care action
    if not actions:
        actions.append(
            ActionRecommendationItem(
                action_id=_make_action_id(patient_id, "general", "routine_care"),
                patient_id=patient_id,
                visit_id=visit_id,
                domain="general",
                trigger_observation="All physical, mental, nutritional, and immunization findings within normal limits",
                explanation="Mother is progressing well with no acute risk factors identified.",
                action_text="✓ Continue routine monthly antenatal checkups. Ensure 1 IFA and 1 Calcium tablet daily. Teach family danger signs.",
                urgency="routine",
                responsible_person="ASHA Worker",
                timeframe="routine_monthly",
                referral_required=False,
                rule_source="National Maternal Health Operational Guidelines",
                rule_version="v2.0"
            )
        )

    if persist:
        payloads = [a.model_dump() for a in actions]
        store.save_action_recommendations(payloads)

    return actions


def format_action_plan_response(patient_id: int) -> UnifiedActionPlanResponse:
    raw_actions = store.get_action_recommendations(patient_id)
    items = [ActionRecommendationItem(**a) for a in raw_actions]

    emergencies = [i for i in items if i.urgency == "emergency"]
    urgents = [i for i in items if i.urgency == "urgent"]
    timely = [i for i in items if i.urgency == "timely"]
    routines = [i for i in items if i.urgency == "routine"]
    infos = [i for i in items if i.urgency == "info"]

    pending = len([i for i in items if i.status == "pending"])
    completed = len([i for i in items if i.status in ["completed", "referred"]])

    return UnifiedActionPlanResponse(
        patient_id=patient_id,
        total_actions=len(items),
        emergency_actions=emergencies,
        urgent_actions=urgents,
        timely_actions=timely,
        routine_actions=routines,
        info_actions=infos,
        pending_count=pending,
        completed_count=completed,
    )
