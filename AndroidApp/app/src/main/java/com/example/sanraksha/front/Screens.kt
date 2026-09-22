package com.example.sanraksha.front

sealed class Screens(val route: String) {
    object Home : Screens("home")
    object AddPatient : Screens("add_patient")
    object Profile : Screens("profile/{patientId}") {
        fun passId(patientId: Long): String = "profile/$patientId"
    }
    object RecordVitals : Screens("recordvitals/{patientId}") {
        fun passId(patientId: Long): String = "recordvitals/$patientId"
    }
    object MentalHealthScreening : Screens("mental_health_screening/{patientId}") {
        fun passId(patientId: Long): String = "mental_health_screening/$patientId"
    }
    object ContextualRisk : Screens("contextual_risk/{patientId}") {
        fun passId(patientId: Long): String = "contextual_risk/$patientId"
    }
    object MentalHealthResult : Screens("mental_health_result/{patientId}") {
        fun passId(patientId: Long): String = "mental_health_result/$patientId"
    }
    object PatientHistory : Screens("patient_history/{patientId}") {
        fun passId(patientId: Long): String = "patient_history/$patientId"
    }
}