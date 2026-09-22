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
  • 🧠 Maternal Mental Health & Longitudinal Monitoring Tab:
    - Interactive patient selector with pregnancy & postpartum tracking
    - Real-time PHQ-9 score, severity, and urgent suicidal ideation safety alerts
    - Contextual ML vulnerability estimation and contributing factors
    - Longitudinal trajectory Plotly charts (PHQ-9 progression, risk probability, vitals)
    - Append-only chronological visit timeline
    - Transparent scientific model limitation notes
"""

import os
import sqlite3
from pathlib import Path
import requests
import pandas as pd
import streamlit as st
import folium
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import folium_static
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
API_BASE = os.environ.get("SANRAKSHA_API", "http://localhost:8000")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

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
        .block-container { padding-top: 2rem; }
        .stApp { background: linear-gradient(135deg, #F7FAFC, #EDF2F7); color: #1A202C; }
        .top-container { display: flex; align-items: center; margin-bottom: 2rem; }
        .logo { width: 75px; height: 75px; border-radius: 50%; margin-right: 20px; }
        .title-text h1 { font-size: 2.8rem; font-weight: bold; color: #1A202C;
                         margin: 0; padding: 0; line-height: 1.1; }
        [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
        [data-testid="stMetric"] { background-color: #FFFFFF;
                                   border: 1px solid #E2E8F0;
                                   border-radius: 14px; padding: 20px; }
        [data-testid="stMetric"] > label { color: #2B6CB0; }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #1A202C; background-color: rgba(43,108,176,0.12);
            border-bottom: 3px solid #2B6CB0; }
        .section-title { font-size: 22px; font-weight: 600; color: #1A202C;
                         margin-bottom: 18px; border-left: 5px solid #2B6CB0;
                         padding-left: 12px; }
        .ack-card { background: #FFFFFF; border-radius: 10px;
                    padding: 14px 18px; margin-bottom: 10px;
                    border-left: 4px solid #E53E3E;
                    border: 1px solid #E2E8F0; }
        .ack-card.reviewed  { border-left-color: #2B6CB0; }
        .ack-card.referred  { border-left-color: #38A169; }
        .ack-card.dismissed { border-left-color: #718096; }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span,
        [data-testid="stText"] { color: #1A202C; }
    </style>
    """, unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
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


# ── Mental Health Data Access (API with SQLite Fallback) ──────────────────────

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


