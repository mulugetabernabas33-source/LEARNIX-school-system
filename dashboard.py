"""
School Administration Dashboard
Comprehensive section-level and grade-level performance analytics.
"""

# file connections / imports
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from helpers.data_gen import (
    ALL_CLASSES, get_subjects_for_class, get_class_data,
    get_all_classes_for_grade, get_track_label,
    get_class_data_by_term, get_all_class_averages_cached,
)
from helpers.analytics import (
    get_class_avg_per_subject, get_strongest_weakest,
    get_top_n_students, get_grade_top_students,
    get_prediction_trend, get_class_overall_avg, get_student_count,
    get_pass_rate, get_fail_rate, get_distinction_rate,
    get_at_risk_students, get_top_performer_index,
    get_subject_performance_gap, get_performance_variance,
    get_engagement_level, get_section_ranking, get_term_improvement,
)
from helpers.charts import (
    subject_avg_bar_chart, performance_trend_chart,
    grade_comparison_chart, top_students_chart,
)

try:
    # page configuration
    st.set_page_config(
        page_title="School Admin Dashboard",
        page_icon="School Admin",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
except st.errors.StreamlitAPIException:
    pass


# inject css
def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        * { font-family: 'Inter', sans-serif; }
        html, body { background: #ffffff !important; color: #334155; }
        .stApp { background: #ffffff !important; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .main .block-container { max-width: 1400px; padding: 2rem 3rem; background: transparent !important; }

        .page-title { font-size: clamp(32px,4vw,42px); font-weight:900; color:#0f172a; margin-bottom:10px; letter-spacing:-0.04em; line-height:1.02; }
        .page-subtitle { font-size:16px; color:#64748b; margin-bottom:32px; line-height:1.75; }
        .grade-header { font-size:26px; font-weight:800; color:#0f172a; margin:28px 0 16px; padding-bottom:10px; border-bottom:2px solid rgba(203,213,225,0.75); letter-spacing:-0.03em; }
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

        .kpi-bar-wrap { margin-top:10px; }
        .kpi-bar-bg   { background:#e2e8f0; border-radius:4px; height:7px; width:100%; }
        .kpi-bar-fill { height:7px; border-radius:4px; transition:width 0.4s ease; }

        .top-student-card { background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.78); border-radius:22px; padding:22px 24px; box-shadow:0 18px 40px rgba(15,23,42,0.09); margin-bottom:18px; border-left:5px solid #0f4c81; }
        .top-student-card.rank-1 { border-left-color:#D4AF37; background:linear-gradient(180deg,#fffbeb,#fffdf5); }
        .top-student-card.rank-2 { border-left-color:#A8A9AD; background:linear-gradient(180deg,#f8fafc,#ffffff); }
        .top-student-card.rank-3 { border-left-color:#CD7F32; background:linear-gradient(180deg,#fff7ed,#fffbf5); }
        .student-name { font-size:18px; font-weight:800; color:#0f172a; letter-spacing:-0.02em; }
        .student-avg  { font-size:15px; font-weight:700; color:#0f4c81; }
        .student-class{ font-size:13px; color:#64748b; font-weight:500; }

        .badge { display:inline-flex; align-items:center; padding:6px 14px; border-radius:999px; font-size:13px; font-weight:800; letter-spacing:0.05em; }
        .badge-gold   { background:linear-gradient(180deg,#fef3c7,#fef9e7); color:#b45309; border:1px solid rgba(212,175,55,0.3); }
        .badge-silver { background:linear-gradient(180deg,#f1f5f9,#f8fafc); color:#475569; border:1px solid rgba(168,169,173,0.3); }
        .badge-bronze { background:linear-gradient(180deg,#fed7aa,#fff7ed); color:#9a3412; border:1px solid rgba(205,127,50,0.3); }
        .badge-rank   { background:linear-gradient(180deg,#dbeafe,#eff6ff); color:#1d4ed8; border:1px solid rgba(59,130,246,0.25); }

        .prediction-box { background:linear-gradient(180deg,#f0f9ff,#f8fbff); border:1px solid rgba(56,189,248,0.22); border-radius:22px; padding:22px 26px; box-shadow:0 18px 40px rgba(15,23,42,0.09); border-left:5px solid #0f4c81; margin:18px 0 32px; }
        .prediction-title { font-size:18px; font-weight:800; color:#0f172a; margin-bottom:10px; letter-spacing:-0.02em; }
        .prediction-text  { font-size:15px; color:#334155; line-height:1.65; }

        .school-summary-box { background:linear-gradient(135deg,#0f172a 0%,#0f4c81 100%); border-radius:22px; padding:28px 32px; margin-bottom:32px; box-shadow:0 24px 50px rgba(15,23,42,0.18); }
        .school-summary-title { color:#f8fafc; font-size:22px; font-weight:900; letter-spacing:-0.03em; margin-bottom:6px; }
        .school-summary-sub   { color:rgba(226,232,240,0.8); font-size:14px; margin-bottom:20px; }
        .school-kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
        .school-kpi-card { background:rgba(255,255,255,0.10); border:1px solid rgba(255,255,255,0.14); border-radius:16px; padding:16px 18px; }
        .school-kpi-label { color:#93c5fd; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:6px; }
        .school-kpi-value { color:#ffffff; font-size:26px; font-weight:900; letter-spacing:-0.03em; }
        .school-kpi-note  { color:rgba(226,232,240,0.75); font-size:12px; margin-top:4px; }

        .subject-gap-table { width:100%; border-collapse:collapse; font-size:14px; margin-top:14px; }
        .subject-gap-table th, .subject-gap-table td { padding:9px 12px; text-align:left; border-bottom:1px solid rgba(203,213,225,0.6); }
        .subject-gap-table th { background:rgba(248,250,252,0.95); font-weight:700; color:#475569; font-size:13px; }
        .subject-gap-table td { color:#334155; }
        .gap-bar { display:inline-block; height:8px; border-radius:4px; background:linear-gradient(90deg,#3b82f6,#0f4c81); vertical-align:middle; margin-left:8px; }

        .subject-marks-table { width:100%; border-collapse:collapse; font-size:14px; margin-top:14px; }
        .subject-marks-table th, .subject-marks-table td { padding:10px 12px; text-align:left; border-bottom:1px solid rgba(203,213,225,0.65); }
        .subject-marks-table th { background:rgba(248,250,252,0.95); font-weight:700; color:#475569; font-size:13px; }
        .subject-marks-table td { color:#334155; line-height:1.45; }

        .chart-container { background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.75); border-radius:22px; padding:20px; box-shadow:0 20px 42px rgba(15,23,42,0.09); margin-bottom:26px; }
        .track-section { margin:26px 0; padding:24px; background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.78); border-radius:22px; box-shadow:0 18px 40px rgba(15,23,42,0.09); }
        .track-section-title { font-size:20px; font-weight:800; color:#0f172a; margin-bottom:18px; letter-spacing:-0.02em; }

        .stButton > button { width:100%; background:#ffffff !important; border:1px solid #e2e8f0 !important; border-radius:10px !important; padding:14px 20px !important; font-size:15px !important; font-weight:600 !important; color:#334155 !important; transition:all 0.2s cubic-bezier(0.4,0,0.2,1) !important; box-shadow:0 1px 2px rgba(0,0,0,0.05) !important; }
        .stButton > button:hover { background:#f8fafc !important; border-color:#94a3b8 !important; color:#0f4c81 !important; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1) !important; transform:translateY(-1px) !important; }

        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
            background:rgba(255,255,255,0.94) !important; border:1px solid rgba(203,213,225,0.75) !important;
            border-radius:22px !important; box-shadow:0 20px 42px rgba(15,23,42,0.09) !important; padding:18px 20px !important;
        }
        @media (max-width:1100px) { .stat-cards, .school-kpi-grid { grid-template-columns:1fr 1fr !important; } }
        @media (max-width:768px)  { .stat-cards, .school-kpi-grid { grid-template-columns:1fr !important; } .main .block-container { padding:1rem 1.5rem; } }
    </style>
    """, unsafe_allow_html=True)


# navigate to
def navigate_to(page):
    st.session_state.dash_page = page
    st.rerun()


if "dash_page" not in st.session_state:
    st.session_state.dash_page = "home"


# kpi bar
def _kpi_bar(color: str, pct: float) -> str:
    w = min(max(pct, 0), 100)
    return (
        f'<div class="kpi-bar-wrap"><div class="kpi-bar-bg">'
        f'<div class="kpi-bar-fill" style="background:{color};width:{w}%;"></div>'
        f'</div></div>'
    )


# color for pass
def _color_for_pass(v: float) -> str:
    if v >= 80:
        return "linear-gradient(90deg,#16a34a,#22c55e)"
    if v >= 60:
        return "linear-gradient(90deg,#ca8a04,#facc15)"
    return "linear-gradient(90deg,#dc2626,#f87171)"


# stat card
def _stat_card(label, value, note, bar_color=None, bar_pct=None, value_color="#0f172a") -> str:
    bar_html = ""
    if bar_color and bar_pct is not None:
        bar_html = _kpi_bar(bar_color, bar_pct)
    return (
        f'<div class="stat-card">'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-value" style="color:{value_color};">{value}</div>'
        f'{bar_html}'
        f'<div class="stat-note">{note}</div>'
        f'</div>'
    )


# compute school summary
def _compute_school_summary():
    """Aggregate KPIs across the whole school (all classes)."""
    all_marks = []
    all_student_avgs = []
    for cls in ALL_CLASSES:
        df = get_class_data(cls)
        all_marks.extend(df["Mark"].tolist())
        all_student_avgs.extend(df.groupby("Student")["Mark"].mean().tolist())
    total = len(all_student_avgs)
    school_avg = round(sum(all_marks) / len(all_marks), 1) if all_marks else 0.0
    pass_r = round(sum(1 for a in all_student_avgs if a >= 60) / total * 100, 1) if total > 0 else 0.0
    dist_r = round(sum(1 for a in all_student_avgs if a >= 75) / total * 100, 1) if total > 0 else 0.0
    at_risk = round(100 - pass_r, 1)
    return school_avg, pass_r, dist_r, at_risk


# show home
def show_home():
    st.markdown('<div class="page-title">School Administration Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Comprehensive academic performance monitoring for all sections and grades.</div>', unsafe_allow_html=True)

    school_avg, pass_r, dist_r, at_risk = _compute_school_summary()

    st.markdown(f"""
    <div class="school-summary-box">
        <div class="school-summary-title">School-Wide Performance Overview</div>
        <div class="school-summary-sub">Aggregated across all grades and sections</div>
        <div class="school-kpi-grid">
            <div class="school-kpi-card">
                <div class="school-kpi-label">Overall Average</div>
                <div class="school-kpi-value">{school_avg}%</div>
                <div class="school-kpi-note">All subjects combined</div>
            </div>
            <div class="school-kpi-card">
                <div class="school-kpi-label">Pass Rate</div>
                <div class="school-kpi-value">{pass_r}%</div>
                <div class="school-kpi-note">Students ≥ 60% average</div>
            </div>
            <div class="school-kpi-card">
                <div class="school-kpi-label">Distinction Rate</div>
                <div class="school-kpi-value">{dist_r}%</div>
                <div class="school-kpi-note">Students ≥ 75% average</div>
            </div>
            <div class="school-kpi-card">
                <div class="school-kpi-label">At-Risk Students</div>
                <div class="school-kpi-value">{at_risk}%</div>
                <div class="school-kpi-note">Below pass threshold</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Select a Section</div>', unsafe_allow_html=True)

    for grade in [9, 10, 11, 12]:
        label = f"Grade {grade} — Natural & Social Tracks" if grade in [11, 12] else f"Grade {grade}"
        st.markdown(f'<div class="grade-header">{label}</div>', unsafe_allow_html=True)

        classes = get_all_classes_for_grade(grade)
        cols = st.columns(4)
        for idx, cls in enumerate(classes):
            with cols[idx]:
                track = get_track_label(cls)
                if track:
                    tc = "natural" if "Natural" in track else "social"
                    st.markdown(f'<span class="track-label {tc}">{track}</span>', unsafe_allow_html=True)
                if st.button(f"Class {cls}", key=f"admin_btn_{cls}", use_container_width=True):
                    navigate_to(f"class_{cls}")

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        if st.button(f"View Grade {grade} Overview", key=f"admin_grade_{grade}"):
            navigate_to(f"grade_{grade}")
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)


# show class page
def show_class_page(class_name: str):
    st.markdown('<div class="back-button-area">', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="admin_back_btn"):
        navigate_to("home")
    st.markdown('</div>', unsafe_allow_html=True)

    track = get_track_label(class_name)
    if track:
        tc = "natural" if "Natural" in track else "social"
        st.markdown(f'<div class="page-title">Section {class_name}</div><span class="track-label {tc}">{track}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="page-title">Section {class_name}</div>', unsafe_allow_html=True)

    st.markdown('<div class="page-subtitle">Comprehensive section performance analytics with all KPIs.</div>', unsafe_allow_html=True)

    df       = get_class_data(class_name)
    df_q1    = get_class_data_by_term(class_name, 0)
    df_q2    = get_class_data_by_term(class_name, 1)
    all_avgs = get_all_class_averages_cached()

    num_students  = get_student_count(df)
    overall_avg   = get_class_overall_avg(df)
    strongest, weakest = get_strongest_weakest(df)
    pass_r        = get_pass_rate(df)
    fail_r        = get_fail_rate(df)
    dist_r        = get_distinction_rate(df)
    at_risk       = get_at_risk_students(df)
    top_idx       = get_top_performer_index(df)
    variance      = get_performance_variance(df)
    engagement    = get_engagement_level(df)
    ranking       = get_section_ranking(class_name, all_avgs)
    improvement   = get_term_improvement(df_q1, df_q2)
    gap_dict      = get_subject_performance_gap(df)
    prediction    = get_prediction_trend(df)
    top3          = get_top_n_students(df, 3)
    avg_per_subj  = get_class_avg_per_subject(df)

    total_sections = len(ALL_CLASSES)
    impr_sign = "+" if improvement >= 0 else ""
    impr_color = "#16a34a" if improvement >= 0 else "#dc2626"

    st.markdown(f"""
    <div class="stat-cards">
        {_stat_card("Students Enrolled", str(num_students), "In this section")}
        {_stat_card("Section Average", f"{overall_avg}%", "All subjects combined")}
        {_stat_card("Strongest Subject", strongest, "Highest class average")}
        {_stat_card("Weakest Subject", weakest, "Needs immediate focus", value_color="#dc2626")}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-cards">
        <div class="stat-card">
            <div class="stat-label">Pass Rate</div>
            <div class="stat-value" style="color:#16a34a;">{pass_r}%</div>
            {_kpi_bar(_color_for_pass(pass_r), pass_r)}
            <div class="stat-note">Students ≥ 60% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Fail Rate</div>
            <div class="stat-value" style="color:#dc2626;">{fail_r}%</div>
            {_kpi_bar("linear-gradient(90deg,#dc2626,#f87171)", fail_r)}
            <div class="stat-note">Students below pass mark</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Distinction Rate</div>
            <div class="stat-value" style="color:#7c3aed;">{dist_r}%</div>
            {_kpi_bar("linear-gradient(90deg,#7c3aed,#a855f7)", dist_r)}
            <div class="stat-note">Students ≥ 75% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">At-Risk Students</div>
            <div class="stat-value" style="color:#ea580c;">{at_risk}%</div>
            {_kpi_bar("linear-gradient(90deg,#ea580c,#fb923c)", at_risk)}
            <div class="stat-note">Flagged for intervention</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    rank_label = f"#{ranking} of {total_sections}"
    st.markdown(f"""
    <div class="stat-cards">
        <div class="stat-card">
            <div class="stat-label">Top Performer Index</div>
            <div class="stat-value" style="color:#0f4c81;">{top_idx}%</div>
            {_kpi_bar("linear-gradient(90deg,#0f4c81,#3b82f6)", top_idx)}
            <div class="stat-note">Students in top 10%</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Performance Variance</div>
            <div class="stat-value">{variance}</div>
            <div class="stat-note">Score spread among students</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Term-to-Term Improvement</div>
            <div class="stat-value" style="color:{impr_color};">{impr_sign}{improvement}%</div>
            <div class="stat-note">Q1 → Q2 change in avg score</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Section Ranking</div>
            <div class="stat-value">{rank_label}</div>
            <span class="badge badge-rank">Within School</span>
            <div class="stat-note" style="margin-top:8px;">Compared to all sections</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-cards" style="grid-template-columns:repeat(2,minmax(0,1fr));">
        <div class="stat-card">
            <div class="stat-label">Student Engagement Level</div>
            <div class="stat-value" style="color:#0891b2;">{engagement}%</div>
            {_kpi_bar("linear-gradient(90deg,#0891b2,#22d3ee)", engagement)}
            <div class="stat-note">Students actively participating (avg ≥ 65)</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Section Pass Rate (Verification)</div>
            <div class="stat-value" style="color:#16a34a;">{pass_r}%</div>
            {_kpi_bar(_color_for_pass(pass_r), pass_r)}
            <div class="stat-note">Cross-check with Pass Rate above — should match</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(subject_avg_bar_chart(avg_per_subj, class_name), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(performance_trend_chart(avg_per_subj, class_name), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Subject Performance Gap (Score Spread)</div>', unsafe_allow_html=True)
    max_gap = max(gap_dict.values()) if gap_dict else 1

    gap_df = pd.DataFrame([
        {"Subject": s, "Gap (pts)": g}
        for s, g in sorted(gap_dict.items(), key=lambda x: x[1], reverse=True)
    ])
    fig_gap = px.bar(
        gap_df, x="Gap (pts)", y="Subject", orientation="h",
        color="Gap (pts)", color_continuous_scale=["#dbeafe", "#1d4ed8"],
        title=f"Score Spread per Subject — Section {class_name}"
    )
    fig_gap.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248,250,252,0.8)",
        font=dict(family="Inter", color="#334155"),
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=False,
    )
    fig_gap.update_traces(marker_line_width=0)
    st.plotly_chart(fig_gap, use_container_width=True)

    st.markdown(f"""
    <div class="prediction-box">
        <div class="prediction-title">Performance Prediction & Insight</div>
        <div class="prediction-text">{prediction}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Top 3 Students</div>', unsafe_allow_html=True)
    student_cols = st.columns(3)
    excl = ["Student", "Average", "Class"]
    subj_list = [c for c in top3.columns if c not in excl]

    for idx in range(min(3, len(top3))):
        with student_cols[idx]:
            row = top3.iloc[idx]
            sname = row["Student"]
            savg  = round(row["Average"], 1)
            rank  = idx + 1
            badge_cls, badge_txt = (
                ("badge-gold",   "1st Place") if rank == 1 else
                ("badge-silver", "2nd Place") if rank == 2 else
                ("badge-bronze", "3rd Place")
            )
            st.markdown(f"""
            <div class="top-student-card rank-{rank}">
                <div class="student-name">{sname}</div>
                <div class="student-avg">Average: {savg}%</div>
                <span class="badge {badge_cls}">{badge_txt}</span>
            </div>
            """, unsafe_allow_html=True)

            marks_html = '<table class="subject-marks-table"><thead><tr><th>Subject</th><th>Mark</th></tr></thead><tbody>'
            for subj in subj_list:
                marks_html += f'<tr><td>{subj}</td><td>{int(row[subj])}</td></tr>'
            marks_html += '</tbody></table>'
            st.markdown(marks_html, unsafe_allow_html=True)


# show grade overview
def show_grade_overview(grade: int):
    st.markdown('<div class="back-button-area">', unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="admin_back_btn_grade"):
        navigate_to("home")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="page-title">Grade {grade} — Section Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Comparative performance across all sections in this grade.</div>', unsafe_allow_html=True)

    classes = get_all_classes_for_grade(grade)

    if grade in [9, 10]:
        grade_avgs = {}
        grade_pass  = {}
        for cls in classes:
            df = get_class_data(cls)
            grade_avgs[cls] = get_class_overall_avg(df)
            grade_pass[cls] = get_pass_rate(df)

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(grade_comparison_chart(grade_avgs, grade), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        rows = []
        for cls in classes:
            df = get_class_data(cls)
            rows.append({
                "Section":       cls,
                "Avg Score":     get_class_overall_avg(df),
                "Pass Rate (%)": get_pass_rate(df),
                "Distinction (%)": get_distinction_rate(df),
                "At-Risk (%)":   get_at_risk_students(df),
                "Top Performer (%)": get_top_performer_index(df),
            })
        kpi_df = pd.DataFrame(rows).sort_values("Avg Score", ascending=False).reset_index(drop=True)
        st.markdown('<div class="section-title">Section KPI Comparison</div>', unsafe_allow_html=True)
        st.dataframe(kpi_df, use_container_width=True, hide_index=True)

        st.markdown(f'<div class="section-title">Top 3 Students — Grade {grade}</div>', unsafe_allow_html=True)
        top3_grade = get_grade_top_students(grade, 3)
        student_cols = st.columns(3)
        for idx in range(min(3, len(top3_grade))):
            with student_cols[idx]:
                r = top3_grade.iloc[idx]
                rank = idx + 1
                badge_cls, badge_txt = (
                    ("badge-gold",   "1st Place") if rank == 1 else
                    ("badge-silver", "2nd Place") if rank == 2 else
                    ("badge-bronze", "3rd Place")
                )
                st.markdown(f"""
                <div class="top-student-card rank-{rank}">
                    <div class="student-name">{r['Student']}</div>
                    <div class="student-class">Section: {r['Class']}</div>
                    <div class="student-avg">Average: {r['Average']}%</div>
                    <span class="badge {badge_cls}">{badge_txt}</span>
                </div>
                """, unsafe_allow_html=True)

    else:
        natural_cls = [c for c in classes if c[-1] in ["A", "B"]]
        social_cls  = [c for c in classes if c[-1] in ["C", "D"]]

        for track_name, track_classes, tc_css in [
            ("Natural Track", natural_cls, "natural"),
            ("Social Track",  social_cls,  "social"),
        ]:
            st.markdown(f'<span class="track-label {tc_css}">{track_name}</span>', unsafe_allow_html=True)
            track_avgs = {cls: get_class_overall_avg(get_class_data(cls)) for cls in track_classes}

            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(grade_comparison_chart(track_avgs, grade), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            rows = []
            for cls in track_classes:
                df = get_class_data(cls)
                rows.append({
                    "Section":          cls,
                    "Avg Score":        get_class_overall_avg(df),
                    "Pass Rate (%)":    get_pass_rate(df),
                    "Distinction (%)":  get_distinction_rate(df),
                    "At-Risk (%)":      get_at_risk_students(df),
                    "Top Performer (%)": get_top_performer_index(df),
                })
            kpi_df = pd.DataFrame(rows).sort_values("Avg Score", ascending=False).reset_index(drop=True)
            st.markdown(f'<div class="section-title">Section KPI Comparison — {track_name}</div>', unsafe_allow_html=True)
            st.dataframe(kpi_df, use_container_width=True, hide_index=True)

        st.markdown(f'<div class="section-title">Top 3 Students — Grade {grade}</div>', unsafe_allow_html=True)
        top3_grade = get_grade_top_students(grade, 3)
        student_cols = st.columns(3)
        for idx in range(min(3, len(top3_grade))):
            with student_cols[idx]:
                r = top3_grade.iloc[idx]
                rank = idx + 1
                badge_cls, badge_txt = (
                    ("badge-gold",   "1st Place") if rank == 1 else
                    ("badge-silver", "2nd Place") if rank == 2 else
                    ("badge-bronze", "3rd Place")
                )
                st.markdown(f"""
                <div class="top-student-card rank-{rank}">
                    <div class="student-name">{r['Student']}</div>
                    <div class="student-class">Section: {r['Class']}</div>
                    <div class="student-avg">Average: {r['Average']}%</div>
                    <span class="badge {badge_cls}">{badge_txt}</span>
                </div>
                """, unsafe_allow_html=True)


if __name__ == "__main__":
    inject_css()
    page = st.session_state.dash_page
    if page == "home":
        show_home()
    elif page.startswith("class_"):
        show_class_page(page.replace("class_", ""))
    elif page.startswith("grade_"):
        show_grade_overview(int(page.replace("grade_", "")))
    else:
        show_home()
