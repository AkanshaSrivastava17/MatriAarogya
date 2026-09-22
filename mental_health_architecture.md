# SanRaksha Mental Health Extension — Architecture

## 1. Current architecture (verified from code)

```
Android App (Kotlin, TFLite offline inference)  ─┐
                                                    ├──> POST /predict (FastAPI, app/main.py)
Streamlit PHC Dashboard (dashboard/app.py)  ───────┘         │
                                                               ├──> keras_model_improved.keras
                                                               │    + scaler_improved.pkl
                                                               │    (10 physical-vitals features,
                                                               │     one of which is a binary
                                                               │     "Mental_Health" flag)
                                                               │
                                                               └──> appends result to
                                                                    data/captured_vitals.csv
                                                                    (flat file, no patient ID,
                                                                     no visit concept)
```

**Verified, not assumed:**
- No database. No ORM. No `patient_id`. No `visit_id`.
- `/predict` is fully stateless — each call is independent; nothing links two
  calls as belonging to the same woman.
- `data/risk_cases.csv`'s `id` column is a row index, not a patient identity.
- Mental health today = a single binary yes/no flag, no screening instrument,
  no scoring logic, no safety check.
- Dashboard reads CSVs directly; also has an "asha_id" concept for filtering
  cases by health worker, but this is not a patient identifier.

**Conclusion:** the "longitudinal history" and "patient/visit" components in
this spec cannot be an extension of something that exists — they are new
infrastructure. Documenting this now so later phases aren't built on a false
assumption.

## 2. Data audit conclusion (mandatory before any future-risk claim)

Both available datasets (PERI_DEP/Pakistan, ~14,000 rows; Dataset_1/Bangladesh,
~800 rows) are **cross-sectional**: one questionnaire response per woman, no
repeated visits, no recorded outcome at a later date, no pregnancy→postpartum
linkage. Neither dataset contains what would be needed to train a genuine
"will this woman develop depression in the future" model.

**Per spec section 28, this means:**
- We CAN build a deterministic **current screening** (PHQ-9/EPDS scoring).
- We CAN build a **contextual risk model** — predicting current depression-risk
  likelihood from background factors, evaluated on cross-sectional data. This
  is what `context_risk_model.py` / `context_risk_model_bd.py` already are.
- We CANNOT build, and this project does NOT claim to have built, a model
  that predicts *future* or *postpartum* depression from a genuine
  longitudinal outcome, because no such labeled outcome exists in any
  available dataset.
- What we build instead: the **software architecture** for longitudinal
  tracking and risk-trend computation (patient history, visit-over-visit
  feature deltas, trend direction), fully functional and ready to accept a
  genuine longitudinal model the moment appropriate outcome data exists.
  Until then, "future risk" in this system means "current contextual risk
  re-evaluated at each visit," not a learned prediction of what will happen
  later.

## 3. Current screening task vs. contextual risk task (kept separate)

| | Current Screening | Contextual Risk |
|---|---|---|
| Method | Deterministic PHQ-9 sum + threshold (`mental_health/screening.py`) | Trained Random Forest on background factors, no symptom items (`mental_health/context_model.py`, ported from `context_risk_model.py`) |
| Input | 9 symptom item responses, this visit only | Education, financial sufficiency, family system, gender-preference pressure, miscarriage history, gestational age, children count, age — no symptom items |
| Output | Total score, severity band, at-risk flag, safety flag | Risk probability + Low/Moderate/Elevated category |
| Why separate | Feeding symptom items into a model that also uses them for the label is exact label leakage (verified during earlier development: PERI_DEP's own label is 100% reconstructible from summing the 9 items) | Genuinely predictive, non-circular; usable even when a full symptom screen hasn't been done |
| Validated on | 500-row exact-match check against PERI_DEP's own label | 5-fold CV, mean AUC 0.80 |

## 4. Longitudinal data structure

```
Patient (patient_id, created_at, demographic fields)
   └── Visit (visit_id, patient_id, visit_date, gestational_age, trimester)
          ├── Vitals (BP, HR, BMI, blood sugar — reuses existing physical-risk fields)
          ├── MentalHealthAssessment (screening_type, item scores, total_score,
          │                            severity, safety_flag)
          ├── ContextualRiskAssessment (model_version, risk_probability,
          │                              risk_category, top_factors)
          └── LongitudinalFeatures (computed at write time from this visit +
                                     all prior visits for this patient:
                                     score deltas, trend direction, visit count)
```

Stored in SQLite (`app/mental_health/store.db`) — chosen because the existing
project has no database at all, and SQLite requires no new infrastructure or
deployment change, fitting a student-project/PHC-offline context. Every
assessment is inserted, never overwritten, so history is preserved.

## 5. Model inputs / outputs

**Screening** (`score_symptoms`): 9 PHQ-9 item scores (0–3 each) → total,
severity band, `at_risk` bool, `urgent_flag` bool (item 9 > 0, independent of
total — this can never be suppressed by a low total score).

**Contextual risk** (`predict_context_risk`): categorical + numeric background
features → probability + category (Low <0.4, Moderate 0.4–0.65, Elevated
>0.65 — thresholds documented, adjustable, not clinically validated cutoffs).

**Longitudinal features** (`build_longitudinal_features`): given a patient's
prior visits + current visit, computes: change in total screening score,
change in contextual risk probability, number of previous elevated
screenings, max previous score, visit count, time since last visit, trend
label (`increasing` / `stable` / `decreasing`, using a documented minimum
change threshold, not raw noise).

## 6. Safety architecture

Item 9 (self-harm/suicidal ideation) > 0 always sets `urgent_flag = True`,
computed independently of and never overridden by the total score or the
contextual risk category. The API response always surfaces this field
separately, and the mandatory language used is escalation language ("requires
urgent professional evaluation"), never a diagnosis.

## 7. Privacy

- Patients referenced by `patient_id` in all API responses; no name is
  required by the schema (optional field only).
- Raw PHQ-9/EPDS item responses are stored in the DB (needed for scoring
  history) but never written to application logs — logging in the new module
  logs only visit_id/patient_id/outcome, never item-level responses.
- No mental-health data is sent to any external API/service.

## 8. Validation strategy

- Unit tests: scoring, severity bands, safety flag, trimester calculation,
  longitudinal feature computation (score deltas, trend labeling), imputation
  of missing context fields.
- Integration test: create patient → visit 1 → visit 2 → verify history
  retrieval shows both visits, computed trend, and that visit 1's data is
  untouched by visit 2's write (no overwrite).
- Regression test: existing `/predict` endpoint and its request/response
  schema are unchanged — verified by re-running it with the same inputs used
  in `PROJECT_COMPLETION_SUMMARY.md`'s examples.

## 9. What this phase does NOT include (explicit, not silently skipped)

- Android/Kotlin UI screens are **not implemented** in this pass — this
  sandbox has no Android SDK/emulator to build or test Kotlin against, so
  writing untested Kotlin would violate the "test it, show the result"
  requirement in the spec. A concrete screen-by-screen plan is given in
  `docs/android_integration_plan.md` for you to implement/test in Android
  Studio.
- Dashboard visual extension (trend charts) is scaffolded as a plan, not
  built, for the same reason — Streamlit renders fine but I can't visually
  verify a chart in this environment the way I can verify a pytest result.
- Genuine longitudinal/postpartum ML model: not built, per §2 — no data
  supports it. Architecture is ready to accept one later.
