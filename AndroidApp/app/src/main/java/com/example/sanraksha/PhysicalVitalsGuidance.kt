package com.example.sanraksha

/**
 * Clinical rules & guidance generator for frontline ASHA workers evaluating maternal physical vitals.
 * Aligned with National Health Mission (NHM) / Pradhan Mantri Surakshit Matritva Abhiyan (PMSMA) protocols.
 */
object PhysicalVitalsGuidance {

    fun evaluateFactorsAndActions(
        sys: Float?,
        dia: Float?,
        bs: Float?,
        bmi: Float?,
        prevComp: Int,
        preDiabetes: Int,
        gestDiabetes: Int,
        mentalHealth: Int,
        isHighRisk: Boolean
    ): Pair<List<String>, List<String>> {
        val factors = mutableListOf<String>()
        val actions = mutableListOf<String>()

        val s = sys ?: 120f
        val d = dia ?: 80f
        val b = bs ?: 5.0f
        val bodyMass = bmi ?: 22.0f

        // Blood Pressure
        if (s >= 160f || d >= 110f) {
            factors.add("Severe hypertension: BP ${s.toInt()}/${d.toInt()} mmHg (Stage 2 / Severe Preeclampsia danger threshold)")
            actions.add("🚨 Immediate Hospital Referral: Check urine albumin for pre-eclampsia. Initiate Magnesium Sulfate under MO supervision. Arrange 108 emergency transport.")
        } else if (s >= 140f || d >= 90f) {
            factors.add("Hypertension in pregnancy: BP ${s.toInt()}/${d.toInt()} mmHg (Stage 1)")
            actions.add("⚠️ Monitor BP bi-weekly. Advise left-lateral rest and low-sodium diet. Schedule urgent MO review.")
        } else if (s < 90f || d < 60f) {
            factors.add("Hypotension: BP ${s.toInt()}/${d.toInt()} mmHg")
            actions.add("• Increase fluid and oral rehydration intake. Assess for dehydration or bleeding.")
        } else {
            factors.add("Blood pressure within normal target range (${s.toInt()}/${d.toInt()} mmHg)")
        }

        // Blood Sugar
        if (b >= 11.1f) {
            factors.add("Severe hyperglycemia: Blood glucose $b mmol/L")
            actions.add("🚨 Urgent PHC/CHC referral for glycemic management and insulin evaluation.")
        } else if (b >= 7.8f) {
            factors.add("Elevated blood glucose: $b mmol/L")
            actions.add("⚠️ Advise dietary counseling: eliminate simple refined sugars. Schedule Oral Glucose Tolerance Test (OGTT).")
        }

        // BMI
        if (bodyMass < 18.5f) {
            factors.add("Maternal underweight: BMI $bodyMass kg/m²")
            actions.add("• Enroll mother immediately in Anganwadi Supplementary Nutrition Programme (take-home ration).")
            actions.add("• Verify daily adherence to double-dose Iron Folic Acid (IFA) and Calcium supplementation.")
        } else if (bodyMass >= 30.0f) {
            factors.add("Maternal obesity: BMI $bodyMass kg/m²")
            actions.add("• Monitor gestational weight gain closely; recommend 30 minutes of gentle daily walking.")
        }

        // Complications & Diabetes
        if (prevComp > 0) {
            factors.add("History of previous obstetric complications")
            actions.add("• Formulate High-Risk Pregnancy (HRP) Birth Preparedness Plan: Mandate delivery at First Referral Unit (FRU) / District Hospital.")
        }
        if (preDiabetes > 0 || gestDiabetes > 0) {
            factors.add("Active diabetic condition during pregnancy")
            actions.add("• Maintain strict daily glycemic log; coordinate with PHC Medical Officer.")
        }
        if (mentalHealth > 0) {
            factors.add("Indication of mental health concern")
            actions.add("• Conduct maternal PHQ-9 screening and provide psychosocial support.")
        }

        // Low risk default
        if (!isHighRisk && actions.isEmpty()) {
            actions.add("✓ Continue routine Antenatal Care (ANC) visits (ensure minimum 4 mandatory ANC checkups).")
            actions.add("✓ Ensure daily compliance with Iron Folic Acid (IFA) and Calcium tablets.")
            actions.add("✓ Educate mother and family on danger signs: severe headache, blurry vision, or reduced fetal movement.")
        }

        return Pair(factors, actions)
    }
}
