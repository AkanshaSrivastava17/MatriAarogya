package com.example.sanraksha.front

import android.adservices.ondevicepersonalization.LogReader
import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.Divider
import androidx.compose.material.Tab
import androidx.compose.material.TabRow
import androidx.compose.material.TabRowDefaults.tabIndicatorOffset
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material.icons.filled.Warning
import com.example.sanraksha.PhysicalVitalsGuidance
import androidx.compose.runtime.Composable
import androidx.compose.runtime.ComposeCompilerApi
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.key.Key.Companion.Tab
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import co.yml.charts.axis.AxisData
import co.yml.charts.common.model.Point
import co.yml.charts.ui.linechart.LineChart
import co.yml.charts.ui.linechart.model.GridLines
import co.yml.charts.ui.linechart.model.IntersectionPoint
import co.yml.charts.ui.linechart.model.Line
import co.yml.charts.ui.linechart.model.LineChartData
import co.yml.charts.ui.linechart.model.LinePlotData
import co.yml.charts.ui.linechart.model.LineStyle


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(patientId:Long,
                  patientViewModel:PatientViewModel = viewModel(),
                  vitalsViewModel:VitalsViewModel = viewModel(),
                  navController: NavHostController

) {
    val patient by patientViewModel.getAPatientById(patientId).collectAsState(initial = null)
    val vitalsList by vitalsViewModel.getVitalsByPatientId(patientId)
        .collectAsState(initial = emptyList())
    Log.d("vitalsList","$vitalsList")

    Scaffold(
        containerColor = Color(0xFFFDFDFD),
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Text(
                        text = patient?.name ?: "",
                        fontSize = 30.sp,
                        fontWeight = FontWeight.Bold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 16.dp),
            contentPadding = PaddingValues(bottom = 80.dp)
        ) {
            item { Divider() }
            item { patient?.let { PatientHeader(it) } }

            item {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 10.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFF3E5F5)),
                    elevation = CardDefaults.cardElevation(3.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "🧠 Maternal Mental Health & Postpartum",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF6A1B9A)
                            )
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "PHQ-9 depression screening, acute safety assessment & visit-over-visit trajectory.",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF4A148C)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(
                                onClick = { navController.navigate(Screens.MentalHealthScreening.passId(patientId)) },
                                modifier = Modifier.weight(1.2f),
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7B1FA2))
                            ) {
                                Text("Start PHQ-9", fontSize = 13.sp, fontWeight = FontWeight.Bold)
                            }
                            OutlinedButton(
                                onClick = { navController.navigate(Screens.PatientHistory.passId(patientId)) },
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("📈 Trajectory", fontSize = 13.sp)
                            }
                        }
                    }
                }
            }

            item {
                if (vitalsList.isNotEmpty()) {
                    val latestVitals = vitalsList.last()
                    val latestRisk = latestVitals.predictedRisk
                    Log.d("latestRisk","$latestRisk")
                    val riskText = if (latestVitals.predictedRiskLabel.isNotBlank()) {
                        latestVitals.predictedRiskLabel
                    } else if (latestRisk == 1) {
                        "High Risk"
                    } else {
                        "Low Risk"
                    }
                    val isHighRisk = latestRisk == 1
                    val riskColor = if (isHighRisk) Color(0xFFC62828) else Color(0xFF2E7D32)

                    val (factors, actions) = PhysicalVitalsGuidance.evaluateFactorsAndActions(
                        sys = latestVitals.Systolic_BP,
                        dia = latestVitals.Diastolic,
                        bs = latestVitals.BS,
                        bmi = latestVitals.BMI,
                        prevComp = latestVitals.Previous_Complications,
                        preDiabetes = latestVitals.Preexisting_Diabetes,
                        gestDiabetes = latestVitals.Gestational_Diabetes,
                        mentalHealth = latestVitals.Mental_Health,
                        isHighRisk = isHighRisk
                    )

                    var showActions by remember { mutableStateOf(false) }

                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp),
                        shape = RoundedCornerShape(14.dp),
                        elevation = CardDefaults.cardElevation(3.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = if (isHighRisk) Color(0xFFFFEBEE) else Color(0xFFF1F8E9)
                        )
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier.weight(1f)
                                ) {
                                    Icon(
                                        imageVector = if (isHighRisk) Icons.Default.Warning else Icons.Default.Favorite,
                                        contentDescription = null,
                                        tint = riskColor,
                                        modifier = Modifier.padding(end = 8.dp)
                                    )
                                    Column {
                                        Text(
                                            text = "Physical Vitals: $riskText",
                                            color = riskColor,
                                            fontSize = 16.sp,
                                            fontWeight = FontWeight.Bold
                                        )
                                        if (factors.isNotEmpty()) {
                                            Text(
                                                text = factors.first(),
                                                fontSize = 12.sp,
                                                color = Color(0xFF455A64)
                                            )
                                        }
                                    }
                                }
                                TextButton(onClick = { showActions = !showActions }) {
                                    Text(
                                        text = if (showActions) "Hide ▲" else "ASHA Steps ▼",
                                        color = riskColor,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 12.sp
                                    )
                                }
                            }

                            if (showActions) {
                                Spacer(modifier = Modifier.height(8.dp))
                                Divider(color = Color(0xFFE0E0E0))
                                Spacer(modifier = Modifier.height(8.dp))

                                Text(
                                    text = "Actionable Steps for ASHA Worker:",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 13.sp,
                                    color = if (isHighRisk) Color(0xFFC62828) else Color(0xFF1B5E20)
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                actions.forEach { action ->
                                    val isCritical = action.startsWith("🚨")
                                    val isWarning = action.startsWith("⚠️")
                                    Text(
                                        text = action,
                                        fontSize = 12.sp,
                                        fontWeight = if (isCritical || isWarning) FontWeight.SemiBold else FontWeight.Normal,
                                        color = when {
                                            isCritical -> Color(0xFFB71C1C)
                                            isWarning -> Color(0xFFE65100)
                                            else -> Color(0xFF2E7D32)
                                        },
                                        modifier = Modifier.padding(vertical = 2.dp)
                                    )
                                }
                            }
                        }
                    }
                }
            }

            item {
                val tabTitles = listOf("BP", "BMI", "HR")
                var selectedTabIndex by remember { mutableStateOf(0) }

                Card(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                    shape = RoundedCornerShape(20.dp),
                    elevation = CardDefaults.cardElevation(4.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFF5F5F5))
                ) {
                    TabRow(
                        selectedTabIndex = selectedTabIndex,
                        backgroundColor = Color.Transparent,
                        contentColor = Color.Black,
                        indicator = { tabPositions ->
                            Box(
                                modifier = Modifier
                                    .tabIndicatorOffset(tabPositions[selectedTabIndex])
                                    .height(4.dp)
                                    .clip(RoundedCornerShape(4.dp))
                                    .background(Color(0xFF6200EE))
                            )
                        },
                        divider = {}
                    ) {
                        tabTitles.forEachIndexed { index, title ->
                            Tab(
                                selected = selectedTabIndex == index,
                                onClick = { selectedTabIndex = index },
                                text = {
                                    Text(
                                        text = title,
                                        fontWeight = FontWeight.SemiBold,
                                        color = if (selectedTabIndex == index) Color(0xFF6200EE) else Color.DarkGray
                                    )
                                }
                            )
                        }
                    }
                }

                when (selectedTabIndex) {
                    0 -> BPSection(vitalsList)
                    1 -> BMISection(vitalsList)
                    2 -> HRSection(vitalsList)
                }
            }

