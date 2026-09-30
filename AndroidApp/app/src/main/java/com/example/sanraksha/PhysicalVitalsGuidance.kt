package com.example.sanraksha

/**
 * Clinical rules & guidance generator for frontline ASHA workers evaluating maternal physical vitals.
 * Aligned with National Health Mission (NHM) / Pradhan Mantri Surakshit Matritva Abhiyan (PMSMA) protocols.
 * Formatted in clear, simple language easily understood by frontline ASHA workers.
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
        isHighRisk: Boolean,
        age: Int? = null,
        heartRate: Float? = null
    ): Pair<List<String>, List<String>> {
        val factors = mutableListOf<String>()
        val actions = mutableListOf<String>()

        val s = sys ?: 120f
        val d = dia ?: 80f
        val b = bs ?: 5.0f
        val bodyMass = bmi ?: 22.0f

        // 1. Contributing Factors (Simple Language for ASHA Workers)
        if (s >= 160f || d >= 110f) {
            factors.add("Dangerously High Blood Pressure (${s.toInt()}/${d.toInt()} mmHg) - Risk of swelling and fits")
        } else if (s >= 140f || d >= 90f) {
            factors.add("High Blood Pressure (${s.toInt()}/${d.toInt()} mmHg) - Needs regular monitoring")
        } else if (s >= 130f || d >= 85f) {
            factors.add("Slightly Elevated Blood Pressure (${s.toInt()}/${d.toInt()} mmHg)")
        } else if (s < 90f || d < 60f) {
            factors.add("Low Blood Pressure (${s.toInt()}/${d.toInt()} mmHg) - Feeling weak or dizzy")
        }

        if (b >= 11.1f) {
            factors.add("Very High Blood Sugar (${String.format("%.1f", b)} mmol/L)")
        } else if (b >= 7.8f) {
            factors.add("High Blood Sugar (${String.format("%.1f", b)} mmol/L)")
        } else if (b < 3.5f) {
            factors.add("Low Blood Sugar (${String.format("%.1f", b)} mmol/L) - Feeling weak or dizzy")
        }

        if (prevComp > 0) {
            factors.add("Trouble in Past Pregnancy (History of past delivery complications)")
        }

        if (preDiabetes > 0 || gestDiabetes > 0) {
            factors.add("Sugar / Diabetes Problem during pregnancy")
        }

        if (bodyMass >= 30.0f) {
            factors.add("Mother is Overweight (High weight: BMI ${String.format("%.1f", bodyMass)})")
        } else if (bodyMass < 18.5f) {
            factors.add("Mother is Underweight (Low weight: BMI ${String.format("%.1f", bodyMass)})")
        }

        heartRate?.let { hr ->
            if (hr > 100f) {
                factors.add("Fast Heart Rate (${hr.toInt()} bpm)")
            } else if (hr < 60f) {
                factors.add("Slow Heart Rate (${hr.toInt()} bpm)")
            }
        }

        age?.let { a ->
            if (a > 35) {
                factors.add("Mother's Age ($a years) - Needs extra care")
            } else if (a < 18) {
                factors.add("Very Young Mother ($a years) - Needs extra care")
            }
        }

        if (mentalHealth > 0) {
            factors.add("Feeling Very Sad, Worried, or Anxious")
        }

        if (factors.isEmpty()) {
            factors.add("All measured vitals look healthy and normal")
        }

        // 2. Simple Actionable Steps for Frontline ASHA Workers
        if (s >= 160f || d >= 110f) {
            actions.add("🚨 Check urine for protein at the clinic today to check for swelling and fits risk.")
            actions.add("🚨 Take mother to the hospital / PHC doctor within 24 hours without delay.")
            actions.add("• Ask mother to sleep on her left side and use less salt in food.")
            actions.add("• Save 108 ambulance number on the family phone for quick hospital transport.")
        } else if (isHighRisk || s >= 140f || d >= 90f) {
            actions.add("⚠️ Re-check BP in 2 days. Tell mother to alert you if she has severe headache, blurred vision, or upper stomach pain.")
            actions.add("• Bring mother to the doctor on the 9th of the month (PMSMA checkup day).")
            actions.add("• Ask mother to sleep on her left side, use less salt, and rest well.")
        } else if (s < 90f || d < 60f) {
            actions.add("• Give mother water with ORS, lemon water, or coconut water to drink. Check if she is eating well.")
        }

        if (b >= 11.1f) {
            actions.add("🚨 Urgent: Take mother to the PHC / hospital doctor for sugar medicine and tests.")
        } else if (b >= 7.8f || preDiabetes > 0 || gestDiabetes > 0) {
            actions.add("• Take mother to the PHC lab in the morning without breakfast for a sugar test (OGTT).")
            actions.add("• Tell mother to stop sweets and sugar in tea. Eat more green vegetables, dal, and roti.")
        }

        if (bodyMass < 18.5f) {
            actions.add("• Register mother for extra Anganwadi ration (take-home food / poshahar).")
            actions.add("• Make sure she takes her red iron tablet (IFA) and calcium tablet daily.")
        } else if (bodyMass >= 30.0f) {
            actions.add("• Track mother's weight every month. Encourage a gentle 30-minute daily walk.")
        }

        if (prevComp > 0) {
            actions.add("• Mark as High-Risk Pregnancy. Plan delivery at the District Hospital or CHC (not at home).")
        }

        if (mentalHealth > 0) {
            actions.add("• Talk kindly with the mother. Use the 9-question mental health screen to check how she is feeling.")
        }

        if (!isHighRisk && actions.isEmpty()) {
            actions.add("✓ Continue regular monthly checkups (ensure at least 4 clinic visits before delivery).")
            actions.add("✓ Ensure mother takes 1 red iron tablet (IFA) and 1 calcium tablet daily after meals.")
            actions.add("✓ Teach family the danger signs: bleeding, severe headache, blurred vision, or baby moving less.")
        }

        return Pair(factors, actions)
    }
}
