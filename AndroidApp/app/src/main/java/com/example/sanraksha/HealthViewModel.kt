package com.example.sanraksha

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ApiPredictionResult(
    val prediction: Int,
    val label: String,
    val contributingFactors: List<String> = emptyList(),
    val actionableGuidance: List<String> = emptyList()
)

class HealthViewModel : ViewModel() {

    // ── Existing Physical Vitals Prediction (Preserved) ──────────────────────
    fun sendHealthDataToApi(inputs: healthDataItem, onResult: (ApiPredictionResult?) -> Unit) {
        val healthDataList = listOf(inputs)
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.sendHealthData(healthDataList)
                if (response.isSuccessful) {
                    val body = response.body()
                    val prediction = body?.prediction?.firstOrNull()
                    if (prediction != null) {
                        val label = body.prediction_label?.firstOrNull()
                            ?: when (prediction) {
                                0 -> "Low Risk"
                                1 -> "High Risk"
                                else -> "Unknown"
                            }
                        val factors = body.contributing_factors?.firstOrNull() ?: emptyList()
                        val actions = body.actionable_guidance?.firstOrNull() ?: emptyList()
                        Log.d("API_SUCCESS", "Prediction: $prediction, Label: $label, Factors: $factors, Actions: $actions")
                        onResult(
                            ApiPredictionResult(
                                prediction = prediction,
                                label = label,
                                contributingFactors = factors,
                                actionableGuidance = actions
                            )
                        )
                    } else {
                        onResult(null)
                    }
                } else {
                    Log.e("API_ERROR", "Response Code: ${response.code()}")
                    Log.e("API_ERROR", "Error Body: ${response.errorBody()?.string()}")
                    onResult(null)
                }
            } catch (e: Exception) {
                Log.d("API_REQUEST", "Sending data: $healthDataList")
                Log.e("API_EXCEPTION", "Exception: ${e.message}", e)
                onResult(null)
            }
        }
    }

    // ── Mental Health & Longitudinal State Management ────────────────────────
    private val _latestAssessment = MutableStateFlow<MentalHealthAssessmentResponse?>(null)
    val latestAssessment: StateFlow<MentalHealthAssessmentResponse?> = _latestAssessment.asStateFlow()

    private val _patientHistory = MutableStateFlow<List<PatientHistoryVisitItem>>(emptyList())
    val patientHistory: StateFlow<List<PatientHistoryVisitItem>> = _patientHistory.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()

    fun submitMentalHealthVisit(
        patientId: Long,
        request: CreateMentalHealthVisitRequest,
        onComplete: (MentalHealthAssessmentResponse?) -> Unit
    ) {
        _isLoading.value = true
        _errorMessage.value = null
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.submitMentalHealthVisit(patientId, request)
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    _latestAssessment.value = result
                    Log.d("MH_SUCCESS", "Visit submitted: visit_id=${result.visitId}, score=${result.currentScreening.phq9Score}")
                    onComplete(result)
                } else {
                    val err = response.errorBody()?.string() ?: "Submission failed with code ${response.code()}"
                    Log.e("MH_ERROR", err)
                    _errorMessage.value = err
                    onComplete(null)
                }
            } catch (e: Exception) {
                Log.e("MH_EXCEPTION", "Error submitting mental health visit: ${e.message}", e)
                _errorMessage.value = e.localizedMessage ?: "Network error connecting to backend"
                onComplete(null)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun fetchPatientHistory(patientId: Long) {
        _isLoading.value = true
        _errorMessage.value = null
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.getPatientHistory(patientId)
                if (response.isSuccessful && response.body() != null) {
                    _patientHistory.value = response.body()!!.visits
                    Log.d("MH_HISTORY", "Fetched ${_patientHistory.value.size} visits for patient $patientId")
                } else {
                    val err = response.errorBody()?.string() ?: "Failed to fetch history"
                    Log.e("MH_HISTORY_ERR", err)
                    _errorMessage.value = err
                }
            } catch (e: Exception) {
                Log.e("MH_HISTORY_EXC", "Error fetching history: ${e.message}", e)
                _errorMessage.value = e.localizedMessage ?: "Failed to load patient history"
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun fetchLatestAssessment(patientId: Long) {
        _isLoading.value = true
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.getLatestVisit(patientId)
                if (response.isSuccessful && response.body() != null) {
                    val map = response.body()!!
                    val latest = map["latest_visit"] as? Map<String, Any>
                    if (latest != null) {
                        val visitId = (latest["visit_id"] as? Number)?.toLong() ?: 0L
                        val score = (latest["total_score"] as? Number)?.toInt() ?: 0
                        val sev = latest["severity"] as? String ?: "Minimal"
                        val atRisk = (latest["at_risk"] as? Number)?.toInt() == 1
                        val safetyFlag = (latest["urgent_safety_flag"] as? Number)?.toInt() == 1
                        val safetyMsg = latest["safety_message"] as? String ?: ""
                        val prob = (latest["risk_probability"] as? Number)?.toFloat() ?: 0f
                        val cat = latest["risk_category"] as? String ?: "Low"
                        val factors = (latest["top_contributing_factors"] as? List<*>)?.filterIsInstance<String>() ?: emptyList()
                        val expl = latest["explanation_text"] as? String ?: ""
                        val guidance = (latest["actionable_guidance"] as? List<*>)?.filterIsInstance<String>() ?: emptyList()
                        val trend = latest["trend"] as? String ?: "stable"
                        val visitCount = (latest["visit_count"] as? Number)?.toInt() ?: 1
                        val scoreChange = (latest["score_change"] as? Number)?.toInt()
                        val priorElevated = (latest["num_previous_elevated_screenings"] as? Number)?.toInt() ?: 0

                        _latestAssessment.value = MentalHealthAssessmentResponse(
                            patientId = patientId,
                            visitId = visitId,
                            visitDate = latest["visit_date"] as? String ?: "",
                            trimester = latest["trimester"] as? String ?: "Third trimester",
                            visitType = latest["visit_type"] as? String ?: "prenatal",
                            currentScreening = Phq9ResultDto(
                                screeningType = latest["screening_type"] as? String ?: "PHQ-9",
                                phq9Score = score,
                                severity = sev,
                                screenPositive = atRisk,
                                urgentFlag = safetyFlag,
                                safetyMessage = safetyMsg
                            ),
                            contextualRisk = ContextualRiskDto(
                                modelName = latest["model_name"] as? String ?: "ContextualRandomForest",
                                modelVersion = latest["model_version"] as? String ?: "v1",
                                probability = prob,
                                category = cat,
                                topContributingFactors = factors,
                                explanation = expl
                            ),
                            longitudinal = LongitudinalDto(
                                visitCount = visitCount,
                                phq9Change = scoreChange,
                                riskChange = (latest["risk_probability_change"] as? Number)?.toFloat(),
                                trend = trend,
                                previousElevatedScreenings = priorElevated
                            ),
                            postpartumPrediction = PostpartumPredictionDto(
                                available = false,
                                modelName = "Longitudinal-Prospective-Ensemble",
                                reason = "Cross-sectional data limits prospective predictions."
                            ),
                            safetyFlag = safetyFlag,
                            urgentMessage = if (safetyFlag) safetyMsg else null,
                            actionableGuidance = guidance
                        )
                    }
                }
            } catch (e: Exception) {
                Log.e("MH_LATEST", "Error fetching latest visit: ${e.message}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun clearError() {
        _errorMessage.value = null
    }

    // ── NUTRITION STATE MANAGEMENT ───────────────────────────────────────────
    private val _latestNutrition = MutableStateFlow<NutritionEvaluationDto?>(null)
    val latestNutrition: StateFlow<NutritionEvaluationDto?> = _latestNutrition.asStateFlow()

    fun submitNutritionAssessment(
        request: CreateNutritionAssessmentDto,
        onComplete: (NutritionEvaluationDto?) -> Unit
    ) {
        _isLoading.value = true
        _errorMessage.value = null
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.submitNutritionAssessment(request)
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    _latestNutrition.value = result
                    Log.d("NUTR_SUCCESS", "Assessment saved: ${result.assessmentId}, gaps: ${result.gaps.size}")
                    onComplete(result)
                } else {
                    val err = response.errorBody()?.string() ?: "Nutrition submission failed"
                    Log.e("NUTR_ERR", err)
                    _errorMessage.value = err
                    onComplete(null)
                }
            } catch (e: Exception) {
                Log.e("NUTR_EXC", "Error submitting nutrition assessment: ${e.message}", e)
                _errorMessage.value = e.localizedMessage ?: "Network error submitting nutrition"
                onComplete(null)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun fetchLatestNutrition(patientId: Long) {
        _isLoading.value = true
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.getLatestNutrition(patientId)
                if (response.isSuccessful && response.body() != null) {
                    _latestNutrition.value = response.body()
                }
            } catch (e: Exception) {
                Log.e("NUTR_FETCH", "Error fetching nutrition: ${e.message}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    // ── IMMUNIZATION STATE MANAGEMENT ────────────────────────────────────────
    private val _immunizationStatus = MutableStateFlow<PatientImmunizationStatusDto?>(null)
    val immunizationStatus: StateFlow<PatientImmunizationStatusDto?> = _immunizationStatus.asStateFlow()

    fun recordVaccination(
        request: CreateImmunizationRecordDto,
        onComplete: (Boolean) -> Unit
    ) {
        _isLoading.value = true
        _errorMessage.value = null
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.recordVaccination(request)
                if (response.isSuccessful) {
                    fetchImmunizationStatus(request.patientId)
                    onComplete(true)
                } else {
                    val err = response.errorBody()?.string() ?: "Failed to record vaccine"
                    _errorMessage.value = err
                    onComplete(false)
                }
            } catch (e: Exception) {
                Log.e("IMM_REC", "Error recording vaccine: ${e.message}", e)
                _errorMessage.value = e.localizedMessage ?: "Network error recording vaccine"
                onComplete(false)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun fetchImmunizationStatus(patientId: Long) {
        _isLoading.value = true
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.getImmunizationStatus(patientId)
                if (response.isSuccessful && response.body() != null) {
                    _immunizationStatus.value = response.body()
                }
            } catch (e: Exception) {
                Log.e("IMM_FETCH", "Error fetching immunization status: ${e.message}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    // ── ACTION GUIDANCE & TASK TRACKING ──────────────────────────────────────
    private val _actionPlan = MutableStateFlow<UnifiedActionPlanDto?>(null)
    val actionPlan: StateFlow<UnifiedActionPlanDto?> = _actionPlan.asStateFlow()

    fun fetchActionPlan(patientId: Long) {
        _isLoading.value = true
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.getActionPlan(patientId)
                if (response.isSuccessful && response.body() != null) {
                    _actionPlan.value = response.body()
                }
            } catch (e: Exception) {
                Log.e("ACTION_FETCH", "Error fetching action plan: ${e.message}", e)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun updateActionStatus(actionId: String, status: String, notes: String?, patientId: Long) {
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.updateActionStatus(actionId, UpdateActionStatusDto(status, notes))
                if (response.isSuccessful) {
                    fetchActionPlan(patientId)
                }
            } catch (e: Exception) {
                Log.e("ACTION_UPDATE", "Error updating action: ${e.message}", e)
            }
        }
    }

    // ── COMPREHENSIVE SUMMARY ────────────────────────────────────────────────
    private val _comprehensiveSummary = MutableStateFlow<ComprehensiveMaternalHealthSummaryDto?>(null)
    val comprehensiveSummary: StateFlow<ComprehensiveMaternalHealthSummaryDto?> = _comprehensiveSummary.asStateFlow()

    fun fetchComprehensiveSummary(patientId: Long) {
        _isLoading.value = true
        _errorMessage.value = null
        viewModelScope.launch {
            try {
                val response = retrofitInstance.api.getComprehensiveSummary(patientId)
                if (response.isSuccessful && response.body() != null) {
                    _comprehensiveSummary.value = response.body()
                } else {
                    _errorMessage.value = response.errorBody()?.string() ?: "Failed to load summary"
                }
            } catch (e: Exception) {
                Log.e("SUMMARY_FETCH", "Error fetching summary: ${e.message}", e)
                _errorMessage.value = e.localizedMessage ?: "Network error loading summary"
            } finally {
                _isLoading.value = false
            }
        }
    }
}