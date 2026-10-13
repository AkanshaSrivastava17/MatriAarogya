"""
shap_service.py — Genuine instance-level SHAP explanation service for SanRaksha models.

Provides:
1. KernelExplainer SHAP for the Keras Maternal Physical Vitals model.
2. TreeExplainer SHAP for the scikit-learn Contextual Mental Health Random Forest.
"""
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging
import joblib
import numpy as np
import pandas as pd
import shap
import tensorflow as tf

from .schemas import FeatureContribution, ModelExplanationResponse
from app.mental_health import store

logger = logging.getLogger("sanraksha.explainability")

BASE_DIR = Path(__file__).resolve().parent.parent
PHYSICAL_FEATURES = [
    "Age", "Systolic_BP", "Diastolic", "BS", "BMI",
    "Previous_Complications", "Preexisting_Diabetes", "Gestational_Diabetes",
    "Mental_Health", "Heart_Rate"
]

PHYSICAL_FEATURE_LABELS = {
    "Age": ("Mother's Age", "years"),
    "Systolic_BP": ("Systolic Blood Pressure", "mmHg"),
    "Diastolic": ("Diastolic Blood Pressure", "mmHg"),
    "BS": ("Blood Sugar", "mmol/L"),
    "BMI": ("Body Mass Index", "kg/m²"),
    "Previous_Complications": ("Past Pregnancy Complications", "status"),
    "Preexisting_Diabetes": ("Pre-existing Diabetes", "status"),
    "Gestational_Diabetes": ("Gestational Diabetes", "status"),
    "Mental_Health": ("Depression / Anxiety Indicator", "status"),
    "Heart_Rate": ("Resting Heart Rate", "bpm"),
}

CONTEXT_CATEGORICAL = [
    "Female Education", "Husband Education", "Working Status",
    "Previous Miscarriage", "Sufficient Money for Basic Needs",
    "Family System", "Male Gender Preference", "Relationship with Mother in-law",
    "Gravida", "Physical Health ", "Current Appereance Acceptance",
]
CONTEXT_NUMERIC = ["Gestational Age", "Number of sons ", "Number of daughters", "Total Number of Children"]

CONTEXT_FEATURE_LABELS = {
    "Relationship with Mother in-law": ("Family relationship with in-laws", "level"),
    "Sufficient Money for Basic Needs": ("Money for basic needs", "status"),
    "Male Gender Preference": ("Pressure for boy child", "status"),
    "Previous Miscarriage": ("Past pregnancy loss", "status"),
    "Current Appereance Acceptance": ("Body changes acceptance", "level"),
    "Physical Health ": ("General physical health", "level"),
    "Female Education": ("Mother's education", "level"),
    "Husband Education": ("Husband's education", "level"),
    "Working Status": ("Employment status", "status"),
    "Family System": ("Family living setup", "type"),
    "Gravida": ("Number of pregnancies", "count"),
    "Gestational Age": ("Weeks of pregnancy", "weeks"),
    "Number of sons ": ("Number of sons", "count"),
    "Number of daughters": ("Number of daughters", "count"),
    "Total Number of Children": ("Total number of children", "count"),
    "Age": ("Mother's age", "years"),
}

# ── Lazy-loaded model & explainer caches ──────────────────────────────────────
_keras_model = None
_keras_scaler = None
_keras_explainer = None
_rf_model = None
_rf_encoder = None
_rf_scaler = None
_rf_explainer = None


def _get_keras_explainer():
    global _keras_model, _keras_scaler, _keras_explainer
    if _keras_explainer is None:
        if _keras_model is None:
            _keras_model = tf.keras.models.load_model(BASE_DIR / "keras_model_improved.keras")
        if _keras_scaler is None:
            _keras_scaler = joblib.load(BASE_DIR / "scaler_improved.pkl")

        # Representative baseline background (diverse representative physiological reference rows)
        bg_raw = np.array([
            [22, 110, 70, 5.0, 21.0, 0, 0, 0, 0, 72],
            [25, 120, 80, 5.5, 23.0, 0, 0, 0, 0, 76],
            [28, 125, 82, 6.0, 24.5, 0, 0, 0, 0, 78],
            [32, 135, 88, 7.5, 27.0, 1, 0, 0, 0, 82],
            [35, 150, 95, 9.0, 31.0, 1, 1, 0, 1, 88],
        ])
        bg_scaled = _keras_scaler.transform(bg_raw)

        def predict_fn(x):
            return _keras_model.predict(x, verbose=0).flatten()

        _keras_explainer = shap.KernelExplainer(predict_fn, bg_scaled)
        logger.info("Initialized Keras KernelExplainer with representative background.")
    return _keras_model, _keras_scaler, _keras_explainer


