package com.example.sanraksha.front

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument

import com.example.sanraksha.HealthViewModel

@Composable
fun Navigation(
    viewModel: PatientViewModel = viewModel(),
    healthViewModel: HealthViewModel = viewModel(),
    navController: NavHostController = rememberNavController()
) {
    // Temporary holder for PHQ-9 answers across screening and contextual steps
    var sharedPhqScores by remember { mutableStateOf<Map<String, Int>>(emptyMap()) }

    NavHost(
        navController = navController,
        startDestination = Screens.Home.route
    ) {
        composable(Screens.Home.route) {
            val patients by viewModel.getAllPatients.collectAsState(initial = emptyList())

            HomeScreen(
                patients = patients,
                onPatientClick = { patient ->
                    navController.navigate(Screens.Profile.passId(patient.id))
                },
                onMentalHealthClick = { patient ->
                    navController.navigate(Screens.MentalHealthScreening.passId(patient.id))
                },
                onAddClick = {
                    navController.navigate(Screens.AddPatient.route)
                }
            )
        }

        composable(Screens.AddPatient.route) {
            AddPatientScreen(
                onSaveClick = { name, week, date, state ->
                    viewModel.addPatient(
                        Patient(
                            name = name,
                            pregnancyWeek = week,
                            lastCheckup = date,
                            state = state
                        )
                    )
                    navController.popBackStack()
                },
                onBackClick = {
                    navController.popBackStack()
                }
            )
        }

        composable(
            route = Screens.Profile.route,
            arguments = listOf(navArgument("patientId") { type = NavType.LongType })
        ) { backStackEntry ->
            val patientId = backStackEntry.arguments?.getLong("patientId") ?: 0L
            ProfileScreen(patientId = patientId, navController = navController)
        }

        composable(
            route = Screens.RecordVitals.route,
            arguments = listOf(navArgument("patientId") { type = NavType.LongType })
        ) { backStackEntry ->
            val patientId = backStackEntry.arguments?.getLong("patientId") ?: 0L
            RecordVitalsScreen(patientId = patientId, navController = navController)
        }

        // ── Mental Health Routes ─────────────────────────────────────────────

        composable(
            route = Screens.MentalHealthScreening.route,
            arguments = listOf(navArgument("patientId") { type = NavType.LongType })
        ) { backStackEntry ->
            val patientId = backStackEntry.arguments?.getLong("patientId") ?: 0L
            MentalHealthScreeningScreen(
                patientId = patientId,
                navController = navController,
                onProceedToContext = { pid, scores ->
                    sharedPhqScores = scores
                    navController.navigate(Screens.ContextualRisk.passId(pid))
                }
            )
        }

        composable(
            route = Screens.ContextualRisk.route,
            arguments = listOf(navArgument("patientId") { type = NavType.LongType })
        ) { backStackEntry ->
            val patientId = backStackEntry.arguments?.getLong("patientId") ?: 0L
            ContextualRiskScreen(
                patientId = patientId,
                phqScores = sharedPhqScores,
                navController = navController,
                healthViewModel = healthViewModel
            )
        }

        composable(
            route = Screens.MentalHealthResult.route,
            arguments = listOf(navArgument("patientId") { type = NavType.LongType })
        ) { backStackEntry ->
            val patientId = backStackEntry.arguments?.getLong("patientId") ?: 0L
            MentalHealthResultScreen(
                patientId = patientId,
                navController = navController,
                healthViewModel = healthViewModel
            )
        }

        composable(
            route = Screens.PatientHistory.route,
            arguments = listOf(navArgument("patientId") { type = NavType.LongType })
        ) { backStackEntry ->
            val patientId = backStackEntry.arguments?.getLong("patientId") ?: 0L
            PatientHistoryScreen(
                patientId = patientId,
                navController = navController,
                healthViewModel = healthViewModel
            )
        }
    }
}