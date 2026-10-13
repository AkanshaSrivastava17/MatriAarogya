from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Union
from pathlib import Path
from datetime import datetime
import joblib
import pandas as pd
import numpy as np
import tensorflow as tf


# Update these labels if your training label encoding changes.
RISK_LABELS = {
    0: "Low Risk",
    1: "High Risk",
}

print("Loading IMPROVED Keras model (98.73% accuracy)...")

# Load the improved Keras model (98.73% accuracy)
try:
    keras_model = tf.keras.models.load_model("app/keras_model_improved.keras")
    print("[OK] Improved Keras model loaded (98.73% accuracy)")
except Exception as e:
    print(f"[ERROR] Error loading improved Keras model: {e}")
    keras_model = None

# Load the improved StandardScaler (for 10 features)
try:
    scaler = joblib.load("app/scaler_improved.pkl")
    print("[OK] Improved StandardScaler loaded (10 features)")
except Exception as e:
    print(f"[ERROR] Error loading improved scaler: {e}")
    scaler = None


class PatientParams(BaseModel):
    Age: int
    Systolic_BP: float = None
    Diastolic: float = None
    BS: float = None
    Body_Temp: float = None
    BMI: float
    Previous_Complications: int = None
    Preexisting_Diabetes: int = None
    Gestational_Diabetes: int = None
    Mental_Health: int = None
    Heart_Rate: float = None
    state: str = None


app = FastAPI(title="SanRaksha Maternal Health Intelligence API", version="2.0.0")

from app.mental_health.router import router as mental_health_router
from app.nutrition.router import router as nutrition_router
from app.immunization.router import router as immunization_router
from app.explainability.router import router as explainability_router
from app.guidance.router import router as guidance_router
from app.analytics.router import router as analytics_router
from app.summary.router import router as summary_router

app.include_router(mental_health_router)
app.include_router(nutrition_router)
app.include_router(immunization_router)
app.include_router(explainability_router)
app.include_router(guidance_router)
app.include_router(analytics_router)
app.include_router(summary_router)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
CAPTURED_VITALS_PATH = PROJECT_ROOT / "data" / "captured_vitals.csv"


def append_captured_vitals(item: PatientParams, prediction: int, label: str) -> None:
    """Persist a captured app submission so the dashboard can read it later."""
    payload = item.model_dump() if hasattr(item, "model_dump") else item.dict()
    row = {
        **payload,
        "prediction": prediction,
        "prediction_label": label,
        "captured_at": datetime.now().isoformat(),
        "source": "android_app",
    }

    CAPTURED_VITALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CAPTURED_VITALS_PATH.exists():
        existing = pd.read_csv(CAPTURED_VITALS_PATH)
        updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
    else:
        updated = pd.DataFrame([row])

    updated.to_csv(CAPTURED_VITALS_PATH, index=False)


@app.get("/")
async def root():
    return {"message": "Hello World"}


