package com.example.sanraksha

data class predictionResponse(
    val prediction : List<Int>,
    val prediction_label: List<String>? = null
)
