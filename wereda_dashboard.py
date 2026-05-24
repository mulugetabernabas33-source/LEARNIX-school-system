"""
Wereda School Performance Dashboard
Displays grade-level performance analytics with full KPI suite for all schools.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from helpers.wereda_data import (
    WEREDA_SCHOOLS, get_subjects_for_grade, get_wereda_grade_data,
    get_grade_configs, get_all_wereda_schools_overall_avg,
    get_wereda_overall_subject_analysis, get_wereda_kpis, get_school_kpis,
)
from helpers.analytics import (
    get_class_avg_per_subject, get_strongest_weakest,
    get_top_n_students, get_prediction_trend,
    get_class_overall_avg, get_student_count,
    get_pass_rate, get_fail_rate, get_distinction_rate,
    get_at_risk_students, get_top_performer_index,
    get_performance_variance, get_engagement_level, get_term_improvement,
)
from helpers.charts import subject_avg_bar_chart, performance_trend_chart
from helpers.ui_components import inject_school_card_css, render_clickable_school_card

try:
    st.set_page_config(
        page_title="Wereda Dashboard", page_icon="Wereda",
        layout="wide", initial_sidebar_state="collapsed",
    )
except st.errors.StreamlitAPIException:
    pass


# css

def inject_wereda_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        * { font-family: 'Inter', sans-serif; }
        html, body { background: #ffffff !important; color: #334155; }
        .stApp { background: #ffffff !important; }
        #MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
        .main .block-container { max-width:1400px; padding:2rem 3rem; background:transparent !important; }

        .page-title    { font-size:clamp(32px,4vw,42px); font-weight:900; color:#0f172a; margin-bottom:10px; letter-spacing:-0.04em; line-height:1.02; }
        .page-subtitle { font-size:16px; color:#64748b; margin-bottom:32px; line-height:1.75; }
        .section-title { font-size:26px; font-weight:800; color:#0f172a; margin:32px 0 16px; letter-spacing:-0.03em; }
        .back-button-area { margin-bottom:18px; }

        .track-label { display:inline-flex; align-items:center; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:0.12em; padding:7px 12px; border-radius:999px; margin-bottom:12px; }
        .track-label.natural { background:rgba(12,74,110,0.10); color:#0c4a6e; border:1px solid rgba(56,189,248,0.22); }
        .track-label.social  { background:rgba(139,92,246,0.10);  color:#7c3aed; border:1px solid rgba(139,92,246,0.22); }

        .stat-cards { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:18px; margin-bottom:26px; }
        .stat-card { background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.78); border-radius:22px; padding:22px 22px 18px; box-shadow:0 18px 40px rgba(15,23,42,0.09); min-height:148px; }
        .stat-card .stat-label { color:#0f4c81; font-size:13px; font-weight:800; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px; }
        .stat-card .stat-value { display:block; color:#0f172a; font-size:31px; line-height:1.08; margin:10px 0 12px; font-weight:900; letter-spacing:-0.04em; }
        .stat-card .stat-note  { color:#64748b; font-size:15px; line-height:1.6; margin-top:4px; }

        .kpi-bar-bg   { background:#e2e8f0; border-radius:4px; height:7px; width:100%; margin-top:8px; }
        .kpi-bar-fill { height:7px; border-radius:4px; }

        .kpi-summary-box { background:linear-gradient(135deg,#0f172a 0%,#0f4c81 100%); border-radius:22px; padding:26px 30px; margin-bottom:28px; box-shadow:0 22px 48px rgba(15,23,42,0.16); }
        .kpi-summary-title { color:#f8fafc; font-size:20px; font-weight:900; letter-spacing:-0.03em; margin-bottom:4px; }
        .kpi-summary-sub   { color:rgba(226,232,240,0.75); font-size:13px; margin-bottom:18px; }
        .kpi-inner-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
        .kpi-inner-card { background:rgba(255,255,255,0.10); border:1px solid rgba(255,255,255,0.14); border-radius:14px; padding:14px 16px; }
        .kpi-inner-label { color:#93c5fd; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:5px; }
        .kpi-inner-value { color:#ffffff; font-size:24px; font-weight:900; letter-spacing:-0.03em; }
        .kpi-inner-note  { color:rgba(226,232,240,0.7); font-size:11px; margin-top:3px; }

        .focus-chip { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; background:rgba(239,68,68,0.12); color:#dc2626; border:1px solid rgba(239,68,68,0.25); margin:3px 4px 3px 0; }
        .attention-chip { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; background:rgba(234,88,12,0.10); color:#ea580c; border:1px solid rgba(234,88,12,0.22); margin:3px 4px 3px 0; }

        .top-student-card { background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.78); border-radius:22px; padding:22px 24px; box-shadow:0 18px 40px rgba(15,23,42,0.09); margin-bottom:18px; border-left:5px solid #0f4c81; }
        .top-student-card.rank-1 { border-left-color:#D4AF37; background:linear-gradient(180deg,#fffbeb,#fffdf5); }
        .top-student-card.rank-2 { border-left-color:#A8A9AD; background:linear-gradient(180deg,#f8fafc,#ffffff); }
        .top-student-card.rank-3 { border-left-color:#CD7F32; background:linear-gradient(180deg,#fff7ed,#fffbf5); }
        .student-name  { font-size:18px; font-weight:800; color:#0f172a; letter-spacing:-0.02em; }
        .student-avg   { font-size:15px; font-weight:700; color:#0f4c81; }

        .badge { display:inline-flex; align-items:center; padding:6px 14px; border-radius:999px; font-size:13px; font-weight:800; letter-spacing:0.05em; }
        .badge-gold   { background:linear-gradient(180deg,#fef3c7,#fef9e7); color:#b45309; border:1px solid rgba(212,175,55,0.3); }
        .badge-silver { background:linear-gradient(180deg,#f1f5f9,#f8fafc); color:#475569; border:1px solid rgba(168,169,173,0.3); }
        .badge-bronze { background:linear-gradient(180deg,#fed7aa,#fff7ed); color:#9a3412; border:1px solid rgba(205,127,50,0.3); }

        .prediction-box { background:linear-gradient(180deg,#f0f9ff,#f8fbff); border:1px solid rgba(56,189,248,0.22); border-radius:22px; padding:22px 26px; box-shadow:0 18px 40px rgba(15,23,42,0.09); border-left:5px solid #0f4c81; margin:18px 0 32px; }
        .prediction-title { font-size:18px; font-weight:800; color:#0f172a; margin-bottom:10px; letter-spacing:-0.02em; }
        .prediction-text  { font-size:15px; color:#334155; line-height:1.65; }

        .subject-marks-table { width:100%; border-collapse:collapse; font-size:14px; margin-top:14px; }
        .subject-marks-table th, .subject-marks-table td { padding:10px 12px; text-align:left; border-bottom:1px solid rgba(203,213,225,0.65); }
        .subject-marks-table th { background:rgba(248,250,252,0.95); font-weight:700; color:#475569; font-size:13px; }
        .subject-marks-table td { color:#334155; line-height:1.45; }

        .chart-container { background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.75); border-radius:22px; padding:20px; box-shadow:0 20px 42px rgba(15,23,42,0.09); margin-bottom:26px; }

        .stButton > button { width:100%; background:#ffffff !important; border:1px solid #e2e8f0 !important; border-radius:10px !important; padding:14px 20px !important; font-size:15px !important; font-weight:600 !important; color:#334155 !important; transition:all 0.2s ease !important; box-shadow:0 1px 2px rgba(0,0,0,0.05) !important; }
        .stButton > button:hover { background:#f8fafc !important; border-color:#94a3b8 !important; color:#0f4c81 !important; transform:translateY(-1px) !important; }

        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] { background:rgba(255,255,255,0.94) !important; border:1px solid rgba(203,213,225,0.75) !important; border-radius:22px !important; box-shadow:0 20px 42px rgba(15,23,42,0.09) !important; padding:18px 20px !important; }
        @media (max-width:1100px) { .stat-cards, .kpi-inner-grid { grid-template-columns:1fr 1fr !important; } }
        @media (max-width:768px)  { .stat-cards, .kpi-inner-grid { grid-template-columns:1fr !important; } }
    </style>
    """, unsafe_allow_html=True)


