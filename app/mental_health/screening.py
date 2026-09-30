"""
screening.py — deterministic current-state mental health screening.

This is NOT a machine-learning model, deliberately. PHQ-9 is scored by
summing item responses and applying a validated cutoff. Training a model to
predict this from the same 9 items would just be re-deriving arithmetic
(verified during earlier development against PERI_DEP: its own label is a
100%-exact function of summing these items). So this module implements the
scoring rule directly.

Answers the spec's "Task A — current mental-health screening" question:
"does she currently screen positive for depression?" — not "what will
happen in the future" (that's the separate, explicitly-not-ML-predicted
contextual/future task, see context_model.py + docs/mental_health_architecture.md §2).
"""
from typing import Dict

PHQ9_ITEMS = [
    "phq_anhedonia", "phq_depressed_mood", "phq_sleep", "phq_fatigue",
    "phq_appetite", "phq_worthlessness", "phq_concentration",
    "phq_psychomotor", "phq_suicidal_ideation",
]

SEVERITY_BANDS = [
    (0, 4, "Minimal"),
    (5, 9, "Mild"),
    (10, 14, "Moderate"),
    (15, 19, "Moderately Severe"),
    (20, 27, "Severe"),
]
PHQ9_AT_RISK_CUTOFF = 10  # standard PHQ-9 convention, also PERI_DEP's own cutoff


def score_phq9(item_scores: Dict[str, int]) -> dict:
    """
    item_scores: dict with the 9 PHQ9_ITEMS keys, each an int 0-3.
    Raises ValueError on missing items or out-of-range values, rather than
    silently defaulting them — a missing safety-item response must not be
    silently treated as 0.
    """
    missing = [k for k in PHQ9_ITEMS if k not in item_scores]
    if missing:
        raise ValueError(f"Missing required PHQ-9 item(s): {missing}")
    for k in PHQ9_ITEMS:
        v = item_scores[k]
        if not isinstance(v, int) or not (0 <= v <= 3):
            raise ValueError(f"Item '{k}' must be an integer 0-3, got {v!r}")

    total = sum(item_scores[k] for k in PHQ9_ITEMS)
    severity = next(band for lo, hi, band in SEVERITY_BANDS if lo <= total <= hi)

    urgent = item_scores["phq_suicidal_ideation"] > 0
    at_risk = total >= PHQ9_AT_RISK_CUTOFF
    safety_msg = (
        "URGENT: Mother is having dark thoughts or feeling hopeless (Question 9 answered yes). "
        "Do NOT leave the mother alone. Keep a family member with her and take her to the clinic or doctor today."
        if urgent else "No acute safety concern reported on screening."
    )

    return {
        "screening_type": "PHQ-9",
        "total_score": total,
        "severity": severity,
        "at_risk": at_risk,
        "screening_status": "Positive" if at_risk else "Negative",
        # Item 9 = self-harm/suicidal ideation. This flag is computed
        # independently and must never be suppressed by a low total score,
        # per spec §4/§18 (a positive safety item must not be hidden).
        "urgent_safety_flag": urgent,
        "urgent_message": safety_msg if urgent else None,
        "safety_message": safety_msg,
    }


# EPDS scoring included for completeness (per spec §4, "PHQ-9 and/or EPDS if
# the existing project/data supports this"). Item 10 is the self-harm item;
# same safety-flag rule applies. Standard EPDS cutoff for high-risk is 13.
EPDS_AT_RISK_CUTOFF = 13


def score_epds(item_scores: Dict[str, int]) -> dict:
    epds_items = [f"epds_{i}" for i in range(1, 11)]
    missing = [k for k in epds_items if k not in item_scores]
    if missing:
        raise ValueError(f"Missing required EPDS item(s): {missing}")
    for k in epds_items:
        v = item_scores[k]
        if not isinstance(v, int) or not (0 <= v <= 3):
            raise ValueError(f"Item '{k}' must be an integer 0-3, got {v!r}")

    total = sum(item_scores[k] for k in epds_items)
    return {
        "screening_type": "EPDS",
        "total_score": total,
        "at_risk": total >= EPDS_AT_RISK_CUTOFF,
        "urgent_safety_flag": item_scores["epds_10"] > 0,
    }
