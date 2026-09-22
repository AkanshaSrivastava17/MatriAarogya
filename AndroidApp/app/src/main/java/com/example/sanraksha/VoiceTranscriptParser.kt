package com.example.sanraksha

import java.util.Locale

data class VoiceTranscriptResult(
    val age: Int? = null,
    val systolicBp: Int? = null,
    val diastolicBp: Int? = null,
    val bloodSugar: Float? = null,
    val bmi: Float? = null,
    val bodyTemp: Float? = null,
    val heartRate: Int? = null,
    val previousComplications: Int? = null,
    val preexistingDiabetes: Int? = null,
    val gestationalDiabetes: Int? = null,
    val mentalHealth: Int? = null,
)

private fun parseYesNoValue(text: String, positiveKeywords: List<String>, negativeKeywords: List<String>): Int? {
    positiveKeywords.forEach { keyword ->
        if (text.contains(keyword)) return 1
    }
    negativeKeywords.forEach { keyword ->
        if (text.contains(keyword)) return 0
    }
    return null
}

private fun parseFirstInt(text: String, patterns: List<Regex>): Int? {
    for (pattern in patterns) {
        val match = pattern.find(text)
        if (match != null) {
            return match.groupValues[1].toIntOrNull()
        }
    }
    return null
}

private fun parseFirstFloat(text: String, patterns: List<Regex>): Float? {
    for (pattern in patterns) {
        val match = pattern.find(text)
        if (match != null) {
            return match.groupValues[1].toFloatOrNull()
        }
    }
    return null
}

fun parseVoiceTranscript(transcript: String): VoiceTranscriptResult {
    val normalized = transcript.lowercase(Locale.getDefault())

    val age = parseFirstInt(
        normalized,
        listOf(Regex("(?:age|umar|umr|age is)\\D*(\\d{1,3})"))
    )

    var systolicBp: Int? = null
    var diastolicBp: Int? = null

    Regex("(?:blood pressure|bp|blood pressure is)\\D*(\\d{2,3})\\s*(?:/|over|by)\\s*(\\d{2,3})").find(normalized)?.let { match ->
        systolicBp = match.groupValues[1].toIntOrNull()
        diastolicBp = match.groupValues[2].toIntOrNull()
    }

    if (systolicBp == null) {
        systolicBp = parseFirstInt(
            normalized,
            listOf(
                Regex("(?:systolic|upper|high)\\D*(\\d{2,3})"),
                Regex("(?:bp|blood pressure)\\D*(\\d{2,3})\\s*(?:/|over|by)"),
            )
        )
    }

    if (diastolicBp == null) {
        diastolicBp = parseFirstInt(
            normalized,
            listOf(
                Regex("(?:diastolic|lower)\\D*(\\d{2,3})"),
                Regex("(?:/|over|by)\\s*(\\d{2,3})"),
            )
        )
    }

    val bloodSugar = parseFirstFloat(
        normalized,
        listOf(Regex("(?:blood sugar|sugar|glucose)\\D*(\\d+(?:\\.\\d+)?)"))
    )

    val bmi = parseFirstFloat(
        normalized,
        listOf(Regex("(?:bmi|body mass index)\\D*(\\d+(?:\\.\\d+)?)"))
    )

    val bodyTemp = parseFirstFloat(
        normalized,
        listOf(Regex("(?:body temp|body temperature|temperature|temp)\\D*(\\d+(?:\\.\\d+)?)"))
    )

    val heartRate = parseFirstInt(
        normalized,
        listOf(Regex("(?:heart rate|pulse|hr)\\D*(\\d{1,3})"))
    )

    val previousComplications = parseYesNoValue(
        normalized,
        positiveKeywords = listOf("previous complications yes", "previous complication yes", "complications yes", "complication yes"),
        negativeKeywords = listOf("previous complications no", "previous complication no", "complications no", "complication no")
    )

    val preexistingDiabetes = parseYesNoValue(
        normalized,
        positiveKeywords = listOf("preexisting diabetes yes", "pre existing diabetes yes", "diabetes yes", "pre diabetes yes"),
        negativeKeywords = listOf("preexisting diabetes no", "pre existing diabetes no", "diabetes no", "pre diabetes no")
    )

    val gestationalDiabetes = parseYesNoValue(
        normalized,
        positiveKeywords = listOf("gestational diabetes yes", "gdm yes"),
        negativeKeywords = listOf("gestational diabetes no", "gdm no")
    )

    val mentalHealth = parseYesNoValue(
        normalized,
        positiveKeywords = listOf("mental health yes", "mental health issues yes", "mental issue yes"),
        negativeKeywords = listOf("mental health no", "mental health issues no", "mental issue no")
    )

    return VoiceTranscriptResult(
        age = age,
        systolicBp = systolicBp,
        diastolicBp = diastolicBp,
        bloodSugar = bloodSugar,
        bmi = bmi,
        bodyTemp = bodyTemp,
        heartRate = heartRate,
        previousComplications = previousComplications,
        preexistingDiabetes = preexistingDiabetes,
        gestationalDiabetes = gestationalDiabetes,
        mentalHealth = mentalHealth,
    )
}