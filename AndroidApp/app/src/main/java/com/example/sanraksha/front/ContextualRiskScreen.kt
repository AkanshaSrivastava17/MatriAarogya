package com.example.sanraksha.front

import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import com.example.sanraksha.*
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ContextualRiskScreen(
    patientId: Long,
    phqScores: Map<String, Int>,
    navController: NavHostController,
    healthViewModel: HealthViewModel = viewModel(),
    patientViewModel: PatientViewModel = viewModel(),
    vitalsViewModel: VitalsViewModel = viewModel()
) {
    val context = LocalContext.current
    val scrollState = rememberScrollState()

    val patient by patientViewModel.getAPatientById(patientId).collectAsState(initial = null)
    val vitalsList by vitalsViewModel.getVitalsByPatientId(patientId).collectAsState(initial = emptyList())
    val isLoading by healthViewModel.isLoading.collectAsState()
    val errorMsg by healthViewModel.errorMessage.collectAsState()

    // Form inputs initialized with clinical human-readable defaults
    var femaleEducation by remember { mutableStateOf("Secondary") }
    var husbandEducation by remember { mutableStateOf("Secondary") }
    var workingStatus by remember { mutableStateOf("Housewife") }
    var previousMiscarriage by remember { mutableStateOf("No") }
    var sufficientMoney by remember { mutableStateOf("Yes") }
    var familySystem by remember { mutableStateOf("Nuclear") }
    var malePreference by remember { mutableStateOf("No") }
    var relationshipMil by remember { mutableStateOf("Good") }
    var gravida by remember { mutableStateOf("Primigravida") }
    var physicalHealth by remember { mutableStateOf("Good") }
    var appearanceAcceptance by remember { mutableStateOf("Satisfied") }

    var gestationalAgeWeeks by remember { mutableStateOf(patient?.pregnancyWeek?.toString() ?: "20") }
    var numSons by remember { mutableStateOf("0") }
    var numDaughters by remember { mutableStateOf("0") }
    var isPostpartum by remember { mutableStateOf(false) }

    LaunchedEffect(patient) {
        if (patient != null && patient!!.pregnancyWeek > 0) {
            gestationalAgeWeeks = patient!!.pregnancyWeek.toString()
        }
    }

    LaunchedEffect(errorMsg) {
        errorMsg?.let {
            Toast.makeText(context, "Error: $it", Toast.LENGTH_LONG).show()
        }
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Psychosocial Context", fontWeight = FontWeight.Bold, fontSize = 20.sp) },
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
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Info, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(modifier = Modifier.width(10.dp))
                    Text(
                        text = "This psychosocial context is used by the contextual ML risk model to estimate baseline vulnerability without symptom label leakage.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Postpartum toggle
            Card(
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(14.dp).fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text("Postpartum Follow-up Visit", fontWeight = FontWeight.Bold)
                        Text(
                            text = if (isPostpartum) "Patient has delivered (Postpartum status)" else "Patient is currently pregnant",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color.Gray
                        )
                    }
                    Switch(
                        checked = isPostpartum,
                        onCheckedChange = { isPostpartum = it }
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            if (!isPostpartum) {
                OutlinedTextField(
                    value = gestationalAgeWeeks,
                    onValueChange = { gestationalAgeWeeks = it },
                    label = { Text("Gestational Age (weeks)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(10.dp)
                )
                Spacer(modifier = Modifier.height(12.dp))
            }

            // Dropdowns for contextual categorical features
            ContextDropdownField("Female Education", listOf("Illiterate", "Primary", "Secondary", "Higher Secondary", "Graduate or Higher"), femaleEducation) { femaleEducation = it }
            ContextDropdownField("Husband Education", listOf("Illiterate", "Primary", "Secondary", "Higher Secondary", "Graduate or Higher"), husbandEducation) { husbandEducation = it }
            ContextDropdownField("Working Status", listOf("Housewife", "Employed", "Self-employed", "Unemployed"), workingStatus) { workingStatus = it }
            ContextDropdownField("Financial Sufficiency for Basic Needs", listOf("Yes", "No"), sufficientMoney) { sufficientMoney = it }
            ContextDropdownField("Family System", listOf("Nuclear", "Joint"), familySystem) { familySystem = it }
            ContextDropdownField("Male Gender Preference Pressure", listOf("No", "Yes"), malePreference) { malePreference = it }
            ContextDropdownField("Relationship with Mother-in-Law", listOf("Good", "Fair", "Poor", "Not applicable"), relationshipMil) { relationshipMil = it }
            ContextDropdownField("Previous Miscarriage", listOf("No", "Yes"), previousMiscarriage) { previousMiscarriage = it }
            ContextDropdownField("Gravida Status", listOf("Primigravida", "Multigravida"), gravida) { gravida = it }
            ContextDropdownField("Perceived Physical Health", listOf("Good", "Fair", "Poor"), physicalHealth) { physicalHealth = it }
            ContextDropdownField("Appearance Acceptance", listOf("Satisfied", "Neutral", "Dissatisfied"), appearanceAcceptance) { appearanceAcceptance = it }

            Spacer(modifier = Modifier.height(8.dp))

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(
                    value = numSons,
                    onValueChange = { numSons = it },
                    label = { Text("No. of Sons") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(10.dp)
                )
                OutlinedTextField(
                    value = numDaughters,
                    onValueChange = { numDaughters = it },
                    label = { Text("No. of Daughters") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(10.dp)
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Submit Button
            Button(
                onClick = {
                    val today = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
                    val ga = if (!isPostpartum) gestationalAgeWeeks.toIntOrNull() ?: 20 else null
                    val deliveryDate = if (isPostpartum) today else null
                    val sons = numSons.toIntOrNull() ?: 0
                    val daughters = numDaughters.toIntOrNull() ?: 0
                    val totalKids = sons + daughters
                    val patientAge = 25f // default age if not recorded

                    val contextValues = mapOf<String, Any>(
                        "Female Education" to femaleEducation,
                        "Husband Education" to husbandEducation,
                        "Working Status" to workingStatus,
                        "Previous Miscarriage" to previousMiscarriage,
                        "Sufficient Money for Basic Needs" to sufficientMoney,
                        "Family System" to familySystem,
                        "Male Gender Preference" to malePreference,
                        "Relationship with Mother in-law" to relationshipMil,
                        "Gravida" to gravida,
                        "Physical Health " to physicalHealth,
                        "Current Appereance Acceptance" to appearanceAcceptance,
                        "Gestational Age" to (ga ?: 0),
                        "Number of sons " to sons,
                        "Number of daughters" to daughters,
                        "Total Number of Children" to totalKids
                    )

                    val latestVitals = vitalsList.lastOrNull()
                    val vitalsDto = if (latestVitals != null) {
                        MentalHealthVitalsDto(
                            systolicBp = latestVitals.Systolic_BP,
                            diastolicBp = latestVitals.Diastolic,
                            bloodSugar = latestVitals.BS,
                            bmi = latestVitals.BMI,
                            heartRate = latestVitals.Heart_Rate,
                            bodyTemp = latestVitals.Body_Temp,
                            previousComplications = latestVitals.Previous_Complications,
                            preexistingDiabetes = latestVitals.Preexisting_Diabetes,
                            gestationalDiabetes = latestVitals.Gestational_Diabetes
                        )
                    } else null

                    val req = CreateMentalHealthVisitRequest(
                        visitDate = today,
                        gestationalAge = ga,
                        deliveryDate = deliveryDate,
                        visitType = if (isPostpartum) "postpartum_followup" else "prenatal",
                        vitals = vitalsDto,
                        phq9ItemScores = phqScores,
                        context = MentalHealthContextDto(values = contextValues, age = patientAge)
                    )

                    healthViewModel.submitMentalHealthVisit(patientId, req) { res ->
                        if (res != null) {
                            navController.navigate(Screens.MentalHealthResult.passId(patientId))
                        }
                    }
                },
                enabled = !isLoading,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                } else {
                    Text("Evaluate & Save Visit", style = MaterialTheme.typography.labelLarge, fontSize = 16.sp)
                }
            }

            Spacer(modifier = Modifier.height(40.dp))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ContextDropdownField(
    label: String,
    options: List<String>,
    selected: String,
    onSelect: (String) -> Unit
) {
    var expanded by remember { mutableStateOf(false) }

    Column(modifier = Modifier.padding(vertical = 4.dp)) {
        ExposedDropdownMenuBox(
            expanded = expanded,
            onExpandedChange = { expanded = !expanded }
        ) {
            OutlinedTextField(
                value = selected,
                onValueChange = {},
                readOnly = true,
                label = { Text(label) },
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                modifier = Modifier.menuAnchor().fillMaxWidth(),
                shape = RoundedCornerShape(10.dp)
            )
            ExposedDropdownMenu(
                expanded = expanded,
                onDismissRequest = { expanded = false }
            ) {
                options.forEach { option ->
                    DropdownMenuItem(
                        text = { Text(option) },
                        onClick = {
                            onSelect(option)
                            expanded = false
                        }
                    )
                }
            }
        }
    }
}
