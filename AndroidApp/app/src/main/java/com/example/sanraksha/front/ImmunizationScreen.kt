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
import java.time.LocalDate

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ImmunizationScreen(
    patientId: Long,
    navController: NavHostController,
    healthViewModel: HealthViewModel = viewModel(),
    patientViewModel: PatientViewModel = viewModel()
) {
    val patient by patientViewModel.getAPatientById(patientId).collectAsState(initial = null)
    val immunizationStatus by healthViewModel.immunizationStatus.collectAsState()
    val isLoading by healthViewModel.isLoading.collectAsState()
    val errorMessage by healthViewModel.errorMessage.collectAsState()

    var selectedVaccine by remember { mutableStateOf("Td-1") }
    var doseNumber by remember { mutableStateOf("1") }
    var administrationDate by remember { mutableStateOf(LocalDate.now().toString()) }
    var confirmationSource by remember { mutableStateOf("mcp_card") }
    var cardVerified by remember { mutableStateOf(true) }

    val scrollState = rememberScrollState()

    LaunchedEffect(patientId) {
        healthViewModel.fetchImmunizationStatus(patientId)
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Maternal Immunization Tracker", fontWeight = FontWeight.Bold, fontSize = 20.sp) },
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
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header Card
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFE3F2FD)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Patient: ${patient?.name ?: "ID #$patientId"}",
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = Color(0xFF0D47A1)
                    )
                    Text(
                        text = "Universal Immunization Programme (UIP) India — Td Maternal Schedule",
                        fontSize = 12.sp,
                        color = Color(0xFF1565C0)
                    )
                }
            }

            // Status Overview Card
            if (immunizationStatus != null) {
                val status = immunizationStatus!!
                val isFullyProtected = status.overallCompliance == "fully_protected"
                val hasOverdue = status.overallCompliance == "action_needed"

                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = when {
                            isFullyProtected -> Color(0xFFE8F5E9)
                            hasOverdue -> Color(0xFFFFEBEE)
                            else -> Color(0xFFFFF8E1)
                        }
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = if (isFullyProtected) Icons.Default.CheckCircle else Icons.Default.Warning,
                                contentDescription = null,
                                tint = if (isFullyProtected) Color(0xFF2E7D32) else if (hasOverdue) Color(0xFFC62828) else Color(0xFFF57F17)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Compliance: ${status.overallCompliance.replace('_', ' ').uppercase()}",
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp,
                                color = if (isFullyProtected) Color(0xFF1B5E20) else if (hasOverdue) Color(0xFFB71C1C) else Color(0xFFE65100)
                            )
                        }

                        Spacer(modifier = Modifier.height(8.dp))
                        status.doses.forEach { dose ->
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text("${dose.vaccineName} (Dose ${dose.doseNumber}):", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                                Text(dose.statusLabel, fontSize = 13.sp, color = if (dose.status == "completed") Color(0xFF2E7D32) else Color(0xFFC62828))
                            }
                        }
                    }
                }

                // Action Checklist
                if (status.ashaActionChecklist.isNotEmpty()) {
                    Card(
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFFAFAFA)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Text("📋 ASHA Immunization Tasks:", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                            status.ashaActionChecklist.forEach { act ->
                                Text("• $act", fontSize = 13.sp, modifier = Modifier.padding(vertical = 2.dp))
                            }
                        }
                    }
                }
            }

            Divider()

            // Form: Record Vaccine Dose
            Card(
                shape = RoundedCornerShape(12.dp),
                elevation = CardDefaults.cardElevation(2.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("Record Administered Vaccine Dose", fontWeight = FontWeight.Bold, fontSize = 16.sp)

                    // Vaccine Selector Buttons
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf("Td-1", "Td-2", "Td-Booster").forEach { vName ->
                            val isSel = selectedVaccine == vName
                            Button(
                                onClick = {
                                    selectedVaccine = vName
                                    doseNumber = if (vName == "Td-2") "2" else "1"
                                },
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (isSel) Color(0xFF1565C0) else Color(0xFFE0E0E0),
                                    contentColor = if (isSel) Color.White else Color.Black
                                )
                            ) {
                                Text(vName, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }

                    OutlinedTextField(
                        value = administrationDate,
                        onValueChange = { administrationDate = it },
                        label = { Text("Date of Administration (YYYY-MM-DD)") },
                        modifier = Modifier.fillMaxWidth()
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text("Physical MCP Card Verified", fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                            Text("Verified on mother's physical card or register", fontSize = 12.sp, color = Color.Gray)
                        }
                        Switch(
                            checked = cardVerified,
                            onCheckedChange = { cardVerified = it }
                        )
                    }

                    Button(
                        onClick = {
                            val req = CreateImmunizationRecordDto(
                                patientId = patientId,
                                vaccineName = selectedVaccine,
                                doseNumber = doseNumber.toIntOrNull() ?: 1,
                                status = "completed",
                                administrationDate = administrationDate,
                                confirmationSource = if (cardVerified) "mcp_card" else "verbal_recall",
                                cardVerified = cardVerified
                            )
                            healthViewModel.recordVaccination(req) { }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0D47A1)),
                        enabled = !isLoading
                    ) {
                        if (isLoading) {
                            CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
                        } else {
                            Text("Save Immunization Record", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }
    }
}