//            item {
//                if (vitalsList.isNotEmpty()) {
//                    val latestRisk = vitalsList.last().predictedRisk
//                    Log.d("latestRisk","$latestRisk")
//                    val riskText = if (latestRisk == 1) "High Risk" else "Low Risk"
//                    val riskColor = if (latestRisk == 1) Color.Red else Color(0xFF4CAF50)
//
//                    Card(
//                        modifier = Modifier
//                            .fillMaxWidth()
//                            .padding(vertical = 8.dp),
//                        shape = RoundedCornerShape(12.dp),
//                        elevation = CardDefaults.cardElevation(4.dp),
//                        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF8E1))
//                    ) {
//                        Row(
//                            modifier = Modifier
//                                .padding(16.dp),
//                            verticalAlignment = Alignment.CenterVertically
//                        ) {
//                            Icon(
//                                imageVector = Icons.Default.Favorite,
//                                contentDescription = null,
//                                tint = riskColor,
//                                modifier = Modifier.padding(end = 8.dp)
//                            )
//                            Text(
//                                text = "Recent Risk Prediction: $riskText",
//                                color = riskColor,
//                                fontSize = 16.sp,
//                                fontWeight = FontWeight.SemiBold
//                            )
//                        }
//                    }
//                }
//            }

            item {
                Button(
                    onClick = { navController.navigate(Screens.RecordVitals.passId(patientId)) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 16.dp)
                ) {
                    Text("Record Physical Vitals & Predict Risk")
                }

                Spacer(modifier = Modifier.height(10.dp))

                Button(
                    onClick = { navController.navigate(Screens.MentalHealthScreening.passId(patientId)) },
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("🧠 Maternal Mental Health Screen (PHQ-9)")
                }

                Spacer(modifier = Modifier.height(10.dp))

                OutlinedButton(
                    onClick = { navController.navigate(Screens.PatientHistory.passId(patientId)) },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("📈 Longitudinal Trajectory & History")
                }

                Spacer(modifier = Modifier.height(10.dp))

                Button(
                    onClick = { navController.navigate(Screens.NutritionAssessment.passId(patientId)) },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2E7D32)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("🥗 Maternal Diet & Nutrition (ICMR-NIN)")
                }

                Spacer(modifier = Modifier.height(10.dp))

                Button(
                    onClick = { navController.navigate(Screens.ImmunizationTracking.passId(patientId)) },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0D47A1)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("💉 Maternal Immunization Tracker (Td UIP)")
                }

                Spacer(modifier = Modifier.height(10.dp))

                Button(
                    onClick = { navController.navigate(Screens.ActionPlan.passId(patientId)) },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFE65100)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("📋 Prioritized ASHA Action Plan")
                }

                Spacer(modifier = Modifier.height(10.dp))

                Button(
                    onClick = { navController.navigate(Screens.ComprehensiveSummary.passId(patientId)) },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4A148C)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("📄 Comprehensive Health Dossier")
                }
            }
        }
    }
}



@Composable
fun PatientHeader(patient: Patient) {
    Card(
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp),
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF2F2F7))
    ) {
        Row(modifier = Modifier.padding(16.dp)) {
            Icon(
                imageVector = Icons.Default.Person,
                contentDescription = "Profile Icon",
                modifier = Modifier.size(64.dp)
                    .clip(CircleShape)
                    .background(Color(0xFFE0E0E0))
                    .padding(12.dp),
                tint = Color.Gray
            )

            Spacer(modifier = Modifier.width(16.dp))

            Column {
                Text(text = patient.name, style = MaterialTheme.typography.titleMedium, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                Row {
                    Text(text = "Pregnancy Week: ",color= Color.Gray)
                    Text(text="${patient.pregnancyWeek}", fontWeight = FontWeight.Bold)
                }
                Row{
                    Text(
                    text = "Last Checkup:",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.Gray
                )
                    Text(text = " ${patient.lastCheckup}",
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Bold
                    )

                }

            }

        }
    }
}