def explain_physical_vitals_risk(item: PatientParams, pred: int, label: str):
    factors = []
    actions = []

    sbp = item.Systolic_BP if item.Systolic_BP is not None else 120.0
    dbp = item.Diastolic if item.Diastolic is not None else 80.0
    bs = item.BS if item.BS is not None else 5.0
    hr = item.Heart_Rate if item.Heart_Rate is not None else 75.0
    bmi = item.BMI if item.BMI is not None else 22.0
    age = item.Age
    prev_comp = item.Previous_Complications or 0
    pre_diab = item.Preexisting_Diabetes or 0
    gest_diab = item.Gestational_Diabetes or 0
    mh = item.Mental_Health or 0

    # 1. Contributing Biomarker & Obstetric Factors (Simple Language for ASHA Workers)
    if sbp >= 160 or dbp >= 110:
        factors.append(f"Dangerously High Blood Pressure ({int(sbp)}/{int(dbp)} mmHg) - Risk of swelling and fits")
    elif sbp >= 140 or dbp >= 90:
        factors.append(f"High Blood Pressure ({int(sbp)}/{int(dbp)} mmHg) - Needs regular monitoring")
    elif sbp >= 130 or dbp >= 85:
        factors.append(f"Slightly Elevated Blood Pressure ({int(sbp)}/{int(dbp)} mmHg)")

    if bs >= 11.1:
        factors.append(f"Very High Blood Sugar ({bs:.1f} mmol/L)")
    elif bs >= 7.8:
        factors.append(f"High Blood Sugar ({bs:.1f} mmol/L)")
    elif bs < 3.5:
        factors.append(f"Low Blood Sugar ({bs:.1f} mmol/L) - Feeling weak or dizzy")

    if prev_comp > 0:
        factors.append("Trouble in Past Pregnancy (History of past delivery complications)")

    if pre_diab > 0 or gest_diab > 0:
        factors.append("Sugar / Diabetes Problem during pregnancy")

    if bmi >= 30.0:
        factors.append(f"Mother is Overweight (High weight: BMI {bmi:.1f})")
    elif bmi < 18.5:
        factors.append(f"Mother is Underweight (Low weight: BMI {bmi:.1f})")

    if hr > 100:
        factors.append(f"Fast Heart Rate ({int(hr)} bpm)")
    elif hr < 60:
        factors.append(f"Slow Heart Rate ({int(hr)} bpm)")

    if age > 35:
        factors.append(f"Mother's Age ({age} years) - Needs extra care")
    elif age < 18:
        factors.append(f"Very Young Mother ({age} years) - Needs extra care")

    if mh > 0:
        factors.append("Feeling Very Sad, Worried, or Anxious")

    if not factors:
        factors.append("All measured vitals look healthy and normal")

    # 2. Simple Actionable Steps for Frontline ASHA Workers
    if sbp >= 160 or dbp >= 110:
        actions.append("🚨 Check urine for protein at the clinic today to check for swelling and fits risk.")
        actions.append("🚨 Take mother to the hospital / PHC doctor within 24 hours without delay.")
        actions.append("• Ask mother to sleep on her left side and use less salt in food.")
        actions.append("• Save 108 ambulance number on the family phone for quick hospital transport.")
    elif pred == 1 or sbp >= 140 or dbp >= 90:
        actions.append("⚠️ Re-check BP in 2 days. Tell mother to alert you if she has severe headache, blurred vision, or upper stomach pain.")
        actions.append("• Bring mother to the doctor on the 9th of the month (PMSMA checkup day).")
        actions.append("• Ask mother to sleep on her left side, use less salt, and rest well.")

    if bs >= 11.1:
        actions.append("🚨 Urgent: Take mother to the PHC / hospital doctor for sugar medicine and tests.")
    elif bs >= 7.8 or pre_diab > 0 or gest_diab > 0:
        actions.append("• Take mother to the PHC lab in the morning without breakfast for a sugar test (OGTT).")
        actions.append("• Tell mother to stop sweets and sugar in tea. Eat more green vegetables, dal, and roti.")

    if bmi < 18.5:
        actions.append("• Register mother for extra Anganwadi ration (take-home food / poshahar).")
        actions.append("• Make sure she takes her red iron tablet (IFA) and calcium tablet daily.")
    elif bmi >= 30.0:
        actions.append("• Track mother's weight every month. Encourage a gentle 30-minute daily walk.")

    if prev_comp > 0:
        actions.append("• Mark as High-Risk Pregnancy. Plan delivery at the District Hospital or CHC (not at home).")

    if mh > 0:
        actions.append("• Talk kindly with the mother. Use the 9-question mental health screen to check how she is feeling.")

    if pred == 0 and len(actions) == 0:
        actions.append("✓ Continue regular monthly checkups (ensure at least 4 clinic visits before delivery).")
        actions.append("✓ Ensure mother takes 1 red iron tablet (IFA) and 1 calcium tablet daily after meals.")
        actions.append("✓ Teach family the danger signs: bleeding, severe headache, blurred vision, or baby moving less.")

    return factors, actions


@app.post("/predict")
async def predict(data: Union[PatientParams, List[PatientParams]]):
    if isinstance(data, PatientParams):
        data = [data]

    predictions = []
    prediction_labels = []
    all_contributing_factors = []
    all_actionable_guidance = []
    all_shap_explanations = []

    for item in data:
        # Create feature vector with 10 features (Body Temp removed)
        # Order: Age, Systolic BP, Diastolic, BS, BMI, Previous Complications,
        #        Preexisting Diabetes, Gestational Diabetes, Mental Health, Heart Rate

        features = [
            item.Age,
            item.Systolic_BP if item.Systolic_BP is not None else 120.0,
            item.Diastolic if item.Diastolic is not None else 80.0,
            item.BS if item.BS is not None else 5.0,
            item.BMI,
            item.Previous_Complications if item.Previous_Complications is not None else 0,
            item.Preexisting_Diabetes if item.Preexisting_Diabetes is not None else 0,
            item.Gestational_Diabetes if item.Gestational_Diabetes is not None else 0,
            item.Mental_Health if item.Mental_Health is not None else 0,
            item.Heart_Rate if item.Heart_Rate is not None else 75.0,
        ]

        # Scale features using the improved scaler
        features_array = np.array(features).reshape(1, -1)
        features_scaled = scaler.transform(features_array)

        # Get prediction from improved Keras model
        prob = float(keras_model.predict(features_scaled, verbose=0)[0, 0])
        pred = 1 if prob > 0.5 else 0
        label = RISK_LABELS.get(pred, "Unknown")

        factors, actions = explain_physical_vitals_risk(item, pred, label)

        # Compute genuine instance-level SHAP explanation
        try:
            from app.explainability.shap_service import explain_physical_vitals_prediction
            payload = item.model_dump() if hasattr(item, "model_dump") else item.dict()
            shap_res = explain_physical_vitals_prediction(payload, pred, prob)
            all_shap_explanations.append(shap_res.model_dump())
        except Exception as e:
            all_shap_explanations.append(None)

        append_captured_vitals(item, pred, label)

        predictions.append(pred)
        prediction_labels.append(label)
        all_contributing_factors.append(factors)
        all_actionable_guidance.append(actions)

    return {
        "prediction": predictions,
        "prediction_label": prediction_labels,
        "contributing_factors": all_contributing_factors,
        "actionable_guidance": all_actionable_guidance,
        "shap_explanations": all_shap_explanations,
    }


