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
}