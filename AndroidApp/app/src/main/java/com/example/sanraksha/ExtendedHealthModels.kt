package com.example.sanraksha

import com.google.gson.annotations.SerializedName

// ── NUTRITION DTOs ───────────────────────────────────────────────────────────

data class NutrientIntakeDto(
    @SerializedName("energy_kcal") val energyKcal: Float? = null,
    @SerializedName("protein_g") val proteinG: Float? = null,
    @SerializedName("carbohydrates_g") val carbohydratesG: Float? = null,
    @SerializedName("fat_g") val fatG: Float? = null,
    @SerializedName("fibre_g") val fibreG: Float? = null,
    @SerializedName("iron_mg") val ironMg: Float? = null,
    @SerializedName("folate_mcg") val folateMcg: Float? = null,
    @SerializedName("calcium_mg") val calciumMg: Float? = null,
    @SerializedName("vitamin_d_iu") val vitaminDIu: Float? = null,
    @SerializedName("vitamin_b12_mcg") val vitaminB12Mcg: Float? = null
)

data class CreateNutritionAssessmentDto(
    @SerializedName("patient_id") val patientId: Long,
    @SerializedName("visit_id") val visitId: Long? = null,
    @SerializedName("gestational_age") val gestationalAge: Int? = null,
    @SerializedName("trimester") val trimester: String? = null,
    @SerializedName("height_cm") val heightCm: Float? = null,
    @SerializedName("current_weight_kg") val currentWeightKg: Float? = null,
    @SerializedName("pre_pregnancy_weight_kg") val prePregnancyWeightKg: Float? = null,
    @SerializedName("intake") val intake: NutrientIntakeDto,
    @SerializedName("dietary_pattern") val dietaryPattern: String = "vegetarian",
    @SerializedName("food_restrictions") val foodRestrictions: String? = null,
    @SerializedName("appetite_difficulty") val appetiteDifficulty: String = "normal",
    @SerializedName("food_insecurity") val foodInsecurity: Boolean = false,
    @SerializedName("supplements_taken") val supplementsTaken: List<String> = emptyList(),
    @SerializedName("assessment_completeness") val assessmentCompleteness: String = "partial",
    @SerializedName("notes") val notes: String? = null
)

data class NutrientComparisonDto(
    @SerializedName("nutrient") val nutrient: String,
    @SerializedName("label") val label: String,
    @SerializedName("reported_value") val reportedValue: Float?,
    @SerializedName("reference_value") val referenceValue: Float,
    @SerializedName("unit") val unit: String,
    @SerializedName("reference_type") val referenceType: String,
    @SerializedName("status") val status: String,
    @SerializedName("percent_of_reference") val percentOfReference: Float?,
    @SerializedName("difference") val difference: Float?,
    @SerializedName("explanation") val explanation: String
)

data class WeightProgressionDto(
    @SerializedName("height_cm") val heightCm: Float?,
    @SerializedName("current_weight_kg") val currentWeightKg: Float?,
    @SerializedName("current_bmi") val currentBmi: Float?,
    @SerializedName("current_bmi_category") val currentBmiCategory: String?,
    @SerializedName("pre_pregnancy_weight_kg") val prePregnancyWeightKg: Float?,
    @SerializedName("pre_pregnancy_bmi") val prePregnancyBmi: Float?,
    @SerializedName("pre_pregnancy_bmi_category") val prePregnancyBmiCategory: String?,
    @SerializedName("gestational_weight_gain_kg") val gestationalWeightGainKg: Float?,
    @SerializedName("recommended_gain_range") val recommendedGainRange: String?,
    @SerializedName("weight_trend_status") val weightTrendStatus: String,
    @SerializedName("guidance") val guidance: String
)

data class NutritionEvaluationDto(
    @SerializedName("assessment_id") val assessmentId: Long?,
    @SerializedName("patient_id") val patientId: Long,
    @SerializedName("visit_id") val visitId: Long?,
    @SerializedName("assessment_date") val assessmentDate: String,
    @SerializedName("trimester") val trimester: String,
    @SerializedName("gestational_age") val gestationalAge: Int?,
    @SerializedName("completeness") val completeness: String,
    @SerializedName("weight_progression") val weightProgression: WeightProgressionDto,
    @SerializedName("nutrient_comparisons") val nutrientComparisons: List<NutrientComparisonDto> = emptyList(),
    @SerializedName("gaps") val gaps: List<String> = emptyList(),
    @SerializedName("recommendations") val recommendations: List<String> = emptyList(),
    @SerializedName("unassessed_nutrients") val unassessedNutrients: List<String> = emptyList(),
    @SerializedName("food_security_flag") val foodSecurityFlag: Boolean = false,
    @SerializedName("reference_source") val referenceSource: String,
    @SerializedName("reference_version") val referenceVersion: String,
    @SerializedName("scientific_disclaimer") val scientificDisclaimer: String
)

