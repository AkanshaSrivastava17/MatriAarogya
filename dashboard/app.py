"""
app.py  ·  SanRaksha PHC Dashboard
=====================================
Features:
  • Authentication: simple OTP-style PIN login with session state.
    Two roles: "asha" (own patients only) and "doctor" (block-wide view).
  • Referral acknowledgment loop: doctors can mark alerts as
    "Reviewed", "Referred", or "Dismissed".
  • Time-series trend view: week-over-week high-risk case count per block.
  • Data persistence: feedback/complaints POST to FastAPI backend.
  • 🧠 Maternal Mental Health & Longitudinal Monitoring:
    - Interactive patient selector with pregnancy & postpartum tracking
    - Real-time PHQ-9 score, severity, and urgent suicidal ideation safety alerts
    - Contextual ML vulnerability estimation and contributing factors
    - Longitudinal trajectory Plotly charts (PHQ-9 progression, risk probability, vitals)
    - Append-only chronological visit timeline
  • 🥗 Maternal Diet & Nutrition Assessment:
    - Comparison with ICMR-NIN 2020 RDA benchmarks by trimester
    - Macro/micro nutrient deficit & surplus tracking
    - Weight and gestational weight gain progression curves
    - Indian food recommendations (dal, ragi, moringa, jaggery)
  • 💉 Immunization Tracker:
    - MoHFW UIP India Tetanus & Diphtheria (Td) schedule compliance
    - Dose history (Td-1, Td-2, Td-Booster) with facility & batch verification
    - Automated overdue warning alerts with escalation guidance
  • 🔍 Genuine SHAP-Based AI Explainability:
    - KernelExplainer attribution waterfall & bar plots for Keras physical risk model
    - TreeExplainer attribution for Random Forest mental health contextual model
    - Plain-language non-jargon explanations for ASHA workers
    - Interactive simulator for real-time what-if vitals explanation
    - Transparent scientific disclaimer regarding model sensitivity vs biological causality
  • 📋 Prioritized & Unified Action Recommendations:
    - Multi-domain synthesis categorized into Emergency, Urgent, Timely, Routine, Info
    - Interactive task manager with status toggling (Pending, In Progress, Completed, Deferred)
  • 📊 Real-World Comparative Benchmarks:
    - Longitudinal cohort comparison against NFHS-5 (2019-21) national & state indicators
    - Anemia, ANC 4+, Institutional Delivery, and Td immunization benchmarks
  • 📄 Comprehensive Maternal Health Dossier:
    - Multi-domain single-page synthesis with rule-based overall status determination
    - Red flags checklist and exportable clinical summary report
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
import streamlit as st
import folium
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import folium_static

# ── Paths and Configuration ───────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

API_BASE = os.environ.get("SANRAKSHA_API", "http://localhost:8000")

DATA_PATH     = str(PROJECT_ROOT / "data" / "risk_cases.csv")
CAPTURED_PATH = str(PROJECT_ROOT / "data" / "captured_vitals.csv")
ACK_PATH      = str(PROJECT_ROOT / "data" / "acknowledged_cases.csv")
STORE_DB_PATH = PROJECT_ROOT / "app" / "mental_health" / "store.db"

# ── Hardcoded users for demo ──────────────────────────────────────────────────
USERS = {
    "doctor1":  ("1234", "doctor"),
    "asha_riya": ("5678", "asha"),
}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SanRaksha PHC Dashboard",
    page_icon="https://raw.githubusercontent.com/sys6-exe/SanRaksha/main/assets/Sanraksha.png",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CSS ───────────────────────────────────────────────────────────────────────
def load_css():
    st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        .stApp { background: linear-gradient(135deg, #F8FAFC, #EDF2F7); color: #1A202C; }
        .top-container { display: flex; align-items: center; margin-bottom: 1.5rem; }
        .logo { width: 70px; height: 70px; border-radius: 50%; margin-right: 18px; }
        .title-text h1 { font-size: 2.5rem; font-weight: bold; color: #1A202C;
                         margin: 0; padding: 0; line-height: 1.1; }
        [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
        [data-testid="stMetric"] { background-color: #FFFFFF;
                                   border: 1px solid #E2E8F0;
                                   border-radius: 12px; padding: 16px; }
        [data-testid="stMetric"] > label { color: #2B6CB0; font-weight: 600; }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #1A202C; background-color: rgba(43,108,176,0.12);
            border-bottom: 3px solid #2B6CB0; font-weight: 600; }
        .section-title { font-size: 20px; font-weight: 700; color: #1A202C;
                         margin-bottom: 14px; border-left: 5px solid #2B6CB0;
                         padding-left: 10px; }
        .ack-card { background: #FFFFFF; border-radius: 10px;
                    padding: 14px 18px; margin-bottom: 10px;
                    border-left: 4px solid #E53E3E;
                    border: 1px solid #E2E8F0; }
        .priority-emergency { background:#FFF5F5; border-left:5px solid #E53E3E; border-radius:8px; padding:12px 16px; margin-bottom:10px; border:1px solid #FED7D7; }
        .priority-urgent    { background:#FFFAF0; border-left:5px solid #DD6B20; border-radius:8px; padding:12px 16px; margin-bottom:10px; border:1px solid #FEEBC8; }
        .priority-timely    { background:#EBF8FF; border-left:5px solid #3182CE; border-radius:8px; padding:12px 16px; margin-bottom:10px; border:1px solid #BEE3F8; }
        .priority-routine   { background:#F0FFF4; border-left:5px solid #38A169; border-radius:8px; padding:12px 16px; margin-bottom:10px; border:1px solid #C6F6D5; }
        .priority-info      { background:#F7FAFC; border-left:5px solid #718096; border-radius:8px; padding:12px 16px; margin-bottom:10px; border:1px solid #E2E8F0; }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span,
        [data-testid="stText"] { color: #1A202C; }
    </style>
    """, unsafe_allow_html=True)


# ── Data loading (Physical Vitals) ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@st.cache_data(ttl=30)
def load_captured_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "captured_at" in df.columns:
        df["captured_at"] = pd.to_datetime(df["captured_at"], errors="coerce")
    return df


def load_ack() -> pd.DataFrame:
    if os.path.exists(ACK_PATH):
        return pd.read_csv(ACK_PATH)
    return pd.DataFrame(columns=["case_id", "status", "doctor", "ack_time"])


def transform_captured_data(captured_df: pd.DataFrame) -> pd.DataFrame:
    if captured_df.empty:
        return pd.DataFrame()
    df = captured_df.copy()
    df["id"] = range(1, len(df) + 1)
    df["risk_level"] = df["prediction"].apply(lambda x: "high" if x == 1 else "low")
    df["systolic_bp"] = df["Systolic_BP"]
    df["diastolic_bp"] = df["Diastolic"]
    df["blood_sugar"] = df["BS"]
    df["bmi"] = df["BMI"]
    df["timestamp"] = df["captured_at"]
    df["state"] = df["state"].fillna("Unknown") if "state" in df.columns else "Unknown"
    df["latitude"] = 26.8 + (df.index * 0.01)
    df["longitude"] = 80.9 + (df.index * 0.01)
    return df[["id", "risk_level", "state", "latitude", "longitude", "timestamp",
               "systolic_bp", "diastolic_bp", "blood_sugar", "bmi"]]


def save_ack(case_id: str, status: str, doctor: str):
    ack_df = load_ack()
    row = {
        "case_id": case_id,
        "status":  status,
        "doctor":  doctor,
        "ack_time": datetime.now().isoformat(),
    }
    ack_df = ack_df[ack_df["case_id"] != case_id]
    ack_df = pd.concat([ack_df, pd.DataFrame([row])], ignore_index=True)
    os.makedirs(PROJECT_ROOT / "data", exist_ok=True)
    ack_df.to_csv(ACK_PATH, index=False)
    try:
        requests.post(f"{API_BASE}/referrals/acknowledge", json=row, timeout=2)
    except Exception:
        pass


def post_feedback(name: str, issue: str):
    payload = {
        "name": name or "Anonymous",
        "issue": issue,
        "timestamp": datetime.now().isoformat(),
    }
    try:
        requests.post(f"{API_BASE}/feedback", json=payload, timeout=2)
    except Exception:
        os.makedirs(PROJECT_ROOT / "reports", exist_ok=True)
        with open(PROJECT_ROOT / "reports" / "complaints.txt", "a") as f:
            f.write(f"{payload['timestamp']} - {payload['name']}: {issue}\n")


# ── Patient & History Access ──────────────────────────────────────────────────
def load_mh_patients() -> pd.DataFrame:
    try:
        r = requests.get(f"{API_BASE}/mental-health/patients", timeout=2)
        if r.status_code == 200:
            p_list = r.json().get("patients", [])
            if p_list:
                return pd.DataFrame(p_list)
    except Exception:
        pass

    if STORE_DB_PATH.exists():
        try:
            conn = sqlite3.connect(STORE_DB_PATH)
            df = pd.read_sql_query("SELECT * FROM patient ORDER BY patient_id ASC", conn)
            conn.close()
            return df
        except Exception:
            pass
    return pd.DataFrame()


