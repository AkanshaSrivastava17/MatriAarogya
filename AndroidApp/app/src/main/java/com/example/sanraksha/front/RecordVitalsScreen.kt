package com.example.sanraksha.front

import android.app.DatePickerDialog
import android.content.Intent
import android.speech.RecognizerIntent
import android.util.Log
import android.widget.DatePicker
import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.Divider
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.FavoriteBorder
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.room.util.splitToIntList
import com.example.sanraksha.AndroidConnectivityObserver
import com.example.sanraksha.ApiPredictionResult
import com.example.sanraksha.ConnectivityVIewModel
import com.example.sanraksha.HealthViewModel
import com.example.sanraksha.ImprovedDataStandardization
import com.example.sanraksha.R
import com.example.sanraksha.RiskPredictor
import com.example.sanraksha.healthDataItem
import com.example.sanraksha.parseVoiceTranscript
import com.example.sanraksha.riskInput
import com.example.sanraksha.ui.theme.ConnectivityViewModelFactory
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecordVitalsScreen(
    patientId: Long,
    navController: NavHostController,
    vitalsViewModel: VitalsViewModel = viewModel(),
    healthViewModel: HealthViewModel = viewModel(),
    patientViewModel: PatientViewModel = viewModel()
) {
    val patient by patientViewModel.getAPatientById(patientId).collectAsState(initial = null)


    val context = LocalContext.current
    val connectivityObserver = remember{
        AndroidConnectivityObserver(context.applicationContext)
    }

    val connectivityViewModel: ConnectivityVIewModel = viewModel(
        factory = ConnectivityViewModelFactory(connectivityObserver)
    )
    val isConnected by connectivityViewModel.isConnected.collectAsState()

    var date by remember { mutableStateOf("") }
    var age by remember { mutableStateOf("") }
    var systolicBP by remember { mutableStateOf("") }
    var diastolic by remember { mutableStateOf("") }
    var bs by remember { mutableStateOf("") }
    var bodyTemp by remember { mutableStateOf("") }
    var bmi by remember { mutableStateOf("") }
    var heartRate by remember { mutableStateOf("") }
    var transcript by remember { mutableStateOf("") }
    var transcriptStatus by remember { mutableStateOf("Speak or paste a transcript to auto-fill fields") }

    var previousComplications by remember { mutableStateOf<Int?>(null) }
    var preexistingDiabetes by remember { mutableStateOf<Int?>(null) }
    var gestationalDiabetes by remember { mutableStateOf<Int?>(null) }
    var mentalHealth by remember { mutableStateOf<Int?>(null) }


    val calendar = Calendar.getInstance()
    val year = calendar.get(Calendar.YEAR)
    val month = calendar.get(Calendar.MONTH)
    val day = calendar.get(Calendar.DAY_OF_MONTH)

    val datePickerDialog = remember{
        DatePickerDialog(
            context,
            { _: DatePicker, selectedYear: Int, selectedMonth: Int, selectedDay: Int ->
                date = String.format(Locale.US, "%02d-%02d-%04d", selectedDay, selectedMonth + 1, selectedYear)
            },
            year, month, day
        )
    }

    val speechLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == android.app.Activity.RESULT_OK) {
            val spokenText = result.data
                ?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                ?.firstOrNull()
                .orEmpty()

            if (spokenText.isNotBlank()) {
                transcript = spokenText
                transcriptStatus = "Transcript captured. Use auto-fill to populate fields."
            } else {
                transcriptStatus = "No speech recognized. Try again."
            }
        } else {
            transcriptStatus = "Speech capture cancelled."
        }
    }

    fun applyTranscriptToFields() {
        if (transcript.isBlank()) {
            transcriptStatus = "Enter or record a transcript first."
            return
        }

        val parsed = parseVoiceTranscript(transcript)

        parsed.age?.let { age = it.toString() }
        parsed.systolicBp?.let { systolicBP = it.toString() }
        parsed.diastolicBp?.let { diastolic = it.toString() }
        parsed.bloodSugar?.let { bs = it.toString() }
        parsed.bmi?.let { bmi = it.toString() }
        parsed.bodyTemp?.let { bodyTemp = it.toString() }
        parsed.heartRate?.let { heartRate = it.toString() }
        parsed.previousComplications?.let { previousComplications = it }
        parsed.preexistingDiabetes?.let { preexistingDiabetes = it }
        parsed.gestationalDiabetes?.let { gestationalDiabetes = it }
        parsed.mentalHealth?.let { mentalHealth = it }

        transcriptStatus = "Auto-filled fields from transcript. Review the form before saving."
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(title = { Text("Record New Vitals",
                fontSize = 30.sp,
                fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = {navController.popBackStack()}){
                        Icon(Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }
                }
                )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .padding(paddingValues)
                .padding(horizontal = 24.dp, vertical = 16.dp)
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {

            Text("Date",style = MaterialTheme.typography.labelLarge)
            OutlinedTextField(value = date, onValueChange = {},leadingIcon = { Image(painter = painterResource(id= R.drawable.baseline_calendar_today_24),
                contentDescription = "Checkup Date"
            ) },
                placeholder = { Text("Enter date : DD-MM-YYYY") } ,
                             keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth().clickable {  datePickerDialog.show()  },
                enabled = false,
                shape = RoundedCornerShape(12.dp)
                )
            Text("Age",style = MaterialTheme.typography.labelLarge)
            OutlinedTextField(value = age, onValueChange = { age = it }, leadingIcon = { Icon(Icons.Default.Person, contentDescription = "Age") },
                placeholder = { Text("Enter age") } ,   keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
                )

            Text("Systolic BP",style = MaterialTheme.typography.labelLarge)
            OutlinedTextField(value = systolicBP, onValueChange = { systolicBP = it }, leadingIcon = { Icon(Icons.Default.Favorite, contentDescription = "Systolic BP") },
                placeholder = { Text("Enter systolic : mm Hg") } ,   keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
                )

            Text("Diastolic",style = MaterialTheme.typography.labelLarge)
            OutlinedTextField(value = diastolic, onValueChange = { diastolic = it },  leadingIcon = { Icon(Icons.Default.FavoriteBorder, contentDescription = "Diastolic") },
                placeholder = { Text("Enter diastolic : mm Hg") },   keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
                )

            Text("Blood Sugar",style = MaterialTheme.typography.labelLarge)
                OutlinedTextField(value = bs,
                    onValueChange = { bs = it },
                    leadingIcon = {
                        Image(
                            painter = painterResource(id = R.drawable.baseline_bloodtype_24),
                            contentDescription = "Blood Sugar"
                        )
                    },
                    placeholder = { Text("Enter blood sugar : mmol/L") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp)
                )



            Text("Body Temp",style = MaterialTheme.typography.labelLarge)
            OutlinedTextField(value = bodyTemp, onValueChange = { bodyTemp = it },leadingIcon = { Image(painter = painterResource(id=R.drawable.baseline_device_thermostat_24), contentDescription = "Body Temperature") },
                placeholder = { Text("Enter temperature : °F") } ,   keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
                )
            Text("BMI",style = MaterialTheme.typography.labelLarge)
            OutlinedTextField(value = bmi, onValueChange = { bmi = it }, leadingIcon = { Image(painter = painterResource(id=R.drawable.baseline_monitor_weight_24), contentDescription = "BMI") },
                placeholder = { Text("Enter BMI : Kg/m^2") },   keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
                )
            Text("Heart Rate",style = MaterialTheme.typography.labelLarge)
            OutlinedTextField(value = heartRate, onValueChange = { heartRate = it },  leadingIcon = { Icon(Icons.Default.Favorite, contentDescription = "Heart Rate") },
                placeholder = { Text("Enter heart rate") },   keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
                )
            Spacer(modifier = Modifier.height(4.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors()
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("Voice Note / Transcript", style = MaterialTheme.typography.labelLarge)
                    Text(
                        "Use speech-to-text or paste a transcript. The app can extract BP, sugar, BMI, heart rate, age, and yes/no risk flags.",
                        style = MaterialTheme.typography.bodySmall
                    )
                    OutlinedTextField(
                        value = transcript,
                        onValueChange = { transcript = it },
                        placeholder = { Text("Example: age 30, blood pressure 120 over 80, sugar 6.5, BMI 25, heart rate 75") },
                        modifier = Modifier.fillMaxWidth().height(120.dp),
                        shape = RoundedCornerShape(12.dp)
                    )
                    Text(transcriptStatus, style = MaterialTheme.typography.bodySmall)
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Button(onClick = {
                            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                                putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak the vitals for this patient")
                                putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault().toLanguageTag())
                            }
                            speechLauncher.launch(intent)
                        }) {
                            Text("Speak")
                        }

                        Button(onClick = { applyTranscriptToFields() }) {
                            Text("Auto-fill")
                        }
                    }
                }
            }
            Dropdown("Previous Complications", previousComplications) { previousComplications = it }
            Dropdown("Preexisting Diabetes", preexistingDiabetes) { preexistingDiabetes = it }
            Dropdown("Gestational Diabetes", gestationalDiabetes) { gestationalDiabetes = it }
            Dropdown("Mental Health Issues", mentalHealth) { mentalHealth = it }

            Spacer(modifier = Modifier.height(20.dp))

            Button(
                onClick = {
                    Log.d("PRED_DEBUG", "Save clicked - isConnected = $isConnected")
                    if (isConnected) {
                        //call api
                        val input = healthDataItem(
                            Age = age.toFloatOrNull()?.toInt()?:0,
                            Systolic_BP = systolicBP.toFloatOrNull(),
                            Diastolic = diastolic.toFloatOrNull(),
                            BS = bs.toFloatOrNull(),
                            Body_Temp = bodyTemp.toFloatOrNull(),
                            BMI = bmi.toFloatOrNull() ?: 0f,
                            Previous_Complications = previousComplications ?: 0,
                            Preexisting_Diabetes = preexistingDiabetes ?: 0,
                            Gestational_Diabetes = gestationalDiabetes ?: 0,
                            Mental_Health = mentalHealth ?: 0,
                            Heart_Rate = heartRate.toFloatOrNull(),
                            state = patient?.state

                        )
                        healthViewModel.sendHealthDataToApi(input){result: ApiPredictionResult?->
                            if(result != null){
                                Log.d("APIPrediction","Predicted Risk Score : ${result.prediction}")
                                Log.d("APIPrediction","Predicted Risk Label : ${result.label}")
                                Toast.makeText(context, "Predicted Risk: ${result.label}", Toast.LENGTH_SHORT).show()
                                val vitals = Vitals(
                                    patientId = patientId,
                                    date = date,
                                    Age = age.toIntOrNull()?:0,
                                    Systolic_BP = systolicBP.toFloatOrNull()?:0f,
                                    Diastolic = diastolic.toFloatOrNull()?:0f,
                                    BS = bs.toFloatOrNull()?:0f,
                                    Body_Temp = bodyTemp.toFloatOrNull()?:0f,
                                    BMI = bmi.toFloatOrNull() ?: 0f,
                                    Heart_Rate = heartRate.toFloatOrNull()?:0f,
                                    Previous_Complications = previousComplications ?: 0,
                                    Preexisting_Diabetes = preexistingDiabetes ?: 0,
                                    Gestational_Diabetes = gestationalDiabetes ?: 0,
                                    Mental_Health = mentalHealth ?: 0,
                                    predictedRisk = result.prediction,
                                    predictedRiskLabel = result.label
                                )
                                Log.d("InsertVitals", "Calling insert for patientId = ${vitals.patientId}")

                                // 🔍 AND THIS:
                                Log.d("InsertVitals", "Vitals Object = $vitals")
                                vitalsViewModel.insertVitals(vitals)


                                val week = getWeek(startDateStr = patient?.lastCheckup?:"", endDateStr = date)
                                val finalweek = (patient?.pregnancyWeek?:0) + week

                                patientViewModel.updatePatient(patient = Patient(patientId,patient?.name?:"",
                                    finalweek,date
                                    ))

                                 navController.popBackStack()

                            }else{
                               Log.d("APIPrediction","error: ")

                            }

                        }
                    } else {
                        //else ml model
                        val input = riskInput(
                            Age = age.toFloatOrNull()?.toInt()?:0,
                            Systolic_BP = systolicBP.toFloatOrNull()?.toInt()?:0,
                            Diastolic = diastolic.toFloatOrNull()?.toInt()?:0,
                            BS = bs.toFloatOrNull()?:0f,
                            Body_Temp = bodyTemp.toFloatOrNull()?:0f,
                            BMI = bmi.toFloatOrNull() ?: 0f,
                            Previous_Complications = previousComplications ?: 0,
                            Preexisting_Diabetes = preexistingDiabetes ?: 0,
                            Gestational_Diabetes = gestationalDiabetes ?: 0,
                            Mental_Health = mentalHealth ?: 0,
                            Heart_Rate = heartRate.toFloatOrNull()?.toInt()?:0
                        )
                        // Use improved model (98.73% accuracy)
                        val inputforMlModel = ImprovedDataStandardization(input)
                        Log.d("PRED_DEBUG", "TFLite input vector: ${inputforMlModel.joinToString()}")
                        val predictor = RiskPredictor(context)
                        val prediction = try {
                            predictor.predict(inputforMlModel)
                        } catch (e: Exception) {
                            Log.e("PRED_DEBUG", "TFLite prediction failed", e)
                            Float.NaN
                        }
                        val intPrediction = if(prediction > 0.5f)1 else 0

                        Log.d("TFLitePrediction", "Predicted Risk Score : $prediction")
                        Log.d("TFLitePredictioninINt", "Predicted  Score : $intPrediction")
                        val vitals = Vitals(
                            patientId = patientId,
                            date = date,
                            Age = age.toIntOrNull()?:0,
                            Systolic_BP = systolicBP.toFloatOrNull()?:0f,
                            Diastolic = diastolic.toFloatOrNull()?:0f,
                            BS = bs.toFloatOrNull()?:0f,
                            Body_Temp = bodyTemp.toFloatOrNull()?:0f,
                            BMI = bmi.toFloatOrNull() ?: 0f,
                            Heart_Rate = heartRate.toFloatOrNull()?:0f,
                            Previous_Complications = previousComplications ?: 0,
                            Preexisting_Diabetes = preexistingDiabetes ?: 0,
                            Gestational_Diabetes = gestationalDiabetes ?: 0,
                            Mental_Health = mentalHealth ?: 0,
                            predictedRisk = intPrediction,
                            predictedRiskLabel = if (intPrediction == 1) "High Risk" else "Low Risk",
                        )

                          vitalsViewModel.insertVitals(vitals)

                        val week = getWeek(startDateStr = patient?.lastCheckup?:"", endDateStr = date)
                        val finalweek = (patient?.pregnancyWeek?:0) + week

                        patientViewModel.updatePatient(patient = Patient(patientId,patient?.name?:"",
                            finalweek,date
                        ))

                          navController.popBackStack()
                    }


                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Save & Predict Risk",style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun Dropdown(
    label: String,
    selectedValue: Int?,
    onValueChange: (Int) -> Unit
) {
    var expanded by remember { mutableStateOf(false) }
    val options = listOf("Yes" to 1, "No" to 0)
    val selectedText = when (selectedValue) {
        1 -> "Yes"
        0 -> "No"
        else -> ""
    }

    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = !expanded }
    ) {
        OutlinedTextField(
            value = selectedText,
            onValueChange = {},
            readOnly = true,
            label = { Text(label) },
            trailingIcon = {
                ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
            },
            modifier = Modifier
                .menuAnchor()
                .fillMaxWidth()
        )

        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false }
        ) {
            options.forEach { (text, value) ->
                DropdownMenuItem(
                    text = { Text(text) },
                    onClick = {
                        onValueChange(value)
                        expanded = false
                    }
                )
            }
        }
    }
}


fun getWeek(startDateStr:String,endDateStr:String):Int{

    val sdf = SimpleDateFormat("dd-MM-yyyy", Locale.getDefault())

    val startDate = sdf.parse(startDateStr)
    val endDate = sdf.parse(endDateStr)

    if(startDate == null || endDate == null ){
        return 0
    }


    val diffrence = endDate.time - startDate.time

     val week = (diffrence / (1000 * 60 * 60 * 24*7)).toInt()

    return week

}

















