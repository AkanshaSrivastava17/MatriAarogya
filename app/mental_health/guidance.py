"""
guidance.py — Actionable clinical and community guidance engine for ASHA workers.

Translates:
1. Acute suicide/self-harm risk (PHQ-9 Item 9 > 0)
2. Symptom severity bands (PHQ-9 score)
3. Longitudinal trajectory velocity (worsening / increasing scores)
4. Contextual vulnerability drivers (family system, gender pressure, prior loss, financial stress)
into concrete, protocolized, actionable community health steps for the frontline ASHA worker.
"""
from typing import List, Dict, Optional, Any


def generate_mental_health_actionable_guidance(
    screening_result: Dict[str, Any],
    context_result: Optional[Dict[str, Any]],
    longitudinal_result: Dict[str, Any],
    context_inputs: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Returns prioritized list of actionable steps for frontline healthcare workers (ASHAs).
    """
    actions: List[str] = []

    # 1. 🚨 IMMEDIATE CRISIS & SAFETY PROTOCOL
    if screening_result.get("urgent_safety_flag"):
        actions.append(
            "🚨 CRITICAL CRISIS ESCALATION: Patient indicated self-harm or suicidal thoughts (PHQ-9 Item 9 > 0). "
            "Do NOT leave the mother unattended under any circumstances."
        )
        actions.append(
            "🚨 Immediate Helpline Connection: Call the National Tele-MANAS Helpline (14416 / 1800-891-4416) "
            "with the patient or her primary caregiver immediately."
        )
        actions.append(
            "🚨 Urgent Facility Transfer: Coordinate immediate escort to the PHC/CHC Medical Officer or nearest "
            "psychiatric emergency facility."
        )

    # 2. PHQ-9 SYMPTOM SEVERITY INTERVENTIONS
    phq_score = screening_result.get("total_score", 0)
    severity = screening_result.get("severity", "")

    if phq_score >= 15:
        actions.append(
            "• Severe Symptoms (PHQ-9 >= 15): Facilitate urgent referral to PHC Medical Officer within 24-48 hours "
            "for comprehensive psychiatric assessment and medication review if indicated."
        )
        actions.append(
            "• High-Intensity Home Visits: Schedule an in-person home visit within 3-5 days to evaluate sleep, "
            "daily functioning, and infant care support."
        )
    elif phq_score >= 10:
        actions.append(
            "• Moderate Symptoms (PHQ-9 10-14): Schedule consultation with the PHC doctor or community counselor within 7 days."
        )
        actions.append(
            "• Perinatal Psychoeducation: Counsel the mother and partner that perinatal depression is a common, treatable medical condition."
        )
    elif phq_score >= 5:
        actions.append(
            "• Mild Symptoms (PHQ-9 5-9): Provide supportive empathetic listening, emphasize sleep hygiene, and re-screen in 2-4 weeks."
        )
    else:
        actions.append(
            "• Minimal Symptoms (PHQ-9 0-4): Commend the mother on current coping practices and continue routine ANC/PNC monitoring."
        )

    # 3. LONGITUDINAL TRAJECTORY ACCELERATION
    trend = longitudinal_result.get("trend")
    score_change = longitudinal_result.get("score_change")
    if trend == "increasing" or (score_change is not None and score_change >= 3):
        delta_str = f"+{score_change}" if score_change else "elevated"
        actions.append(
            f"⚠️ WORSENING TRAJECTORY DETECTED: Mental health score worsened by {delta_str} points since prior visit. "
            "Shorten checkup interval to weekly community visits to monitor mood stability."
        )

    # 4. CONTEXTUAL DRIVERS INTERVENTIONS
    if context_inputs:
        # Son/gender preference pressure
        gender_pref = str(context_inputs.get("Male Gender Preference", "")).strip().lower()
        if gender_pref in ["yes", "1", "high"]:
            actions.append(
                "• Gender Preference Mitigation: Engage the husband and family elders in supportive dialogue; "
                "address son-preference pressure and highlight mother-child health over child gender."
            )

        # Relationship with Mother-in-Law / In-law conflict
        mil = str(context_inputs.get("Relationship with Mother in-law", "")).strip().lower()
        if any(w in mil for w in ["bad", "poor", "conflict", "difficult"]):
            actions.append(
                "• Family Stress Mediation: Identify a secondary trusted support person (e.g. maternal grandmother, sister, or peer) "
                "to provide relief and emotional safety during high domestic friction."
            )

        # Prior Miscarriage / Pregnancy loss history
        prev_misc = str(context_inputs.get("Previous Miscarriage", "")).strip().lower()
        if prev_misc in ["yes", "1"]:
            actions.append(
                "• Grief & Loss Reassurance: Acknowledge previous pregnancy loss; provide empathetic reassurance regarding current fetal progress "
                "and ensure all routine ultrasound checks are completed."
            )

        # Financial vulnerability
        money = str(context_inputs.get("Sufficient Money for Basic Needs", "")).strip().lower()
        if money in ["no", "0"]:
            actions.append(
                "• Financial Entitlement Linkage: Facilitate immediate enrollment in Pradhan Mantri Matru Vandana Yojana (PMMVY) "
                "and Janani Suraksha Yojana (JSY) cash transfer schemes."
            )

    if not actions:
        actions.append("• Continue standard monthly antenatal/postpartum checkups, balanced maternal diet, and positive family engagement.")

    return actions
