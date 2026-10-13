"""
service.py — Maternal Diet and Nutrition Assessment Service.

Evaluates reported nutrient intakes and anthropometrics against ICMR-NIN (2020)
Recommended Dietary Allowances and Gestational Weight Gain reference ranges.
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime

from .references import (
    NUTRIENT_REFERENCES_BY_STAGE,
    REFERENCE_METADATA,
    WEIGHT_GAIN_GUIDELINES,
    CULTURAL_FOOD_SUGGESTIONS,
)
from .schemas import (
    CreateNutritionAssessmentRequest,
    NutrientComparisonResult,
    WeightProgressionResult,
    NutritionEvaluationResponse,
)
from app.mental_health import store


def determine_trimester(gestational_age: Optional[int], trimester_str: Optional[str]) -> str:
    if trimester_str and trimester_str in NUTRIENT_REFERENCES_BY_STAGE:
        return trimester_str
    if gestational_age is None:
        return "Trimester 2"  # conservative default
    if gestational_age <= 12:
        return "Trimester 1"
    elif gestational_age <= 27:
        return "Trimester 2"
    elif gestational_age <= 42:
        return "Trimester 3"
    else:
        return "Postpartum"


def compute_bmi(weight_kg: Optional[float], height_cm: Optional[float]) -> Optional[float]:
    if weight_kg and height_cm and height_cm > 50:
        height_m = height_cm / 100.0
        return round(weight_kg / (height_m * height_m), 1)
    return None


def categorize_bmi(bmi: Optional[float]) -> Optional[str]:
    if bmi is None:
        return None
    if bmi < 18.5:
        return "underweight"
    elif bmi < 25.0:
        return "normal"
    elif bmi < 30.0:
        return "overweight"
    else:
        return "obese"


def evaluate_weight_progression(
    height_cm: Optional[float],
    current_weight_kg: Optional[float],
    pre_pregnancy_weight_kg: Optional[float],
    gestational_age: Optional[int],
    trimester: str
) -> WeightProgressionResult:
    current_bmi = compute_bmi(current_weight_kg, height_cm)
    current_cat = categorize_bmi(current_bmi)
    pre_bmi = compute_bmi(pre_pregnancy_weight_kg, height_cm)
    pre_cat = categorize_bmi(pre_bmi)
    
    gain_kg = None
    if current_weight_kg and pre_pregnancy_weight_kg:
        gain_kg = round(current_weight_kg - pre_pregnancy_weight_kg, 1)

    recommended_gain_range = None
    weight_trend_status = "insufficient_data"
    guidance = "Monitor weight monthly at the Anganwadi / PHC checkup."

    if pre_cat and pre_cat in WEIGHT_GAIN_GUIDELINES:
        guide = WEIGHT_GAIN_GUIDELINES[pre_cat]
        recommended_gain_range = f"{guide['total_gain_min_kg']} - {guide['total_gain_max_kg']} kg"
        
        if gain_kg is not None and gestational_age is not None:
            # Expected gain up to current gestational week
            if gestational_age <= 12:
                # 1st trimester expected total gain: 0.5 - 2.0 kg
                if gain_kg < -1.0:
                    weight_trend_status = "low_gain"
                    guidance = "Weight loss in 1st trimester. Check for severe morning sickness (hyperemesis)."
                elif gain_kg > 4.0:
                    weight_trend_status = "excessive_gain"
                    guidance = "Rapid early weight gain. Screen for fluid retention and blood sugar."
                else:
                    weight_trend_status = "on_track"
                    guidance = "Early pregnancy weight gain is normal and healthy."
            else:
                weeks_in_t2_t3 = gestational_age - 12
                expected_gain = 1.0 + (weeks_in_t2_t3 * guide["weekly_rate_kg"])
                lower_bound = max(0.0, expected_gain - 2.5)
                upper_bound = expected_gain + 3.0
                
                if gain_kg < lower_bound:
                    weight_trend_status = "low_gain"
                    guidance = f"Weight gain ({gain_kg} kg) is below expected curve for week {gestational_age}. Needs nutritious take-home ration (poshahar) and protein-rich foods."
                elif gain_kg > upper_bound:
                    weight_trend_status = "excessive_gain"
                    guidance = f"Weight gain ({gain_kg} kg) is higher than expected. Check blood pressure and screen for edema/fits risk."
                else:
                    weight_trend_status = "on_track"
                    guidance = f"Steady gestational weight gain ({gain_kg} kg) is within healthy reference target."
    elif current_cat == "underweight":
        guidance = "Mother is currently underweight. Provide extra take-home ration and daily IFA tablet."
    elif current_cat in ["overweight", "obese"]:
        guidance = "Mother has high body weight. Encourage balanced home meals and gentle 30-minute daily walking."

    return WeightProgressionResult(
        height_cm=height_cm,
        current_weight_kg=current_weight_kg,
        current_bmi=current_bmi,
        current_bmi_category=current_cat,
        pre_pregnancy_weight_kg=pre_pregnancy_weight_kg,
        pre_pregnancy_bmi=pre_bmi,
        pre_pregnancy_bmi_category=pre_cat,
        gestational_weight_gain_kg=gain_kg,
        recommended_gain_range=recommended_gain_range,
        weight_trend_status=weight_trend_status,
        guidance=guidance,
    )


def evaluate_nutrition_assessment(
    req: CreateNutritionAssessmentRequest,
    persist: bool = True
) -> NutritionEvaluationResponse:
    stage = determine_trimester(req.gestational_age, req.trimester)
    ref_dict = NUTRIENT_REFERENCES_BY_STAGE.get(stage, NUTRIENT_REFERENCES_BY_STAGE["Trimester 2"])
    
    intake_data = req.intake.model_dump()
    comparisons: List[NutrientComparisonResult] = []
    gaps: List[str] = []
    unassessed: List[str] = []
    recommendations: List[str] = []

    for nutrient_key, ref_info in ref_dict.items():
        val = intake_data.get(nutrient_key)
        ref_val = ref_info["reference_value"]
        unit = ref_info["unit"]
        ref_type = ref_info["type"]
        label = ref_info["label"]

        if val is None:
            unassessed.append(label)
            comparisons.append(
                NutrientComparisonResult(
                    nutrient=nutrient_key,
                    label=label,
                    reported_value=None,
                    reference_value=ref_val,
                    unit=unit,
                    reference_type=ref_type,
                    status="not_assessed",
                    percent_of_reference=None,
                    difference=None,
                    explanation=f"{label} was not assessed during this visit."
                )
            )
            continue

        pct = round((val / ref_val) * 100.0, 1)
        diff = round(val - ref_val, 1)

        if pct < 70.0:
            status = "severely_below"
            expl = f"{label} intake ({val} {unit}) is severely below the ICMR-NIN reference ({ref_val} {unit}, {pct}% of requirement)."
            gaps.append(f"Severe deficiency in {label} ({pct}% of requirement)")
        elif pct < 90.0:
            status = "moderately_below"
            expl = f"{label} intake ({val} {unit}) is slightly below the reference ({ref_val} {unit}, {pct}% of requirement)."
            gaps.append(f"Moderate gap in {label} ({pct}% of requirement)")
        elif pct <= 130.0:
            status = "adequate"
            expl = f"{label} intake ({val} {unit}) meets the ICMR-NIN reference ({pct}% of requirement)."
        else:
            status = "above"
            expl = f"{label} intake ({val} {unit}) exceeds daily reference requirement ({pct}%)."

        comparisons.append(
            NutrientComparisonResult(
                nutrient=nutrient_key,
                label=label,
                reported_value=val,
                reference_value=ref_val,
                unit=unit,
                reference_type=ref_type,
                status=status,
                percent_of_reference=pct,
                difference=diff,
                explanation=expl,
            )
        )

    # Anthropometrics
    weight_progression = evaluate_weight_progression(
        height_cm=req.height_cm,
        current_weight_kg=req.current_weight_kg,
        pre_pregnancy_weight_kg=req.pre_pregnancy_weight_kg,
        gestational_age=req.gestational_age,
        trimester=stage
    )

    # Generate Culturally Appropriate Action Recommendations
    # Protein guidance
    prot_comp = next((c for c in comparisons if c.nutrient == "protein_g"), None)
    if prot_comp and prot_comp.status in ["severely_below", "moderately_below"]:
        recommendations.append("🍗 Protein Boost: " + CULTURAL_FOOD_SUGGESTIONS["protein"][0])
        recommendations.append("🥜 Snack Option: " + CULTURAL_FOOD_SUGGESTIONS["protein"][1])
        if req.dietary_pattern in ["non_vegetarian", "eggetarian"]:
            recommendations.append("🥚 " + CULTURAL_FOOD_SUGGESTIONS["protein"][3])

    # Iron & Folate guidance
    iron_comp = next((c for c in comparisons if c.nutrient == "iron_mg"), None)
    if iron_comp and iron_comp.status in ["severely_below", "moderately_below"]:
        recommendations.append("🥬 Green Veggies: " + CULTURAL_FOOD_SUGGESTIONS["iron"][0])
        recommendations.append("🍬 Jaggery & Chana: " + CULTURAL_FOOD_SUGGESTIONS["iron"][1])
        recommendations.append("💊 IFA Tablet: " + CULTURAL_FOOD_SUGGESTIONS["iron"][2])

    # Calcium guidance
    calc_comp = next((c for c in comparisons if c.nutrient == "calcium_mg"), None)
    if calc_comp and calc_comp.status in ["severely_below", "moderately_below"]:
        recommendations.append("🥛 Dairy Intake: " + CULTURAL_FOOD_SUGGESTIONS["calcium"][0])
        recommendations.append("🌾 Millet (Ragi): " + CULTURAL_FOOD_SUGGESTIONS["calcium"][1])

    # Food Insecurity & Anganwadi linkage
    if req.food_insecurity:
        recommendations.append("🍲 Anganwadi Support: Mother reports food affordability or access difficulty. Immediately register family for Take-Home Ration (Poshahar) and PMMVY maternity cash benefit.")

    # Appetite difficulties
    if req.appetite_difficulty in ["nausea_vomiting", "poor"]:
        recommendations.append("🥣 Small Frequent Meals: Advise eating 5-6 small light meals rather than 2 large heavy meals. Avoid empty stomach; take dry crackers or roasted chana in the morning.")

    if not recommendations:
        recommendations.append("✓ Maintain Current Balanced Diet: Reported dietary intake meets the ICMR-NIN pregnancy reference standard. Continue daily IFA and calcium supplementation.")

    assessment_id = None
    assessment_date_str = req.assessment_date.isoformat() if req.assessment_date else datetime.now().date().isoformat()

    if persist:
        db_payload = {
            "patient_id": req.patient_id,
            "visit_id": req.visit_id,
            "assessment_date": assessment_date_str,
            "gestational_age": req.gestational_age,
            "trimester": stage,
            "height_cm": req.height_cm,
            "current_weight_kg": req.current_weight_kg,
            "pre_pregnancy_weight_kg": req.pre_pregnancy_weight_kg,
            "current_bmi": weight_progression.current_bmi,
            "pre_pregnancy_bmi": weight_progression.pre_pregnancy_bmi,
            "energy_kcal": intake_data.get("energy_kcal"),
            "carbohydrates_g": intake_data.get("carbohydrates_g"),
            "protein_g": intake_data.get("protein_g"),
            "fat_g": intake_data.get("fat_g"),
            "fibre_g": intake_data.get("fibre_g"),
            "iron_mg": intake_data.get("iron_mg"),
            "folate_mcg": intake_data.get("folate_mcg"),
            "calcium_mg": intake_data.get("calcium_mg"),
            "vitamin_d_iu": intake_data.get("vitamin_d_iu"),
            "vitamin_b12_mcg": intake_data.get("vitamin_b12_mcg"),
            "dietary_pattern": req.dietary_pattern,
            "food_restrictions": req.food_restrictions,
            "appetite_difficulty": req.appetite_difficulty,
            "food_insecurity": req.food_insecurity,
            "supplements_taken": req.supplements_taken,
            "assessment_completeness": req.assessment_completeness,
            "gaps": gaps,
            "recommendations": recommendations,
            "notes": req.notes,
        }
        assessment_id = store.save_nutrition_assessment(db_payload)

    return NutritionEvaluationResponse(
        assessment_id=assessment_id,
        patient_id=req.patient_id,
        visit_id=req.visit_id,
        assessment_date=assessment_date_str,
        trimester=stage,
        gestational_age=req.gestational_age,
        completeness=req.assessment_completeness,
        weight_progression=weight_progression,
        nutrient_comparisons=comparisons,
        gaps=gaps,
        recommendations=recommendations,
        unassessed_nutrients=unassessed,
        food_security_flag=req.food_insecurity,
        reference_source=REFERENCE_METADATA["source"],
        reference_version=REFERENCE_METADATA["version"],
        scientific_disclaimer=(
            "Note for ASHA Worker & Clinical Team: Nutritional screening estimates dietary intake against "
            "ICMR-NIN (2020) reference standards. This is a supportive screening aid, not a clinical diagnosis "
            "of malnutrition or biochemical deficiency. Consult ANM/MO for suspected anemia or clinical symptoms."
        ),
    )
