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


app = FastAPI()

from app.mental_health.router import router as mental_health_router
app.include_router(mental_health_router)

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

    # 1. Contributing Biomarker & Obstetric Factors
    if sbp >= 140 or dbp >= 90:
        factors.append(f"High Blood Pressure ({int(sbp)}/{int(dbp)} mmHg) - Stage 2 Hypertension / Pre-eclampsia Risk")
    elif sbp >= 130 or dbp >= 85:
        factors.append(f"Elevated Blood Pressure ({int(sbp)}/{int(dbp)} mmHg) - Pre-hypertensive")

    if bs >= 7.8:
        factors.append(f"Elevated Blood Glucose ({bs:.1f} mmol/L) - Gestational Hyperglycemia")
    elif bs < 3.5:
        factors.append(f"Low Blood Glucose ({bs:.1f} mmol/L) - Hypoglycemia Risk")

    if prev_comp > 0:
        factors.append("History of Prior Pregnancy Complications / High-Risk Obstetric History")

    if pre_diab > 0 or gest_diab > 0:
        factors.append("Documented Pre-existing or Gestational Diabetes")

    if bmi >= 30.0:
        factors.append(f"Elevated BMI ({bmi:.1f}) - Maternal Obesity (Thromboembolism & Macrosomia risk)")
    elif bmi < 18.5:
        factors.append(f"Low BMI ({bmi:.1f}) - Underweight (Intrauterine Growth Restriction risk)")

    if hr > 100:
        factors.append(f"Elevated Heart Rate ({int(hr)} bpm) - Maternal Tachycardia")
    elif hr < 60:
        factors.append(f"Low Heart Rate ({int(hr)} bpm) - Bradycardia")

    if age > 35:
        factors.append(f"Advanced Maternal Age ({age} years)")
    elif age < 18:
        factors.append(f"Adolescent Pregnancy ({age} years)")

    if mh > 0:
        factors.append("Co-occurring Maternal Psychological / Emotional Distress")

    if not factors:
        factors.append("All primary vitals within standard clinical baseline ranges")

    # 2. Protocolized Actionable Guidance for ASHA Workers
    if pred == 1 or sbp >= 140 or dbp >= 90:
        actions.append("🚨 Check urine for albumin/protein immediately at Sub-Centre/PHC to screen for Pre-eclampsia.")
        actions.append("🚨 Arrange prompt referral to Medical Officer at PHC/CHC within 24 hours.")
        actions.append("• Advise patient on left-lateral resting position and low-sodium diet; recheck BP within 24 hours.")
        actions.append("• Ensure family is pre-registered with 108/102 Emergency Ambulance for institutional delivery.")

    if bs >= 7.8 or pre_diab > 0 or gest_diab > 0:
        actions.append("• Schedule Fasting & Postprandial Oral Glucose Tolerance Test (OGTT) at the PHC lab.")
        actions.append("• Provide dietary counseling: avoid simple refined sugars, increase dietary fiber and green leafy vegetables.")

    if bmi < 18.5:
        actions.append("• Enroll mother immediately in Anganwadi Supplementary Nutrition Programme (take-home ration).")
        actions.append("• Verify daily adherence to double-dose Iron Folic Acid (IFA) and Calcium supplementation.")
    elif bmi >= 30.0:
        actions.append("• Monitor gestational weight gain carefully; advise 30 minutes of gentle daily walking.")

    if prev_comp > 0:
        actions.append("• Formulate High-Risk Pregnancy (HRP) Birth Preparedness Plan: Mandate delivery at First Referral Unit (FRU) / District Hospital.")

    if mh > 0:
        actions.append("• Screen for perinatal mood changes using PHQ-9 and offer supportive counseling.")

    if pred == 0 and len(actions) == 0:
        actions.append("• Continue routine Antenatal Care (ANC) visits (ensure minimum 4 mandatory ANC checkups).")
        actions.append("• Ensure daily compliance with Iron Folic Acid (IFA) and Calcium tablets after first trimester.")
        actions.append("• Educate family on danger signs: severe headache, blurry vision, epigastric pain, or reduced fetal movement.")

    return factors, actions


@app.post("/predict")
async def predict(data: Union[PatientParams, List[PatientParams]]):
    if isinstance(data, PatientParams):
        data = [data]

    predictions = []
    prediction_labels = []
    all_contributing_factors = []
    all_actionable_guidance = []

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
        prob = keras_model.predict(features_scaled, verbose=0)[0, 0]
        pred = 1 if prob > 0.5 else 0
        label = RISK_LABELS.get(pred, "Unknown")

        factors, actions = explain_physical_vitals_risk(item, pred, label)

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
    }


