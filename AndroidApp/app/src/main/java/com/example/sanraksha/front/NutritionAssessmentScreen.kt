package com.example.sanraksha.front

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.example.sanraksha.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NutritionAssessmentScreen(
    patientId: Long,
    navController: NavHostController,
    healthViewModel: HealthViewModel = viewModel(),
    patientViewModel: PatientViewModel = viewModel()
) {
    val patient by patientViewModel.getAPatientById(patientId).collectAsState(initial = null)
    val latestNutrition by healthViewModel.latestNutrition.collectAsState()
    val isLoading by healthViewModel.isLoading.collectAsState()
    val errorMessage by healthViewModel.errorMessage.collectAsState()

    var heightCm by remember { mutableStateOf("155") }
    var weightKg by remember { mutableStateOf("54") }
    var preWeightKg by remember { mutableStateOf("50") }
    var energyKcal by remember { mutableStateOf("1850") }
    var proteinG by remember { mutableStateOf("45") }
    var carbG by remember { mutableStateOf("250") }
    var fatG by remember { mutableStateOf("30") }
    var ironMg by remember { mutableStateOf("20") }
    var calciumMg by remember { mutableStateOf("800") }
    var foodInsecurity by remember { mutableStateOf(false) }
    var dietaryPattern by remember { mutableStateOf("vegetarian") }

    val scrollState = rememberScrollState()

    LaunchedEffect(patientId) {
        healthViewModel.fetchLatestNutrition(patientId)
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Maternal Diet & Nutrition", fontWeight = FontWeight.Bold, fontSize = 20.sp) },
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
                colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Patient: ${patient?.name ?: "ID #$patientId"}",
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = Color(0xFF1B5E20)
                    )
                    Text(
                        text = "ICMR-NIN (2020) Dietary Assessment for Indian Pregnant Women",
                        fontSize = 12.sp,
                        color = Color(0xFF2E7D32)
                    )
                }
            }

            // Section 1: Anthropometrics
            Card(
                shape = RoundedCornerShape(12.dp),
                elevation = CardDefaults.cardElevation(2.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("1. Height & Weight Tracking", fontWeight = FontWeight.Bold, fontSize = 16.sp)

                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(
                            value = heightCm,
                            onValueChange = { heightCm = it },
                            label = { Text("Height (cm)") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = weightKg,
                            onValueChange = { weightKg = it },
                            label = { Text("Current Wt (kg)") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.weight(1f)
                        )
                    }

                    OutlinedTextField(
                        value = preWeightKg,
                        onValueChange = { preWeightKg = it },
                        label = { Text("Pre-pregnancy Weight (kg)") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }

            // Section 2: Dietary Intake (24h Recall)
            Card(
                shape = RoundedCornerShape(12.dp),
                elevation = CardDefaults.cardElevation(2.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("2. Estimated Daily Nutrient Intake", fontWeight = FontWeight.Bold, fontSize = 16.sp)

                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(
                            value = energyKcal,
                            onValueChange = { energyKcal = it },
                            label = { Text("Energy (kcal)") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = proteinG,
                            onValueChange = { proteinG = it },
                            label = { Text("Protein (g)") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.weight(1f)
                        )
                    }

                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(
                            value = carbG,
                            onValueChange = { carbG = it },
                            label = { Text("Carbs (g)") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = fatG,
                            onValueChange = { fatG = it },
                            label = { Text("Visible Fat (g)") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.weight(1f)
                        )
                    }

                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(
                            value = ironMg,
                            onValueChange = { ironMg = it },
                            label = { Text("Iron (mg)") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = calciumMg,
                            onValueChange = { calciumMg = it },
                            label = { Text("Calcium (mg)") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }

            // Section 3: Household & Food Insecurity
            Card(
                shape = RoundedCornerShape(12.dp),
                elevation = CardDefaults.cardElevation(2.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("3. Household Context", fontWeight = FontWeight.Bold, fontSize = 16.sp)

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text("Food Affordability / Access Difficulty", fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                            Text("Family struggles with regular nutritious food access", fontSize = 12.sp, color = Color.Gray)
                        }
                        Switch(
                            checked = foodInsecurity,
                            onCheckedChange = { foodInsecurity = it }
                        )
                    }
                }
            }

            if (errorMessage != null) {
                Text(
                    text = errorMessage ?: "",
                    color = MaterialTheme.colorScheme.error,
                    fontSize = 13.sp
                )
            }

            Button(
                onClick = {
                    val req = CreateNutritionAssessmentDto(
                        patientId = patientId,
                        gestationalAge = patient?.pregnancyWeek ?: 20,
                        heightCm = heightCm.toFloatOrNull(),
                        currentWeightKg = weightKg.toFloatOrNull(),
                        prePregnancyWeightKg = preWeightKg.toFloatOrNull(),
                        intake = NutrientIntakeDto(
                            energyKcal = energyKcal.toFloatOrNull(),
                            proteinG = proteinG.toFloatOrNull(),
                            carbohydratesG = carbG.toFloatOrNull(),
                            fatG = fatG.toFloatOrNull(),
                            ironMg = ironMg.toFloatOrNull(),
                            calciumMg = calciumMg.toFloatOrNull()
                        ),
                        dietaryPattern = dietaryPattern,
                        foodInsecurity = foodInsecurity
                    )
                    healthViewModel.submitNutritionAssessment(req) { }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2E7D32)),
                enabled = !isLoading
            ) {
                if (isLoading) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
                } else {
                    Text("Evaluate Nutrition & Compare ICMR-NIN", fontWeight = FontWeight.Bold)
                }
            }

            // Display Results if Available
            if (latestNutrition != null) {
                val eval = latestNutrition!!
                Divider(modifier = Modifier.padding(vertical = 8.dp))

                Text("Assessment Results & Recommendations", fontWeight = FontWeight.Bold, fontSize = 18.sp)

                // Weight Progression Card
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFF1F8E9)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text("⚖️ Weight & BMI Progression", fontWeight = FontWeight.Bold, fontSize = 15.sp, color = Color(0xFF1B5E20))
                        eval.weightProgression.currentBmi?.let { bmi ->
                            Text("Current BMI: $bmi kg/m² (${eval.weightProgression.currentBmiCategory ?: "Normal"})", fontSize = 13.sp)
                        }
                        eval.weightProgression.gestationalWeightGainKg?.let { gain ->
                            Text("Gestational Weight Gain: +$gain kg (Target: ${eval.weightProgression.recommendedGainRange ?: "11.5 - 16.0 kg"})", fontSize = 13.sp)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(eval.weightProgression.guidance, fontSize = 12.sp, color = Color(0xFF33691E))
                    }
                }

                // Gaps Card
                if (eval.gaps.isNotEmpty()) {
                    Card(
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF3E0)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Warning, contentDescription = null, tint = Color(0xFFE65100))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Nutritional Gaps Identified:", fontWeight = FontWeight.Bold, color = Color(0xFFE65100))
                            }
                            eval.gaps.forEach { gap ->
                                Text("• $gap", fontSize = 13.sp, modifier = Modifier.padding(vertical = 2.dp))
                            }
                        }
                    }
                }

                // Action Recommendations Card
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Check, contentDescription = null, tint = Color(0xFF2E7D32))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("Food Recommendations for Mother:", fontWeight = FontWeight.Bold, color = Color(0xFF1B5E20))
                        }
                        eval.recommendations.forEach { rec ->
                            Text(rec, fontSize = 13.sp, modifier = Modifier.padding(vertical = 2.dp))
                        }
                    }
                }
            }
        }
    }
}
