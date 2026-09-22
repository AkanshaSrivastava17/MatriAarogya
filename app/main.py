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


@app.post("/predict")
async def predict(data: Union[PatientParams, List[PatientParams]]):
    if isinstance(data, PatientParams):
        data = [data]

    predictions = []
    prediction_labels = []
    
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

        append_captured_vitals(item, pred, label)
        
        predictions.append(pred)
        prediction_labels.append(label)
    
    return {
        "prediction": predictions,
        "prediction_label": prediction_labels,
    }

