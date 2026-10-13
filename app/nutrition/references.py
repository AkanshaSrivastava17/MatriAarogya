"""
references.py — ICMR-NIN (2020) Dietary Guidelines & Nutrient Reference Standards for Indian Pregnant Women.

Authoritative Source:
- Indian Council of Medical Research (ICMR) & National Institute of Nutrition (NIN)
- "Recommended Dietary Allowances and Estimated Average Requirements for Indians" (2020 Report)
- Applicable Population: Adult Indian Women during Pregnancy and Lactation.
"""
from typing import Dict, Any, List

REFERENCE_METADATA = {
    "source": "ICMR-NIN (Indian Council of Medical Research - National Institute of Nutrition)",
    "publication_year": 2020,
    "guideline_title": "Nutrient Requirements for Indians: Recommended Dietary Allowances (RDA) and Estimated Average Requirements (EAR)",
    "target_population": "Adult Indian Women (18-45 years) across Pregnancy Trimesters and Lactation",
    "country": "India",
    "version": "ICMR-NIN-2020-v1.0"
}

# Baseline Sedentary Adult Female (Non-pregnant non-lactating):
# Energy: 1660 kcal/d, Protein: 46.0 g/d, Calcium: 1000 mg/d, Iron: 15 mg/d

NUTRIENT_REFERENCES_BY_STAGE: Dict[str, Dict[str, Dict[str, Any]]] = {
    "Trimester 1": {
        "energy_kcal": {
            "reference_value": 1660.0,
            "unit": "kcal/day",
            "type": "EAR",
            "label": "Daily Energy",
            "clinical_note": "No additional energy requirement in 1st trimester beyond basal 1660 kcal/day."
        },
        "protein_g": {
            "reference_value": 46.5,
            "unit": "g/day",
            "type": "RDA",
            "label": "Protein",
            "clinical_note": "+0.5 g/day additional protein in 1st trimester."
        },
        "fat_g": {
            "reference_value": 30.0,
            "unit": "g/day",
            "type": "RDA",
            "label": "Visible Fat",
            "clinical_note": "30 g/day visible fat requirement."
        },
        "fibre_g": {
            "reference_value": 25.0,
            "unit": "g/day",
            "type": "AI",
            "label": "Dietary Fibre",
            "clinical_note": "Adequate intake for gastrointestinal motility."
        },
        "iron_mg": {
            "reference_value": 27.0,
            "unit": "mg/day",
            "type": "RDA",
            "label": "Iron",
            "clinical_note": "Increased requirement (27 mg/day). Universal daily IFA tablet indicated."
        },
        "folate_mcg": {
            "reference_value": 570.0,
            "unit": "mcg/day",
            "type": "RDA",
            "label": "Folate / Folic Acid",
            "clinical_note": "Critical in 1st trimester to prevent neural tube defects."
        },
        "calcium_mg": {
            "reference_value": 1000.0,
            "unit": "mg/day",
            "type": "RDA",
            "label": "Calcium",
            "clinical_note": "Fetal skeletal development baseline."
        },
        "vitamin_d_iu": {
            "reference_value": 600.0,
            "unit": "IU/day",
            "type": "RDA",
            "label": "Vitamin D",
            "clinical_note": "15 mcg (600 IU) daily."
        },
        "vitamin_b12_mcg": {
            "reference_value": 2.2,
            "unit": "mcg/day",
            "type": "RDA",
            "label": "Vitamin B12",
            "clinical_note": "Essential for neurological and red blood cell development."
        }
    },
    "Trimester 2": {
        "energy_kcal": {
            "reference_value": 2010.0,
            "unit": "kcal/day",
            "type": "EAR",
            "label": "Daily Energy",
            "clinical_note": "+350 kcal/day extra energy for maternal and fetal tissue expansion."
        },
        "protein_g": {
            "reference_value": 55.5,
            "unit": "g/day",
            "type": "RDA",
            "label": "Protein",
            "clinical_note": "+9.5 g/day additional protein for rapid fetal growth."
        },
        "fat_g": {
            "reference_value": 30.0,
            "unit": "g/day",
            "type": "RDA",
            "label": "Visible Fat",
            "clinical_note": "30 g/day visible fat requirement."
        },
        "fibre_g": {
            "reference_value": 25.0,
            "unit": "g/day",
            "type": "AI",
            "label": "Dietary Fibre",
            "clinical_note": "Prevent pregnancy-related constipation."
        },
        "iron_mg": {
            "reference_value": 27.0,
            "unit": "mg/day",
            "type": "RDA",
            "label": "Iron",
            "clinical_note": "27 mg/day requirement. Continue daily IFA tablet."
        },
        "folate_mcg": {
            "reference_value": 570.0,
            "unit": "mcg/day",
            "type": "RDA",
            "label": "Folate",
            "clinical_note": "570 mcg/day RDA throughout pregnancy."
        },
        "calcium_mg": {
            "reference_value": 1000.0,
            "unit": "mg/day",
            "type": "RDA",
            "label": "Calcium",
            "clinical_note": "1000 mg/day RDA. Daily calcium supplementation from week 14."
        },
        "vitamin_d_iu": {
            "reference_value": 600.0,
            "unit": "IU/day",
            "type": "RDA",
            "label": "Vitamin D",
            "clinical_note": "600 IU/day."
        },
        "vitamin_b12_mcg": {
            "reference_value": 2.2,
            "unit": "mcg/day",
            "type": "RDA",
            "label": "Vitamin B12",
            "clinical_note": "2.2 mcg/day."
        }
    },
    "Trimester 3": {
        "energy_kcal": {
            "reference_value": 2010.0,
            "unit": "kcal/day",
            "type": "EAR",
            "label": "Daily Energy",
            "clinical_note": "+350 kcal/day extra energy."
        },
        "protein_g": {
            "reference_value": 68.0,
            "unit": "g/day",
            "type": "RDA",
            "label": "Protein",
            "clinical_note": "+22.0 g/day additional protein for peak fetal weight gain."
        },
        "fat_g": {
            "reference_value": 30.0,
            "unit": "g/day",
            "type": "RDA",
            "label": "Visible Fat",
            "clinical_note": "30 g/day."
        },
        "fibre_g": {
            "reference_value": 25.0,
            "unit": "g/day",
            "type": "AI",
            "label": "Dietary Fibre",
            "clinical_note": "25 g/day."
        },
        "iron_mg": {
            "reference_value": 27.0,
            "unit": "mg/day",
            "type": "RDA",
            "label": "Iron",
            "clinical_note": "27 mg/day."
        },
        "folate_mcg": {
            "reference_value": 570.0,
            "unit": "mcg/day",
            "type": "RDA",
            "label": "Folate",
            "clinical_note": "570 mcg/day."
        },
        "calcium_mg": {
            "reference_value": 1000.0,
            "unit": "mg/day",
            "type": "RDA",
            "label": "Calcium",
            "clinical_note": "Peak fetal bone mineralization."
        },
        "vitamin_d_iu": {
            "reference_value": 600.0,
            "unit": "IU/day",
            "type": "RDA",
            "label": "Vitamin D",
            "clinical_note": "600 IU/day."
        },
        "vitamin_b12_mcg": {
            "reference_value": 2.2,
            "unit": "mcg/day",
            "type": "RDA",
            "label": "Vitamin B12",
            "clinical_note": "2.2 mcg/day."
        }
    },
    "Postpartum": {
        "energy_kcal": {
            "reference_value": 2260.0,
            "unit": "kcal/day",
            "type": "EAR",
            "label": "Daily Energy",
            "clinical_note": "+600 kcal/day for lactation support (0-6 months postpartum)."
        },
        "protein_g": {
            "reference_value": 63.0,
            "unit": "g/day",
            "type": "RDA",
            "label": "Protein",
            "clinical_note": "+17.0 g/day additional protein for breast milk production."
        },
        "fat_g": {
            "reference_value": 30.0,
            "unit": "g/day",
            "type": "RDA",
            "label": "Visible Fat",
            "clinical_note": "30 g/day."
        },
        "fibre_g": {
            "reference_value": 25.0,
            "unit": "g/day",
            "type": "AI",
            "label": "Dietary Fibre",
            "clinical_note": "25 g/day."
        },
        "iron_mg": {
            "reference_value": 15.0,
            "unit": "mg/day",
            "type": "RDA",
            "label": "Iron",
            "clinical_note": "15 mg/day (lactation period)."
        },
        "folate_mcg": {
            "reference_value": 330.0,
            "unit": "mcg/day",
            "type": "RDA",
            "label": "Folate",
            "clinical_note": "330 mcg/day."
        },
        "calcium_mg": {
            "reference_value": 1200.0,
            "unit": "mg/day",
            "type": "RDA",
            "label": "Calcium",
            "clinical_note": "Increased to 1200 mg/day for breast milk calcium secretion."
        },
        "vitamin_d_iu": {
            "reference_value": 600.0,
            "unit": "IU/day",
            "type": "RDA",
            "label": "Vitamin D",
            "clinical_note": "600 IU/day."
        },
        "vitamin_b12_mcg": {
            "reference_value": 3.2,
            "unit": "mcg/day",
            "type": "RDA",
            "label": "Vitamin B12",
            "clinical_note": "Increased to 3.2 mcg/day."
        }
    }
}

