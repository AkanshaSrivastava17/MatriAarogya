"""
guidance.py — Actionable community guidance engine for ASHA workers.

Translates:
1. Acute safety concern / feeling hopeless (PHQ-9 Item 9 > 0)
2. Symptom severity bands (PHQ-9 score)
3. Longitudinal trajectory velocity (worsening / increasing scores)
4. Contextual vulnerability drivers (family system, gender pressure, prior loss, financial stress)
into concrete, protocolized, plain-language community health steps for the frontline ASHA worker.
"""
from typing import List, Dict, Optional, Any


def generate_mental_health_actionable_guidance(
    screening_result: Dict[str, Any],
    context_result: Optional[Dict[str, Any]],
    longitudinal_result: Dict[str, Any],
    context_inputs: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Returns prioritized list of actionable steps for frontline healthcare workers (ASHAs)
    in clear, simple, easy-to-understand language.
    """
    actions: List[str] = []

    # 1. 🚨 IMMEDIATE CRISIS & SAFETY PROTOCOL (Simple Language for ASHA Workers)
    if screening_result.get("urgent_safety_flag"):
        actions.append(
            "🚨 Urgent Safety Care: Mother is having dark thoughts or feeling hopeless (Question 9 answered yes). "
            "Do NOT leave the mother alone under any circumstances. Keep a trusted family member with her at all times."
        )
        actions.append(
            "🚨 Call Free Tele-MANAS Helpline: Dial 14416 or 1800-891-4416 together with the mother or family right now for free 24/7 counseling support."
        )
        actions.append(
            "🚨 Go to Hospital / Clinic: Take mother to the PHC doctor or hospital today for medical checkup and care."
        )

    # 2. PHQ-9 SYMPTOM SEVERITY INTERVENTIONS (Simple Language for ASHA Workers)
    phq_score = screening_result.get("total_score", 0)

    if phq_score >= 15:
        actions.append(
            "• Very Sad or Anxious (Score 15 or higher): Take mother to the PHC doctor in the next 1–2 days for checkup and care."
        )
        actions.append(
            "• Home Visit in 3 to 5 Days: Visit the mother at home in 3 to 5 days to see how she is sleeping, eating, and caring for the baby."
        )
    elif phq_score >= 10:
        actions.append(
            "• Feeling Down or Worried (Score 10–14): Take mother to meet the PHC doctor or nurse within 7 days."
        )
        actions.append(
            "• Talk with Family: Explain to the mother and husband that sadness and worry during or after pregnancy are common and treatable with care."
        )
    elif phq_score >= 5:
        actions.append(
            "• Mild Worry or Sadness (Score 5–9): Listen kindly to the mother. Encourage her to rest whenever the baby sleeps. Visit her again in 2 to 4 weeks."
        )
    else:
        actions.append(
            "• Good Well-being (Score 0–4): Mother is feeling well. Encourage the family to keep supporting her and continue routine checkups."
        )

    # 3. LONGITUDINAL TRAJECTORY ACCELERATION (Simple Language for ASHA Workers)
    trend = longitudinal_result.get("trend")
    score_change = longitudinal_result.get("score_change")
    if trend == "increasing" or (score_change is not None and score_change >= 3):
        delta_str = f"+{score_change}" if score_change else "higher"
        actions.append(
            f"⚠️ Mood Getting Worse: Mother's sadness/worry score went up by {delta_str} points since last visit. "
            "Visit her weekly at home to support and check how she is doing."
        )

    # 4. CONTEXTUAL DRIVERS INTERVENTIONS (Simple Language for ASHA Workers)
    if context_inputs:
        # Son/gender preference pressure
        gender_pref = str(context_inputs.get("Male Gender Preference", "")).strip().lower()
        if gender_pref in ["yes", "1", "high"]:
            actions.append(
                "• Boy Child Family Pressure: Talk gently with the husband and in-laws. Remind them that a healthy mother and baby are what matters most, whether it is a boy or a girl."
            )

        # Relationship with Mother-in-Law / In-law conflict
        mil = str(context_inputs.get("Relationship with Mother in-law", "")).strip().lower()
        if any(w in mil for w in ["bad", "poor", "conflict", "difficult"]):
            actions.append(
                "• Family Tension: Help the mother connect with a trusted person (her mother, sister, or close friend) to share her feelings and get relief."
            )

        # Prior Miscarriage / Pregnancy loss history
        prev_misc = str(context_inputs.get("Previous Miscarriage", "")).strip().lower()
        if prev_misc in ["yes", "1"]:
            actions.append(
                "• Worry from Past Pregnancy Loss: Comfort the mother about her past loss. Reassure her about her baby's current health, and ensure she attends all clinic checkups."
            )

        # Financial vulnerability
        money = str(context_inputs.get("Sufficient Money for Basic Needs", "")).strip().lower()
        if money in ["no", "0"]:
            actions.append(
                "• Money Help: Help the family apply for government cash support schemes like Matru Vandana Yojana (PMMVY) and Janani Suraksha Yojana (JSY)."
            )

    if not actions:
        actions.append("• Continue regular monthly checkups, nutritious food, and positive family support.")

    return actions
