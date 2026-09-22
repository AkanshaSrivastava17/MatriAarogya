# Android + Dashboard Integration Plan (NOT implemented/tested in this pass)

This sandbox has no Android SDK/emulator and no way to visually verify a
Streamlit chart, so nothing in this file has been built or tested — it's a
concrete plan for you to implement in Android Studio / locally, where you
can actually run and check it. Writing Kotlin I can't compile or test would
violate the same "show the test result" standard the rest of this work
follows.

## New screens to add to `AndroidApp/`

1. **Mental Health Screening screen** — 9 PHQ-9 items as radio-button groups
   (reuse the existing form-input pattern already in the app for vitals
   entry), submits to `POST /mental-health/patients/{id}/visits`.
2. **Result screen** — three clearly separated sections, matching the API
   response shape exactly so no client-side reinterpretation is needed:
   - Current Screening (`current_screening.total_score`, `.severity`)
   - Contextual Risk (`contextual_risk.risk_category`, if present)
   - Safety (`safety_flag` — if true, render this section first/most
     prominently, in a visually distinct color, above the other two, per
     spec §18's "must not be hidden" requirement)
3. **Patient History screen** — table view from `GET /mental-health/patients/{id}/history`,
   one row per visit, matching the layout in spec §15/§32.

## Suggested request flow (Kotlin/Retrofit, illustrative only)

```kotlin
// Illustrative shape only -- not tested against a real Retrofit setup.
interface MentalHealthApi {
    @POST("mental-health/patients")
    suspend fun createPatient(@Body req: CreatePatientRequest): PatientResponse

    @POST("mental-health/patients/{id}/visits")
    suspend fun createVisit(@Path("id") patientId: Int, @Body req: CreateVisitRequest): VisitResult

    @GET("mental-health/patients/{id}/history")
    suspend fun getHistory(@Path("id") patientId: Int): HistoryResponse
}
```

## Offline-first consideration (spec §34, on-device inference)

The contextual risk model is currently a ~38MB scikit-learn Random Forest —
too large and not in a mobile-friendly format for TFLite conversion as-is.
Two realistic options, not yet decided:
1. Keep contextual risk as a server-side call only (simplest; matches how
   `/predict` already works today).
2. If offline contextual risk is required, retrain a smaller model (e.g. a
   shallow tree or logistic regression capped at fewer features) that can
   export to TFLite the same way `model.tflite` already does for the
   physical-risk model — this would trade some of the 0.78 AUC for
   on-device capability, and that trade-off should be a deliberate decision,
   not a default.
The deterministic PHQ-9 scoring (`screening.py`) is trivial to port to
Kotlin directly (it's ~15 lines of arithmetic) and should run on-device
regardless, since it needs no model file at all.

## Dashboard (`dashboard/app.py`) extension plan

Add a per-patient trend chart (Plotly, already a dependency) plotting
`total_score` over `visit_date` from the history endpoint, with the
`urgent_safety_flag` visits marked distinctly (e.g., red marker) — mirroring
the ASCII sketch in spec §13. Population-level view: aggregate `risk_category`
counts per block/ASHA, same pattern already used for physical `risk_level` in
the existing dashboard. Not implemented here; same reasoning as above.
