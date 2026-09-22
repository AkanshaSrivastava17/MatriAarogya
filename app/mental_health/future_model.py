"""
future_model.py — Interface and specification for future/postpartum depression prediction.

SCIENTIFIC JUSTIFICATION & ARCHITECTURAL INTENT:
As documented in mental_health_architecture.md §2 and project specifications:
Both available training datasets (PERI_DEP/Pakistan ~14,000 rows and Dataset_1/Bangladesh ~800 rows)
are strictly CROSS-SECTIONAL. Neither dataset tracks patients longitudinally from prenatal checkups
through postpartum delivery with verified future clinical outcomes for the same individuals.

Consequently:
1. We DO NOT claim that the current contextual model predicts future postpartum depression.
2. We DO NOT fabricate artificial longitudinal outcomes or simulate postpartum labels.
3. We provide this explicit FutureRiskModel interface so that when genuine prospective
   longitudinal cohort data is collected and validated, a trained model can be plugged
   in seamlessly without altering the rest of the application or API contracts.
"""
from typing import Dict, List, Optional
from datetime import date


class FutureRiskModelInterface:
    """
    Standard interface for prospective postpartum risk prediction models.
    """
    MODEL_NAME = "ProspectivePostpartumPredictor"
    MODEL_VERSION = "unsupported_data_cross_sectional_only"

    def predict_future_risk(
        self,
        patient_id: int,
        current_gestational_age: Optional[int],
        delivery_date: Optional[date],
        longitudinal_history: List[Dict],
        current_vitals: Optional[Dict],
        current_context: Optional[Dict],
    ) -> Dict:
        """
        Evaluates whether a prospective prediction is scientifically supported.
        Currently returns available=False with clinical rationale.
        """
        return {
            "available": False,
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "reason": (
                "Current training datasets (PERI_DEP Pakistan, Dataset_1 Bangladesh) are cross-sectional "
                "and lack prospectively tracked pregnancy-to-postpartum outcomes for the same patients. "
                "Prospective prediction requires a validated prospective longitudinal cohort."
            ),
            "predicted_outcome": "postpartum_depression",
            "future_probability": None,
            "risk_category": None,
            "readiness_for_future_model": True,
        }


# Global singleton instance
future_risk_evaluator = FutureRiskModelInterface()