def _get_rf_explainer():
    global _rf_model, _rf_encoder, _rf_scaler, _rf_explainer
    if _rf_explainer is None:
        art_dir = BASE_DIR / "mental_health" / "artifacts"
        _rf_model = joblib.load(art_dir / "context_model_random_forest.pkl")
        _rf_encoder = joblib.load(art_dir / "context_encoder.pkl")
        _rf_scaler = joblib.load(art_dir / "context_num_scaler.pkl")
        _rf_explainer = shap.TreeExplainer(_rf_model)
        logger.info("Initialized Random Forest TreeExplainer.")
    return _rf_model, _rf_encoder, _rf_scaler, _rf_explainer


def explain_physical_vitals_prediction(
    inputs: Dict[str, Any],
    pred: int,
    prob: float
) -> ModelExplanationResponse:
    """
    Computes genuine SHAP values for the 10-feature Keras Maternal Physical Risk model.
    """
    _, scaler, explainer = _get_keras_explainer()

    # Form feature array in exact order
    raw_vals = [
        inputs.get("Age", 25),
        inputs.get("Systolic_BP", 120.0) if inputs.get("Systolic_BP") is not None else 120.0,
        inputs.get("Diastolic", 80.0) if inputs.get("Diastolic") is not None else 80.0,
        inputs.get("BS", 5.0) if inputs.get("BS") is not None else 5.0,
        inputs.get("BMI", 22.0) if inputs.get("BMI") is not None else 22.0,
        inputs.get("Previous_Complications", 0) or 0,
        inputs.get("Preexisting_Diabetes", 0) or 0,
        inputs.get("Gestational_Diabetes", 0) or 0,
        inputs.get("Mental_Health", 0) or 0,
        inputs.get("Heart_Rate", 75.0) if inputs.get("Heart_Rate") is not None else 75.0,
    ]
    raw_array = np.array([raw_vals])
    scaled_array = scaler.transform(raw_array)

    # Compute SHAP values with KernelExplainer
    shap_vals = explainer.shap_values(scaled_array, nsamples=60)
    if isinstance(shap_vals, list):
        # some versions return list for binary output
        shap_vector = np.array(shap_vals[0]).flatten()
    else:
        shap_vector = np.array(shap_vals).flatten()

    base_val = float(explainer.expected_value if not isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value[0])

    contributions: List[FeatureContribution] = []
    top_drivers: List[str] = []
    top_protective: List[str] = []

    for name, raw_v, s_val in zip(PHYSICAL_FEATURES, raw_vals, shap_vector):
        label, unit = PHYSICAL_FEATURE_LABELS.get(name, (name, ""))
        s_val_rounded = round(float(s_val), 4)

        if s_val_rounded > 0.015:
            direction = "increases_risk"
            interp = f"{label} ({raw_v} {unit}) pushed the prediction towards High Risk (+{s_val_rounded:.2f})."
            top_drivers.append(f"{label} ({raw_v} {unit})")
        elif s_val_rounded < -0.015:
            direction = "decreases_risk"
            interp = f"{label} ({raw_v} {unit}) acted as a protective indicator lowering risk ({s_val_rounded:.2f})."
            top_protective.append(f"{label} ({raw_v} {unit})")
        else:
            direction = "neutral"
            interp = f"{label} ({raw_v} {unit}) had minimal impact on the prediction score."

        contributions.append(
            FeatureContribution(
                feature_name=name,
                feature_label=label,
                observed_value=raw_v,
                unit=unit,
                shap_value=s_val_rounded,
                direction=direction,
                clinical_interpretation=interp,
            )
        )

    # Sort contributions by absolute SHAP magnitude
    contributions.sort(key=lambda c: abs(c.shap_value), reverse=True)

    return ModelExplanationResponse(
        model_name="Improved Keras Maternal Risk Classifier",
        model_version="v2_10feature_ann",
        prediction_class="High Risk" if pred == 1 else "Low Risk",
        prediction_score=round(float(prob), 4),
        base_value=round(base_val, 4),
        contributions_sum=round(float(np.sum(shap_vector)), 4),
        feature_contributions=contributions,
        top_risk_drivers=top_drivers[:3] if top_drivers else ["Vitals within normal limits"],
        top_protective_factors=top_protective[:3] if top_protective else ["Normal baseline indicators"],
        disclaimer=(
            "Note for ASHA Worker: This SHAP explanation shows which vital measurements influenced the AI model's "
            "risk calculation. It is a mathematical model explanation, not a clinical diagnosis or proof of biological causation. "
            "Always follow standard clinical referral protocols for elevated blood pressure or glucose."
        ),
        provenance="Computed via SHAP KernelExplainer with representative maternal baseline background.",
    )


