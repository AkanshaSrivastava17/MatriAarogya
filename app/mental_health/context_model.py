"""
context_model.py — the "contextual risk" component.

IMPORTANT NAMING NOTE: this is deliberately NOT called a "future risk" or
"postpartum risk" model anywhere in this module or its outputs. It predicts
depression-risk likelihood from background/contextual factors alone (no
symptom items), trained and cross-validated on cross-sectional PERI_DEP data
(mean AUC 0.80, 5-fold CV — see /pipeline/README.md and
docs/mental_health_architecture.md §2 for why "future/postpartum" would be
an unsupported claim given the available data).

Loads the artifacts already trained and validated in the separate pipeline
work (context_risk_model.py) rather than retraining at app startup.
"""
from pathlib import Path
from typing import Dict
import joblib
import numpy as np
import pandas as pd

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_VERSION = "context_rf_v1_periDep"

CONTEXT_CATEGORICAL = [
    "Female Education", "Husband Education", "Working Status",
    "Previous Miscarriage", "Sufficient Money for Basic Needs",
    "Family System", "Male Gender Preference", "Relationship with Mother in-law",
    "Gravida", "Physical Health ", "Current Appereance Acceptance",
]
CONTEXT_NUMERIC = ["Gestational Age", "Number of sons ", "Number of daughters", "Total Number of Children"]

_encoder = None
_num_scaler = None
_model = None


def _load():
    global _encoder, _num_scaler, _model
    if _encoder is None:
        _encoder = joblib.load(ARTIFACT_DIR / "context_encoder.pkl")
    if _num_scaler is None:
        _num_scaler = joblib.load(ARTIFACT_DIR / "context_num_scaler.pkl")
    if _model is None:
        _model = joblib.load(ARTIFACT_DIR / "context_model_random_forest.pkl")


RISK_CATEGORY_THRESHOLDS = [
    (0.0, 0.4, "Low"),
    (0.4, 0.65, "Moderate"),
    (0.65, 1.01, "Elevated"),
]  # Documented, adjustable heuristic thresholds -- not independently
   # clinically validated cutoffs. Flagged explicitly rather than presented
   # as a validated clinical threshold.


def predict_context_risk(context: Dict, age: float) -> dict:
    """
    context: dict with keys from CONTEXT_CATEGORICAL + CONTEXT_NUMERIC.
    age: patient age (numeric feature the model was trained with).
    Returns risk probability + category + top contributing factors
    (feature-importance based, not causal — see docs §6).
    """
    _load()
    missing_cat = [c for c in CONTEXT_CATEGORICAL if c not in context]
    missing_num = [c for c in CONTEXT_NUMERIC if c not in context]
    if missing_cat or missing_num:
        raise ValueError(f"Missing context fields: {missing_cat + missing_num}")

    cat_row = pd.DataFrame([[context[c] for c in CONTEXT_CATEGORICAL]], columns=CONTEXT_CATEGORICAL)
    cat_encoded = _encoder.transform(cat_row)
    num_row = pd.DataFrame([[context[c] for c in CONTEXT_NUMERIC] + [age]], columns=CONTEXT_NUMERIC + ["Age"])
    # The Random Forest's split thresholds were learned in SCALED units at
    # training time (verified: feeding unscaled values gives a materially
    # different probability, 0.477 vs 0.506 on a test row -- tree thresholds
    # are NOT invariant to this once the model is fixed, only invariant if
    # you were free to refit; a loaded model is not). The scaler is
    # therefore mandatory here, not optional.
    num_scaled = _num_scaler.transform(num_row)
    features = np.column_stack([cat_encoded, num_scaled])

    prob = float(_model.predict_proba(features)[0, 1])
    category = next(cat for lo, hi, cat in RISK_CATEGORY_THRESHOLDS if lo <= prob < hi)

    importances = dict(zip(
        list(_encoder.get_feature_names_out(CONTEXT_CATEGORICAL)) + CONTEXT_NUMERIC + ["Age"],
        _model.feature_importances_,
    ))
    top_factors = sorted(importances.items(), key=lambda x: -x[1])[:5]
    factors_list = [f for f, _ in top_factors]

    # Map raw feature column names to plain language for ASHA workers
    factor_labels = {
        "Relationship with Mother in-law": "Family relationship with in-laws",
        "Sufficient Money for Basic Needs": "Money for basic needs",
        "Male Gender Preference": "Pressure for boy child",
        "Previous Miscarriage": "Past pregnancy loss",
        "Current Appereance Acceptance": "Body changes acceptance",
        "Physical Health ": "General physical health",
        "Female Education": "Mother's education",
        "Husband Education": "Husband's education",
        "Working Status": "Employment status",
        "Family System": "Family living setup",
        "Gravida": "Number of pregnancies",
        "Gestational Age": "Weeks of pregnancy",
        "Number of sons ": "Number of sons",
        "Number of daughters": "Number of daughters",
        "Total Number of Children": "Total number of children",
        "Age": "Mother's age",
    }
    clean_summary_items = []
    for f in factors_list[:3]:
        base = f.split("_")[0].strip()
        clean_summary_items.append(factor_labels.get(f, factor_labels.get(base, f)))
    factors_summary = ", ".join(clean_summary_items)

    explanation = (
        f"Key life factors checked: {factors_summary}. "
        "These factors give helpful background clues for the ASHA worker, but are not a medical diagnosis."
    )

    from datetime import datetime
    return {
        "model_name": "ContextualRandomForest",
        "model_version": MODEL_VERSION,
        "risk_probability": round(prob, 4),
        "risk_category": category,
        "top_contributing_factors": factors_list,
        "explanation": explanation,
        "assessment_timestamp": datetime.now().isoformat(),
    }