def load_mh_history(patient_id: int) -> pd.DataFrame:
    try:
        r = requests.get(f"{API_BASE}/mental-health/patients/{patient_id}/history", timeout=2)
        if r.status_code == 200:
            visits = r.json().get("visits", [])
            if visits:
                df = pd.DataFrame(visits)
                if "visit_date" in df.columns:
                    df["visit_date"] = pd.to_datetime(df["visit_date"])
                return df
    except Exception:
        pass

    if STORE_DB_PATH.exists():
        try:
            conn = sqlite3.connect(STORE_DB_PATH)
            query = """
            SELECT v.visit_id, v.visit_date, v.trimester, v.gestational_age, v.delivery_date, v.visit_type,
                   m.total_score, m.severity, m.at_risk, m.urgent_safety_flag, m.screening_status,
                   c.model_name, c.risk_category, c.risk_probability, c.explanation_text,
                   l.trend, l.score_change, l.num_previous_elevated_screenings,
                   vt.systolic_bp, vt.diastolic_bp, vt.heart_rate, vt.blood_sugar, vt.bmi
            FROM visit v
            JOIN mental_health_assessment m ON m.visit_id = v.visit_id
            LEFT JOIN contextual_risk_assessment c ON c.visit_id = v.visit_id
            LEFT JOIN longitudinal_features l ON l.visit_id = v.visit_id
            LEFT JOIN vitals vt ON vt.visit_id = v.visit_id
            WHERE v.patient_id = ?
            ORDER BY v.visit_date ASC, v.visit_id ASC
            """
            df = pd.read_sql_query(query, conn, params=(patient_id,))
            conn.close()
            if not df.empty and "visit_date" in df.columns:
                df["visit_date"] = pd.to_datetime(df["visit_date"])
            return df
        except Exception:
            pass
    return pd.DataFrame()


# ── Nutrition Helpers ─────────────────────────────────────────────────────────
def load_nutrition_assessments(patient_id: int) -> list:
    try:
        r = requests.get(f"{API_BASE}/nutrition/patients/{patient_id}/assessments", timeout=2)
        if r.status_code == 200:
            return r.json().get("assessments", [])
    except Exception:
        pass
    if STORE_DB_PATH.exists():
        try:
            from app.mental_health.store import MentalHealthStore
            store = MentalHealthStore(str(STORE_DB_PATH))
            return store.get_nutrition_assessments(patient_id)
        except Exception:
            pass
    return []