def explain_contextual_mental_health_prediction(
    context_values: Dict[str, Any],
    age: float,
    prob: float
) -> ModelExplanationResponse:
    """
    Computes genuine SHAP values for the scikit-learn Contextual Mental Health Random Forest.
    """
    rf_model, encoder, scaler, explainer = _get_rf_explainer()

    cat_row = pd.DataFrame([[context_values[c] for c in CONTEXT_CATEGORICAL]], columns=CONTEXT_CATEGORICAL)
    cat_encoded = encoder.transform(cat_row)
    num_row = pd.DataFrame([[context_values[c] for c in CONTEXT_NUMERIC] + [age]], columns=CONTEXT_NUMERIC + ["Age"])
    num_scaled = scaler.transform(num_row)
    features = np.column_stack([cat_encoded, num_scaled])

    # TreeExplainer returns shape (n_samples, n_features, n_classes) or (n_samples, n_features)
    shap_vals = explainer.shap_values(features)
    if isinstance(shap_vals, list):
        # Class 1 is elevated depressive risk
        shap_vector = np.array(shap_vals[1])[0]
        base_val = float(explainer.expected_value[1])
    elif shap_vals.ndim == 3:
        shap_vector = shap_vals[0, :, 1]
        base_val = float(explainer.expected_value[1])
    else:
        shap_vector = shap_vals[0]
        base_val = float(explainer.expected_value)

    all_feature_names = list(encoder.get_feature_names_out(CONTEXT_CATEGORICAL)) + CONTEXT_NUMERIC + ["Age"]

    # Aggregate one-hot encoded categories back to their parent category for clear ASHA interpretation
    aggregated_shap: Dict[str, float] = {}
    observed_vals: Dict[str, Any] = {}

    for col in CONTEXT_CATEGORICAL:
        prefix = f"{col}_"
        matching_indices = [i for i, name in enumerate(all_feature_names) if name.startswith(prefix)]
        total_cat_shap = sum(shap_vector[i] for i in matching_indices)
        aggregated_shap[col] = total_cat_shap
        observed_vals[col] = context_values.get(col, "")

    for num_col in CONTEXT_NUMERIC:
        idx = all_feature_names.index(num_col)
        aggregated_shap[num_col] = float(shap_vector[idx])
        observed_vals[num_col] = context_values.get(num_col, 0)

    age_idx = all_feature_names.index("Age")
    aggregated_shap["Age"] = float(shap_vector[age_idx])
    observed_vals["Age"] = age

    contributions: List[FeatureContribution] = []
    top_drivers: List[str] = []
    top_protective: List[str] = []

    for name, s_val in aggregated_shap.items():
        label, unit = CONTEXT_FEATURE_LABELS.get(name, (name, ""))
        obs = observed_vals.get(name, "")
        s_val_rounded = round(float(s_val), 4)

        if s_val_rounded > 0.02:
            direction = "increases_risk"
            interp = f"{label} ({obs}) contributed to higher vulnerability likelihood (+{s_val_rounded:.2f})."
            top_drivers.append(f"{label} ({obs})")
        elif s_val_rounded < -0.02:
            direction = "decreases_risk"
            interp = f"{label} ({obs}) acted as a protective background factor ({s_val_rounded:.2f})."
            top_protective.append(f"{label} ({obs})")
        else:
            direction = "neutral"
            interp = f"{label} had neutral influence on the context estimate."

        contributions.append(
            FeatureContribution(
                feature_name=name,
                feature_label=label,
                observed_value=obs,
                unit=unit,
                shap_value=s_val_rounded,
                direction=direction,
                clinical_interpretation=interp,
            )
        )

    contributions.sort(key=lambda c: abs(c.shap_value), reverse=True)

    category = "Elevated" if prob >= 0.65 else ("Moderate" if prob >= 0.40 else "Low")

    return ModelExplanationResponse(
        model_name="Contextual Random Forest Vulnerability Classifier",
        model_version="context_rf_v1_periDep",
        prediction_class=f"{category} Vulnerability",
        prediction_score=round(float(prob), 4),
        base_value=round(base_val, 4),
        contributions_sum=round(float(sum(aggregated_shap.values())), 4),
        feature_contributions=contributions,
        top_risk_drivers=top_drivers[:3] if top_drivers else ["Favorable family and demographic indicators"],
        top_protective_factors=top_protective[:3] if top_protective else ["Stable social environment"],
        disclaimer=(
            "Note for ASHA Worker: This model explains cross-sectional vulnerability likelihood derived from "
            "sociodemographic and family background features. It is NOT a clinical diagnosis of depression and does NOT "
            "predict future postpartum depression onset. Diagnostic assessment must be conducted by a qualified doctor or psychologist."
        ),
        provenance="Computed via SHAP TreeExplainer from cross-validated Random Forest ensemble.",
    )