# ── Mental Health & Longitudinal Tab ──────────────────────────────────────────
def render_mental_health_tab(role: str, user: str):
    st.markdown("<p class='section-title'>Maternal Mental Health & Longitudinal Trajectory</p>", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([4, 1])
    with col_t2:
        if st.button("🔄 Refresh Data", key="refresh_mh"):
            st.cache_data.clear()
            st.rerun()

    patients_df = load_mh_patients()
    if patients_df.empty:
        st.info("ℹ️ No patients registered in the mental health database yet. Register patients and submit PHQ-9 screenings via the Android App or FastAPI backend.")
        return

    # Patient Selector
    patient_options = {}
    for _, row in patients_df.iterrows():
        p_id = row["patient_id"]
        name = row.get("name") or "Anonymous"
        status = str(row.get("pregnancy_status", "pregnant")).capitalize()
        label = f"ID #{p_id} — {name} ({status})"
        patient_options[label] = p_id

    sel_label = st.selectbox("Select Patient to Monitor", list(patient_options.keys()), key="sel_mh_patient")
    sel_pid = patient_options[sel_label]

    # Selected patient header banner
    pat_row = patients_df[patients_df["patient_id"] == sel_pid].iloc[0]
    p_name = pat_row.get("name") or "Anonymous"
    p_status = str(pat_row.get("pregnancy_status", "pregnant"))
    p_state = pat_row.get("state") or "Unspecified"
    p_delivery = pat_row.get("delivery_date")

    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #CBD5E0; border-radius:12px; padding:16px 20px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:#1A202C;">{p_name} <span style="font-size:14px; color:#718096; font-weight:normal;">(Patient ID: #{sel_pid})</span></h3>
                    <p style="margin:4px 0 0 0; color:#4A5568; font-size:14px;">State: <b>{p_state}</b> &nbsp;|&nbsp; Status: <b>{p_status.upper()}</b> {f'&nbsp;|&nbsp; Delivery Date: <b>{p_delivery}</b>' if p_delivery else ''}</p>
                </div>
                <div style="background:{'#FED7D7' if p_status == 'postpartum' else '#C6F6D5'}; padding:6px 14px; border-radius:20px; font-weight:bold; color:{'#C53030' if p_status == 'postpartum' else '#22543D'};">
                    {'Postpartum Tracking' if p_status == 'postpartum' else 'Prenatal Monitoring'}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    history_df = load_mh_history(sel_pid)
    if history_df.empty:
        st.warning(f"No visit records logged for patient #{sel_pid} yet.")
        return

    latest = history_df.iloc[-1]
    is_urgent = (latest.get("urgent_safety_flag") == 1)

    # Urgent Safety Alert Banner
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

    # Metric Cards Row
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

    # Longitudinal Visualizations
    st.markdown("##### 📈 Longitudinal Trajectory Analysis")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig_phq = go.Figure()
        fig_phq.add_hline(
            y=10, line_dash="dash", line_color="orange",
            annotation_text="Cutoff (>=10: At Risk)", annotation_position="top left"
        )
        visit_labels = [f"V{i+1}: {d.strftime('%d %b') if pd.notna(d) else ''}" for i, d in enumerate(history_df["visit_date"])]

        dot_colors = ["#E53E3E" if u == 1 else "#3182CE" for u in history_df["urgent_safety_flag"]]
        fig_phq.add_trace(go.Scatter(
            x=visit_labels,
            y=history_df["total_score"],
            mode="lines+markers",
            name="PHQ-9 Score",
            line=dict(color="#3182CE", width=3),
            marker=dict(size=10, color=dot_colors),
            hovertemplate="<b>%{x}</b><br>Score: %{y}/27<extra></extra>"
        ))
        fig_phq.update_layout(
            title="PHQ-9 Score Trajectory Over Visits (Red Marker = Urgent Safety Flag)",
            xaxis_title="Visit Sequence",
            yaxis_title="PHQ-9 Total Score (0-27)",
            yaxis=dict(range=[0, 27]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#1A202C"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=320
        )
        st.plotly_chart(fig_phq, use_container_width=True)

    with col_chart2:
        if "risk_probability" in history_df.columns and history_df["risk_probability"].notna().any():
            fig_risk = go.Figure()
            prob_pct = history_df["risk_probability"] * 100
            fig_risk.add_trace(go.Scatter(
                x=visit_labels,
                y=prob_pct,
                mode="lines+markers",
                name="Contextual Risk %",
                line=dict(color="#DD6B20", width=3),
                marker=dict(size=9, color="#DD6B20"),
                hovertemplate="<b>%{x}</b><br>Risk: %{y:.1f}%<extra></extra>"
            ))
            fig_risk.update_layout(
                title="Contextual ML Risk Probability Trajectory",
                xaxis_title="Visit Sequence",
                yaxis_title="Estimated Risk Probability (%)",
                yaxis=dict(range=[0, 100]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1A202C"),
                margin=dict(l=20, r=20, t=40, b=20),
                height=320
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.info("Contextual ML assessments not available for all visits.")

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
            xaxis_title="Visit Sequence",
            yaxis_title="Value",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#1A202C"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=280
        )
        st.plotly_chart(fig_vitals, use_container_width=True)

    # Chronological Visit Table
    st.write("---")
    st.markdown("##### 📋 Complete Chronological Visit History (Append-Only)")
    display_history = history_df.copy()
    if "visit_date" in display_history.columns:
        display_history["visit_date"] = display_history["visit_date"].dt.strftime("%Y-%m-%d")

    table_cols = [c for c in [
        "visit_id", "visit_date", "trimester", "gestational_age", "total_score", "severity",
        "risk_category", "risk_probability", "trend", "score_change", "urgent_safety_flag",
        "systolic_bp", "diastolic_bp", "heart_rate"
    ] if c in display_history.columns]
    st.dataframe(display_history[table_cols], use_container_width=True)

    # Scientific Transparency Callout
    st.info("🔬 **Scientific Model Disclaimer:** Validated prospective postpartum prediction is not claimed as models are derived from cross-sectional data (PERI_DEP Pakistan & Dataset_1 Bangladesh). The system provides deterministic PHQ-9 screening, socio-demographic risk estimation, and longitudinal trajectory monitoring.")


# ── Login Screen ──────────────────────────────────────────────────────────────
def login_screen():
    st.markdown(
        """
        <div style='display:flex;flex-direction:column;align-items:center;margin-top:60px;'>
            <img src='https://raw.githubusercontent.com/sys6-exe/SanRaksha/main/assets/Sanraksha.png'
                 style='width:80px;border-radius:50%;margin-bottom:16px;'/>
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


# ── Main app ──────────────────────────────────────────────────────────────────
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
        st.markdown(f"**Logged in as:** `{user}` ({role})")
        if st.button("Sign out"):
            st.session_state.clear()
            st.rerun()

        st.write("---")
        st.header("Information")
        st.info(f"**Date:** {datetime.now().strftime('%d %B %Y')}")
        st.info(f"**Time:** {datetime.now().strftime('%I:%M %p')}")
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

    # Header
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
    tabs = ["📍 Overview", "📊 State Analysis", "📈 Trends", "🧠 Mental Health & Longitudinal"]
    if role == "doctor":
        tabs.append("🔔 Pending Alerts")
    tab_objects = st.tabs(tabs)

    # ── Tab 1: Overview ───────────────────────────────────────────────────────
    with tab_objects[0]:
        st.markdown("<p class='section-title'>Real-time Health Summary</p>", unsafe_allow_html=True)

        if df.empty:
            st.warning("📊 No physical vitals submissions captured yet from the mobile app.")
            st.info("Submit vitals from the Android app or see the '🧠 Mental Health & Longitudinal' tab for mental health records.")
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
                folium_static(m, width=None, height=450)

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

    # ── Tab 2: State analysis ─────────────────────────────────────────────────
    with tab_objects[1]:
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

    # ── Tab 3: Trends ─────────────────────────────────────────────────────────
    with tab_objects[2]:
        if not df.empty:
            states = df["state"].dropna().unique().tolist()
            sel = st.selectbox("Filter by state", ["All States"] + sorted(states), key="trend_state")
            render_trend(df, sel)
        else:
            st.info("Trend analysis will appear once multiple submissions are recorded.")

    # ── Tab 4: Mental Health & Longitudinal Monitoring ────────────────────────
    with tab_objects[3]:
        render_mental_health_tab(role, user)

    # ── Tab 5: Pending Alerts (Doctors only) ───────────────────────────────────
    if role == "doctor":
        with tab_objects[4]:
            if not df.empty:
                render_referral_panel(df)
            else:
                st.info("No physical risk alerts pending.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