# navigation

def navigate_to(page):
    st.session_state.wereda_page = page
    st.rerun()


def navigate_to_school(school_name):
    st.session_state.wereda_page = "school"
    st.session_state.wereda_school = school_name
    st.rerun()


def navigate_to_grade(school_name, grade, track):
    st.session_state.wereda_page = "grade_detail"
    st.session_state.wereda_school = school_name
    st.session_state.wereda_grade = grade
    st.session_state.wereda_track = track
    st.rerun()


if "wereda_page" not in st.session_state:
    st.session_state.wereda_page = "home"


# helpers

def _bar(color, pct):
    w = min(max(pct, 0), 100)
    return f'<div class="kpi-bar-bg"><div class="kpi-bar-fill" style="background:{color};width:{w}%;"></div></div>'


def _pass_color(v):
    if v >= 80: return "linear-gradient(90deg,#16a34a,#22c55e)"
    if v >= 60: return "linear-gradient(90deg,#ca8a04,#facc15)"
    return "linear-gradient(90deg,#dc2626,#f87171)"


# home page

def show_wereda_home():
    st.markdown('<div class="page-title">Wereda School Performance Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Select a school to view grade-level analytics, or review Wereda-wide KPIs below.</div>', unsafe_allow_html=True)

    inject_school_card_css()
    
    cols_r1 = st.columns(4)
    for idx, school_name in enumerate(WEREDA_SCHOOLS[:4]):
        with cols_r1[idx]:
            if render_clickable_school_card(school_name, key=f"wereda_btn_{school_name}"):
                navigate_to_school(school_name)
                
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    
    cols_r2 = st.columns(4)
    for idx, school_name in enumerate(WEREDA_SCHOOLS[4:]):
        with cols_r2[idx]:
            if render_clickable_school_card(school_name, key=f"wereda_btn_{school_name}"):
                navigate_to_school(school_name)

    st.markdown("<hr style='margin:40px 0;'>", unsafe_allow_html=True)

    # ── Wereda-level KPIs ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Wereda-Level KPI Overview</div>', unsafe_allow_html=True)
    kpis = get_wereda_kpis()

    focus_chips = "".join(f'<span class="focus-chip">{s}</span>' for s in kpis["subjects_needing_focus"])
    attn_chips  = "".join(f'<span class="attention-chip">{s}</span>' for s in kpis["schools_needing_attention"])

    st.markdown(f"""
    <div class="kpi-summary-box">
        <div class="kpi-summary-title">Wereda Academic Dashboard</div>
        <div class="kpi-summary-sub">Aggregated across all schools and grade levels</div>
        <div class="kpi-inner-grid">
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Overall Avg Score</div>
                <div class="kpi-inner-value">{kpis['overall_avg']}%</div>
                <div class="kpi-inner-note">All subjects & grades</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Pass Rate</div>
                <div class="kpi-inner-value">{kpis['pass_rate']}%</div>
                <div class="kpi-inner-note">Students ≥ 60% average</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Distinction Rate</div>
                <div class="kpi-inner-value">{kpis['distinction_rate']}%</div>
                <div class="kpi-inner-note">Students ≥ 75% average</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">At-Risk Students</div>
                <div class="kpi-inner-value">{kpis['at_risk']}%</div>
                <div class="kpi-inner-note">Below pass threshold</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Top Performer Rate</div>
                <div class="kpi-inner-value">{kpis['top_performer_rate']}%</div>
                <div class="kpi-inner-note">Students ≥ 85% average</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Term Improvement</div>
                <div class="kpi-inner-value">+{kpis['improvement']}%</div>
                <div class="kpi-inner-note">Q1 → Q2 average change</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_focus, col_attn = st.columns(2)
    with col_focus:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Subjects Needing Focus</div>
            <div style="margin-top:12px;">{focus_chips}</div>
            <div class="stat-note" style="margin-top:10px;">Lowest Wereda-wide average scores</div>
        </div>""", unsafe_allow_html=True)
    with col_attn:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Schools Needing Attention</div>
            <div style="margin-top:12px;">{attn_chips}</div>
            <div class="stat-note" style="margin-top:10px;">Lowest overall average in Wereda</div>
        </div>""", unsafe_allow_html=True)

    # ── School comparison chart ───────────────────────────────────────────────
    st.markdown("<hr style='margin:32px 0;'>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">School Ranking Comparison</div>', unsafe_allow_html=True)
    school_df = get_all_wereda_schools_overall_avg()
    strongest_subj, weakest_subj = get_wereda_overall_subject_analysis()
    top_school = school_df.iloc[0]["School"]
    bot_school = school_df.iloc[-1]["School"]

    st.markdown(f"""
    <div class="prediction-box">
        <div class="prediction-title">School & Subject Performance Insight</div>
        <div class="prediction-text">
            <b>Institution:</b> The highest performing institution is <b>{top_school}</b>.
            Focused support is recommended for <b>{bot_school}</b>.<br><br>
            <b>Subject:</b> Students excel most in <b>{strongest_subj}</b>. However, <b>{weakest_subj}</b>
            has the lowest Wereda-wide average — immediate instructional intervention is advised.
        </div>
    </div>
    """, unsafe_allow_html=True)

    fig = px.bar(
        school_df, x="School", y="Average", color="Average",
        color_continuous_scale="Teal", text="Average",
        title="Aggregate Overall Score per School in Wereda"
    )
    fig.update_layout(yaxis_range=[50, 100], plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Inter"))
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)


# school overview page

def show_school_overview(school_name: str):
    st.markdown('<div class="back-button-area">', unsafe_allow_html=True)
    if st.button("← Back to Schools", key="wereda_back_schools"):
        navigate_to("home")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="page-title">{school_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Grade-level performance overview</div>', unsafe_allow_html=True)

    grade_configs = get_grade_configs()
    total_students = 0
    all_marks = []
    for cfg in grade_configs:
        df = get_wereda_grade_data(school_name, cfg["grade"], cfg["track"])
        total_students += get_student_count(df)
        all_marks.extend(df["Mark"].tolist())

    overall_avg = round(sum(all_marks) / len(all_marks), 1) if all_marks else 0.0
    school_kpis = get_school_kpis(school_name)

    st.markdown(f"""
    <div class="stat-cards">
        <div class="stat-card">
            <div class="stat-label">Total Students</div>
            <div class="stat-value">{total_students}</div>
            <div class="stat-note">Across all grades</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">School Average</div>
            <div class="stat-value">{overall_avg}%</div>
            <div class="stat-note">All subjects combined</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Pass Rate</div>
            <div class="stat-value" style="color:#16a34a;">{school_kpis['pass_rate']}%</div>
            {_bar(_pass_color(school_kpis['pass_rate']), school_kpis['pass_rate'])}
            <div class="stat-note">Students ≥ 60% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">At-Risk Students</div>
            <div class="stat-value" style="color:#ea580c;">{school_kpis['at_risk']}%</div>
            {_bar("linear-gradient(90deg,#ea580c,#fb923c)", school_kpis['at_risk'])}
            <div class="stat-note">Below pass threshold</div>
        </div>
    </div>
    <div class="stat-cards">
        <div class="stat-card">
            <div class="stat-label">Distinction Rate</div>
            <div class="stat-value" style="color:#7c3aed;">{school_kpis['distinction_rate']}%</div>
            {_bar("linear-gradient(90deg,#7c3aed,#a855f7)", school_kpis['distinction_rate'])}
            <div class="stat-note">Students ≥ 75% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Top Performer Rate</div>
            <div class="stat-value" style="color:#0f4c81;">{school_kpis['top_performer_rate']}%</div>
            {_bar("linear-gradient(90deg,#0f4c81,#3b82f6)", school_kpis['top_performer_rate'])}
            <div class="stat-note">Students ≥ 85% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Strongest Subject</div>
            <div class="stat-value" style="font-size:20px;">{school_kpis['strongest_subject']}</div>
            <div class="stat-note">Highest school-wide average</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Weakest Subject</div>
            <div class="stat-value" style="font-size:20px;color:#dc2626;">{school_kpis['weakest_subject']}</div>
            <div class="stat-note">Needs immediate focus</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Select a Grade</div>', unsafe_allow_html=True)
    cols_r1 = st.columns(3)
    with cols_r1[0]:
        cfg = grade_configs[0]
        if st.button(cfg["label"], key=f"wg_{school_name}_{cfg['grade']}_{cfg['track']}", use_container_width=True):
            navigate_to_grade(school_name, cfg["grade"], cfg["track"])
    with cols_r1[1]:
        cfg = grade_configs[1]
        if st.button(cfg["label"], key=f"wg_{school_name}_{cfg['grade']}_{cfg['track']}", use_container_width=True):
            navigate_to_grade(school_name, cfg["grade"], cfg["track"])
    with cols_r1[2]:
        cfg = grade_configs[2]
        st.markdown('<span class="track-label natural">Natural Track</span>', unsafe_allow_html=True)
        if st.button(cfg["label"], key=f"wg_{school_name}_{cfg['grade']}_{cfg['track']}", use_container_width=True):
            navigate_to_grade(school_name, cfg["grade"], cfg["track"])

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    cols_r2 = st.columns(3)
    with cols_r2[0]:
        cfg = grade_configs[3]
        st.markdown('<span class="track-label social">Social Track</span>', unsafe_allow_html=True)
        if st.button(cfg["label"], key=f"wg_{school_name}_{cfg['grade']}_{cfg['track']}", use_container_width=True):
            navigate_to_grade(school_name, cfg["grade"], cfg["track"])
    with cols_r2[1]:
        cfg = grade_configs[4]
        st.markdown('<span class="track-label natural">Natural Track</span>', unsafe_allow_html=True)
        if st.button(cfg["label"], key=f"wg_{school_name}_{cfg['grade']}_{cfg['track']}", use_container_width=True):
            navigate_to_grade(school_name, cfg["grade"], cfg["track"])
    with cols_r2[2]:
        cfg = grade_configs[5]
        st.markdown('<span class="track-label social">Social Track</span>', unsafe_allow_html=True)
        if st.button(cfg["label"], key=f"wg_{school_name}_{cfg['grade']}_{cfg['track']}", use_container_width=True):
            navigate_to_grade(school_name, cfg["grade"], cfg["track"])


