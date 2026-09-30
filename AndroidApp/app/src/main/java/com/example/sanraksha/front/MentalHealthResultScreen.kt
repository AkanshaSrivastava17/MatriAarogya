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
                                text = "URGENT SAFETY ALERT",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.ExtraBold,
                                color = Color(0xFFC62828)
                            )
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = res.urgentMessage
                                ?: "Mother is having dark thoughts or feeling hopeless (Question 9 answered yes). " +
                                  "Do NOT leave the mother alone. Keep a family member with her and take her to the clinic or doctor today.",
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
                                text = "Free Tele-MANAS Helpline: 14416 / 1800-891-4416 (Call 24/7)",
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
                        text = "Mental Health Checkup (9 Questions)",
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
                            Text("Total Score", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                            Text(
                                text = "${res.currentScreening.phq9Score} / 27",
                                style = MaterialTheme.typography.headlineMedium,
                                fontWeight = FontWeight.Bold,
                                color = if (res.currentScreening.screenPositive) Color(0xFFE65100) else Color(0xFF2E7D32)
                            )
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            Text("Mood Level", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                            Surface(
                                shape = RoundedCornerShape(16.dp),
                                color = when (res.currentScreening.severity) {
                                    "Severe", "Moderately Severe" -> Color(0xFFFFCDD2)
                                    "Moderate" -> Color(0xFFFFE0B2)
                                    "Mild" -> Color(0xFFFFF9C4)
                                    else -> Color(0xFFE8F5E9)
                                }
                            ) {
                                val moodLabel = when (res.currentScreening.severity) {
                                    "Severe" -> "Severe Worry / Sadness"
                                    "Moderately Severe" -> "High Worry / Sadness"
                                    "Moderate" -> "Moderate Worry / Sadness"
                                    "Mild" -> "Mild Worry / Sadness"
                                    else -> "Normal / Doing Well"
                                }
                                Text(
                                    text = moodLabel,
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
                        Text("Screening Result:", fontWeight = FontWeight.SemiBold)
                        Text(
                            text = if (res.currentScreening.screenPositive) "Needs Medical Care (Score 10 or more)" else "Normal / Low Worry (Score below 10)",
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
                            text = "Life & Family Risk Factors",
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
                                Text("Risk Chance", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
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
                                Text("Risk Level", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                                Surface(
                                    shape = RoundedCornerShape(16.dp),
                                    color = when (ctx.category) {
                                        "Elevated" -> Color(0xFFFFCDD2)
                                        "Moderate" -> Color(0xFFFFE0B2)
                                        else -> Color(0xFFE8F5E9)
                                    }
                                ) {
                                    val catLabel = when (ctx.category) {
                                        "Elevated" -> "High Risk"
                                        "Moderate" -> "Medium Risk"
                                        else -> "Low Risk"
                                    }
                                    Text(
                                        text = catLabel,
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
                        text = "Visit-to-Visit Mood Tracking",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF37474F)
                    )
                    Spacer(modifier = Modifier.height(10.dp))

                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Visit Number:", color = Color.Gray)
                        Text("Visit #${long.visitCount}", fontWeight = FontWeight.Bold)
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Change Since Last Visit:", color = Color.Gray)
                        Text(
                            text = when {
                                long.phq9Change == null -> "First Checkup (Baseline)"
                                long.phq9Change > 0 -> "+${long.phq9Change} pts (Mood Worsened)"
                                long.phq9Change < 0 -> "${long.phq9Change} pts (Mood Improved)"
                                else -> "0 pts (Same as last visit)"
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
                        Text("Mood Direction:", color = Color.Gray)
                        Text(
                            text = when (long.trend) {
                                "increasing" -> "Getting Worse ↗"
                                "decreasing" -> "Getting Better ↘"
                                "stable" -> "Stable →"
                                else -> "First Assessment"
                            },
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Times High Score in Past:", color = Color.Gray)
                        Text("${long.previousElevatedScreenings}", fontWeight = FontWeight.Bold)
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // ── SECTION 5: ACTIONABLE GUIDANCE FOR ASHA WORKER ─────────────────────────
            val guidanceList = res.actionableGuidance
            if (guidanceList.isNotEmpty()) {
                Card(
                    shape = RoundedCornerShape(14.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFF1F8E9)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = "Actionable Steps",
                                tint = Color(0xFF2E7D32),
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Actionable Steps for ASHA Worker",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF1B5E20)
                            )
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "Simple, step-by-step actions to help the mother right now:",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF33691E)
                        )
                        Spacer(modifier = Modifier.height(10.dp))

                        guidanceList.forEach { action ->
                            val isCritical = action.startsWith("🚨") || action.contains("CRITICAL")
                            val isWarning = action.startsWith("⚠️") || action.contains("WORSENING")
                            val cardBg = when {
                                isCritical -> Color(0xFFFFEBEE)
                                isWarning -> Color(0xFFFFF3E0)
                                else -> Color.White
                            }
                            val borderClr = when {
                                isCritical -> Color(0xFFEF9A9A)
                                isWarning -> Color(0xFFFFCC80)
                                else -> Color(0xFFC8E6C9)
                            }
                            val textClr = when {
                                isCritical -> Color(0xFFB71C1C)
                                isWarning -> Color(0xFFE65100)
                                else -> Color(0xFF2E7D32)
                            }

                            Card(
                                shape = RoundedCornerShape(10.dp),
                                colors = CardDefaults.cardColors(containerColor = cardBg),
                                border = androidx.compose.foundation.BorderStroke(1.dp, borderClr),
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 4.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(10.dp),
                                    verticalAlignment = Alignment.Top
                                ) {
                                    Text(
                                        text = if (isCritical) "🚨" else if (isWarning) "⚠️" else "✓",
                                        fontWeight = FontWeight.Bold,
                                        color = textClr,
                                        modifier = Modifier.padding(end = 8.dp)
                                    )
                                    Text(
                                        text = action.removePrefix("🚨 ").removePrefix("⚠️ ").removePrefix("• "),
                                        style = MaterialTheme.typography.bodySmall,
                                        fontWeight = if (isCritical || isWarning) FontWeight.SemiBold else FontWeight.Normal,
                                        color = Color(0xFF263238),
                                        lineHeight = 18.sp
                                    )
                                }
                            }
                        }
                    }
                }
                Spacer(modifier = Modifier.height(14.dp))
            }

            // ── SECTION 6: SCIENTIFIC TRANSPARENCY DISCLAIMER ─────────────────────────
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFECEFF1)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Info, contentDescription = null, tint = Color(0xFF546E7A))
                    Spacer(modifier = Modifier.width(10.dp))
                    Text(
                        text = "Note for ASHA Worker: This tool helps you screen mood and track changes over time. Always take the mother to the doctor or PHC for medical checkup and diagnosis.",
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
