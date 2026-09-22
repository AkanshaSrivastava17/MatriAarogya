package com.example.sanraksha.front

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController

data class PhqQuestion(
    val key: String,
    val text: String,
    val description: String,
    val isSafetyQuestion: Boolean = false
)

val PHQ9_QUESTION_LIST = listOf(
    PhqQuestion("phq_anhedonia", "1. Little interest or pleasure in doing things", "Loss of enjoyment in daily activities or hobbies"),
    PhqQuestion("phq_depressed_mood", "2. Feeling down, depressed, or hopeless", "Persistent sadness or emotional low"),
    PhqQuestion("phq_sleep", "3. Trouble falling or staying asleep, or sleeping too much", "Insomnia, frequent waking, or excessive sleeping"),
    PhqQuestion("phq_fatigue", "4. Feeling tired or having little energy", "Unusual physical exhaustion unrelated to exertion"),
    PhqQuestion("phq_appetite", "5. Poor appetite or overeating", "Significant changes in hunger or dietary intake"),
    PhqQuestion("phq_worthlessness", "6. Feeling bad about yourself — or that you are a failure", "Feelings of guilt, inadequacy, or letting family down"),
    PhqQuestion("phq_concentration", "7. Trouble concentrating on things", "Difficulty focusing on conversations, tasks, or media"),
    PhqQuestion("phq_psychomotor", "8. Moving or speaking noticeably slowly, or being restless", "Sluggishness or fidgety/agitated movement"),
    PhqQuestion(
        "phq_suicidal_ideation",
        "9. Thoughts that you would be better off dead, or of hurting yourself",
        "Critical safety indicator — any positive response triggers immediate clinical review",
        isSafetyQuestion = true
    )
)

val RESPONSE_OPTIONS = listOf(
    0 to "Not at all (0)",
    1 to "Several days (+1)",
    2 to "More than half (+2)",
    3 to "Nearly every day (+3)"
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MentalHealthScreeningScreen(
    patientId: Long,
    navController: NavHostController,
    onProceedToContext: (patientId: Long, phqScores: Map<String, Int>) -> Unit
) {
    val context = LocalContext.current
    val scrollState = rememberScrollState()

    // State holding the selected value (0..3) for each of the 9 questions
    val answers = remember { mutableStateMapOf<String, Int>() }

    val answeredCount = answers.size
    val totalScore = answers.values.sum()
    val isItem9Positive = (answers["phq_suicidal_ideation"] ?: 0) > 0

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("PHQ-9 Mental Health Screen", fontWeight = FontWeight.Bold, fontSize = 20.sp) },
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
            // Instructions Card
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Info, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(modifier = Modifier.width(10.dp))
                    Text(
                        text = "Over the last 2 weeks, how often has the patient been bothered by any of the following problems? Answer all 9 items.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Running Score & Progress Banner
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(
                    containerColor = if (isItem9Positive) Color(0xFFFFEBEE) else Color(0xFFF1F8E9)
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(14.dp).fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "Questions Completed: $answeredCount / 9",
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.SemiBold
                        )
                        if (isItem9Positive) {
                            Text(
                                text = "⚠️ Acute Safety Flag Triggered (Item 9)",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color(0xFFC62828),
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                    Text(
                        text = "Score: $totalScore / 27",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = if (isItem9Positive) Color(0xFFC62828) else MaterialTheme.colorScheme.primary
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 9 PHQ-9 Question Cards
            PHQ9_QUESTION_LIST.forEachIndexed { index, q ->
                val selectedScore = answers[q.key]
                val isAnswered = selectedScore != null

                Card(
                    shape = RoundedCornerShape(12.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = if (q.isSafetyQuestion && (selectedScore ?: 0) > 0)
                            Color(0xFFFFEBEE)
                        else Color.White
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 6.dp)
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            if (q.isSafetyQuestion) {
                                Icon(
                                    Icons.Default.Warning,
                                    contentDescription = "Safety Alert",
                                    tint = Color(0xFFD32F2F),
                                    modifier = Modifier.size(20.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                            }
                            Text(
                                text = q.text,
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.Bold,
                                color = if (q.isSafetyQuestion) Color(0xFFC62828) else Color(0xFF263238)
                            )
                        }
                        Text(
                            text = q.description,
                            style = MaterialTheme.typography.bodySmall,
                            color = Color.Gray,
                            modifier = Modifier.padding(top = 2.dp, bottom = 8.dp)
                        )

                        // 4 Radio button choices in horizontal/wrapping flow
                        Column {
                            RESPONSE_OPTIONS.forEach { (value, label) ->
                                val isSelected = selectedScore == value
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(if (isSelected) MaterialTheme.colorScheme.secondaryContainer else Color.Transparent)
                                        .clickable { answers[q.key] = value }
                                        .padding(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    RadioButton(
                                        selected = isSelected,
                                        onClick = { answers[q.key] = value }
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        text = label,
                                        style = MaterialTheme.typography.bodyMedium,
                                        fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Normal
                                    )
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Next / Proceed Button
            Button(
                onClick = {
                    if (answeredCount < 9) {
                        val missing = 9 - answeredCount
                        Toast.makeText(context, "Please answer all 9 questions ($missing remaining)", Toast.LENGTH_SHORT).show()
                    } else {
                        onProceedToContext(patientId, answers.toMap())
                    }
                },
                enabled = answeredCount == 9,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = if (answeredCount == 9) "Continue to Contextual Assessment ➜" else "Answer All 9 Questions to Proceed",
                    style = MaterialTheme.typography.labelLarge,
                    fontSize = 16.sp
                )
            }
        }
    }
}