def load_latest_nutrition(patient_id: int):
    try:
        r = requests.get(f"{API_BASE}/nutrition/patients/{patient_id}/latest", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    try:
        from app.mental_health.store import MentalHealthStore
        from app.nutrition.service import NutritionService
        store = MentalHealthStore(str(STORE_DB_PATH))
        service = NutritionService(store)
        return service.get_latest_assessment(patient_id)
    except Exception:
        pass
    return None


# ── Immunization Helpers ──────────────────────────────────────────────────────
def load_immunization_status(patient_id: int):
    try:
        r = requests.get(f"{API_BASE}/immunization/patients/{patient_id}/status", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    try:
        from app.mental_health.store import MentalHealthStore
        from app.immunization.service import ImmunizationService
        store = MentalHealthStore(str(STORE_DB_PATH))
        service = ImmunizationService(store)
        return service.get_patient_status(patient_id)
    except Exception:
        pass
    return None


def load_immunization_records(patient_id: int) -> list:
    try:
        r = requests.get(f"{API_BASE}/immunization/patients/{patient_id}/records", timeout=2)
        if r.status_code == 200:
            return r.json().get("records", [])
    except Exception:
        pass
    if STORE_DB_PATH.exists():
        try:
            from app.mental_health.store import MentalHealthStore
            store = MentalHealthStore(str(STORE_DB_PATH))
            return store.get_immunization_records(patient_id)
        except Exception:
            pass
    return []


# ── Guidance & Action Helpers ─────────────────────────────────────────────────
def load_action_recommendations(patient_id: int) -> list:
    try:
        r = requests.get(f"{API_BASE}/guidance/patients/{patient_id}/actions", timeout=2)
        if r.status_code == 200:
            return r.json().get("recommendations", [])
    except Exception:
        pass
    if STORE_DB_PATH.exists():
        try:
            from app.mental_health.store import MentalHealthStore
            store = MentalHealthStore(str(STORE_DB_PATH))
            return store.get_action_recommendations(patient_id)
        except Exception:
            pass
    return []


def update_action_status(action_id: str, new_status: str) -> bool:
    try:
        r = requests.put(f"{API_BASE}/guidance/actions/{action_id}/status", json={"status": new_status}, timeout=2)
        if r.status_code == 200:
            return True
    except Exception:
        pass
    if STORE_DB_PATH.exists():
        try:
            from app.mental_health.store import MentalHealthStore
            store = MentalHealthStore(str(STORE_DB_PATH))
            return store.update_action_status(action_id, new_status)
        except Exception:
            pass
    return False


# ── Explainability Helpers ────────────────────────────────────────────────────
def explain_physical_risk(payload: dict) -> dict:
    try:
        r = requests.post(f"{API_BASE}/explainability/physical-risk", json=payload, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    try:
        from app.explainability.shap_service import ShapExplainabilityService
        service = ShapExplainabilityService()
        return service.explain_physical_risk(payload)
    except Exception as e:
        return {"error": str(e)}


def explain_contextual_risk(payload: dict) -> dict:
    try:
        r = requests.post(f"{API_BASE}/explainability/contextual-risk", json=payload, timeout=6)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    try:
        from app.explainability.shap_service import ShapExplainabilityService
        service = ShapExplainabilityService()
        return service.explain_contextual_risk(payload)
    except Exception as e:
        return {"error": str(e)}


# ── Summary Dossier Helpers ───────────────────────────────────────────────────
def load_comprehensive_summary(patient_id: int):
    try:
        r = requests.get(f"{API_BASE}/summary/patients/{patient_id}", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    try:
        from app.mental_health.store import MentalHealthStore
        from app.summary.summary_service import SummaryService
        store = MentalHealthStore(str(STORE_DB_PATH))
        service = SummaryService(store)
        return service.generate_patient_summary(patient_id)
    except Exception:
        pass
    return None


# ── Render Patient Banner ─────────────────────────────────────────────────────
def render_patient_banner(pat_row: pd.Series):
    p_id = pat_row["patient_id"]
    p_name = pat_row.get("name") or "Anonymous"
    p_status = str(pat_row.get("pregnancy_status", "pregnant"))
    p_state = pat_row.get("state") or "Unspecified"
    p_age = pat_row.get("age", "N/A")
    p_parity = pat_row.get("parity", 0)

    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #CBD5E0; border-radius:12px; padding:14px 18px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:#1A202C;">{p_name} <span style="font-size:14px; color:#718096; font-weight:normal;">(Patient ID: #{p_id})</span></h3>
                    <p style="margin:4px 0 0 0; color:#4A5568; font-size:13px;">Age: <b>{p_age}</b> &nbsp;|&nbsp; Parity: <b>{p_parity}</b> &nbsp;|&nbsp; State: <b>{p_state}</b> &nbsp;|&nbsp; Status: <b>{p_status.upper()}</b></p>
                </div>
                <div style="background:{'#FED7D7' if p_status == 'postpartum' else '#C6F6D5'}; padding:6px 14px; border-radius:20px; font-weight:bold; color:{'#C53030' if p_status == 'postpartum' else '#22543D'}; font-size:13px;">
                    {'Postpartum Tracking' if p_status == 'postpartum' else 'Prenatal Monitoring'}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ── Trend Chart ───────────────────────────────────────────────────────────────
def render_trend(df: pd.DataFrame, selected_state: str):
    st.markdown("<p class='section-title'>Risk Trend — Week over Week</p>", unsafe_allow_html=True)
    scope = df if selected_state == "All States" else df[df["state"] == selected_state]
    if scope.empty:
        st.info("No data for trend analysis.")
        return

    scope = scope.copy()
    scope["week"] = scope["timestamp"].dt.to_period("W").astype(str)
    trend = (
        scope[scope["risk_level"] == "high"]
        .groupby(["week", "state"])
        .size()
        .reset_index(name="high_risk_count")
    )
    if trend.empty:
        st.info("No high-risk cases to trend.")
        return

    fig = px.line(
        trend, x="week", y="high_risk_count", color="state",
        title="High-risk cases per week by state",
        labels={"week": "Week", "high_risk_count": "High-Risk Cases"},
        template="plotly_dark",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#1A202C", legend_title_text="State",
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Referral Panel ────────────────────────────────────────────────────────────
def render_referral_panel(df: pd.DataFrame):
    if st.session_state.get("role") != "doctor":
        return

    st.markdown("<p class='section-title'>Pending Alerts — Action Required</p>", unsafe_allow_html=True)
    ack_df  = load_ack()
    acked   = set(ack_df["case_id"].astype(str))
    pending = df[(df["risk_level"] == "high") & (~df.index.astype(str).isin(acked))]

    if pending.empty:
        st.success("All high-risk alerts have been acknowledged.")
        return

    st.warning(f"{len(pending)} unacknowledged high-risk case(s).")
    for idx, row in pending.iterrows():
        case_id = str(idx)
        with st.container():
            st.markdown(
                f"""<div class='ack-card'>
                    <b>{row.get('state','Unknown')}</b> &nbsp;|&nbsp;
                    Lat: {row.get('latitude','?')}, Lon: {row.get('longitude','?')}
                    &nbsp;|&nbsp; {pd.to_datetime(row.get('timestamp','')).strftime('%d %b %Y %H:%M') if row.get('timestamp') else 'N/A'}
                </div>""",
                unsafe_allow_html=True,
            )
            c1, c2, c3, _ = st.columns([1, 1, 1, 3])
            if c1.button("✅ Reviewed",  key=f"rev_{case_id}"):
                save_ack(case_id, "reviewed",  st.session_state["user"])
                st.rerun()
            if c2.button("🏥 Referred",  key=f"ref_{case_id}"):
                save_ack(case_id, "referred",  st.session_state["user"])
                st.rerun()
            if c3.button("🗑 Dismissed", key=f"dis_{case_id}"):
                save_ack(case_id, "dismissed", st.session_state["user"])
                st.rerun()

    with st.expander("View acknowledgment history"):
        if not ack_df.empty:
            st.dataframe(ack_df.sort_values("ack_time", ascending=False), use_container_width=True)
        else:
            st.info("No acknowledgments yet.")


# ── Tab: Mental Health & Longitudinal ─────────────────────────────────────────
def render_mental_health_tab(role: str, user: str):
    st.markdown("<p class='section-title'>Maternal Mental Health & Longitudinal Trajectory</p>", unsafe_allow_html=True)

    patients_df = load_mh_patients()
    if patients_df.empty:
        st.info("ℹ️ No patients registered in the database yet.")
        return

    patient_options = {f"ID #{row['patient_id']} — {row.get('name', 'Anonymous')} ({str(row.get('pregnancy_status','pregnant')).capitalize()})": row['patient_id']
                       for _, row in patients_df.iterrows()}
    sel_label = st.selectbox("Select Patient to Monitor", list(patient_options.keys()), key="sel_mh_patient")
    sel_pid = patient_options[sel_label]
    pat_row = patients_df[patients_df["patient_id"] == sel_pid].iloc[0]

    render_patient_banner(pat_row)

    history_df = load_mh_history(sel_pid)
    if history_df.empty:
        st.warning(f"No visit records logged for patient #{sel_pid} yet.")
        return

    latest = history_df.iloc[-1]
    is_urgent = (latest.get("urgent_safety_flag") == 1)

    if is_urgent:
        st.markdown(
            """
            <div style="background-color:#FFF5F5; border-left:6px solid #E53E3E; border-radius:8px; padding:16px; margin-bottom:16px;">
                <h4 style="color:#C53030; margin:0 0 6px 0;">🚨 ACUTE CLINICAL SAFETY ALERT (Suicidal Ideation / Self-Harm Flag)</h4>
                <p style="color:#9B2C2C; margin:0;">Patient answered positively to PHQ-9 Item 9. Immediate clinical escalation and specialist psychiatric evaluation required. Do not leave the mother unattended.</p>
                <p style="color:#9B2C2C; margin:6px 0 0 0; font-size:13px;"><b>Tele-MANAS Support Helpline:</b> 14416 / 1800-891-4416</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Latest PHQ-9 Score", f"{latest.get('total_score', 'N/A')} / 27", delta=f"{latest.get('severity', '')}")
    with m2:
        screen_pos = latest.get("at_risk") == 1 or latest.get("total_score", 0) >= 10
        st.metric("Screening Status", "Positive" if screen_pos else "Negative", delta=">=10 Cutoff" if screen_pos else "<10")
    with m3:
        risk_prob = latest.get("risk_probability")
        prob_str = f"{(risk_prob * 100):.0f}%" if pd.notna(risk_prob) else "N/A"
        st.metric("Contextual ML Risk", prob_str, delta=f"{latest.get('risk_category', 'Low')}")
    with m4:
        trend_val = str(latest.get("trend", "insufficient_data"))
        score_chg = latest.get("score_change")
        chg_str = f"{score_chg:+d} pts" if pd.notna(score_chg) else "Baseline"
        st.metric("Trajectory Trend", trend_val.capitalize(), delta=chg_str)
    with m5:
        st.metric("Total Visits Logged", f"{len(history_df)}", delta=f"{latest.get('trimester', '')}")

    st.write("---")
    st.markdown("##### 📈 Longitudinal Trajectory Analysis")
    col_chart1, col_chart2 = st.columns(2)

    visit_labels = [f"V{i+1}: {d.strftime('%d %b') if pd.notna(d) else ''}" for i, d in enumerate(history_df["visit_date"])]

    with col_chart1:
        fig_phq = go.Figure()
        fig_phq.add_hline(y=10, line_dash="dash", line_color="orange", annotation_text="Cutoff (>=10: At Risk)", annotation_position="top left")
        dot_colors = ["#E53E3E" if u == 1 else "#3182CE" for u in history_df["urgent_safety_flag"]]
        fig_phq.add_trace(go.Scatter(
            x=visit_labels, y=history_df["total_score"],
            mode="lines+markers", name="PHQ-9 Score",
            line=dict(color="#3182CE", width=3), marker=dict(size=10, color=dot_colors),
            hovertemplate="<b>%{x}</b><br>Score: %{y}/27<extra></extra>"
        ))
        fig_phq.update_layout(
            title="PHQ-9 Score Trajectory Over Visits (Red Marker = Urgent Safety Flag)",
            xaxis_title="Visit Sequence", yaxis_title="PHQ-9 Total Score (0-27)",
            yaxis=dict(range=[0, 27]), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#1A202C"), margin=dict(l=20, r=20, t=40, b=20), height=300
        )
        st.plotly_chart(fig_phq, use_container_width=True)

    with col_chart2:
        if "risk_probability" in history_df.columns and history_df["risk_probability"].notna().any():
            fig_risk = go.Figure()
            prob_pct = history_df["risk_probability"] * 100
            fig_risk.add_trace(go.Scatter(
                x=visit_labels, y=prob_pct,
                mode="lines+markers", name="Contextual Risk %",
                line=dict(color="#DD6B20", width=3), marker=dict(size=9, color="#DD6B20"),
                hovertemplate="<b>%{x}</b><br>Risk: %{y:.1f}%<extra></extra>"
            ))
            fig_risk.update_layout(
                title="Contextual ML Risk Probability Trajectory",
                xaxis_title="Visit Sequence", yaxis_title="Estimated Risk Probability (%)",
                yaxis=dict(range=[0, 100]), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1A202C"), margin=dict(l=20, r=20, t=40, b=20), height=300
            )
            st.plotly_chart(fig_risk, use_container_width=True)

    # Vitals Trajectory
    if "systolic_bp" in history_df.columns and history_df["systolic_bp"].notna().any():
        st.markdown("##### 🩺 Physiological Vitals Trajectory")
        fig_vitals = go.Figure()
        fig_vitals.add_trace(go.Scatter(x=visit_labels, y=history_df["systolic_bp"], mode="lines+markers", name="Systolic BP (mmHg)", line=dict(color="#E53E3E")))
        fig_vitals.add_trace(go.Scatter(x=visit_labels, y=history_df["diastolic_bp"], mode="lines+markers", name="Diastolic BP (mmHg)", line=dict(color="#3182CE")))
        if "heart_rate" in history_df.columns and history_df["heart_rate"].notna().any():
            fig_vitals.add_trace(go.Scatter(x=visit_labels, y=history_df["heart_rate"], mode="lines+markers", name="Heart Rate (bpm)", line=dict(color="#38A169")))
        fig_vitals.update_layout(
            title="Blood Pressure & Heart Rate Progression Across Visits",
            xaxis_title="Visit Sequence", yaxis_title="Value",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#1A202C"), margin=dict(l=20, r=20, t=40, b=20), height=280
        )
        st.plotly_chart(fig_vitals, use_container_width=True)

    st.info("🔬 **Scientific Model Disclaimer:** Validated prospective postpartum prediction is not claimed as models are derived from cross-sectional data. The system provides deterministic PHQ-9 screening, socio-demographic risk estimation, and longitudinal trajectory monitoring.")


# ── Tab: Maternal Diet & Nutrition ────────────────────────────────────────────
def render_nutrition_tab(role: str, user: str):
    st.markdown("<p class='section-title'>Maternal Diet & Nutrition Assessment</p>", unsafe_allow_html=True)

    patients_df = load_mh_patients()
    if patients_df.empty:
        st.info("ℹ️ No registered patients found.")
        return

    patient_options = {f"ID #{row['patient_id']} — {row.get('name', 'Anonymous')}": row['patient_id'] for _, row in patients_df.iterrows()}
    sel_label = st.selectbox("Select Patient for Nutrition Assessment", list(patient_options.keys()), key="sel_nutr_patient")
    sel_pid = patient_options[sel_label]
    pat_row = patients_df[patients_df["patient_id"] == sel_pid].iloc[0]

    render_patient_banner(pat_row)

    eval_data = load_latest_nutrition(sel_pid)

    if not eval_data:
        st.warning(f"No nutrition assessment recorded for patient #{sel_pid} yet.")
        st.info("ASHA workers can record dietary intake and vitals using the Android mobile app, or you can record an assessment below.")
        return

    # Unpack latest evaluation
    wp = eval_data.get("weight_progression") or {}
    comparisons = eval_data.get("comparisons") or []
    gaps = eval_data.get("gaps") or []
    recs = eval_data.get("recommendations") or []
    assessment = eval_data.get("assessment") or {}

    # Top metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Gestational Stage", f"{assessment.get('trimester', 'N/A').title()}", delta=f"{assessment.get('gestational_age', 'N/A')} weeks")
    with c2:
        curr_bmi = wp.get("current_bmi")
        st.metric("Current BMI", f"{curr_bmi:.1f} kg/m²" if curr_bmi else "N/A", delta=wp.get("current_bmi_category", "Normal"))
    with c3:
        gwg = wp.get("gestational_weight_gain_kg")
        gwg_str = f"+{gwg:.1f} kg" if gwg is not None else "N/A"
        st.metric("Weight Gain (GWG)", gwg_str, delta=f"Target: {wp.get('recommended_gain_range', '11.5-16 kg')}")
    with c4:
        deficit_count = sum(1 for c in comparisons if c.get("status") == "deficit")
        st.metric("Nutritional Gaps", f"{deficit_count} Deficit(s)", delta="ICMR-NIN 2020 RDA")

    st.write("---")

    # Weight Progression Guidance
    st.markdown("##### ⚖️ Weight Progression & Maternal BMI Analysis")
    col_w1, col_w2 = st.columns([3, 2])
    with col_w1:
        st.info(f"**Clinical Weight Guidance:** {wp.get('guidance', 'Adequate weight gain supports healthy fetal growth.')}")
        pre_wt = wp.get("pre_pregnancy_weight_kg")
        cur_wt = wp.get("current_weight_kg")
        if pre_wt and cur_wt:
            fig_wt = go.Figure()
            fig_wt.add_trace(go.Bar(
                x=["Pre-Pregnancy Weight", "Current Weight"],
                y=[pre_wt, cur_wt],
                marker_color=["#3182CE", "#38A169"],
                text=[f"{pre_wt} kg", f"{cur_wt} kg"],
                textposition="auto"
            ))
            fig_wt.update_layout(
                title=f"Weight Gain: +{cur_wt - pre_wt:.1f} kg (Pre-Pregnancy: {wp.get('pre_pregnancy_bmi_category', 'Normal')})",
                yaxis_title="Weight (kg)",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1A202C"), height=260, margin=dict(l=20, r=20, t=35, b=20)
            )
            st.plotly_chart(fig_wt, use_container_width=True)
    with col_w2:
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:14px;">
                <h5 style="margin:0 0 8px 0; color:#2B6CB0;">ICMR-NIN 2020 Pregnancy Reference:</h5>
                <p style="margin:0; font-size:13px; color:#4A5568;">
                    • <b>1st Trimester:</b> +0.5 – 2.0 kg total gain<br>
                    • <b>2nd & 3rd Trimester:</b> ~0.4 – 0.5 kg/week<br>
                    • <b>Normal Pre-BMI:</b> 11.5 – 16.0 kg total<br>
                    • <b>Underweight Pre-BMI:</b> 12.5 – 18.0 kg total<br>
                    • <b>Overweight Pre-BMI:</b> 7.0 – 11.5 kg total
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Nutrient RDA Comparison Chart
    st.write("---")
    st.markdown("##### 🥗 Macro & Micronutrient Intake vs ICMR-NIN 2020 RDA")

    if comparisons:
        chart_data = []
        for c in comparisons:
            if c.get("reported_value") is not None:
                chart_data.append({
                    "Nutrient": c.get("label", c.get("nutrient")),
                    "Reported Intake": c.get("reported_value"),
                    "Reference RDA": c.get("reference_value"),
                    "Unit": c.get("unit"),
                    "Status": c.get("status", "unknown").capitalize(),
                    "% of RDA": f"{c.get('percent_of_reference', 0):.0f}%" if c.get("percent_of_reference") else "N/A"
                })

        if chart_data:
            df_nutr = pd.DataFrame(chart_data)
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="Reported Intake",
                x=df_nutr["Nutrient"],
                y=df_nutr["Reported Intake"],
                marker_color="#3182CE"
            ))
            fig_bar.add_trace(go.Bar(
                name="ICMR-NIN RDA Benchmark",
                x=df_nutr["Nutrient"],
                y=df_nutr["Reference RDA"],
                marker_color="#A0AEC0"
            ))
            fig_bar.update_layout(
                barmode="group",
                title="Nutrient Intake Comparison (Reported vs Authoritative Indian Reference)",
                xaxis_title="Nutrient",
                yaxis_title="Intake Amount (Refer to table for units)",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1A202C"), height=350, margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Details Table
            st.dataframe(df_nutr[["Nutrient", "Reported Intake", "Reference RDA", "Unit", "Status", "% of RDA"]], use_container_width=True)

    # Practical Dietary Recommendations
    if recs:
        st.write("---")
        st.markdown("##### 🌾 Personalized Indian Dietary Recommendations & Practical Food Steps")
        for r in recs:
            st.markdown(
                f"""
                <div style="background:#FFFFFF; border-left:4px solid #38A169; border-radius:8px; padding:12px 16px; margin-bottom:10px; border:1px solid #E2E8F0;">
                    <b style="color:#22543D; font-size:14px;">{r}</b>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Supplements
    sups = assessment.get("supplements_taken", [])
    if sups:
        st.markdown(f"**Supplements Currently Taken:** {', '.join(sups)}")


# ── Tab: Immunization Tracker ─────────────────────────────────────────────────
def render_immunization_tab(role: str, user: str):
    st.markdown("<p class='section-title'>Maternal Vaccination & Immunization Tracker (UIP India)</p>", unsafe_allow_html=True)

    patients_df = load_mh_patients()
    if patients_df.empty:
        st.info("ℹ️ No registered patients found.")
        return

    patient_options = {f"ID #{row['patient_id']} — {row.get('name', 'Anonymous')}": row['patient_id'] for _, row in patients_df.iterrows()}
    sel_label = st.selectbox("Select Patient for Immunization Tracking", list(patient_options.keys()), key="sel_immu_patient")
    sel_pid = patient_options[sel_label]
    pat_row = patients_df[patients_df["patient_id"] == sel_pid].iloc[0]

    render_patient_banner(pat_row)

    status_data = load_immunization_status(sel_pid)
    records = load_immunization_records(sel_pid)

    if not status_data:
        st.warning(f"No immunization records logged for patient #{sel_pid} yet.")
        st.info("ASHA workers can log Td doses using the mobile app.")
        return

    overall_status = status_data.get("overall_status", "pending")
    status_color = {"up_to_date": "#38A169", "partially_immunized": "#3182CE", "overdue": "#E53E3E"}.get(overall_status, "#718096")
    status_label = {"up_to_date": "✅ Fully Immunized / Up to Date", "partially_immunized": "⏱️ Partially Immunized (Next Dose Pending)", "overdue": "🚨 Dose Overdue (Action Required)"}.get(overall_status, "Pending")

    st.markdown(
        f"""
        <div style="background:{'#F0FFF4' if overall_status == 'up_to_date' else ('#FFF5F5' if overall_status == 'overdue' else '#EBF8FF')};
                    border:2px solid {status_color}; border-radius:12px; padding:16px; margin-bottom:16px;">
            <h4 style="margin:0; color:{status_color};">{status_label}</h4>
            <p style="margin:6px 0 0 0; font-size:14px; color:#2D3748;">
                <b>Vaccine Protocol:</b> Tetanus & Adult Diphtheria (Td) Toxoid as mandated by Universal Immunization Programme (UIP), MoHFW India.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Next Recommended Dose Callout
    next_dose = status_data.get("next_recommended_dose")
    due_date = status_data.get("next_dose_due_date")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Doses Administered", f"{len(status_data.get('doses_administered', []))}")
    with c2:
        st.metric("Next Required Dose", next_dose or "None Required")
    with c3:
        st.metric("Due Date", due_date or "Complete")

    # Overdue Alerts
    overdue_alerts = status_data.get("overdue_alerts", [])
    if overdue_alerts:
        st.write("---")
        for alert in overdue_alerts:
            st.markdown(
                f"""
                <div style="background:#FFF5F5; border-left:5px solid #E53E3E; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                    <b style="color:#C53030;">🚨 {alert.get('dose_name')} is OVERDUE by {alert.get('days_overdue')} days!</b><br>
                    <span style="font-size:13px; color:#742A2A;">Target gestational age: {alert.get('target_gestational_age')} weeks. Recommended Action: {alert.get('recommended_action')}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Administered Doses Table
    st.write("---")
    st.markdown("##### 💉 Administered Doses Log")
    if records:
        df_immu = pd.DataFrame(records)
        display_cols = [c for c in ["dose_name", "dose_date", "gestational_age_weeks", "facility_name", "batch_number", "card_verified", "adverse_event_reported"] if c in df_immu.columns]
        st.dataframe(df_immu[display_cols], use_container_width=True)
    else:
        st.info("No dose records logged in system yet.")

    # UIP India Guidelines Reference
    with st.expander("📖 Universal Immunization Programme (UIP) India Maternal Guidelines"):
        st.markdown("""
        - **Td-1:** Administer as early in pregnancy as possible (first ANC visit).
        - **Td-2:** Administer 4 weeks after Td-1 (recommended before 36 weeks of gestation).
        - **Td-Booster:** If the mother received 2 Td doses in a previous pregnancy within the last 3 years, only 1 booster dose is required.
        - **Card Verification:** Always verify and record details in the Mother & Child Protection (MCP) card.
        """)


# ── Tab: AI Explainability (SHAP) ─────────────────────────────────────────────
def render_explainability_tab(role: str, user: str):
    st.markdown("<p class='section-title'>AI Explainability & Model Interpretation (SHAP)</p>", unsafe_allow_html=True)

    st.markdown("""
    This module uses **SHAP (SHapley Additive exPlanations)** grounded in cooperative game theory to uncover
    the exact contribution of every clinical and contextual factor toward the model's risk output.
    """)

    model_choice = st.radio("Select Model to Inspect:", ["🩺 Physical Risk Model (Keras Deep Learning / MLP)", "🧠 Mental Health Contextual Model (Random Forest)"], horizontal=True)

    if "Physical Risk" in model_choice:
        st.markdown("##### 🩺 Physical Maternal Risk Model SHAP Explanation")
        st.write("Examine how physiological vitals drive the Keras Neural Network prediction using **SHAP KernelExplainer**.")

        # Interactive Vitals Inputs
        st.markdown("###### 🎛️ Adjust Patient Vitals for Real-Time SHAP Simulation:")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            age = st.slider("Age (years)", 15, 60, 28)
            sbp = st.slider("Systolic BP (mmHg)", 80, 180, 135)
            dbp = st.slider("Diastolic BP (mmHg)", 50, 120, 88)
        with col2:
            bs = st.slider("Blood Sugar (mmol/L)", 4.0, 19.0, 9.5, step=0.1)
            temp = st.slider("Body Temp (°F)", 96.0, 103.0, 98.6, step=0.1)
            bmi = st.slider("BMI (kg/m²)", 15.0, 45.0, 27.5, step=0.1)
        with col3:
            hr = st.slider("Heart Rate (bpm)", 55, 125, 78)
            prev_comp = st.selectbox("Previous Complications", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
            pre_diab = st.selectbox("Preexisting Diabetes", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
        with col4:
            gest_diab = st.selectbox("Gestational Diabetes", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
            mh_flag = st.selectbox("Mental Health Distress", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
            calc_btn = st.button("🔬 Compute SHAP Attributions", use_container_width=True, type="primary")

        if calc_btn:
            payload = {
                "Age": age, "Systolic_BP": sbp, "Diastolic": dbp, "BS": bs,
                "Body_Temp": temp, "BMI": bmi, "Previous_Complications": prev_comp,
                "Preexisting_Diabetes": pre_diab, "Gestational_Diabetes": gest_diab,
                "Mental_Health": mh_flag, "Heart_Rate": hr
            }
            with st.spinner("Calculating SHAP KernelExplainer attributions..."):
                result = explain_physical_risk(payload)

            if "error" in result:
                st.error(f"Error computing SHAP: {result['error']}")
            else:
                pred_label = result.get("prediction_label", "Unknown")
                pred_prob = result.get("prediction_probability", 0.0)

                st.write("---")
                # Prediction Banner
                res_color = "#E53E3E" if pred_label == "high" else "#38A169"
                st.markdown(
                    f"""
                    <div style="background:{'#FFF5F5' if pred_label == 'high' else '#F0FFF4'}; border:2px solid {res_color}; border-radius:10px; padding:14px; margin-bottom:14px;">
                        <h4 style="margin:0; color:{res_color};">Predicted Risk: {pred_label.upper()} RISK ({(pred_prob*100):.1f}% confidence)</h4>
                        <p style="margin:4px 0 0 0; color:#2D3748; font-size:14px;">Model: <b>{result.get('model_name', 'Keras MLP')}</b> &nbsp;|&nbsp; Base Expected Value: <b>{result.get('base_value', 0.5):.2f}</b></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # SHAP Feature Attributions Bar Chart
                features = result.get("feature_names", [])
                shap_vals = result.get("shap_values", [])
                if features and shap_vals:
                    df_shap = pd.DataFrame({"Feature": features, "SHAP Attribution": shap_vals})
                    df_shap["Direction"] = df_shap["SHAP Attribution"].apply(lambda x: "Increases Risk (+)" if x > 0 else "Decreases Risk (-)")
                    df_shap = df_shap.sort_values(by="SHAP Attribution", key=abs, ascending=True)

                    fig_shap = px.bar(
                        df_shap, x="SHAP Attribution", y="Feature", orientation="h",
                        color="Direction",
                        color_discrete_map={"Increases Risk (+)": "#E53E3E", "Decreases Risk (-)": "#38A169"},
                        title="SHAP Feature Attributions (Impact on Risk Probability)"
                    )
                    fig_shap.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#1A202C"), height=380, margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_shap, use_container_width=True)

                # Plain-Language Summary for ASHA Worker
                c_sum1, c_sum2 = st.columns(2)
                with c_sum1:
                    st.markdown(
                        f"""
                        <div style="background:#FFFFFF; border:1px solid #CBD5E0; border-radius:10px; padding:14px;">
                            <h5 style="margin:0 0 8px 0; color:#2B6CB0;">🗣️ Easy Explanation for ASHA Worker</h5>
                            <p style="margin:0; font-size:13px; color:#2D3748;">{result.get('human_summary', 'Detailed summary not available.')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with c_sum2:
                    st.markdown(
                        f"""
                        <div style="background:#FFFFFF; border:1px solid #CBD5E0; border-radius:10px; padding:14px;">
                            <h5 style="margin:0 0 8px 0; color:#276749;">📋 Actionable Steps for ASHA Worker</h5>
                            <p style="margin:0; font-size:13px; color:#2D3748;">{result.get('actionable_guidance', 'Follow standard clinical protocol.')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    else:
        st.markdown("##### 🧠 Mental Health Contextual Vulnerability SHAP Explanation")
        st.write("Inspect how psychosocial factors influence contextual risk estimation using **SHAP TreeExplainer**.")

        col1, col2, col3 = st.columns(3)
        with col1:
            sleep = st.slider("Sleep Quality Rating (1=Poor, 5=Good)", 1, 5, 2)
            fin_stress = st.slider("Financial Stress (1=None, 5=Severe)", 1, 5, 4)
            conflict = st.slider("Domestic Conflict (1=None, 5=High)", 1, 5, 3)
        with col2:
            prev_dep = st.selectbox("Previous History of Depression", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
            soc_supp = st.slider("Social Support Level (1=Poor, 5=Strong)", 1, 5, 2)
            parity = st.slider("Parity (Number of Children)", 0, 8, 2)
        with col3:
            unplanned = st.selectbox("Unplanned Pregnancy", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
            calc_mh_btn = st.button("🔬 Compute Mental Health SHAP", use_container_width=True, type="primary")

        if calc_mh_btn:
            payload = {
                "sleep_quality": sleep, "financial_stress": fin_stress,
                "domestic_conflict": conflict, "previous_depression": prev_dep,
                "social_support": soc_supp, "parity": parity, "unplanned_pregnancy": unplanned
            }
            with st.spinner("Calculating SHAP TreeExplainer attributions..."):
                result = explain_contextual_risk(payload)

            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                cat = result.get("risk_category", "low")
                prob = result.get("risk_probability", 0.0)

                st.write("---")
                st.markdown(f"**Vulnerability Category:** `{cat.upper()}` (Probability: `{(prob*100):.1f}%`)")

                features = result.get("feature_names", [])
                shap_vals = result.get("shap_values", [])
                if features and shap_vals:
                    df_shap = pd.DataFrame({"Factor": features, "SHAP Attribution": shap_vals})
                    df_shap["Direction"] = df_shap["SHAP Attribution"].apply(lambda x: "Increases Vulnerability (+)" if x > 0 else "Protective (-)")
                    df_shap = df_shap.sort_values(by="SHAP Attribution", key=abs, ascending=True)

                    fig_shap2 = px.bar(
                        df_shap, x="SHAP Attribution", y="Factor", orientation="h",
                        color="Direction",
                        color_discrete_map={"Increases Vulnerability (+)": "#DD6B20", "Protective (-)": "#3182CE"},
                        title="SHAP TreeExplainer Attributions for Contextual Risk"
                    )
                    fig_shap2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#1A202C"), height=320)
                    st.plotly_chart(fig_shap2, use_container_width=True)

                st.info(f"**Actionable Recommendation:** {result.get('actionable_guidance', 'Provide empathetic supportive counseling.')}")

    st.write("---")
    st.info("🔬 **Scientific Transparency Notice:** SHAP values represent statistical attribution within the model's feature space. They do not constitute biological causation or deterministic medical diagnosis.")


# ── Tab: Prioritized Action Plan ──────────────────────────────────────────────
def render_action_plan_tab(role: str, user: str):
    st.markdown("<p class='section-title'>Unified & Prioritized Clinical Action Plan</p>", unsafe_allow_html=True)

    patients_df = load_mh_patients()
    if patients_df.empty:
        st.info("ℹ️ No registered patients found.")
        return

    patient_options = {f"ID #{row['patient_id']} — {row.get('name', 'Anonymous')}": row['patient_id'] for _, row in patients_df.iterrows()}
    sel_label = st.selectbox("Select Patient for Action Plan", list(patient_options.keys()), key="sel_act_patient")
    sel_pid = patient_options[sel_label]
    pat_row = patients_df[patients_df["patient_id"] == sel_pid].iloc[0]

    render_patient_banner(pat_row)

    actions = load_action_recommendations(sel_pid)

    if not actions:
        st.info(f"No specific action recommendations logged for patient #{sel_pid} yet. Actions are automatically generated following physical vitals, mental health screening, or nutrition assessments.")
        return

    # Filter by Priority
    urgency_filter = st.selectbox("Filter by Priority Level:", ["All Priorities", "🚨 Emergency", "⚠️ Urgent", "⏱️ Timely", "📋 Routine", "ℹ️ Informational"])

    filter_map = {
        "🚨 Emergency": "emergency",
        "⚠️ Urgent": "urgent",
        "⏱️ Timely": "timely",
        "📋 Routine": "routine",
        "ℹ️ Informational": "informational"
    }

    filtered_actions = actions
    if urgency_filter != "All Priorities":
        target_tier = filter_map[urgency_filter]
        filtered_actions = [a for a in actions if a.get("priority_tier") == target_tier]

    st.markdown(f"**Showing {len(filtered_actions)} of {len(actions)} total recommendation(s):**")

    for act in filtered_actions:
        tier = act.get("priority_tier", "routine")
        css_class = f"priority-{tier}"
        act_id = act.get("action_id", "")
        status = act.get("status", "pending")

        badge_emoji = {"emergency": "🚨", "urgent": "⚠️", "timely": "⏱️", "routine": "📋", "informational": "ℹ️"}.get(tier, "📌")

        with st.container():
            st.markdown(
                f"""
                <div class='{css_class}'>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="font-size:15px; color:#1A202C;">{badge_emoji} {tier.upper()}: {act.get('action_title')}</b>
                        <span style="font-size:12px; background:#EDF2F7; padding:3px 8px; border-radius:12px; color:#4A5568;">Category: {act.get('category','general').upper()}</span>
                    </div>
                    <p style="margin:6px 0 2px 0; font-size:13px; color:#2D3748;"><b>Rationale:</b> {act.get('rationale')}</p>
                    <p style="margin:2px 0 2px 0; font-size:13px; color:#2B6CB0;"><b>Recommended Action:</b> {act.get('action_text')}</p>
                    <p style="margin:2px 0 0 0; font-size:12px; color:#718096;">Target Time: <b>{act.get('target_timeframe')}</b> &nbsp;|&nbsp; Responsible: <b>{act.get('responsible_actor')}</b> &nbsp;|&nbsp; Status: <b>{status.upper()}</b></p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Interactive status updater
            c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
            if status != "in_progress" and c1.button("⏳ In Progress", key=f"prog_{act_id}"):
                update_action_status(act_id, "in_progress")
                st.rerun()
            if status != "completed" and c2.button("✅ Complete", key=f"comp_{act_id}"):
                update_action_status(act_id, "completed")
                st.rerun()
            if status != "deferred" and c3.button("⏸️ Defer", key=f"def_{act_id}"):
                update_action_status(act_id, "deferred")
                st.rerun()


# ── Tab: Real-World Benchmarks ────────────────────────────────────────────────
def render_benchmarks_tab(role: str, user: str):
    st.markdown("<p class='section-title'>Real-World Comparative Benchmarks (NFHS-5 India)</p>", unsafe_allow_html=True)

    st.markdown("""
    Compare local maternal health cohort indicators with authoritative national and state reference benchmarks
    from the **National Family Health Survey (NFHS-5, 2019–21)**, Ministry of Health and Family Welfare (MoHFW), Government of India.
    """)

    from app.analytics.reference_data import NATIONAL_BENCHMARKS, STATE_BENCHMARKS

    # National Benchmark Metrics
    st.markdown("##### 🇮🇳 National Benchmarks (NFHS-5, 2019-21)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Pregnant Women with Anemia", f"{NATIONAL_BENCHMARKS['anemia_pregnant_women_pct']}%", delta="Hb < 11.0 g/dL", delta_color="inverse")
    with c2:
        st.metric("ANC 4+ Visits Compliance", f"{NATIONAL_BENCHMARKS['anc_4_or_more_visits_pct']}%", delta="Target: >= 70%")
    with c3:
        st.metric("Institutional Births", f"{NATIONAL_BENCHMARKS['institutional_births_pct']}%", delta="MoHFW Target: 100%")
    with c4:
        st.metric("Tetanus / Td Coverage", f"{NATIONAL_BENCHMARKS['tetanus_toxoid_coverage_pct']}%", delta="Target: >= 95%")

    st.write("---")

    # State-by-State Comparison Chart
    st.markdown("##### 🗺️ State-by-State Comparative Analysis")
    state_names = list(STATE_BENCHMARKS.keys())
    sel_state = st.selectbox("Select State to Benchmark Against:", state_names, index=state_names.index("Uttar Pradesh") if "Uttar Pradesh" in state_names else 0)

    state_data = STATE_BENCHMARKS[sel_state]

    indicators = [
        "Anemia in Pregnant Women (%)",
        "At least 4 ANC Visits (%)",
        "Institutional Deliveries (%)",
        "Tetanus/Td Injections (%)"
    ]

    nat_values = [
        NATIONAL_BENCHMARKS["anemia_pregnant_women_pct"],
        NATIONAL_BENCHMARKS["anc_4_or_more_visits_pct"],
        NATIONAL_BENCHMARKS["institutional_births_pct"],
        NATIONAL_BENCHMARKS["tetanus_toxoid_coverage_pct"]
    ]

    state_values = [
        state_data["anemia_pregnant_women_pct"],
        state_data["anc_4_or_more_visits_pct"],
        state_data["institutional_births_pct"],
        state_data["tetanus_toxoid_coverage_pct"]
    ]

    df_compare = pd.DataFrame({
        "Indicator": indicators,
        "Selected State": state_values,
        "National Average": nat_values
    })

    fig_bench = go.Figure()
    fig_bench.add_trace(go.Bar(
        name=sel_state,
        x=df_compare["Indicator"],
        y=df_compare["Selected State"],
        marker_color="#2B6CB0",
        text=df_compare["Selected State"].apply(lambda x: f"{x}%"),
        textposition="auto"
    ))
    fig_bench.add_trace(go.Bar(
        name="National Average (India)",
        x=df_compare["Indicator"],
        y=df_compare["National Average"],
        marker_color="#CBD5E0",
        text=df_compare["National Average"].apply(lambda x: f"{x}%"),
        textposition="auto"
    ))
    fig_bench.update_layout(
        barmode="group",
        title=f"Maternal Indicators: {sel_state} vs National Benchmark",
        yaxis_title="Percentage (%)",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1A202C"), height=360, margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_bench, use_container_width=True)

    # Reference Provenance Metadata
    st.markdown(
        """
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:12px 16px; margin-top:14px; font-size:12px; color:#718096;">
            <b>Reference Provenance:</b> International Institute for Population Sciences (IIPS) and ICF, 2021. <i>National Family Health Survey (NFHS-5), 2019-21: India</i>. Mumbai: IIPS.<br>
            All benchmarks represent officially published district- and state-level survey aggregates.
        </div>
        """,
        unsafe_allow_html=True
    )


# ── Tab: Comprehensive Dossier ────────────────────────────────────────────────
def render_summary_tab(role: str, user: str):
    st.markdown("<p class='section-title'>Comprehensive Maternal Health Dossier</p>", unsafe_allow_html=True)

    patients_df = load_mh_patients()
    if patients_df.empty:
        st.info("ℹ️ No registered patients found.")
        return

    patient_options = {f"ID #{row['patient_id']} — {row.get('name', 'Anonymous')}": row['patient_id'] for _, row in patients_df.iterrows()}
    sel_label = st.selectbox("Select Patient for Comprehensive Dossier", list(patient_options.keys()), key="sel_dos_patient")
    sel_pid = patient_options[sel_label]
    pat_row = patients_df[patients_df["patient_id"] == sel_pid].iloc[0]

    render_patient_banner(pat_row)

    summary = load_comprehensive_summary(sel_pid)

    if not summary:
        st.warning(f"Could not load comprehensive summary for patient #{sel_pid}.")
        return

    overall_status = summary.get("overall_health_status") or summary.get("overall_status", "LOW_RISK")
    status_rationale = summary.get("overall_status_explanation") or summary.get("status_rationale", "Assessed across all domains.")
    badge_colors = {
        "CRITICAL_ALERT": ("#C53030", "#FFF5F5", "🚨 CRITICAL ALERT — IMMEDIATE CLINICAL ACTION REQUIRED"),
        "HIGH_VULNERABILITY": ("#DD6B20", "#FFFAF0", "⚠️ HIGH VULNERABILITY — URGENT MULTI-DOMAIN FOLLOW-UP"),
        "MODERATE_CONCERN": ("#3182CE", "#EBF8FF", "⏱️ MODERATE CONCERN — TARGETED INTERVENTION NEEDED"),
        "LOW_RISK": ("#276749", "#F0FFF4", "✅ LOW RISK — ROUTINE ANTENATAL CARE")
    }
    b_color, b_bg, b_text = badge_colors.get(overall_status, ("#4A5568", "#F7FAFC", "STATUS UNCERTAIN"))

    # Overall Status Banner
    st.markdown(
        f"""
        <div style="background:{b_bg}; border:2px solid {b_color}; border-radius:12px; padding:18px; margin-bottom:16px;">
            <h3 style="margin:0; color:{b_color};">{b_text}</h3>
            <p style="margin:8px 0 0 0; font-size:14px; color:#2D3748;">
                <b>Deterministic Synthesis Rationale:</b> {status_rationale}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Red Flags Checklist
    red_flags = summary.get("red_flags", [])
    if red_flags:
        st.markdown("##### 🚨 Active Red Flags")
        for rf in red_flags:
            st.markdown(
                f"""
                <div style="background:#FFF5F5; border-left:4px solid #E53E3E; border-radius:6px; padding:8px 14px; margin-bottom:6px; font-size:13px; color:#9B2C2C;">
                    <b>• {rf}</b>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.write("---")

    # Domain Overviews 4-Column Grid
    st.markdown("##### 📋 Domain Health Synthesis")
    d1, d2, d3, d4 = st.columns(4)

    phys = summary.get("physical_health") or {}
    mh = summary.get("mental_health") or {}
    nutr = summary.get("nutrition") or {}
    immu = summary.get("immunization") or {}

    with d1:
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #CBD5E0; border-radius:10px; padding:14px; min-height:220px;">
                <h5 style="margin:0 0 8px 0; color:#2B6CB0;">🩺 Physical Health</h5>
                <p style="margin:0; font-size:13px; color:#2D3748;">
                    <b>Risk:</b> {phys.get('risk_level', 'Unassessed').upper()}<br>
                    <b>BP:</b> {phys.get('latest_systolic_bp', 'N/A')}/{phys.get('latest_diastolic_bp', 'N/A')} mmHg<br>
                    <b>Blood Sugar:</b> {phys.get('latest_blood_sugar', 'N/A')} mmol/L<br>
                    <b>BMI:</b> {phys.get('latest_bmi', 'N/A')} kg/m²<br>
                    <b>Heart Rate:</b> {phys.get('latest_heart_rate', 'N/A')} bpm<br>
                    <b>Total Vitals Logged:</b> {phys.get('num_vitals_logged', 0)}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with d2:
        suicidal = mh.get("urgent_safety_flag") == 1
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #CBD5E0; border-radius:10px; padding:14px; min-height:220px;">
                <h5 style="margin:0 0 8px 0; color:#2B6CB0;">🧠 Mental Health</h5>
                <p style="margin:0; font-size:13px; color:#2D3748;">
                    <b>PHQ-9 Score:</b> {mh.get('latest_phq9_score', 'N/A')}/27<br>
                    <b>Severity:</b> {mh.get('latest_severity', 'N/A').title()}<br>
                    <b>Screening Status:</b> {'Positive' if mh.get('at_risk') else 'Negative'}<br>
                    <b>Safety Flag:</b> {'🚨 POSITIVE (Item 9)' if suicidal else 'Negative'}<br>
                    <b>Trajectory Trend:</b> {mh.get('trend', 'N/A').title()}<br>
                    <b>Total Screenings:</b> {mh.get('num_screenings', 0)}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with d3:
        gaps_list = nutr.get("nutrient_gaps", [])
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #CBD5E0; border-radius:10px; padding:14px; min-height:220px;">
                <h5 style="margin:0 0 8px 0; color:#2B6CB0;">🥗 Nutrition</h5>
                <p style="margin:0; font-size:13px; color:#2D3748;">
                    <b>BMI Category:</b> {nutr.get('bmi_category', 'N/A')}<br>
                    <b>Gestational Gain:</b> {f"+{nutr.get('gestational_weight_gain_kg'):.1f} kg" if nutr.get('gestational_weight_gain_kg') is not None else 'N/A'}<br>
                    <b>Target Gain:</b> {nutr.get('recommended_gain_range', '11.5-16 kg')}<br>
                    <b>Key Gaps:</b> {', '.join(gaps_list) if gaps_list else 'None detected'}<br>
                    <b>Supplements:</b> {', '.join(nutr.get('supplements_taken', [])) or 'None reported'}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with d4:
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #CBD5E0; border-radius:10px; padding:14px; min-height:220px;">
                <h5 style="margin:0 0 8px 0; color:#2B6CB0;">💉 Immunization</h5>
                <p style="margin:0; font-size:13px; color:#2D3748;">
                    <b>Status:</b> {immu.get('status', 'Unassessed').replace('_', ' ').title()}<br>
                    <b>Doses Received:</b> {len(immu.get('doses_administered', []))}<br>
                    <b>Next Dose:</b> {immu.get('next_recommended_dose', 'None')}<br>
                    <b>Due Date:</b> {immu.get('next_dose_due_date', 'Complete')}<br>
                    <b>Overdue:</b> {'🚨 Yes' if immu.get('is_overdue') else '✅ No'}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Top Actions Checklist
    raw_actions = summary.get("action_plan") or summary.get("top_actions") or []
    if isinstance(raw_actions, dict):
        top_actions = raw_actions.get("recommendations", [])
    elif isinstance(raw_actions, list):
        top_actions = raw_actions
    else:
        top_actions = []

    if top_actions:
        st.write("---")
        st.markdown("##### 📌 High-Priority Action Items")
        for a in top_actions:
            st.markdown(f"• **[{a.get('priority_tier','').upper()}]** {a.get('action_title')}: {a.get('action_text')} *(Target: {a.get('target_timeframe')})*")

    # Export Dossier
    st.write("---")
    report_text = f"""SANRAKSHA MATERNAL HEALTH INTELLIGENCE DOSSIER
==============================================
Patient ID: {sel_pid}
Patient Name: {pat_row.get('name', 'Anonymous')}
Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Overall Status: {overall_status}
Synthesis Rationale: {summary.get('status_rationale', '')}

[PHYSICAL HEALTH]
- Risk Level: {phys.get('risk_level', 'N/A')}
- Vitals: BP {phys.get('latest_systolic_bp', 'N/A')}/{phys.get('latest_diastolic_bp', 'N/A')}, BS {phys.get('latest_blood_sugar', 'N/A')}, BMI {phys.get('latest_bmi', 'N/A')}

[MENTAL HEALTH]
- PHQ-9 Score: {mh.get('latest_phq9_score', 'N/A')}/27 ({mh.get('latest_severity', 'N/A')})
- Urgent Safety Flag: {mh.get('urgent_safety_flag', 0)}

[NUTRITION]
- BMI Category: {nutr.get('bmi_category', 'N/A')}
- Gestational Weight Gain: {nutr.get('gestational_weight_gain_kg', 'N/A')} kg
- Nutritional Gaps: {', '.join(nutr.get('nutrient_gaps', []))}

[IMMUNIZATION]
- Status: {immu.get('status', 'N/A')}
- Next Dose: {immu.get('next_recommended_dose', 'N/A')}
"""
    st.download_button(
        label="📥 Download Clinical Health Dossier (.txt)",
        data=report_text,
        file_name=f"sanraksha_dossier_patient_{sel_pid}.txt",
        mime="text/plain"
    )


# ── Login Screen ──────────────────────────────────────────────────────────────
def login_screen():
    st.markdown(
        """
        <div style='display:flex;flex-direction:column;align-items:center;margin-top:50px;'>
            <img src='https://raw.githubusercontent.com/sys6-exe/SanRaksha/main/assets/Sanraksha.png'
                 style='width:80px;border-radius:50%;margin-bottom:14px;'/>
            <h2 style='color:#1A202C;margin-bottom:4px;'>SanRaksha PHC Dashboard</h2>
            <p style='color:#718096;'>Sign in with PIN to continue</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col = st.columns([1, 2, 1])[1]
    with col:
        username = st.text_input("Username (e.g. doctor1, asha_riya)").strip()
        pin      = st.text_input("PIN (e.g. 1234, 5678)", type="password").strip()
        if st.button("Sign In", use_container_width=True):
            if username in USERS and USERS[username][0] == pin:
                st.session_state["user"]   = username
                st.session_state["role"]   = USERS[username][1]
                st.session_state["logged"] = True
                st.rerun()
            else:
                st.error("Invalid username or PIN.")


# ── Main Application ──────────────────────────────────────────────────────────
def main():
    load_css()

    if not st.session_state.get("logged"):
        login_screen()
        return

    user = st.session_state["user"]
    role = st.session_state["role"]

    captured_df = load_captured_data(CAPTURED_PATH)
    df = transform_captured_data(captured_df)

    if role == "asha" and not df.empty and "asha_id" in df.columns:
        df = df[df["asha_id"] == user]

    # Sidebar
    with st.sidebar:
        st.markdown(f"**Logged in as:** `{user}` ({role.upper()})")
        if st.button("Sign out"):
            st.session_state.clear()
            st.rerun()

        st.write("---")
        st.header("PHC Details")
        st.info(f"**Date:** {datetime.now().strftime('%d %B %Y')}")
        st.info(f"**Time:** {datetime.now().strftime('%I:%M %p')}")
        st.info("**Jurisdiction:** Primary Health Centre (PHC) Block A")
        st.write("---")

        st.header("Actions")
        with st.expander("⚠️ Report or Feedback"):
            with st.form("complaint_form", clear_on_submit=True):
                name  = st.text_input("Name (Optional)")
                issue = st.text_area("Describe your issue or feedback")
                submitted = st.form_submit_button("Submit Feedback")
                if submitted and issue.strip():
                    post_feedback(name, issue)
                    st.success("Thank you! Feedback recorded.")

    # Top Brand Header
    st.markdown(
        """
        <div class="top-container">
            <img class="logo"
                 src="https://raw.githubusercontent.com/sys6-exe/SanRaksha/main/assets/Sanraksha.png"/>
            <div class="title-text"><h1>SanRaksha PHC Dashboard</h1></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Tabs Configuration ────────────────────────────────────────────────────
    tab_titles = [
        "📍 Overview",
        "🧠 Mental Health",
        "🥗 Diet & Nutrition",
        "💉 Immunization Tracker",
        "🔍 AI Explainability (SHAP)",
        "📋 Prioritized Action Plan",
        "📊 Real-World Benchmarks",
        "📄 Comprehensive Dossier",
        "📈 Risk Trends",
        "🗺️ State Analysis"
    ]
    if role == "doctor":
        tab_titles.append("🔔 Pending Alerts")

    tab_objects = st.tabs(tab_titles)

    # ── Tab 0: Overview ───────────────────────────────────────────────────────
    with tab_objects[0]:
        st.markdown("<p class='section-title'>Real-time Health Summary</p>", unsafe_allow_html=True)

        if df.empty:
            st.warning("📊 No physical vitals submissions captured yet from the mobile app.")
            st.info("Submit vitals from the Android app or see the '🧠 Mental Health' tab for registered patient records.")
        else:
            high_count    = (df["risk_level"] == "high").sum()
            low_count     = (df["risk_level"] == "low").sum()
            total_checkups = len(df)

            col1, col2, col3 = st.columns(3, gap="large")
            col1.metric("High Risk Cases",  f"🚨 {high_count}")
            col2.metric("Low Risk Cases",   f"✅ {low_count}")
            col3.metric("Total Checkups",   f"📋 {total_checkups}")

            st.write("---")
            st.markdown("<p class='section-title'>Geospatial & Risk Distribution</p>", unsafe_allow_html=True)

            c1, c2 = st.columns([2, 3], gap="large")
            with c1:
                risk_counts = df["risk_level"].value_counts().reset_index()
                fig_pie = px.pie(
                    risk_counts, values="count", names="risk_level",
                    title="Risk Level Distribution", hole=0.5,
                    color_discrete_map={"high": "#FF4B4B", "low": "#28a745"},
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#1A202C",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with c2:
                m = folium.Map(location=[22.9734, 78.6569], zoom_start=4.5, tiles="CartoDB positron")
                for _, row in df.iterrows():
                    color = "red" if row["risk_level"] == "high" else "green"
                    folium.Marker(
                        location=[row["latitude"], row["longitude"]],
                        popup=f"<b>{row['state']}</b><br>Risk: {row['risk_level'].capitalize()}",
                        icon=folium.Icon(color=color, icon="heart", prefix="fa"),
                    ).add_to(m)
                folium_static(m, width=None, height=420)

            st.write("---")
            st.markdown("<p class='section-title'>Captured App Submissions</p>", unsafe_allow_html=True)
            display_cols = [
                col for col in [
                    "captured_at", "Age", "Systolic_BP", "Diastolic", "BS", "Body_Temp",
                    "BMI", "Previous_Complications", "Preexisting_Diabetes",
                    "Gestational_Diabetes", "Mental_Health", "Heart_Rate",
                    "prediction", "prediction_label", "source"
                ] if col in captured_df.columns
            ]
            preview_df = captured_df[display_cols].copy() if display_cols else captured_df.copy()
            if "captured_at" in preview_df.columns:
                preview_df = preview_df.sort_values("captured_at", ascending=False)
            st.dataframe(preview_df.head(20), use_container_width=True)

    # ── Tab 1: Mental Health ──────────────────────────────────────────────────
    with tab_objects[1]:
        render_mental_health_tab(role, user)

    # ── Tab 2: Diet & Nutrition ───────────────────────────────────────────────
    with tab_objects[2]:
        render_nutrition_tab(role, user)

    # ── Tab 3: Immunization Tracker ───────────────────────────────────────────
    with tab_objects[3]:
        render_immunization_tab(role, user)

    # ── Tab 4: AI Explainability (SHAP) ───────────────────────────────────────
    with tab_objects[4]:
        render_explainability_tab(role, user)

    # ── Tab 5: Prioritized Action Plan ────────────────────────────────────────
    with tab_objects[5]:
        render_action_plan_tab(role, user)

    # ── Tab 6: Real-World Benchmarks ──────────────────────────────────────────
    with tab_objects[6]:
        render_benchmarks_tab(role, user)

    # ── Tab 7: Comprehensive Dossier ──────────────────────────────────────────
    with tab_objects[7]:
        render_summary_tab(role, user)

    # ── Tab 8: Risk Trends ────────────────────────────────────────────────────
    with tab_objects[8]:
        if not df.empty:
            states = df["state"].dropna().unique().tolist()
            sel = st.selectbox("Filter by state", ["All States"] + sorted(states), key="trend_state")
            render_trend(df, sel)
        else:
            st.info("Trend analysis will appear once multiple submissions are recorded.")

    # ── Tab 9: State Analysis ─────────────────────────────────────────────────
    with tab_objects[9]:
        st.markdown("<p class='section-title'>State-wise Health Analytics</p>", unsafe_allow_html=True)
        if not df.empty:
            states = df["state"].dropna().unique().tolist()
            selected_state = st.selectbox("Select a State to Analyse", ["All States"] + sorted(states), label_visibility="collapsed")
            filtered_df = df if selected_state == "All States" else df[df["state"] == selected_state]

            if not filtered_df.empty:
                risk_counts = filtered_df.groupby(["state", "risk_level"]).size().unstack(fill_value=0)
                stats = filtered_df.groupby("state").agg(
                    systolic_bp_mean=("systolic_bp", "mean"),
                    diastolic_bp_mean=("diastolic_bp", "mean"),
                    blood_sugar_min=("blood_sugar", "min"),
                    blood_sugar_max=("blood_sugar", "max"),
                    bmi_min=("bmi", "min"),
                    bmi_max=("bmi", "max"),
                ).round(1)

                summary = pd.merge(risk_counts, stats, on="state", how="left")
                if "high" not in summary: summary["high"] = 0
                if "low"  not in summary: summary["low"]  = 0
                summary["Total Cases"] = summary["high"] + summary["low"]
                summary = summary.reset_index()
                summary["Avg BP (Sys/Dia)"]    = summary["systolic_bp_mean"].astype(str) + "/" + summary["diastolic_bp_mean"].astype(str)
                summary["Sugar Range (mg/dL)"] = summary["blood_sugar_min"].astype(str) + " – " + summary["blood_sugar_max"].astype(str)
                summary["BMI Range"]           = summary["bmi_min"].astype(str) + " – " + summary["bmi_max"].astype(str)

                final_cols = ["state", "high", "low", "Total Cases", "Avg BP (Sys/Dia)", "Sugar Range (mg/dL)", "BMI Range"]
                st.dataframe(summary[final_cols], use_container_width=True)

                st.markdown("##### Risk Levels Breakdown")
                chart_data = summary.set_index("state")[["high", "low"]]
                st.bar_chart(chart_data, color=["#FF4B4B", "#28a745"])
            else:
                st.warning("No data available for the selected state.")
        else:
            st.info("State-wise analytics will populate once vitals are submitted.")

    # ── Tab 10: Pending Alerts (Doctors only) ──────────────────────────────────
    if role == "doctor":
        with tab_objects[10]:
            if not df.empty:
                render_referral_panel(df)
            else:
                st.info("No physical risk alerts pending.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
