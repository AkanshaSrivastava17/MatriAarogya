package com.example.sanraksha.front

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.runtime.LaunchedEffect
import androidx.navigation.NavHostController
import com.example.sanraksha.HealthViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MentalHealthResultScreen(
    patientId: Long,
    navController: NavHostController,
    healthViewModel: HealthViewModel = viewModel()
) {
    val assessment by healthViewModel.latestAssessment.collectAsState()
    val isLoading by healthViewModel.isLoading.collectAsState()
    val scrollState = rememberScrollState()

    LaunchedEffect(patientId) {
        if (healthViewModel.latestAssessment.value == null) {
            healthViewModel.fetchLatestAssessment(patientId)
        }
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Assessment Results", fontWeight = FontWeight.Bold, fontSize = 20.sp) },
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
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(scrollState)
                .padding(16.dp)
        ) {
            if (isLoading && assessment == null) {
                Box(modifier = Modifier.fillMaxWidth().height(300.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                return@Scaffold
            }

            if (assessment == null) {
                Box(modifier = Modifier.fillMaxWidth().height(300.dp), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("No recent assessment available.", style = MaterialTheme.typography.bodyLarge)
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = { healthViewModel.fetchLatestAssessment(patientId) }) {
                            Text("Retry Loading")
                        }
                    }
                }
                return@Scaffold
            }

            val res = assessment!!
            val isUrgent = res.safetyFlag || res.currentScreening.urgentFlag

            // ── SECTION 1: TOP PRIORITY SAFETY ESCALATION BANNER ──────────────────────
            if (isUrgent) {
                Card(
                    shape = RoundedCornerShape(14.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFFFEBEE)),
                    elevation = CardDefaults.cardElevation(defaultElevation = 6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                Icons.Default.Warning,
                                contentDescription = "Urgent Safety Alert",
                                tint = Color(0xFFC62828),
                                modifier = Modifier.size(28.dp)
                            )
                            Spacer(modifier = Modifier.width(10.dp))
                            Text(
                                text = "CRITICAL SAFETY ALERT",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.ExtraBold,
                                color = Color(0xFFC62828)
                            )
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = res.urgentMessage
                                ?: "Patient indicated thoughts of self-harm or suicide (PHQ-9 Item 9 > 0). " +
                                  "Immediate clinical evaluation and crisis intervention required. " +
                                  "Do not leave the mother unattended. Initiate referral protocol.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color(0xFFB71C1C),
                            fontWeight = FontWeight.SemiBold
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = Color(0xFFFFCDD2)
                        ) {
                            Text(
                                text = "National Tele-MANAS Helpline: 14416 / 1800-891-4416",
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                                style = MaterialTheme.typography.labelMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFFB71C1C)
                            )
                        }
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))
            }

            // ── SECTION 2: CURRENT MENTAL HEALTH SCREENING (TASK A) ────────────────────
            Card(
                shape = RoundedCornerShape(14.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Current Mental Health Screening (PHQ-9)",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column {
                            Text("PHQ-9 Score", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                            Text(
                                text = "${res.currentScreening.phq9Score} / 27",
                                style = MaterialTheme.typography.headlineMedium,
                                fontWeight = FontWeight.Bold,
                                color = if (res.currentScreening.screenPositive) Color(0xFFE65100) else Color(0xFF2E7D32)
                            )
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            Text("Severity Band", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                            Surface(
                                shape = RoundedCornerShape(16.dp),
                                color = when (res.currentScreening.severity) {
                                    "Severe", "Moderately Severe" -> Color(0xFFFFCDD2)
                                    "Moderate" -> Color(0xFFFFE0B2)
                                    "Mild" -> Color(0xFFFFF9C4)
                                    else -> Color(0xFFE8F5E9)
                                }
                            ) {
                                Text(
                                    text = res.currentScreening.severity,
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                                    fontWeight = FontWeight.Bold,
                                    color = Color.Black
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))
                    Divider(color = Color(0xFFEEEEEE))
                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Screening Status:", fontWeight = FontWeight.SemiBold)
                        Text(
                            text = if (res.currentScreening.screenPositive) "Positive (>=10 Cutoff)" else "Negative (<10)",
                            fontWeight = FontWeight.Bold,
                            color = if (res.currentScreening.screenPositive) Color(0xFFC62828) else Color(0xFF2E7D32)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // ── SECTION 3: CONTEXTUAL RISK ASSESSMENT (TASK B) ─────────────────────────
            res.contextualRisk?.let { ctx ->
                Card(
                    shape = RoundedCornerShape(14.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.White),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = "Contextual Vulnerability Risk (ML)",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.secondary
                        )
                        Spacer(modifier = Modifier.height(12.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column {
                                Text("Risk Probability", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                                Text(
                                    text = "${(ctx.probability * 100).toInt()}%",
                                    style = MaterialTheme.typography.headlineMedium,
                                    fontWeight = FontWeight.Bold,
                                    color = when (ctx.category) {
                                        "Elevated" -> Color(0xFFC62828)
                                        "Moderate" -> Color(0xFFE65100)
                                        else -> Color(0xFF2E7D32)
                                    }
                                )
                            }
                            Column(horizontalAlignment = Alignment.End) {
                                Text("Risk Category", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                                Surface(
                                    shape = RoundedCornerShape(16.dp),
                                    color = when (ctx.category) {
                                        "Elevated" -> Color(0xFFFFCDD2)
                                        "Moderate" -> Color(0xFFFFE0B2)
                                        else -> Color(0xFFE8F5E9)
                                    }
                                ) {
                                    Text(
                                        text = ctx.category,
                                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                                        fontWeight = FontWeight.Bold,
                                        color = Color.Black
                                    )
                                }
                            }
                        }

                        if (ctx.explanation != null) {
                            Spacer(modifier = Modifier.height(10.dp))
                            Text(
                                text = ctx.explanation,
                                style = MaterialTheme.typography.bodySmall,
                                color = Color(0xFF455A64)
                            )
                        }
                    }
                }
                Spacer(modifier = Modifier.height(14.dp))
            }

            // ── SECTION 4: LONGITUDINAL TRAJECTORY & HISTORY ───────────────────────────
            val long = res.longitudinal
            Card(
                shape = RoundedCornerShape(14.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Longitudinal Monitoring",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF37474F)
                    )
                    Spacer(modifier = Modifier.height(10.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Visit Sequence:", color = Color.Gray)
                        Text("Visit #${long.visitCount}", fontWeight = FontWeight.Bold)
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Score Change from Prior:", color = Color.Gray)
                        Text(
                            text = when {
                                long.phq9Change == null -> "Baseline (First Visit)"
                                long.phq9Change > 0 -> "+${long.phq9Change} pts (Worsening)"
                                long.phq9Change < 0 -> "${long.phq9Change} pts (Improving)"
                                else -> "0 pts (Unchanged)"
                            },
                            fontWeight = FontWeight.Bold,
                            color = when {
                                (long.phq9Change ?: 0) > 0 -> Color(0xFFC62828)
                                (long.phq9Change ?: 0) < 0 -> Color(0xFF2E7D32)
                                else -> Color.DarkGray
                            }
                        )
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Trajectory Trend:", color = Color.Gray)
                        Text(
                            text = when (long.trend) {
                                "increasing" -> "Increasing ↗"
                                "decreasing" -> "Decreasing ↘"
                                "stable" -> "Stable →"
                                else -> "Insufficient Data"
                            },
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Prior Elevated Screenings:", color = Color.Gray)
                        Text("${long.previousElevatedScreenings}", fontWeight = FontWeight.Bold)
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // ── SECTION 5: SCIENTIFIC TRANSPARENCY DISCLAIMER ─────────────────────────
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFECEFF1)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Info, contentDescription = null, tint = Color(0xFF546E7A))
                    Spacer(modifier = Modifier.width(10.dp))
                    Text(
                        text = "Scientific Note: Validated prospective postpartum prediction is not claimed as models are derived from cross-sectional data. This system provides screening and trajectory decision support.",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color(0xFF37474F)
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // ── SECTION 6: ACTION BUTTONS ─────────────────────────────────────────────
            Button(
                onClick = { navController.navigate(Screens.PatientHistory.passId(patientId)) },
                modifier = Modifier.fillMaxWidth().height(50.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.DateRange, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("View Patient Timeline & History")
            }

            Spacer(modifier = Modifier.height(10.dp))

            OutlinedButton(
                onClick = {
                    navController.popBackStack(Screens.Profile.passId(patientId), inclusive = false)
                },
                modifier = Modifier.fillMaxWidth().height(50.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Home, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Back to Patient Profile")
            }

            Spacer(modifier = Modifier.height(40.dp))
        }
    }
}