# Gestational Weight Gain Reference Guidelines (IOM/WHO adapted for South Asian women)
# Total recommended gestational weight gain by pre-pregnancy BMI category
WEIGHT_GAIN_GUIDELINES = {
    "underweight": {
        "pre_bmi_range": "< 18.5",
        "total_gain_min_kg": 12.5,
        "total_gain_max_kg": 18.0,
        "weekly_rate_kg": 0.51,
        "guidance": "Mother is underweight. Requires nutrient-dense diet and take-home Anganwadi ration (poshahar)."
    },
    "normal": {
        "pre_bmi_range": "18.5 - 24.9",
        "total_gain_min_kg": 11.5,
        "total_gain_max_kg": 16.0,
        "weekly_rate_kg": 0.42,
        "guidance": "Healthy pre-pregnancy weight. Maintain steady, balanced weekly weight gain."
    },
    "overweight": {
        "pre_bmi_range": "25.0 - 29.9",
        "total_gain_min_kg": 7.0,
        "total_gain_max_kg": 11.5,
        "weekly_rate_kg": 0.28,
        "guidance": "Overweight pre-pregnancy. Advise gentle daily physical activity and avoidance of fried/sugary foods."
    },
    "obese": {
        "pre_bmi_range": ">= 30.0",
        "total_gain_min_kg": 5.0,
        "total_gain_max_kg": 9.0,
        "weekly_rate_kg": 0.22,
        "guidance": "High weight. Monitor blood pressure and blood sugar closely at clinic."
    }
}