# grade detail page — full kpi suite

def show_grade_detail(school_name: str, grade: int, track: str):
    st.markdown('<div class="back-button-area">', unsafe_allow_html=True)
    if st.button("← Back to School", key="wereda_back_school"):
        navigate_to_school(school_name)
    st.markdown('</div>', unsafe_allow_html=True)

    title = f"{school_name} — Grade {grade}"
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if track == "natural":
        st.markdown('<span class="track-label natural">Natural Track</span>', unsafe_allow_html=True)
        chart_label = f"Grade {grade} Natural"
    elif track == "social":
        st.markdown('<span class="track-label social">Social Track</span>', unsafe_allow_html=True)
        chart_label = f"Grade {grade} Social"
    else:
        chart_label = f"Grade {grade}"

    df = get_wereda_grade_data(school_name, grade, track)

    # Analytics
    avg_per_subject = get_class_avg_per_subject(df)
    strongest, weakest = get_strongest_weakest(df)
    overall_avg  = get_class_overall_avg(df)
    num_students = get_student_count(df)
    pass_r       = get_pass_rate(df)
    fail_r       = get_fail_rate(df)
    dist_r       = get_distinction_rate(df)
    at_risk      = get_at_risk_students(df)
    top_idx      = get_top_performer_index(df)
    variance     = get_performance_variance(df)
    engagement   = get_engagement_level(df)
    prediction   = get_prediction_trend(df)
    top3         = get_top_n_students(df, 3)

    # KPI Row 1
    st.markdown(f"""
    <div class="stat-cards">
        <div class="stat-card">
            <div class="stat-label">Students</div>
            <div class="stat-value">{num_students}</div>
            <div class="stat-note">Enrolled in grade</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Grade Average</div>
            <div class="stat-value">{overall_avg}%</div>
            <div class="stat-note">Across all subjects</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Strongest Subject</div>
            <div class="stat-value" style="font-size:20px;">{strongest}</div>
            <div class="stat-note">Highest average</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Weakest Subject</div>
            <div class="stat-value" style="font-size:20px;color:#dc2626;">{weakest}</div>
            <div class="stat-note">Needs attention</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI Row 2 — Pass/Fail/Distinction/At-Risk
    st.markdown(f"""
    <div class="stat-cards">
        <div class="stat-card">
            <div class="stat-label">Pass Rate</div>
            <div class="stat-value" style="color:#16a34a;">{pass_r}%</div>
            {_bar(_pass_color(pass_r), pass_r)}
            <div class="stat-note">Students ≥ 60% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Fail Rate</div>
            <div class="stat-value" style="color:#dc2626;">{fail_r}%</div>
            {_bar("linear-gradient(90deg,#dc2626,#f87171)", fail_r)}
            <div class="stat-note">Below pass mark</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Distinction Rate</div>
            <div class="stat-value" style="color:#7c3aed;">{dist_r}%</div>
            {_bar("linear-gradient(90deg,#7c3aed,#a855f7)", dist_r)}
            <div class="stat-note">Students ≥ 75% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">At-Risk Students</div>
            <div class="stat-value" style="color:#ea580c;">{at_risk}%</div>
            {_bar("linear-gradient(90deg,#ea580c,#fb923c)", at_risk)}
            <div class="stat-note">Flagged for intervention</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI Row 3 — Top Performer / Variance / Engagement
    st.markdown(f"""
    <div class="stat-cards" style="grid-template-columns:repeat(3,minmax(0,1fr));">
        <div class="stat-card">
            <div class="stat-label">Top Performer Index</div>
            <div class="stat-value" style="color:#0f4c81;">{top_idx}%</div>
            {_bar("linear-gradient(90deg,#0f4c81,#3b82f6)", top_idx)}
            <div class="stat-note">Students in top 10%</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Performance Variance</div>
            <div class="stat-value">{variance}</div>
            <div class="stat-note">Score spread (std²)</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Engagement Level</div>
            <div class="stat-value" style="color:#0891b2;">{engagement}%</div>
            {_bar("linear-gradient(90deg,#0891b2,#22d3ee)", engagement)}
            <div class="stat-note">Active students (avg ≥ 65)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(subject_avg_bar_chart(avg_per_subject, chart_label), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(performance_trend_chart(avg_per_subject, chart_label), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Prediction
    st.markdown(f"""
    <div class="prediction-box">
        <div class="prediction-title">Performance Prediction</div>
        <div class="prediction-text">{prediction}</div>
    </div>
    """, unsafe_allow_html=True)

    # Top 3 Students
    st.markdown('<div class="section-title">Top 3 Students</div>', unsafe_allow_html=True)
    student_cols = st.columns(3)
    excl = ["Student", "Average", "Class"]
    subj_list = [c for c in top3.columns if c not in excl]

    for idx in range(min(3, len(top3))):
        with student_cols[idx]:
            row = top3.iloc[idx]
            rank = idx + 1
            badge_cls, badge_txt = (
                ("badge-gold",   "1st Place") if rank == 1 else
                ("badge-silver", "2nd Place") if rank == 2 else
                ("badge-bronze", "3rd Place")
            )
            st.markdown(f"""
            <div class="top-student-card rank-{rank}">
                <div class="student-name">{row['Student']}</div>
                <div class="student-avg">Average: {round(row['Average'], 1)}%</div>
                <span class="badge {badge_cls}">{badge_txt}</span>
            </div>
            """, unsafe_allow_html=True)

            marks_html = '<table class="subject-marks-table"><thead><tr><th>Subject</th><th>Mark</th></tr></thead><tbody>'
            for subj in subj_list:
                marks_html += f'<tr><td>{subj}</td><td>{int(row[subj])}</td></tr>'
            marks_html += '</tbody></table>'
            st.markdown(marks_html, unsafe_allow_html=True)


# main entry

if __name__ == "__main__":
    inject_wereda_css()
    page = st.session_state.wereda_page
    if page == "home":
        show_wereda_home()
    elif page == "school":
        show_school_overview(st.session_state.get("wereda_school", ""))
    elif page == "grade_detail":
        show_grade_detail(
            st.session_state.get("wereda_school", ""),
            st.session_state.get("wereda_grade", 9),
            st.session_state.get("wereda_track", None),
        )
    else:
        show_wereda_home()