// ── IMMUNIZATION DTOs ────────────────────────────────────────────────────────

data class CreateImmunizationRecordDto(
    @SerializedName("patient_id") val patientId: Long,
    @SerializedName("visit_id") val visitId: Long? = null,
    @SerializedName("vaccine_name") val vaccineName: String,
    @SerializedName("dose_number") val doseNumber: Int = 1,
    @SerializedName("status") val status: String = "completed",
    @SerializedName("administration_date") val administrationDate: String? = null,
    @SerializedName("confirmation_source") val confirmationSource: String = "mcp_card",
    @SerializedName("card_verified") val cardVerified: Boolean = true,
    @SerializedName("next_due_date") val nextDueDate: String? = null,
    @SerializedName("notes") val notes: String? = null
)

data class VaccineDoseStatusDto(
    @SerializedName("vaccine_name") val vaccineName: String,
    @SerializedName("dose_number") val doseNumber: Int,
    @SerializedName("status") val status: String,
    @SerializedName("administration_date") val administrationDate: String? = null,
    @SerializedName("confirmation_source") val confirmationSource: String? = null,
    @SerializedName("card_verified") val cardVerified: Boolean = false,
    @SerializedName("next_due_date") val nextDueDate: String? = null,
    @SerializedName("status_label") val statusLabel: String,
    @SerializedName("action_required") val actionRequired: String? = null
)

data class PatientImmunizationStatusDto(
    @SerializedName("patient_id") val patientId: Long,
    @SerializedName("gestational_age_weeks") val gestationalAgeWeeks: Int?,
    @SerializedName("pregnancy_status") val pregnancyStatus: String,
    @SerializedName("schedule_version") val scheduleVersion: String,
    @SerializedName("overall_compliance") val overallCompliance: String,
    @SerializedName("doses") val doses: List<VaccineDoseStatusDto> = emptyList(),
    @SerializedName("asha_action_checklist") val ashaActionChecklist: List<String> = emptyList(),
    @SerializedName("disclaimer") val disclaimer: String
)

// ── SHAP EXPLAINABILITY DTOs ──────────────────────────────────────────────────

data class FeatureContributionDto(
    @SerializedName("feature_name") val featureName: String,
    @SerializedName("feature_label") val featureLabel: String,
    @SerializedName("observed_value") val observedValue: Any,
    @SerializedName("unit") val unit: String,
    @SerializedName("shap_value") val shapValue: Float,
    @SerializedName("direction") val direction: String,
    @SerializedName("clinical_interpretation") val clinicalInterpretation: String
)

data class ModelExplanationDto(
    @SerializedName("model_name") val modelName: String,
    @SerializedName("model_version") val modelVersion: String,
    @SerializedName("prediction_class") val predictionClass: String,
    @SerializedName("prediction_score") val predictionScore: Float,
    @SerializedName("base_value") val baseValue: Float,
    @SerializedName("contributions_sum") val contributionsSum: Float,
    @SerializedName("feature_contributions") val featureContributions: List<FeatureContributionDto> = emptyList(),
    @SerializedName("top_risk_drivers") val topRiskDrivers: List<String> = emptyList(),
    @SerializedName("top_protective_factors") val topProtectiveFactors: List<String> = emptyList(),
    @SerializedName("disclaimer") val disclaimer: String,
    @SerializedName("provenance") val provenance: String
)

// ── ACTION PLAN DTOs ──────────────────────────────────────────────────────────

data class ActionRecommendationDto(
    @SerializedName("action_id") val actionId: String,
    @SerializedName("patient_id") val patientId: Long,
    @SerializedName("visit_id") val visitId: Long? = null,
    @SerializedName("domain") val domain: String,
    @SerializedName("trigger_observation") val triggerObservation: String,
    @SerializedName("explanation") val explanation: String,
    @SerializedName("action_text") val actionText: String,
    @SerializedName("urgency") val urgency: String,
    @SerializedName("responsible_person") val responsiblePerson: String,
    @SerializedName("timeframe") val timeframe: String,
    @SerializedName("referral_required") val referralRequired: Boolean = false,
    @SerializedName("status") val status: String = "pending",
    @SerializedName("outcome_notes") val outcomeNotes: String? = null,
    @SerializedName("completed_at") val completedAt: String? = null,
    @SerializedName("rule_source") val ruleSource: String,
    @SerializedName("rule_version") val ruleVersion: String
)

data class UpdateActionStatusDto(
    @SerializedName("status") val status: String,
    @SerializedName("outcome_notes") val outcomeNotes: String? = null
)

