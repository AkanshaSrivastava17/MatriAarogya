"""
store.py — patient and longitudinal visit persistence using SQLite.

Ensures:
1. Append-only visit model: historical visits are NEVER overwritten or mutated.
2. Complete data model: Patient demographics, visits, vitals, PHQ-9 assessments,
   contextual risk assessments, longitudinal trajectory metrics.
3. Pregnancy to postpartum lifecycle tracking.
4. Privacy: Raw PHQ-9 item scores are stored in DB for clinical audit history,
   but NEVER logged to application logs or console.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).resolve().parent / "store.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS patient (
    patient_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT,
    age               INTEGER,
    state             TEXT,
    pregnancy_status  TEXT NOT NULL DEFAULT 'pregnant', -- 'pregnant', 'postpartum', 'completed'
    delivery_date     TEXT,
    notes             TEXT,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visit (
    visit_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id        INTEGER NOT NULL REFERENCES patient(patient_id),
    visit_date        TEXT NOT NULL,
    gestational_age   INTEGER,
    delivery_date     TEXT,
    trimester         TEXT NOT NULL,
    visit_type        TEXT NOT NULL DEFAULT 'prenatal', -- 'prenatal', 'postpartum_followup', 'routine'
    notes             TEXT
);

CREATE TABLE IF NOT EXISTS vitals (
    visit_id                 INTEGER PRIMARY KEY REFERENCES visit(visit_id),
    systolic_bp              REAL,
    diastolic_bp             REAL,
    blood_sugar              REAL,
    bmi                      REAL,
    heart_rate               REAL,
    body_temp                REAL,
    previous_complications   INTEGER DEFAULT 0,
    preexisting_diabetes     INTEGER DEFAULT 0,
    gestational_diabetes     INTEGER DEFAULT 0,
    recorded_at              TEXT
);

CREATE TABLE IF NOT EXISTS mental_health_assessment (
    visit_id            INTEGER PRIMARY KEY REFERENCES visit(visit_id),
    screening_type      TEXT NOT NULL,
    item_scores_json    TEXT NOT NULL,   -- raw responses, for audit/clinical record
    total_score         INTEGER NOT NULL,
    severity            TEXT,
    at_risk             INTEGER NOT NULL,
    urgent_safety_flag  INTEGER NOT NULL,
    screening_status    TEXT,
    safety_message      TEXT
);

CREATE TABLE IF NOT EXISTS contextual_risk_assessment (
    visit_id                      INTEGER PRIMARY KEY REFERENCES visit(visit_id),
    model_name                    TEXT NOT NULL,
    model_version                 TEXT NOT NULL,
    risk_probability              REAL NOT NULL,
    risk_category                 TEXT NOT NULL,
    top_contributing_factors_json TEXT NOT NULL,
    context_inputs_json           TEXT,
    explanation_text              TEXT,
    assessment_timestamp          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS longitudinal_features (
    visit_id                        INTEGER PRIMARY KEY REFERENCES visit(visit_id),
    visit_count                     INTEGER NOT NULL,
    score_change                    INTEGER,
    risk_probability_change         REAL,
    num_previous_elevated_screenings INTEGER,
    max_previous_score              INTEGER,
    avg_previous_score              REAL,
    days_since_last_visit           INTEGER,
    trend                           TEXT NOT NULL,
    features_json                   TEXT
);

CREATE TABLE IF NOT EXISTS nutrition_assessment (
    assessment_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id               INTEGER NOT NULL REFERENCES patient(patient_id),
    visit_id                 INTEGER REFERENCES visit(visit_id),
    assessment_date          TEXT NOT NULL,
    gestational_age          INTEGER,
    trimester                TEXT,
    height_cm                REAL,
    current_weight_kg        REAL,
    pre_pregnancy_weight_kg  REAL,
    current_bmi              REAL,
    pre_pregnancy_bmi        REAL,
    energy_kcal              REAL,
    carbohydrates_g          REAL,
    protein_g                REAL,
    fat_g                    REAL,
    fibre_g                  REAL,
    iron_mg                  REAL,
    folate_mcg               REAL,
    calcium_mg               REAL,
    vitamin_d_iu             REAL,
    vitamin_b12_mcg          REAL,
    dietary_pattern          TEXT,
    food_restrictions        TEXT,
    appetite_difficulty      TEXT,
    food_insecurity          INTEGER DEFAULT 0,
    supplements_taken        TEXT,
    assessment_completeness  TEXT,
    gaps_json                TEXT,
    recommendations_json     TEXT,
    notes                    TEXT,
    created_at               TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS immunization_record (
    record_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id               INTEGER NOT NULL REFERENCES patient(patient_id),
    visit_id                 INTEGER REFERENCES visit(visit_id),
    vaccine_name             TEXT NOT NULL,
    dose_number              INTEGER NOT NULL,
    status                   TEXT NOT NULL,
    administration_date      TEXT,
    confirmation_source      TEXT,
    card_verified            INTEGER DEFAULT 0,
    next_due_date            TEXT,
    notes                    TEXT,
    recorded_at              TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_recommendation (
    action_id                TEXT PRIMARY KEY,
    patient_id               INTEGER NOT NULL REFERENCES patient(patient_id),
    visit_id                 INTEGER REFERENCES visit(visit_id),
    domain                   TEXT NOT NULL,
    trigger_observation      TEXT NOT NULL,
    explanation              TEXT NOT NULL,
    action_text              TEXT NOT NULL,
    urgency                  TEXT NOT NULL,
    responsible_person       TEXT NOT NULL,
    timeframe                TEXT NOT NULL,
    referral_required        INTEGER DEFAULT 0,
    status                   TEXT NOT NULL DEFAULT 'pending',
    outcome_notes            TEXT,
    completed_at             TEXT,
    rule_source              TEXT NOT NULL,
    rule_version             TEXT NOT NULL,
    created_at               TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prediction_explanation (
    explanation_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id               INTEGER NOT NULL REFERENCES patient(patient_id),
    visit_id                 INTEGER REFERENCES visit(visit_id),
    model_name               TEXT NOT NULL,
    model_version            TEXT NOT NULL,
    prediction_class         TEXT NOT NULL,
    prediction_score         REAL,
    base_value               REAL,
    shap_values_json         TEXT NOT NULL,
    top_features_json        TEXT NOT NULL,
    limitations_disclaimer   TEXT NOT NULL,
    created_at               TEXT NOT NULL
);
"""


