package com.example.sanraksha

import androidx.compose.runtime.Composable
import kotlin.math.exp

//['BS', 'BMI', 'Age', 'Heart Rate','Systolic BP','Diastolic', 'Final_Risk_Score']
    data class StandardizedOutput(
        val BS: Double,
        val BMI: Double,
        val Age: Double,
        val HeartRate: Double,
        val SystolicBP: Double,
        val DiastolicBP: Double,
        val FinalRiskScore: Double
    )

fun DataStandardization(riskInput: riskInput):StandardizedOutput{

    //model1
    val weight1ofmodel1 = -2.3618839494751795
    val weight2ofmodel1 = -4.10436327362052
    val weight3ofmodel1 = -4.7575702806286815
    val weight4ofmodel1 = -2.0561135304354563

    val biasingofmodel1 = 3.3894794466732603

    //col1 = ['Previous Complications','Preexisting Diabetes','Gestational Diabetes','Mental Health']
    val model1result = weight1ofmodel1*riskInput.Previous_Complications +
                        weight2ofmodel1*riskInput.Preexisting_Diabetes +
                        weight3ofmodel1*riskInput.Gestational_Diabetes +
                        weight4ofmodel1*riskInput.Mental_Health + biasingofmodel1

    val  riskScore =  sigmoid(model1result)

    //model2
    //cols = ['is_low_bmi', 'is_high_bmi', 'is_low_bp', 'is_high_bp', 'is_high_bs', 'is_high_hr', 'is_low_hr']

    //X_train_imputed['is_low_bmi'] = (X_train_imputed['BMI'] < 18.5).astype(int)
    //X_train_imputed['is_high_bmi'] = (X_train_imputed['BMI'] > 30).astype(int)
    //X_train_imputed['is_low_bp'] = ((X_train_imputed['Systolic BP'] < 90) | (X_train_imputed['Diastolic'] < 60)).astype(int)
    //X_train_imputed['is_high_bp'] = ((X_train_imputed['Systolic BP'] > 140) | (X_train_imputed['Diastolic'] > 90)).astype(int)
    //X_train_imputed['is_high_bs'] = (X_train_imputed['BS'] > 7.8).astype(int)
    //X_train_imputed['is_high_hr'] = (X_train_imputed['Heart Rate'] > 100).astype(int)
    //X_train_imputed['is_low_hr'] = (X_train_imputed['Heart Rate'] < 60).astype(int)

    val is_low_bmi =   if (riskInput.BMI <= 18.5) 1 else 0
    val is_high_bmi = if (riskInput.BMI >= 30) 1 else 0
    val is_low_bp = if(riskInput.Systolic_BP <= 90 || riskInput.Diastolic <= 60)1 else 0
    val is_high_bp = if(riskInput.Systolic_BP >= 140 || riskInput.Diastolic >= 90)1 else 0
    val is_high_bs = if(riskInput.BS >= 7.8)1 else 0
    val is_high_hr = if(riskInput.Heart_Rate >= 100)1 else 0
    val is_low_hr = if(riskInput.Heart_Rate <= 60)1 else 0

    val weight1ofmodel2 = -3.0585747061010173
    val weight2ofmodel2 = -2.5008934783065744
    val weight3ofmodel2 = 0.23212516267988542
    val weight4ofmodel2 = -1.397350083593462
    val weight5ofmodel2 = -4.082720266366235
    val weight6ofmodel2 = 0.0
    val weight7ofmodel2 = -1.2991199093290822

    val biasingofmodel2 = 1.8588124199686031

    val model2result = weight1ofmodel2*is_low_bmi + weight2ofmodel2*is_high_bmi +
                       weight3ofmodel2*is_low_bp + weight4ofmodel2*is_high_bp +
                       weight5ofmodel2*is_high_bs + weight6ofmodel2*is_high_hr +
                       weight7ofmodel2*is_low_hr + biasingofmodel2

    val riskScore_Abn = sigmoid(model2result)

    //model3
    //['Risk Score','Risk Score Abn']
    val weight1ofmodel3 = 5.8991195017033
    val weight2ofmodel3 = 3.7204274021730193

    val biasingofmodel3 = -5.215292748027206

    val model3result = weight1ofmodel3*riskScore + weight2ofmodel3*riskScore_Abn + biasingofmodel3

    val final_risk_score = sigmoid(model3result)


//{"1": [2.2844805234162426, 4.302126981282638, 4.80806462798848, 2.1557354423347066],
// "2": [2.9534001075263436, 2.541888001487591, -0.1546863106840409, 1.288581542577755, 4.129221296613417, 0.0, 1.274482764741299],
// "3": [6.011838573897318, 3.571762088775957]}
// {"1": -3.3629417153571874, "2": -1.7934540919858957, "3": -4.352072036198044}



    //Standardization for the final result
    //['BS', 'BMI', 'Age', 'Heart Rate','Systolic BP','Diastolic', 'Final_Risk_Score']
    // (x - mean)/standard deviation


    val  standard_BS = (riskInput.BS - 7.545174234424499)/3.0659491152062732
    val  standard_BMI = (riskInput.BMI - 23.34221748400853 )/3.943820324272148
    val  standard_Age = (riskInput.Age -  27.543822597676876)/9.128146207241514
    val  standard_heart_rate = (riskInput.Heart_Rate - 75.7233368532207)/7.331602210795604
    val  standard_Systolic_BP = (riskInput.Systolic_BP - 117.00530222693531)/18.550637856619645
    val standard_Diastolic_BP = (riskInput.Diastolic - 77.25079365079365 )/14.15460969297969

    return StandardizedOutput(
        BS = standard_BS,
        BMI = standard_BMI,
        Age = standard_Age,
        HeartRate = standard_heart_rate,
        SystolicBP = standard_Systolic_BP,
        DiastolicBP = standard_Diastolic_BP,
        FinalRiskScore = final_risk_score
    )


}