data class UnifiedActionPlanDto(
    @SerializedName("patient_id") val patientId: Long,
    @SerializedName("total_actions") val totalActions: Int,
    @SerializedName("emergency_actions") val emergencyActions: List<ActionRecommendationDto> = emptyList(),
    @SerializedName("urgent_actions") val urgentActions: List<ActionRecommendationDto> = emptyList(),
    @SerializedName("timely_actions") val timelyActions: List<ActionRecommendationDto> = emptyList(),
    @SerializedName("routine_actions") val routineActions: List<ActionRecommendationDto> = emptyList(),
    @SerializedName("info_actions") val infoActions: List<ActionRecommendationDto> = emptyList(),
    @SerializedName("pending_count") val pendingCount: Int,
    @SerializedName("completed_count") val completedCount: Int
)

// ── COMPREHENSIVE SUMMARY DTOs ────────────────────────────────────────────────

data class PhysicalHealthSectionDto(
    @SerializedName("has_data") val hasData: Boolean,
    @SerializedName("latest_vitals") val latestVitals: Map<String, Any>? = null,
    @SerializedName("prediction_label") val predictionLabel: String? = null,
    @SerializedName("risk_prediction") val riskPrediction: Int? = null,
    @SerializedName("contributing_factors") val contributingFactors: List<String> = emptyList(),
    @SerializedName("shap_explanation") val shapExplanation: ModelExplanationDto? = null,
    @SerializedName("vitals_trajectory_summary") val vitalsTrajectorySummary: String? = null
)

data class MentalHealthSectionDto(
    @SerializedName("has_data") val hasData: Boolean,
    @SerializedName("total_score") val totalScore: Int? = null,
    @SerializedName("severity") val severity: String? = null,
    @SerializedName("urgent_safety_flag") val urgentSafetyFlag: Boolean = false,
    @SerializedName("safety_message") val safetyMessage: String? = null,
    @SerializedName("contextual_probability") val contextualProbability: Float? = null,
    @SerializedName("contextual_category") val contextualCategory: String? = null,
    @SerializedName("longitudinal_trend") val longitudinalTrend: String? = null,
    @SerializedName("score_change") val scoreChange: Int? = null,
    @SerializedName("previous_elevated_screenings") val previousElevatedScreenings: Int = 0,
    @SerializedName("total_screenings") val totalScreenings: Int = 0
)

data class NutritionSectionDto(
    @SerializedName("has_data") val hasData: Boolean,
    @SerializedName("dietary_pattern") val dietaryPattern: String? = null,
    @SerializedName("current_bmi") val currentBmi: Float? = null,
    @SerializedName("bmi_category") val bmiCategory: String? = null,
    @SerializedName("weight_gain_kg") val weightGainKg: Float? = null,
    @SerializedName("weight_gain_status") val weightGainStatus: String? = null,
    @SerializedName("gaps") val gaps: List<String> = emptyList(),
    @SerializedName("food_insecurity") val foodInsecurity: Boolean = false,
    @SerializedName("evaluation") val evaluation: NutritionEvaluationDto? = null
)

data class ImmunizationSectionDto(
    @SerializedName("has_data") val hasData: Boolean,
    @SerializedName("overall_compliance") val overallCompliance: String,
    @SerializedName("completed_doses") val completedDoses: List<String> = emptyList(),
    @SerializedName("due_doses") val dueDoses: List<String> = emptyList(),
    @SerializedName("overdue_doses") val overdueDoses: List<String> = emptyList(),
    @SerializedName("details") val details: PatientImmunizationStatusDto? = null
)

data class ComprehensiveMaternalHealthSummaryDto(
    @SerializedName("patient_id") val patientId: Long,
    @SerializedName("name") val name: String,
    @SerializedName("age") val age: Int?,
    @SerializedName("state") val state: String,
    @SerializedName("pregnancy_status") val pregnancyStatus: String,
    @SerializedName("gestational_age") val gestationalAge: Int?,
    @SerializedName("trimester") val trimester: String,
    @SerializedName("total_visits") val totalVisits: Int,
    @SerializedName("latest_visit_date") val latestVisitDate: String?,
    @SerializedName("generated_at") val generatedAt: String,
    @SerializedName("overall_health_status") val overallHealthStatus: String,
    @SerializedName("overall_status_explanation") val overallStatusExplanation: String,
    @SerializedName("physical_health") val physicalHealth: PhysicalHealthSectionDto,
    @SerializedName("mental_health") val mentalHealth: MentalHealthSectionDto,
    @SerializedName("nutrition") val nutrition: NutritionSectionDto,
    @SerializedName("immunization") val immunization: ImmunizationSectionDto,
    @SerializedName("trajectory_milestones") val trajectoryMilestones: List<String> = emptyList(),
    @SerializedName("action_plan") val actionPlan: List<ActionRecommendationDto> = emptyList(),
    @SerializedName("scientific_disclaimer") val scientificDisclaimer: String
)
