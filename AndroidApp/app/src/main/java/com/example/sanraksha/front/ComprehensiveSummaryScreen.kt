package com.example.sanraksha.front

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.example.sanraksha.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ComprehensiveSummaryScreen(
    patientId: Long,
    navController: NavHostController,
    healthViewModel: HealthViewModel = viewModel(),
    patientViewModel: PatientViewModel = viewModel()
) {
    val patient by patientViewModel.getAPatientById(patientId).collectAsState(initial = null)
    val summary by healthViewModel.comprehensiveSummary.collectAsState()
    val isLoading by healthViewModel.isLoading.collectAsState()
    val errorMessage by healthViewModel.errorMessage.collectAsState()

    val scrollState = rememberScrollState()

    LaunchedEffect(patientId) {
        healthViewModel.fetchComprehensiveSummary(patientId)
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Maternal Health Dossier", fontWeight = FontWeight.Bold, fontSize = 20.sp) },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            )
        }
    ) { padding ->
        if (isLoading && summary == null) {
            Box(modifier = Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else if (summary == null) {
            Box(modifier = Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(text = errorMessage ?: "No summary records available.", style = MaterialTheme.typography.bodyLarge)
                    Spacer(modifier = Modifier.height(12.dp))
                    Button(onClick = { healthViewModel.fetchComprehensiveSummary(patientId) }) {
                        Text("Retry")
                    }
                }
            }
        } else {
            val res = summary!!
            val statusColor = when {
                res.overallHealthStatus.contains("Emergency") -> Color(0xFFC62828)
                res.overallHealthStatus.contains("Urgent") -> Color(0xFFE65100)
                res.overallHealthStatus.contains("Follow-up") -> Color(0xFF1565C0)
                res.overallHealthStatus.contains("Routine") -> Color(0xFF2E7D32)
                else -> Color.DarkGray
            }

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .verticalScroll(scrollState)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Header Banner
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = res.name,
                            fontWeight = FontWeight.Bold,
                            fontSize = 20.sp,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                        Text(
                            text = "Patient ID: #${res.patientId}  •  State: ${res.state}  •  ${res.trimester}",
                            fontSize = 13.sp,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                        )
                        Text(
                            text = "Total Visits: ${res.totalVisits}  •  Status: ${res.pregnancyStatus.uppercase()}",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                        )
                    }
                }

                // Transparent Rule-Based Overall Health Status
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = when {
                            res.overallHealthStatus.contains("Emergency") -> Color(0xFFFFEBEE)
                            res.overallHealthStatus.contains("Urgent") -> Color(0xFFFFF3E0)
                            res.overallHealthStatus.contains("Follow-up") -> Color(0xFFE3F2FD)
                            res.overallHealthStatus.contains("Routine") -> Color(0xFFE8F5E9)
                            else -> Color(0xFFF5F5F5)
                        }
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = if (res.overallHealthStatus.contains("Routine")) Icons.Default.CheckCircle else Icons.Default.Warning,
                                contentDescription = null,
                                tint = statusColor
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = res.overallHealthStatus,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp,
                                color = statusColor
                            )
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = res.overallStatusExplanation,
                            fontSize = 13.sp,
                            color = Color.DarkGray
                        )
                    }
                }

                // 1. Physical Vitals & SHAP Summary
                Card(shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text("1. Physical Maternal Health", fontWeight = FontWeight.Bold, fontSize = 15.sp)
                        if (res.physicalHealth.hasData) {
                            val v = res.physicalHealth.latestVitals
                            Text("Risk Level: ${res.physicalHealth.predictionLabel ?: "Normal"}", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                            Text("BP: ${v?.get("Systolic_BP")}/${v?.get("Diastolic")} mmHg  •  Sugar: ${v?.get("BS")} mmol/L  •  BMI: ${v?.get("BMI")}", fontSize = 12.sp)

                            res.physicalHealth.shapExplanation?.let { shap ->
                                Spacer(modifier = Modifier.height(6.dp))
                                Text("Top Influencing Factors (SHAP AI):", fontWeight = FontWeight.Bold, fontSize = 12.sp, color = Color(0xFF0D47A1))
                                shap.topRiskDrivers.forEach { driver ->
                                    Text("• $driver", fontSize = 12.sp)
                                }
                            }
                        } else {
                            Text("Physical vitals not recorded yet.", fontSize = 12.sp, color = Color.Gray)
                        }
                    }
                }

                // 2. Mental Health Screening
                Card(shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text("2. Maternal Mental Health (PHQ-9)", fontWeight = FontWeight.Bold, fontSize = 15.sp)
                        if (res.mentalHealth.hasData) {
                            Text("Total Score: ${res.mentalHealth.totalScore}/27 (${res.mentalHealth.severity})", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                            Text("Trajectory: ${res.mentalHealth.longitudinalTrend?.replace('_', ' ')?.capitalize() ?: "Stable"}", fontSize = 12.sp)
                            if (res.mentalHealth.urgentSafetyFlag) {
                                Text("🚨 URGENT SAFETY ALERT: Thoughts of self-harm reported. Tele-MANAS 14416.", color = Color.Red, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                            }
                        } else {
                            Text("PHQ-9 screening not recorded yet.", fontSize = 12.sp, color = Color.Gray)
                        }
                    }
                }

                // 3. Nutrition Assessment
                Card(shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text("3. Maternal Diet & Nutrition (ICMR-NIN 2020)", fontWeight = FontWeight.Bold, fontSize = 15.sp)
                        if (res.nutrition.hasData) {
                            res.nutrition.currentBmi?.let {
                                Text("BMI: $it kg/m² (${res.nutrition.bmiCategory ?: "Normal"})  •  Weight Gain: +${res.nutrition.weightGainKg ?: 0f} kg", fontSize = 12.sp)
                            }
                            if (res.nutrition.foodInsecurity) {
                                Text("⚠️ Household food access difficulty reported.", color = Color(0xFFE65100), fontSize = 12.sp)
                            }
                            if (res.nutrition.gaps.isNotEmpty()) {
                                Text("Gaps: ${res.nutrition.gaps.joinToString(", ")}", fontSize = 12.sp)
                            } else {
                                Text("Nutrient intake meets pregnancy reference standard.", fontSize = 12.sp, color = Color(0xFF2E7D32))
                            }
                        } else {
                            Text("Nutrition assessment not recorded yet.", fontSize = 12.sp, color = Color.Gray)
                        }
                    }
                }

                // 4. Immunization Tracking
                Card(shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text("4. Maternal Immunization Status (Td UIP)", fontWeight = FontWeight.Bold, fontSize = 15.sp)
                        Text("Compliance: ${res.immunization.overallCompliance.replace('_', ' ').capitalize()}", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                        if (res.immunization.completedDoses.isNotEmpty()) {
                            Text("Completed: ${res.immunization.completedDoses.joinToString(", ")}", fontSize = 12.sp, color = Color(0xFF2E7D32))
                        }
                        if (res.immunization.overdueDoses.isNotEmpty()) {
                            Text("⚠️ Overdue: ${res.immunization.overdueDoses.joinToString(", ")}", fontSize = 12.sp, color = Color.Red)
                        }
                    }
                }

                // 5. Consolidated Action Plan
                Card(shape = RoundedCornerShape(12.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFFFAFAFA)), modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text("5. Prioritized Action Plan (${res.actionPlan.size} Items)", fontWeight = FontWeight.Bold, fontSize = 15.sp)
                        Spacer(modifier = Modifier.height(4.dp))
                        res.actionPlan.take(4).forEach { act ->
                            Text("• [${act.urgency.uppercase()}] ${act.actionText}", fontSize = 12.sp, modifier = Modifier.padding(vertical = 2.dp))
                        }
                    }
                }

                // Action Plan Navigation Button
                Button(
                    onClick = { navController.navigate(Screens.ActionPlan.passId(patientId)) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF1565C0))
                ) {
                    Text("Open Interactive ASHA Action Checklist", fontWeight = FontWeight.Bold)
                }

                // Disclaimer
                Text(
                    text = res.scientificDisclaimer,
                    fontSize = 11.sp,
                    color = Color.Gray
                )
            }
        }
    }
}
