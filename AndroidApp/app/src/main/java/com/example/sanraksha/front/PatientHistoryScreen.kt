package com.example.sanraksha.front

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.draw.clip
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.example.sanraksha.HealthViewModel
import com.example.sanraksha.PatientHistoryVisitItem

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PatientHistoryScreen(
    patientId: Long,
    navController: NavHostController,
    healthViewModel: HealthViewModel = viewModel(),
    patientViewModel: PatientViewModel = viewModel()
) {
    val patient by patientViewModel.getAPatientById(patientId).collectAsState(initial = null)
    val history by healthViewModel.patientHistory.collectAsState()
    val isLoading by healthViewModel.isLoading.collectAsState()

    LaunchedEffect(patientId) {
        healthViewModel.fetchPatientHistory(patientId)
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Longitudinal History", fontWeight = FontWeight.Bold, fontSize = 20.sp) },
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
        if (isLoading && history.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else if (history.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("No mental health visit history yet.", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Complete a PHQ-9 screening to record the first visit.", color = Color.Gray)
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(horizontal = 16.dp),
                contentPadding = PaddingValues(bottom = 60.dp, top = 16.dp)
            ) {
                // Header card
                item {
                    Card(
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Text(
                                text = "Patient: ${patient?.name ?: "ID #$patientId"}",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                            Text(
                                text = "Total Logged Visits: ${history.size} (Append-only record)",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }

                // Visual Trajectory Chart
                if (history.size >= 2) {
                    item {
                        Card(
                            shape = RoundedCornerShape(14.dp),
                            elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
                            colors = CardDefaults.cardColors(containerColor = Color.White),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text(
                                    text = "PHQ-9 Score Progression Across Visits",
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary
                                )
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    text = "Threshold line at score 10 (Clinical At-Risk Cutoff)",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = Color.Gray
                                )
                                Spacer(modifier = Modifier.height(12.dp))

                                // Native Compose Canvas Line Chart
                                PhqTrendCanvas(visits = history)
                            }
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                    }
                }

                item {
                    Text(
                        text = "Visit Timeline",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF263238)
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                }

                // Chronological cards for all visits
                itemsIndexed(history) { index, item ->
                    VisitTimelineCard(visitNumber = index + 1, item = item)
                    Spacer(modifier = Modifier.height(10.dp))
                }
            }
        }
    }
}

@Composable
fun VisitTimelineCard(visitNumber: Int, item: PatientHistoryVisitItem) {
    val isUrgent = item.urgentSafetyFlag > 0

    Card(
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isUrgent) Color(0xFFFFEBEE) else Color.White
        ),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(32.dp)
                            .clip(CircleShape)
                            .background(if (isUrgent) Color(0xFFC62828) else MaterialTheme.colorScheme.primary),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "#$visitNumber",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "Visit $visitNumber — ${item.visitDate}",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold
                        )
                        val timing = when {
                            item.trimester == "Postpartum" -> "Postpartum Follow-up"
                            item.gestationalAge != null -> "${item.gestationalAge} weeks (${item.trimester})"
                            else -> item.trimester
                        }
                        Text(text = timing, style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                    }
                }

                if (isUrgent) {
                    Surface(shape = RoundedCornerShape(8.dp), color = Color(0xFFFFCDD2)) {
                        Row(modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Warning, contentDescription = null, tint = Color(0xFFC62828), modifier = Modifier.size(14.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Urgent Safety", style = MaterialTheme.typography.labelSmall, color = Color(0xFFC62828), fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(10.dp))
            Divider(color = Color(0xFFEEEEEE))
            Spacer(modifier = Modifier.height(8.dp))

            // Scores and Risk Row
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column {
                    Text("PHQ-9 Score", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                    Text(
                        text = "${item.totalScore} / 27 (${item.severity ?: "N/A"})",
                        fontWeight = FontWeight.Bold,
                        color = if (item.atRisk == 1) Color(0xFFE65100) else Color(0xFF2E7D32)
                    )
                }

                Column(horizontalAlignment = Alignment.End) {
                    Text("Contextual Risk", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                    val riskProb = item.riskProbability?.let { "${(it * 100).toInt()}%" } ?: "N/A"
                    Text(
                        text = "$riskProb (${item.riskCategory ?: "Unassessed"})",
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // Trajectory indicators
            if (item.trend != null && item.trend != "insufficient_data") {
                Spacer(modifier = Modifier.height(6.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Score Delta:", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                    val delta = item.scoreChange?.let { if (it > 0) "+$it" else "$it" } ?: "0"
                    Text(
                        text = "$delta pts (${item.trend.replaceFirstChar { it.uppercase() }})",
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.SemiBold,
                        color = when (item.trend) {
                            "increasing" -> Color(0xFFC62828)
                            "decreasing" -> Color(0xFF2E7D32)
                            else -> Color.DarkGray
                        }
                    )
                }
            }

            // Vitals summary if present
            if (item.systolicBp != null || item.heartRate != null) {
                Spacer(modifier = Modifier.height(6.dp))
                val bp = if (item.systolicBp != null) "${item.systolicBp.toInt()}/${item.diastolicBp?.toInt() ?: 0} mmHg" else null
                val hr = if (item.heartRate != null) "${item.heartRate.toInt()} bpm" else null
                val vitalsStr = listOfNotNull(bp, hr).joinToString(" • ")
                Text("Vitals: $vitalsStr", style = MaterialTheme.typography.bodySmall, color = Color(0xFF546E7A))
            }
        }
    }
}

@Composable
fun PhqTrendCanvas(visits: List<PatientHistoryVisitItem>) {
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(160.dp)
            .padding(vertical = 8.dp)
    ) {
        val width = size.width
        val height = size.height
        val maxScore = 27f
        val stepX = if (visits.size > 1) width / (visits.size - 1) else width

        // Draw 10-score clinical cutoff guideline
        val cutoffY = height - (10f / maxScore) * height
        drawLine(
            color = Color(0xFFFF8A80),
            start = Offset(0f, cutoffY),
            end = Offset(width, cutoffY),
            strokeWidth = 2f,
            pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 10f), 0f)
        )

        // Draw line connecting scores
        val points = visits.mapIndexed { index, v ->
            val x = index * stepX
            val y = height - (v.totalScore.toFloat() / maxScore) * height
            Offset(x, y)
        }

        for (i in 0 until points.size - 1) {
            drawLine(
                color = Color(0xFF3949AB),
                start = points[i],
                end = points[i + 1],
                strokeWidth = 4f
            )
        }

        // Draw data points with distinct colored markers
        points.forEachIndexed { idx, p ->
            val v = visits[idx]
            val dotColor = when {
                v.urgentSafetyFlag > 0 -> Color(0xFFD32F2F)
                v.atRisk > 0 -> Color(0xFFF57C00)
                else -> Color(0xFF388E3C)
            }
            drawCircle(color = Color.White, radius = 9f, center = p)
            drawCircle(color = dotColor, radius = 6f, center = p)
        }
    }
}