@contextmanager
def _connect(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)

        # Safe schema migration for pre-existing database files
        def _add_column(table: str, col_name: str, col_def: str):
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if col_name not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")

        _add_column("patient", "age", "INTEGER")
        _add_column("patient", "state", "TEXT")
        _add_column("patient", "pregnancy_status", "TEXT NOT NULL DEFAULT 'pregnant'")
        _add_column("patient", "delivery_date", "TEXT")
        _add_column("patient", "notes", "TEXT")

        _add_column("visit", "visit_type", "TEXT NOT NULL DEFAULT 'prenatal'")
        _add_column("visit", "notes", "TEXT")

        _add_column("vitals", "body_temp", "REAL")
        _add_column("vitals", "previous_complications", "INTEGER DEFAULT 0")
        _add_column("vitals", "preexisting_diabetes", "INTEGER DEFAULT 0")
        _add_column("vitals", "gestational_diabetes", "INTEGER DEFAULT 0")
        _add_column("vitals", "recorded_at", "TEXT")

        _add_column("mental_health_assessment", "screening_status", "TEXT")
        _add_column("mental_health_assessment", "safety_message", "TEXT")

        _add_column("contextual_risk_assessment", "model_name", "TEXT DEFAULT 'ContextualRandomForest'")
        _add_column("contextual_risk_assessment", "context_inputs_json", "TEXT")
        _add_column("contextual_risk_assessment", "explanation_text", "TEXT")
        _add_column("contextual_risk_assessment", "assessment_timestamp", "TEXT DEFAULT ''")

        _add_column("longitudinal_features", "features_json", "TEXT")


def create_patient(
    name: Optional[str] = None,
    age: Optional[int] = None,
    state: Optional[str] = None,
    pregnancy_status: str = "pregnant",
    delivery_date: Optional[date] = None,
    notes: Optional[str] = None,
    db_path: Path = DB_PATH
) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO patient (name, age, state, pregnancy_status, delivery_date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                age,
                state,
                pregnancy_status,
                delivery_date.isoformat() if delivery_date else None,
                notes,
                datetime.now().isoformat(),
            ),
        )
        return cur.lastrowid


