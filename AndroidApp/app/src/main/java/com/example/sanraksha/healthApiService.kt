package com.example.sanraksha

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface healthApiService {
    // Existing maternal physical risk endpoint (preserved untouched)
    @POST("predict")
    suspend fun sendHealthData(
        @Body healthData: List<healthDataItem>
    ): Response<predictionResponse>

    // Mental Health: submit assessment & calculate longitudinal risk
    @POST("mental-health/patients/{patient_id}/visits")
    suspend fun submitMentalHealthVisit(
        @Path("patient_id") patientId: Long,
        @Body request: CreateMentalHealthVisitRequest
    ): Response<MentalHealthAssessmentResponse>

    // Mental Health: retrieve patient chronological visit history
    @GET("mental-health/patients/{patient_id}/history")
    suspend fun getPatientHistory(
        @Path("patient_id") patientId: Long
    ): Response<PatientHistoryResponse>

    // Mental Health: retrieve latest assessment
    @GET("mental-health/patients/{patient_id}/latest")
    suspend fun getLatestVisit(
        @Path("patient_id") patientId: Long
    ): Response<Map<String, Any>>

    // ── NUTRITION ENDPOINTS ──────────────────────────────────────────────────
    @POST("nutrition/assessments")
    suspend fun submitNutritionAssessment(
        @Body request: CreateNutritionAssessmentDto
    ): Response<NutritionEvaluationDto>

    @GET("nutrition/patients/{patient_id}/latest")
    suspend fun getLatestNutrition(
        @Path("patient_id") patientId: Long
    ): Response<NutritionEvaluationDto>

    // ── IMMUNIZATION ENDPOINTS ───────────────────────────────────────────────
    @POST("immunization/records")
    suspend fun recordVaccination(
        @Body request: CreateImmunizationRecordDto
    ): Response<Map<String, Any>>

    @GET("immunization/patients/{patient_id}/status")
    suspend fun getImmunizationStatus(
        @Path("patient_id") patientId: Long
    ): Response<PatientImmunizationStatusDto>

    // ── ACTION GUIDANCE & TASK TRACKING ──────────────────────────────────────
    @GET("guidance/patients/{patient_id}/actions")
    suspend fun getActionPlan(
        @Path("patient_id") patientId: Long
    ): Response<UnifiedActionPlanDto>

    @retrofit2.http.PUT("guidance/actions/{action_id}/status")
    suspend fun updateActionStatus(
        @Path("action_id") actionId: String,
        @Body request: UpdateActionStatusDto
    ): Response<Map<String, Any>>

    // ── COMPREHENSIVE SUMMARY ────────────────────────────────────────────────
    @GET("summary/patients/{patient_id}")
    suspend fun getComprehensiveSummary(
        @Path("patient_id") patientId: Long
    ): Response<ComprehensiveMaternalHealthSummaryDto>
}