package com.example.sanraksha.front

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.Divider
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

import androidx.compose.foundation.layout.height
import androidx.compose.material3.FilledTonalButton
import androidx.compose.ui.unit.sp

@Composable
fun HomeScreen(
    patients : List<Patient>,
    onPatientClick : (Patient) -> Unit,
    onMentalHealthClick : (Patient) -> Unit = {},
    onAddClick : ()-> Unit
){
    Scaffold(
        containerColor = Color(0xFFF0F4F8),
        floatingActionButton = {
            FloatingActionButton(
                onClick = {onAddClick()},
                containerColor = Color(0xFF1976D2),
                contentColor = Color.White,
                shape = CircleShape
            ) {
                Icon(imageVector = Icons.Default.Add, contentDescription = "Add Patient")
            }
        }

    ){paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
        ) {
            Text(text = "SanRaksha",
                style = MaterialTheme.typography.headlineMedium.copy(
                    color = Color(0xFF1976D2),
                    fontWeight = FontWeight.Bold
                ),
                modifier = Modifier.padding(bottom = 8.dp)
                    .align(Alignment.CenterHorizontally)
                )

            // Mental Health & Postpartum Feature Banner
            Card(
                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFEDE7F6))
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("🧠", fontSize = 24.sp)
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "Maternal Mental Health & Postpartum",
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF4A148C),
                            fontSize = 14.sp
                        )
                        Text(
                            text = "PHQ-9 screening, acute safety alerts & longitudinal tracking",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF6A1B9A)
                        )
                    }
                }
            }

            Divider(modifier = Modifier.padding(bottom = 10.dp))

            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(patients){ patient ->
                    EachPatient(
                        patient = patient,
                        onClick = { onPatientClick(patient) },
                        onMentalHealthClick = { onMentalHealthClick(patient) }
                    )
                }
            }

        }

    }

}


@Composable
fun EachPatient(
    patient: Patient,
    onClick: () -> Unit,
    onMentalHealthClick: () -> Unit = {}
){

    Card(
        modifier = Modifier.fillMaxWidth()
            .clickable{onClick()},
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(6.dp)
    ){
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ){
                Icon(
                    imageVector = Icons.Default.Person,
                    contentDescription = "User Icon",
                    modifier = Modifier.size(50.dp)
                        .clip(CircleShape)
                        .background(Color(0xFFE0E0E0))
                        .padding(8.dp),
                    tint = Color.Gray
                )

                Spacer(modifier = Modifier.width(14.dp))

                Column(modifier = Modifier.weight(1f)) {
                    Text(text = patient.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text(text = "Week ${patient.pregnancyWeek}",
                         style = MaterialTheme.typography.bodyMedium
                        )
                    Text(
                        text = "Last Checkup : ${patient.lastCheckup}",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.Gray
                    )
                }

                Icon(
                    imageVector = Icons.AutoMirrored.Filled.KeyboardArrowRight,
                    contentDescription = "Navigate",
                    tint = Color.Gray
                )

            }

            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End
            ) {
                FilledTonalButton(
                    onClick = onMentalHealthClick,
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("🧠 Mental Health Screen", fontSize = 12.sp)
                }
            }
        }

    }

}