fun sigmoid(x: Double): Double {
    return 1.0 / (1.0 + exp(-x))
}

// ===== IMPROVED MODEL (98.73% accuracy) =====
// Simplified preprocessing: 10 features directly with StandardScaler
fun ImprovedDataStandardization(riskInput: riskInput): FloatArray {
    // Feature order: Age, Systolic BP, Diastolic, BS, BMI,
    //               Previous Complications, Preexisting Diabetes,
    //               Gestational Diabetes, Mental Health, Heart Rate
    
    // StandardScaler parameters (mean and std from training)
    val means = floatArrayOf(
        27.629883f,  // Age
        116.445313f, // Systolic BP
        76.985352f,  // Diastolic
        134.55f,     // BS (mg/dL)
        23.32959f,   // BMI
        0.170898f,   // Previous Complications
        0.286133f,   // Preexisting Diabetes
        0.117188f,   // Gestational Diabetes
        0.333008f,   // Mental Health
        75.84961f    // Heart Rate
    )
    
    val stds = floatArrayOf(
        9.335057f,   // Age
        18.529615f,  // Systolic BP
        14.310821f,  // Diastolic
        54.06805f,   // BS (mg/dL)
        3.860251f,   // BMI
        0.376420f,   // Previous Complications
        0.451952f,   // Preexisting Diabetes
        0.321644f,   // Gestational Diabetes
        0.471289f,   // Mental Health
        7.199368f    // Heart Rate
    )
    
    // Create raw feature vector (10 features)
    val rawFeatures = floatArrayOf(
        riskInput.Age.toFloat(),
        riskInput.Systolic_BP.toFloat(),
        riskInput.Diastolic.toFloat(),
        riskInput.BS,
        riskInput.BMI,
        riskInput.Previous_Complications.toFloat(),
        riskInput.Preexisting_Diabetes.toFloat(),
        riskInput.Gestational_Diabetes.toFloat(),
        riskInput.Mental_Health.toFloat(),
        riskInput.Heart_Rate.toFloat()
    )
    
    // Apply StandardScaler: (x - mean) / std
    val scaledFeatures = FloatArray(10)
    for (i in 0 until 10) {
        scaledFeatures[i] = (rawFeatures[i] - means[i]) / stds[i]
    }
    
    return scaledFeatures
}