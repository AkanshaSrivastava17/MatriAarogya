"""
longitudinal.py

Builds derived longitudinal features from a patient's PRIOR visits + CURRENT visit.
This is software infrastructure for trajectory monitoring, not a fake postpartum model.

Handles first-visit (no history) cleanly and computes trajectory deltas:
- PHQ-9 score trajectory (current, previous, delta, historical max/average, elevated count)
- Contextual risk probability trajectory (current, previous, delta, historical max/average)
- Gestational age & vitals progression
- Clinical trend classification: "insufficient_data", "increasing", "stable", "decreasing"
"""
from datetime import date
from typing import List, Optional, Dict, Any


TREND_MIN_CHANGE = 3  # Minimum change in PHQ-9 score to label as increasing/decreasing


def build_longitudinal_features(
    previous_visits: List[Dict[str, Any]],
    current: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes longitudinal trajectory metrics from chronological prior visits and current visit.
    Guarantees backwards compatibility for all existing test expectations.
    """
    visit_count = len(previous_visits) + 1
    current_phq9 = current.get("phq9_total_score")
    current_risk = current.get("context_risk_probability")
    current_ga = current.get("gestational_age")
    current_vitals = current.get("vitals") or {}

    if not previous_visits:
        return {
            "visit_count": visit_count,
            "number_of_previous_visits": 0,
            "current_phq9": current_phq9,
            "previous_phq9": None,
            "score_change": None,
            "phq9_change": None,
            "num_previous_elevated_screenings": 0,
            "previous_elevated_screenings": 0,
            "max_previous_score": None,
            "avg_previous_score": None,
            "current_risk": current_risk,
            "previous_risk": None,
            "risk_probability_change": None,
            "risk_change": None,
            "max_previous_risk": None,
            "avg_previous_risk": None,
            "days_since_last_visit": None,
            "gestational_age_progression": None,
            "vitals_changes": None,
            "trend": "insufficient_data",
        }

    last_visit = previous_visits[-1]
    last_phq9 = last_visit.get("phq9_total_score")
    last_risk = last_visit.get("context_risk_probability")
    last_ga = last_visit.get("gestational_age")
    last_vitals = last_visit.get("vitals") or {}

    # Prior PHQ-9 scores
    prior_scores = [v["phq9_total_score"] for v in previous_visits if v.get("phq9_total_score") is not None]
    prior_risks = [v["context_risk_probability"] for v in previous_visits if v.get("context_risk_probability") is not None]

    # Score changes
    score_change = None
    if current_phq9 is not None and last_phq9 is not None:
        score_change = current_phq9 - last_phq9

    # Risk changes
    risk_prob_change = None
    if current_risk is not None and last_risk is not None:
        risk_prob_change = round(current_risk - last_risk, 4)

    # Trend categorization
    if score_change is None:
        trend = "insufficient_data"
    elif score_change >= TREND_MIN_CHANGE:
        trend = "increasing"
    elif score_change <= -TREND_MIN_CHANGE:
        trend = "decreasing"
    else:
        trend = "stable"

    # Days since last visit
    days_since_last = None
    curr_date = current.get("visit_date")
    last_date = last_visit.get("visit_date")
    if curr_date and last_date:
        if isinstance(curr_date, str):
            curr_date = date.fromisoformat(curr_date)
        if isinstance(last_date, str):
            last_date = date.fromisoformat(last_date)
        days_since_last = (curr_date - last_date).days

    # Gestational age progression
    ga_progression = None
    if current_ga is not None and last_ga is not None:
        ga_progression = current_ga - last_ga

    # Vitals changes where available
    vitals_changes = {}
    for vital_key in ["systolic_bp", "diastolic_bp", "bmi", "heart_rate", "blood_sugar"]:
        c_val = current_vitals.get(vital_key)
        p_val = last_vitals.get(vital_key)
        if c_val is not None and p_val is not None:
            vitals_changes[f"{vital_key}_change"] = round(c_val - p_val, 2)
            vitals_changes[f"previous_{vital_key}"] = p_val
            vitals_changes[f"current_{vital_key}"] = c_val

    elevated_count = sum(1 for v in previous_visits if v.get("phq9_at_risk"))

    return {
        "visit_count": visit_count,
        "number_of_previous_visits": len(previous_visits),
        "current_phq9": current_phq9,
        "previous_phq9": last_phq9,
        "score_change": score_change,
        "phq9_change": score_change,
        "num_previous_elevated_screenings": elevated_count,
        "previous_elevated_screenings": elevated_count,
        "max_previous_score": max(prior_scores) if prior_scores else None,
        "avg_previous_score": round(sum(prior_scores) / len(prior_scores), 2) if prior_scores else None,
        "current_risk": current_risk,
        "previous_risk": last_risk,
        "risk_probability_change": risk_prob_change,
        "risk_change": risk_prob_change,
        "max_previous_risk": max(prior_risks) if prior_risks else None,
        "avg_previous_risk": round(sum(prior_risks) / len(prior_risks), 4) if prior_risks else None,
        "days_since_last_visit": days_since_last,
        "gestational_age_progression": ga_progression,
        "vitals_changes": vitals_changes if vitals_changes else None,
        "trend": trend,
    }
