package com.example.sanraksha

import com.google.gson.annotations.SerializedName

data class predictionResponse(
    @SerializedName("prediction")
    val prediction: List<Int>,
    @SerializedName("prediction_label")
    val prediction_label: List<String>? = null,
    @SerializedName("contributing_factors")
    val contributing_factors: List<List<String>>? = null,
    @SerializedName("actionable_guidance")
    val actionable_guidance: List<List<String>>? = null
)
