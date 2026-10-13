package com.example.sanraksha.front

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
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
fun ActionPlanScreen(
    patientId: Long,
    navController: NavHostController,
    healthViewModel: HealthViewModel = viewModel(),
    patientViewModel: PatientViewModel = viewModel()
) {
    val patient by patientViewModel.getAPatientById(patientId).collectAsState(initial = null)
    val actionPlan by healthViewModel.actionPlan.collectAsState()
    val isLoading by healthViewModel.isLoading.collectAsState()

    LaunchedEffect(patientId) {
        healthViewModel.fetchActionPlan(patientId)
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Prioritized Action Plan", fontWeight = FontWeight.Bold, fontSize = 20.sp) },
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
        if (isLoading && actionPlan == null) {
            Box(modifier = Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else {
            val plan = actionPlan
            val allActions = mutableListOf<ActionRecommendationDto>()
            plan?.let {
                allActions.addAll(it.emergencyActions)
                allActions.addAll(it.urgentActions)
                allActions.addAll(it.timelyActions)
                allActions.addAll(it.routineActions)
                allActions.addAll(it.infoActions)
            }

            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(vertical = 16.dp)
            ) {
                // Header Card
                item {
                    Card(
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Action Plan for: ${patient?.name ?: "ID #$patientId"}",
                                fontWeight = FontWeight.Bold,
                                fontSize = 18.sp,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Pending Tasks: ${plan?.pendingCount ?: 0}  |  Completed: ${plan?.completedCount ?: 0}",
                                fontSize = 13.sp,
                                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                            )
                        }
                    }
                }

                if (allActions.isEmpty()) {
                    item {
                        Box(modifier = Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) {
                            Text("No pending action recommendations for this patient.", color = Color.Gray)
                        }
                    }
                } else {
                    items(allActions) { act ->
                        ActionCard(
                            action = act,
                            onComplete = {
                                healthViewModel.updateActionStatus(act.actionId, "completed", "Done by ASHA", patientId)
                            },
                            onRefer = {
                                healthViewModel.updateActionStatus(act.actionId, "referred", "Referred to PHC/CHC", patientId)
                            }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun ActionCard(
    action: ActionRecommendationDto,
    onComplete: () -> Unit,
    onRefer: () -> Unit
) {
    val isEmergency = action.urgency == "emergency"
    val isUrgent = action.urgency == "urgent"
    val isCompleted = action.status in listOf("completed", "referred")

    val cardColor = when {
        isCompleted -> Color(0xFFF5F5F5)
        isEmergency -> Color(0xFFFFEBEE)
        isUrgent -> Color(0xFFFFF3E0)
        action.urgency == "timely" -> Color(0xFFE3F2FD)
        else -> Color(0xFFE8F5E9)
    }

    val badgeColor = when {
        isEmergency -> Color(0xFFC62828)
        isUrgent -> Color(0xFFE65100)
        action.urgency == "timely" -> Color(0xFF1565C0)
        else -> Color(0xFF2E7D32)
    }

    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = cardColor),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = action.urgency.uppercase(),
                    color = badgeColor,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp
                )
                Text(
                    text = "Timeframe: ${action.timeframe.replace('_', ' ')}",
                    fontSize = 11.sp,
                    color = Color.DarkGray
                )
            }

            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = action.triggerObservation,
                fontWeight = FontWeight.Bold,
                fontSize = 14.sp
            )

            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = action.actionText,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
                color = if (isEmergency) Color(0xFFB71C1C) else Color(0xFF1B5E20)
            )

            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Responsible: ${action.responsiblePerson}  •  Source: ${action.ruleSource}",
                fontSize = 11.sp,
                color = Color.Gray
            )

            Spacer(modifier = Modifier.height(8.dp))

            if (!isCompleted) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = onComplete,
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2E7D32))
                    ) {
                        Text("Mark Done", fontSize = 12.sp)
                    }
                    if (action.referralRequired) {
                        OutlinedButton(
                            onClick = onRefer,
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Record Referral", fontSize = 12.sp)
                        }
                    }
                }
            } else {
                Text("✓ Status: ${action.status.replace('_', ' ').capitalize()}", color = Color(0xFF2E7D32), fontWeight = FontWeight.Bold, fontSize = 12.sp)
            }
        }
    }
}