def get_patient(patient_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM patient WHERE patient_id = ?", (patient_id,)).fetchone()
        if not row:
            return None
        return dict(row)


def update_patient(
    patient_id: int,
    name: Optional[str] = None,
    age: Optional[int] = None,
    state: Optional[str] = None,
    pregnancy_status: Optional[str] = None,
    delivery_date: Optional[date] = None,
    notes: Optional[str] = None,
    db_path: Path = DB_PATH
) -> bool:
    fields = []
    values = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if age is not None:
        fields.append("age = ?")
        values.append(age)
    if state is not None:
        fields.append("state = ?")
        values.append(state)
    if pregnancy_status is not None:
        fields.append("pregnancy_status = ?")
        values.append(pregnancy_status)
    if delivery_date is not None:
        fields.append("delivery_date = ?")
        values.append(delivery_date.isoformat() if isinstance(delivery_date, (date, datetime)) else delivery_date)
    if notes is not None:
        fields.append("notes = ?")
        values.append(notes)

    if not fields:
        return False

    values.append(patient_id)
    query = f"UPDATE patient SET {', '.join(fields)} WHERE patient_id = ?"
    with _connect(db_path) as conn:
        cur = conn.execute(query, tuple(values))
        return cur.rowcount > 0


def list_patients(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT p.*,
                   COUNT(v.visit_id) as total_visits,
                   MAX(v.visit_date) as last_visit_date
            FROM patient p
            LEFT JOIN visit v ON v.patient_id = p.patient_id
            GROUP BY p.patient_id
            ORDER BY p.patient_id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_previous_visits(patient_id: int, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Chronological list of this patient's prior visits for longitudinal feature computation."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT v.visit_id, v.visit_date, v.gestational_age, v.trimester, v.delivery_date,
                   m.total_score AS phq9_total_score, m.at_risk AS phq9_at_risk,
                   m.urgent_safety_flag,
                   c.risk_probability AS context_risk_probability,
                   vt.systolic_bp, vt.diastolic_bp, vt.blood_sugar, vt.bmi, vt.heart_rate
            FROM visit v
            JOIN mental_health_assessment m ON m.visit_id = v.visit_id
            LEFT JOIN contextual_risk_assessment c ON c.visit_id = v.visit_id
            LEFT JOIN vitals vt ON vt.visit_id = v.visit_id
            WHERE v.patient_id = ?
            ORDER BY v.visit_date ASC, v.visit_id ASC
            """,
            (patient_id,),
        ).fetchall()

    out = []
    for r in rows:
        v_date = r["visit_date"]
        if isinstance(v_date, str):
            v_date = date.fromisoformat(v_date)
        out.append({
            "visit_id": r["visit_id"],
            "visit_date": v_date,
            "gestational_age": r["gestational_age"],
            "trimester": r["trimester"],
            "delivery_date": r["delivery_date"],
            "phq9_total_score": r["phq9_total_score"],
            "phq9_at_risk": bool(r["phq9_at_risk"]),
            "urgent_safety_flag": bool(r["urgent_safety_flag"]),
            "context_risk_probability": r["context_risk_probability"],
            "vitals": {
                "systolic_bp": r["systolic_bp"],
                "diastolic_bp": r["diastolic_bp"],
                "blood_sugar": r["blood_sugar"],
                "bmi": r["bmi"],
                "heart_rate": r["heart_rate"],
            }
        })
    return out


def save_visit(
    patient_id: int,
    visit_date: date,
    trimester: str,
    screening_result: dict,
    context_result: Optional[dict],
    longitudinal_result: dict,
    gestational_age: Optional[int] = None,
    delivery_date: Optional[date] = None,
    visit_type: str = "prenatal",
    vitals: Optional[dict] = None,
    item_scores: Optional[dict] = None,
    context_inputs: Optional[dict] = None,
    notes: Optional[str] = None,
    db_path: Path = DB_PATH,
) -> int:
    """Inserts a new visit + assessments. Append-only — history is preserved forever."""
    with _connect(db_path) as conn:
        # Check patient existence
        patient = conn.execute("SELECT pregnancy_status, delivery_date FROM patient WHERE patient_id = ?", (patient_id,)).fetchone()
        if patient is None:
            # Auto-create patient record if not present for seamless backwards compatibility
            conn.execute(
                "INSERT INTO patient (patient_id, created_at, pregnancy_status) VALUES (?, ?, ?)",
                (patient_id, datetime.now().isoformat(), "postpartum" if delivery_date else "pregnant")
            )
        elif delivery_date and patient["pregnancy_status"] != "postpartum":
            conn.execute(
                "UPDATE patient SET pregnancy_status = 'postpartum', delivery_date = ? WHERE patient_id = ?",
                (delivery_date.isoformat() if isinstance(delivery_date, date) else delivery_date, patient_id)
            )

        cur = conn.execute(
            """
            INSERT INTO visit (patient_id, visit_date, gestational_age, delivery_date, trimester, visit_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                visit_date.isoformat() if isinstance(visit_date, date) else visit_date,
                gestational_age,
                delivery_date.isoformat() if isinstance(delivery_date, date) else delivery_date,
                trimester,
                visit_type,
                notes,
            ),
        )
        visit_id = cur.lastrowid

        # Insert vitals
        if vitals:
            conn.execute(
                """
                INSERT INTO vitals (
                    visit_id, systolic_bp, diastolic_bp, blood_sugar, bmi, heart_rate,
                    body_temp, previous_complications, preexisting_diabetes, gestational_diabetes, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    visit_id,
                    vitals.get("systolic_bp"),
                    vitals.get("diastolic_bp"),
                    vitals.get("blood_sugar"),
                    vitals.get("bmi"),
                    vitals.get("heart_rate"),
                    vitals.get("body_temp"),
                    vitals.get("previous_complications", 0),
                    vitals.get("preexisting_diabetes", 0),
                    vitals.get("gestational_diabetes", 0),
                    datetime.now().isoformat(),
                ),
            )

        # Insert mental health assessment
        conn.execute(
            """
            INSERT INTO mental_health_assessment (
                visit_id, screening_type, item_scores_json, total_score, severity,
                at_risk, urgent_safety_flag, screening_status, safety_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visit_id,
                screening_result.get("screening_type", "PHQ-9"),
                json.dumps(item_scores or {}),
                screening_result["total_score"],
                screening_result.get("severity"),
                int(screening_result.get("at_risk", False)),
                int(screening_result.get("urgent_safety_flag", False)),
                screening_result.get("screening_status", "Positive" if screening_result.get("at_risk") else "Negative"),
                screening_result.get("safety_message", ""),
            ),
        )

        # Insert contextual risk assessment
        if context_result:
            conn.execute(
                """
                INSERT INTO contextual_risk_assessment (
                    visit_id, model_name, model_version, risk_probability, risk_category,
                    top_contributing_factors_json, context_inputs_json, explanation_text, assessment_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    visit_id,
                    context_result.get("model_name", "ContextualRandomForest"),
                    context_result["model_version"],
                    context_result["risk_probability"],
                    context_result["risk_category"],
                    json.dumps(context_result.get("top_contributing_factors", [])),
                    json.dumps(context_inputs or {}),
                    context_result.get("explanation", ""),
                    context_result.get("assessment_timestamp", datetime.now().isoformat()),
                ),
            )

        # Insert longitudinal features
        conn.execute(
            """
            INSERT INTO longitudinal_features (
                visit_id, visit_count, score_change, risk_probability_change,
                num_previous_elevated_screenings, max_previous_score, avg_previous_score,
                days_since_last_visit, trend, features_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visit_id,
                longitudinal_result["visit_count"],
                longitudinal_result["score_change"],
                longitudinal_result["risk_probability_change"],
                longitudinal_result["num_previous_elevated_screenings"],
                longitudinal_result["max_previous_score"],
                longitudinal_result["avg_previous_score"],
                longitudinal_result["days_since_last_visit"],
                longitudinal_result["trend"],
                json.dumps(longitudinal_result),
            ),
        )

        return visit_id


def get_patient_history(patient_id: int, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Display-ready history of all visits for a patient."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT v.visit_id, v.visit_date, v.trimester, v.gestational_age, v.delivery_date, v.visit_type,
                   m.screening_type, m.total_score, m.severity, m.at_risk, m.urgent_safety_flag,
                   m.screening_status, m.safety_message,
                   c.model_name, c.model_version, c.risk_category, c.risk_probability,
                   c.top_contributing_factors_json, c.explanation_text,
                   l.visit_count, l.trend, l.score_change, l.risk_probability_change,
                   l.num_previous_elevated_screenings, l.days_since_last_visit,
                   vt.systolic_bp, vt.diastolic_bp, vt.blood_sugar, vt.bmi, vt.heart_rate, vt.body_temp
            FROM visit v
            JOIN mental_health_assessment m ON m.visit_id = v.visit_id
            LEFT JOIN contextual_risk_assessment c ON c.visit_id = v.visit_id
            LEFT JOIN longitudinal_features l ON l.visit_id = v.visit_id
            LEFT JOIN vitals vt ON vt.visit_id = v.visit_id
            WHERE v.patient_id = ?
            ORDER BY v.visit_date ASC, v.visit_id ASC
            """,
            (patient_id,),
        ).fetchall()

    history = []
    for r in rows:
        d = dict(r)
        if d.get("top_contributing_factors_json"):
            try:
                d["top_contributing_factors"] = json.loads(d["top_contributing_factors_json"])
            except Exception:
                d["top_contributing_factors"] = []
        history.append(d)
    return history


def get_latest_visit(patient_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    history = get_patient_history(patient_id, db_path)
    return history[-1] if history else None


# ── Nutrition Assessments ─────────────────────────────────────────────────────

def save_nutrition_assessment(data: Dict[str, Any], db_path: Path = DB_PATH) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO nutrition_assessment (
                patient_id, visit_id, assessment_date, gestational_age, trimester,
                height_cm, current_weight_kg, pre_pregnancy_weight_kg, current_bmi, pre_pregnancy_bmi,
                energy_kcal, carbohydrates_g, protein_g, fat_g, fibre_g,
                iron_mg, folate_mcg, calcium_mg, vitamin_d_iu, vitamin_b12_mcg,
                dietary_pattern, food_restrictions, appetite_difficulty, food_insecurity,
                supplements_taken, assessment_completeness, gaps_json, recommendations_json,
                notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["patient_id"],
                data.get("visit_id"),
                data.get("assessment_date", datetime.now().date().isoformat()),
                data.get("gestational_age"),
                data.get("trimester"),
                data.get("height_cm"),
                data.get("current_weight_kg"),
                data.get("pre_pregnancy_weight_kg"),
                data.get("current_bmi"),
                data.get("pre_pregnancy_bmi"),
                data.get("energy_kcal"),
                data.get("carbohydrates_g"),
                data.get("protein_g"),
                data.get("fat_g"),
                data.get("fibre_g"),
                data.get("iron_mg"),
                data.get("folate_mcg"),
                data.get("calcium_mg"),
                data.get("vitamin_d_iu"),
                data.get("vitamin_b12_mcg"),
                data.get("dietary_pattern", "vegetarian"),
                data.get("food_restrictions"),
                data.get("appetite_difficulty", "normal"),
                1 if data.get("food_insecurity") else 0,
                json.dumps(data.get("supplements_taken", [])),
                data.get("assessment_completeness", "partial"),
                json.dumps(data.get("gaps", [])),
                json.dumps(data.get("recommendations", [])),
                data.get("notes"),
                datetime.now().isoformat(),
            )
        )
        return cur.lastrowid


def get_nutrition_assessments(patient_id: int, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM nutrition_assessment
            WHERE patient_id = ?
            ORDER BY assessment_date ASC, assessment_id ASC
            """,
            (patient_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("gaps_json"):
                try: d["gaps"] = json.loads(d["gaps_json"])
                except Exception: d["gaps"] = []
            if d.get("recommendations_json"):
                try: d["recommendations"] = json.loads(d["recommendations_json"])
                except Exception: d["recommendations"] = []
            if d.get("supplements_taken"):
                try: d["supplements_taken"] = json.loads(d["supplements_taken"])
                except Exception: d["supplements_taken"] = []
            result.append(d)
        return result


def get_latest_nutrition_assessment(patient_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    assessments = get_nutrition_assessments(patient_id, db_path)
    return assessments[-1] if assessments else None


# ── Immunization Records ──────────────────────────────────────────────────────

def save_immunization_record(data: Dict[str, Any], db_path: Path = DB_PATH) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO immunization_record (
                patient_id, visit_id, vaccine_name, dose_number, status,
                administration_date, confirmation_source, card_verified, next_due_date,
                notes, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["patient_id"],
                data.get("visit_id"),
                data["vaccine_name"],
                data["dose_number"],
                data["status"],
                data.get("administration_date"),
                data.get("confirmation_source", "mcp_card"),
                1 if data.get("card_verified") else 0,
                data.get("next_due_date"),
                data.get("notes"),
                datetime.now().isoformat(),
            )
        )
        return cur.lastrowid


def get_immunization_records(patient_id: int, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM immunization_record
            WHERE patient_id = ?
            ORDER BY dose_number ASC, record_id ASC
            """,
            (patient_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Action Recommendations ────────────────────────────────────────────────────

def save_action_recommendation(data: Dict[str, Any], db_path: Path = DB_PATH) -> str:
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO action_recommendation (
                action_id, patient_id, visit_id, domain, trigger_observation,
                explanation, action_text, urgency, responsible_person, timeframe,
                referral_required, status, outcome_notes, completed_at,
                rule_source, rule_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["action_id"],
                data["patient_id"],
                data.get("visit_id"),
                data["domain"],
                data["trigger_observation"],
                data["explanation"],
                data["action_text"],
                data["urgency"],
                data["responsible_person"],
                data["timeframe"],
                1 if data.get("referral_required") else 0,
                data.get("status", "pending"),
                data.get("outcome_notes"),
                data.get("completed_at"),
                data.get("rule_source", "SanRaksha Clinical Protocol"),
                data.get("rule_version", "v1.0"),
                datetime.now().isoformat(),
            )
        )
        return data["action_id"]


def save_action_recommendations(actions: List[Dict[str, Any]], db_path: Path = DB_PATH) -> List[str]:
    saved = []
    for a in actions:
        saved.append(save_action_recommendation(a, db_path))
    return saved


def get_action_recommendations(patient_id: int, status: Optional[str] = None, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        if status:
            rows = conn.execute(
                """
                SELECT * FROM action_recommendation
                WHERE patient_id = ? AND status = ?
                ORDER BY CASE urgency
                    WHEN 'emergency' THEN 1
                    WHEN 'urgent' THEN 2
                    WHEN 'timely' THEN 3
                    WHEN 'routine' THEN 4
                    ELSE 5 END ASC, created_at DESC
                """,
                (patient_id, status)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM action_recommendation
                WHERE patient_id = ?
                ORDER BY CASE urgency
                    WHEN 'emergency' THEN 1
                    WHEN 'urgent' THEN 2
                    WHEN 'timely' THEN 3
                    WHEN 'routine' THEN 4
                    ELSE 5 END ASC, created_at DESC
                """,
                (patient_id,)
            ).fetchall()
        return [dict(r) for r in rows]


def update_action_status(
    action_id: str,
    status: str,
    outcome_notes: Optional[str] = None,
    db_path: Path = DB_PATH
) -> bool:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE action_recommendation
            SET status = ?, outcome_notes = ?, completed_at = ?
            WHERE action_id = ?
            """,
            (
                status,
                outcome_notes,
                datetime.now().isoformat() if status in ["completed", "referred"] else None,
                action_id,
            )
        )
        return cur.rowcount > 0


# ── Prediction Explanations ───────────────────────────────────────────────────

def save_prediction_explanation(data: Dict[str, Any], db_path: Path = DB_PATH) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO prediction_explanation (
                patient_id, visit_id, model_name, model_version, prediction_class,
                prediction_score, base_value, shap_values_json, top_features_json,
                limitations_disclaimer, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["patient_id"],
                data.get("visit_id"),
                data["model_name"],
                data["model_version"],
                data["prediction_class"],
                data.get("prediction_score"),
                data.get("base_value"),
                json.dumps(data.get("shap_values", {})),
                json.dumps(data.get("top_features", [])),
                data.get("limitations_disclaimer", ""),
                datetime.now().isoformat(),
            )
        )
        return cur.lastrowid


def get_prediction_explanations(patient_id: int, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM prediction_explanation
            WHERE patient_id = ?
            ORDER BY created_at DESC
            """,
            (patient_id,)
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if d.get("shap_values_json"):
                try: d["shap_values"] = json.loads(d["shap_values_json"])
                except Exception: d["shap_values"] = {}
            if d.get("top_features_json"):
                try: d["top_features"] = json.loads(d["top_features_json"])
                except Exception: d["top_features"] = []
            results.append(d)
        return results

