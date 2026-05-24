"""
Kifle Ketema School Performance Dashboard
Top-level analytics across all Weredas with full KPI suite and heatmap.
"""

# file connections / imports
import streamlit as st
import pandas as pd
import plotly.express as px

from helpers.kk_data import (
    WEREDAS, KK_SCHOOLS,
    get_wereda_rankings, get_schools_in_wereda,
    get_wereda_grade12_analysis, get_kk_kpis, get_wereda_kpis_df,
)
from helpers.wereda_data import get_grade_configs
from helpers.analytics import (
    get_class_avg_per_subject, get_strongest_weakest,
    get_top_n_students, get_class_overall_avg, get_student_count,
)
from helpers.charts import subject_avg_bar_chart, performance_trend_chart


# inject kk css
def inject_kk_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        * { font-family: 'Inter', sans-serif; }
        html, body { background:#ffffff !important; color:#334155; }
        .stApp { background:#ffffff !important; }
        #MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
        .main .block-container { max-width:1400px; padding:2rem 3rem; background:transparent !important; }

        .page-title    { font-size:clamp(32px,4vw,42px); font-weight:900; color:#0f172a; margin-bottom:10px; letter-spacing:-0.04em; line-height:1.02; }
        .page-subtitle { font-size:16px; color:#64748b; margin-bottom:32px; line-height:1.75; }
        .section-title { font-size:26px; font-weight:800; color:#0f172a; margin:32px 0 16px; letter-spacing:-0.03em; }
        .back-button-area { margin-bottom:18px; }

        .stat-cards { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:18px; margin-bottom:26px; }
        .stat-card { background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.78); border-radius:22px; padding:22px 22px 18px; box-shadow:0 18px 40px rgba(15,23,42,0.09); min-height:148px; }
        .stat-card .stat-label { color:#0f4c81; font-size:13px; font-weight:800; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px; }
        .stat-card .stat-value { display:block; color:#0f172a; font-size:31px; line-height:1.08; margin:10px 0 12px; font-weight:900; letter-spacing:-0.04em; }
        .stat-card .stat-note  { color:#64748b; font-size:15px; line-height:1.6; margin-top:4px; }

        .kpi-bar-bg   { background:#e2e8f0; border-radius:4px; height:7px; width:100%; margin-top:8px; }
        .kpi-bar-fill { height:7px; border-radius:4px; }

        .kpi-banner { background:linear-gradient(135deg,#0f172a 0%,#0f4c81 100%); border-radius:22px; padding:26px 30px; margin-bottom:28px; box-shadow:0 22px 48px rgba(15,23,42,0.16); }
        .kpi-banner-title { color:#f8fafc; font-size:20px; font-weight:900; letter-spacing:-0.03em; margin-bottom:4px; }
        .kpi-banner-sub   { color:rgba(226,232,240,0.75); font-size:13px; margin-bottom:18px; }
        .kpi-inner-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
        .kpi-inner-card { background:rgba(255,255,255,0.10); border:1px solid rgba(255,255,255,0.14); border-radius:14px; padding:14px 16px; }
        .kpi-inner-label { color:#93c5fd; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:5px; }
        .kpi-inner-value { color:#ffffff; font-size:24px; font-weight:900; letter-spacing:-0.03em; }
        .kpi-inner-note  { color:rgba(226,232,240,0.7); font-size:11px; margin-top:3px; }

        .focus-chip { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; background:rgba(239,68,68,0.12); color:#dc2626; border:1px solid rgba(239,68,68,0.25); margin:3px 4px 3px 0; }

        .prediction-box { background:linear-gradient(180deg,#f0f9ff,#f8fbff); border:1px solid rgba(56,189,248,0.22); border-radius:22px; padding:22px 26px; box-shadow:0 18px 40px rgba(15,23,42,0.09); border-left:5px solid #0f4c81; margin:18px 0 32px; }
        .prediction-title { font-size:18px; font-weight:800; color:#0f172a; margin-bottom:10px; }
        .prediction-text  { font-size:15px; color:#334155; line-height:1.65; }

        .badge { display:inline-flex; align-items:center; padding:6px 14px; border-radius:999px; font-size:13px; font-weight:800; letter-spacing:0.05em; }
        .badge-gold   { background:linear-gradient(180deg,#fef3c7,#fef9e7); color:#b45309; border:1px solid rgba(212,175,55,0.3); }
        .badge-silver { background:linear-gradient(180deg,#f1f5f9,#f8fafc); color:#475569; border:1px solid rgba(168,169,173,0.3); }
        .badge-bronze { background:linear-gradient(180deg,#fed7aa,#fff7ed); color:#9a3412; border:1px solid rgba(205,127,50,0.3); }

        .track-label { display:inline-flex; align-items:center; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:0.12em; padding:7px 12px; border-radius:999px; margin-bottom:12px; }
        .track-label.natural { background:rgba(12,74,110,0.10); color:#0c4a6e; border:1px solid rgba(56,189,248,0.22); }
        .track-label.social  { background:rgba(139,92,246,0.10); color:#7c3aed; border:1px solid rgba(139,92,246,0.22); }

        .stButton > button { width:100%; background:#ffffff !important; border:1px solid #e2e8f0 !important; border-radius:10px !important; padding:14px 20px !important; font-size:15px !important; font-weight:600 !important; color:#334155 !important; transition:all 0.2s ease !important; box-shadow:0 1px 2px rgba(0,0,0,0.05) !important; }
        .stButton > button:hover { background:#f8fafc !important; border-color:#94a3b8 !important; color:#0f4c81 !important; transform:translateY(-1px) !important; }

        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] { background:rgba(255,255,255,0.94) !important; border:1px solid rgba(203,213,225,0.75) !important; border-radius:22px !important; box-shadow:0 20px 42px rgba(15,23,42,0.09) !important; padding:18px 20px !important; }
        @media (max-width:1100px) { .stat-cards, .kpi-inner-grid { grid-template-columns:1fr 1fr !important; } }
        @media (max-width:768px)  { .stat-cards, .kpi-inner-grid { grid-template-columns:1fr !important; } }
    </style>
    """, unsafe_allow_html=True)


# navigate to
def navigate_to(page):
    st.session_state.kk_page = page
    st.rerun()


# navigate to wereda
def navigate_to_wereda(wereda_name):
    st.session_state.kk_page = "wereda"
    st.session_state.kk_wereda = wereda_name
    st.rerun()


# bar
def _bar(color, pct):
    w = min(max(pct, 0), 100)
    return f'<div class="kpi-bar-bg"><div class="kpi-bar-fill" style="background:{color};width:{w}%;"></div></div>'


# pass color
def _pass_color(v):
    if v >= 80: return "linear-gradient(90deg,#16a34a,#22c55e)"
    if v >= 60: return "linear-gradient(90deg,#ca8a04,#facc15)"
    return "linear-gradient(90deg,#dc2626,#f87171)"


# show home
def show_home():
    st.markdown('<div class="page-title">Kifle Ketema Academic Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Top-level analytics across all Weredas. Select a Wereda to drill down.</div>', unsafe_allow_html=True)

    kpis = get_kk_kpis()
    focus_chips = "".join(f'<span class="focus-chip">{w}</span>' for w in kpis["weredas_needing_focus"])

    st.markdown(f"""
    <div class="kpi-banner">
        <div class="kpi-banner-title">Kifle Ketema Performance Summary</div>
        <div class="kpi-banner-sub">Aggregated across all Weredas and constituent schools</div>
        <div class="kpi-inner-grid">
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Overall Avg Score</div>
                <div class="kpi-inner-value">{kpis['overall_avg']}%</div>
                <div class="kpi-inner-note">All schools & Weredas</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Pass Rate</div>
                <div class="kpi-inner-value">{kpis['pass_rate']}%</div>
                <div class="kpi-inner-note">Institutions ≥ 66% avg</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Distinction Rate</div>
                <div class="kpi-inner-value">{kpis['distinction_rate']}%</div>
                <div class="kpi-inner-note">Institutions ≥ 75% avg</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">At-Risk Rate</div>
                <div class="kpi-inner-value">{kpis['at_risk']}%</div>
                <div class="kpi-inner-note">Below pass threshold</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Top Performer Rate</div>
                <div class="kpi-inner-value">{kpis['top_performer_rate']}%</div>
                <div class="kpi-inner-note">Institutions ≥ 80% avg</div>
            </div>
            <div class="kpi-inner-card">
                <div class="kpi-inner-label">Improvement (Term)</div>
                <div class="kpi-inner-value">+{kpis['improvement']}%</div>
                <div class="kpi-inner-note">Q1 → Q2 aggregate change</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-card" style="margin-bottom:24px;">
        <div class="stat-label">Weredas Needing Focus</div>
        <div style="margin-top:12px;">{focus_chips}</div>
        <div class="stat-note" style="margin-top:10px;">Lowest average scores in Kifle Ketema</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Wereda Navigation Directory</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for i, w_name in enumerate(WEREDAS):
        with cols[i % 5]:
            if st.button(w_name, key=f"kk_w_{w_name}"):
                navigate_to_wereda(w_name)

    st.markdown("<hr style='margin:40px 0;'>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Wereda Performance Comparison</div>', unsafe_allow_html=True)

    rankings_df = get_wereda_rankings()
    top_w  = rankings_df.iloc[0]["Wereda"]
    bot_w  = rankings_df.iloc[-1]["Wereda"]

    st.markdown(f"""
    <div class="prediction-box">
        <div class="prediction-title">Wereda Performance Insight</div>
        <div class="prediction-text">
            <b>{top_w}</b> is currently leading regional performance metrics across the Kifle Ketema.
            <b>{bot_w}</b> is underperforming relatively and requires focused resource allocation and academic support.
        </div>
    </div>
    """, unsafe_allow_html=True)

    fig = px.bar(
        rankings_df, x="Wereda", y="Average", color="Average",
        color_continuous_scale="Blues", text="Average",
        title="Overall Average Score by Wereda"
    )
    fig.update_layout(yaxis_range=[50, 100], plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Inter"))
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">Wereda KPI Heatmap</div>', unsafe_allow_html=True)
    kpi_df = get_wereda_kpis_df()
    kpi_metrics = ["Avg Score", "Pass Rate (%)", "Distinction (%)", "At-Risk (%)", "Top Performer (%)"]

    heatmap_data = kpi_df.set_index("Wereda")[kpi_metrics]
    fig_heat = px.imshow(
        heatmap_data.T,
        color_continuous_scale="Blues",
        text_auto=True,
        title="Wereda × KPI Heatmap",
        labels=dict(x="Wereda", y="KPI", color="Value (%)"),
        aspect="auto",
    )
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#334155"),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('<div class="section-title">Wereda KPI Comparison Table</div>', unsafe_allow_html=True)
    st.dataframe(kpi_df.sort_values("Avg Score", ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)


# show wereda overview
def show_wereda_overview(wereda_name: str):
    st.markdown('<div class="back-button-area">', unsafe_allow_html=True)
    if st.button("← Back to Kifle Ketema Directory", key="btn_back_kk"):
        navigate_to("home")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="page-title">{wereda_name} Performance Evaluation</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Institutional rankings and critical Grade 12 subject analysis.</div>', unsafe_allow_html=True)

    school_df = get_schools_in_wereda(wereda_name)
    top_school = school_df.iloc[0]["School"]
    bot_school = school_df.iloc[-1]["School"]
    avgs = school_df["Average"].tolist()
    total = len(avgs)

    w_pass_rate  = round(sum(1 for a in avgs if a >= 66) / total * 100, 1) if total > 0 else 0.0
    w_dist_rate  = round(sum(1 for a in avgs if a >= 75) / total * 100, 1) if total > 0 else 0.0
    w_at_risk    = round(100 - w_pass_rate, 1)
    w_top_rate   = round(sum(1 for a in avgs if a >= 80) / total * 100, 1) if total > 0 else 0.0
    w_avg        = round(sum(avgs) / total, 1) if total > 0 else 0.0

    st.markdown(f"""
    <div class="stat-cards">
        <div class="stat-card">
            <div class="stat-label">Wereda Avg Score</div>
            <div class="stat-value">{w_avg}%</div>
            <div class="stat-note">Across all schools</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Pass Rate</div>
            <div class="stat-value" style="color:#16a34a;">{w_pass_rate}%</div>
            {_bar(_pass_color(w_pass_rate), w_pass_rate)}
            <div class="stat-note">Schools ≥ 66% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Distinction Rate</div>
            <div class="stat-value" style="color:#7c3aed;">{w_dist_rate}%</div>
            {_bar("linear-gradient(90deg,#7c3aed,#a855f7)", w_dist_rate)}
            <div class="stat-note">Schools ≥ 75% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Top Performer Rate</div>
            <div class="stat-value" style="color:#0f4c81;">{w_top_rate}%</div>
            {_bar("linear-gradient(90deg,#0f4c81,#3b82f6)", w_top_rate)}
            <div class="stat-note">Schools ≥ 80% avg</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">School Performance Rankings</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="prediction-box">
        <div class="prediction-title">Institutional Overview</div>
        <div class="prediction-text">
            Within <b>{wereda_name}</b>, the highest performing institution is <b>{top_school}</b>.
            Strategic improvement plans should be prioritised for <b>{bot_school}</b> to raise regional averages.
        </div>
    </div>
    """, unsafe_allow_html=True)

    fig = px.bar(
        school_df, x="School", y="Average", color="Average",
        color_continuous_scale="Teal", text="Average",
        title=f"Overall Average Score per School — {wereda_name}"
    )
    fig.update_layout(yaxis_range=[50, 100], plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Inter"))
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr style='margin:40px 0;'>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Grade 12 National Exam Preparations</div>', unsafe_allow_html=True)

    nat_strong, nat_weak = get_wereda_grade12_analysis(wereda_name, "natural")
    soc_strong, soc_weak = get_wereda_grade12_analysis(wereda_name, "social")

    col_nat, col_soc = st.columns(2)
    with col_nat:
        st.markdown(f"""
        <div class="prediction-box" style="border-left-color:#ef4444;background:linear-gradient(180deg,#fef2f2,#fff5f5);">
            <div class="prediction-title" style="color:#b91c1c;">Natural Science Alert</div>
            <div class="prediction-text">
                <b>Strongest Subject:</b> {nat_strong}<br>
                <b>Weakest Subject:</b> {nat_weak}<br><br>
                Grade 12 Natural students are at significant risk of failing <b>{nat_weak}</b>.
                Implement structured instructional monitoring and immediate improvement mechanisms.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_soc:
        st.markdown(f"""
        <div class="prediction-box" style="border-left-color:#ef4444;background:linear-gradient(180deg,#fef2f2,#fff5f5);">
            <div class="prediction-title" style="color:#b91c1c;">Social Science Alert</div>
            <div class="prediction-text">
                <b>Strongest Subject:</b> {soc_strong}<br>
                <b>Weakest Subject:</b> {soc_weak}<br><br>
                Grade 12 Social students exhibit severe deficiencies in <b>{soc_weak}</b>.
                Without targeted intervention, failure rates will rise significantly.
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    inject_kk_css()
    if "kk_page" not in st.session_state:
        st.session_state.kk_page = "home"
    page = st.session_state.kk_page
    if page == "home":
        show_home()
    elif page == "wereda":
        show_wereda_overview(st.session_state.get("kk_wereda", "Wereda 1"))
    else:
        show_home()
