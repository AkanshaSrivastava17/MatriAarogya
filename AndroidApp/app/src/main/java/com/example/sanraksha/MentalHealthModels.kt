package com.example.sanraksha

import com.google.gson.annotations.SerializedName

// ── Mental Health Data Transfer Objects ──────────────────────────────────────

data class CreateMentalHealthVisitRequest(
    @SerializedName("visit_date") val visitDate: String,
    @SerializedName("gestational_age") val gestationalAge: Int?,
    @SerializedName("delivery_date") val deliveryDate: String? = null,
    @SerializedName("visit_type") val visitType: String = "prenatal",
    @SerializedName("vitals") val vitals: MentalHealthVitalsDto? = null,
    @SerializedName("phq9_item_scores") val phq9ItemScores: Map<String, Int>,
    @SerializedName("context") val context: MentalHealthContextDto? = null,
    @SerializedName("notes") val notes: String? = null
)

data class MentalHealthVitalsDto(
    @SerializedName("systolic_bp") val systolicBp: Float? = null,
    @SerializedName("diastolic_bp") val diastolicBp: Float? = null,
    @SerializedName("blood_sugar") val bloodSugar: Float? = null,
    @SerializedName("bmi") val bmi: Float? = null,
    @SerializedName("heart_rate") val heartRate: Float? = null,
    @SerializedName("body_temp") val bodyTemp: Float? = null,
    @SerializedName("previous_complications") val previousComplications: Int = 0,
    @SerializedName("preexisting_diabetes") val preexistingDiabetes: Int = 0,
    @SerializedName("gestational_diabetes") val gestationalDiabetes: Int = 0
)

data class MentalHealthContextDto(
    @SerializedName("values") val values: Map<String, Any>,
    @SerializedName("age") val age: Float
)

data class Phq9ResultDto(
    @SerializedName("screening_type") val screeningType: String = "PHQ-9",
    @SerializedName("phq9_score") val phq9Score: Int,
    @SerializedName("severity") val severity: String,
    @SerializedName("screen_positive") val screenPositive: Boolean,
    @SerializedName("urgent_flag") val urgentFlag: Boolean,
    @SerializedName("safety_message") val safetyMessage: String? = null
)

data class ContextualRiskDto(
    @SerializedName("model_name") val modelName: String,
    @SerializedName("model_version") val modelVersion: String,
    @SerializedName("probability") val probability: Float,
    @SerializedName("category") val category: String,
    @SerializedName("top_contributing_factors") val topContributingFactors: List<String> = emptyList(),
    @SerializedName("explanation") val explanation: String? = null
)

data class LongitudinalDto(
    @SerializedName("previous_phq9") val previousPhq9: Int? = null,
    @SerializedName("phq9_change") val phq9Change: Int? = null,
    @SerializedName("previous_risk") val previousRisk: Float? = null,
    @SerializedName("risk_change") val riskChange: Float? = null,
    @SerializedName("previous_elevated_screenings") val previousElevatedScreenings: Int = 0,
    @SerializedName("visit_count") val visitCount: Int = 1,
    @SerializedName("trend") val trend: String = "insufficient_data",
    @SerializedName("days_since_last_visit") val daysSinceLastVisit: Int? = null,
    @SerializedName("gestational_age_progression") val gestationalAgeProgression: Int? = null
)

data class PostpartumPredictionDto(
    @SerializedName("available") val available: Boolean = false,
    @SerializedName("model_name") val modelName: String? = null,
    @SerializedName("reason") val reason: String? = null
)

data class MentalHealthAssessmentResponse(
    @SerializedName("patient_id") val patientId: Long,
    @SerializedName("visit_id") val visitId: Long,
    @SerializedName("visit_date") val visitDate: String,
    @SerializedName("trimester") val trimester: String,
    @SerializedName("visit_type") val visitType: String,
    @SerializedName("current_screening") val currentScreening: Phq9ResultDto,
    @SerializedName("contextual_risk") val contextualRisk: ContextualRiskDto? = null,
    @SerializedName("longitudinal") val longitudinal: LongitudinalDto,
    @SerializedName("postpartum_prediction") val postpartumPrediction: PostpartumPredictionDto,
    @SerializedName("safety_flag") val safetyFlag: Boolean = false,
    @SerializedName("urgent_message") val urgentMessage: String? = null,
    @SerializedName("actionable_guidance") val actionableGuidance: List<String> = emptyList()
)

data class PatientHistoryVisitItem(
    @SerializedName("visit_id") val visitId: Long,
    @SerializedName("visit_date") val visitDate: String,
    @SerializedName("trimester") val trimester: String,
    @SerializedName("gestational_age") val gestationalAge: Int?,
    @SerializedName("delivery_date") val deliveryDate: String?,
    @SerializedName("visit_type") val visitType: String?,
    @SerializedName("total_score") val totalScore: Int,
    @SerializedName("severity") val severity: String?,
    @SerializedName("at_risk") val atRisk: Int,
    @SerializedName("urgent_safety_flag") val urgentSafetyFlag: Int,
    @SerializedName("risk_category") val riskCategory: String?,
    @SerializedName("risk_probability") val riskProbability: Float?,
    @SerializedName("trend") val trend: String?,
    @SerializedName("score_change") val scoreChange: Int?,
    @SerializedName("systolic_bp") val systolicBp: Float?,
    @SerializedName("diastolic_bp") val diastolicBp: Float?,
    @SerializedName("heart_rate") val heartRate: Float?,
    @SerializedName("actionable_guidance") val actionableGuidance: List<String> = emptyList()
)

data class PatientHistoryResponse(
    @SerializedName("patient_id") val patientId: Long,
    @SerializedName("visits") val visits: List<PatientHistoryVisitItem> = emptyList()
)