# Culturally Appropriate Indian Food Alternatives by Deficiency
CULTURAL_FOOD_SUGGESTIONS = {
    "protein": [
        "Include 2 katori thick dal or rajma/chole daily in meals.",
        "Add roasted chana (gram) and roasted peanuts (mungphali) for healthy snacks.",
        "Consume 1 glass of milk or 1 katori curd/chaas (buttermilk) every day.",
        "If non-vegetarian or eggetarian, include 1 boiled egg daily or well-cooked fish/poultry.",
        "Incorporate soybean granules or paneer into vegetables."
    ],
    "iron": [
        "Eat green leafy vegetables (palak, methi, sarson, bathua, drumstick/moringa leaves) 3-4 times a week.",
        "Take roasted chana with a small piece of jaggery (gur) after meals.",
        "Take 1 red Iron-Folic Acid (IFA) tablet daily with lemon water or plain water (never with tea or milk).",
        "Eat seasonal iron-rich fruits: amla, guava, pomegranate (anar), dates (khajoor)."
    ],
    "calcium": [
        "Drink 1-2 glasses of boiled milk, chaas, or eat curd daily.",
        "Incorporate ragi (finger millet / nachni) porridge, roti, or dosa in weekly diet.",
        "Sprinkle roasted sesame seeds (til) on food or eat til laddu.",
        "Take 1 Calcium-Vitamin D tablet daily, spaced at least 2 hours apart from the iron tablet."
    ],
    "energy": [
        "Ensure at least 3 wholesome meals and 2 nutritious snacks every day.",
        "Add 1 teaspoon of ghee or oil to meals for concentrated healthy energy.",
        "Enroll at the local Anganwadi centre for daily Take-Home Ration (THR / Poshahar).",
        "Eat wholesome khichdi enriched with vegetables, dal, and peanuts."
    ],
    "folate": [
        "Eat green leafy vegetables, beans, and oranges/citrus fruits regularly.",
        "Ensure daily IFA supplementation as prescribed by the ANM/doctor."
    ],
    "fibre": [
        "Use whole wheat flour with bran, whole dal with husk, and fresh vegetables to prevent constipation.",
        "Drink at least 8 to 10 glasses of clean, boiled or filtered water daily."
    ]
}
