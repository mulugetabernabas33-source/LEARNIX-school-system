"""
Addis Ababa Educational Performance Dashboard
Top-level: compares all 11 Kifle Ketemas.
Drill-down: Wereda-level view per Kifle Ketema. Stops here — no school/class drill-down.
"""

# file connections / imports
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from helpers.aa_data import (
    ADDIS_ABABA_KKS, KK_WEREDAS,
    get_aa_kpi_df, get_aa_overall_kpis, get_kk_summary_kpis,
    get_kk_subjects_focus, get_kk_wereda_df,
    get_aa_heatmap_df, get_kk_wereda_heatmap_df, get_aa_kpi_comparison_df,
)


# inject aa css
def inject_aa_css():
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

        /* Stat Cards */
        .stat-cards { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:18px; margin-bottom:26px; }
        .stat-card  { background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.78); border-radius:22px; padding:22px 22px 18px; box-shadow:0 18px 40px rgba(15,23,42,0.09); min-height:148px; }
        .stat-card .stat-label { color:#0f4c81; font-size:13px; font-weight:800; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px; }
        .stat-card .stat-value { display:block; color:#0f172a; font-size:31px; line-height:1.08; margin:10px 0 12px; font-weight:900; letter-spacing:-0.04em; }
        .stat-card .stat-note  { color:#64748b; font-size:15px; line-height:1.6; margin-top:4px; }

        /* Progress bars */
        .kpi-bar-bg   { background:#e2e8f0; border-radius:4px; height:7px; width:100%; margin-top:8px; }
        .kpi-bar-fill { height:7px; border-radius:4px; }

        /* AA KPI Banner */
        .aa-banner { background:linear-gradient(135deg,#1a0533 0%,#0f172a 35%,#0f4c81 100%); border-radius:24px; padding:30px 34px; margin-bottom:30px; box-shadow:0 24px 52px rgba(15,23,42,0.20); }
        .aa-banner-title { color:#f8fafc; font-size:22px; font-weight:900; letter-spacing:-0.03em; margin-bottom:4px; }
        .aa-banner-sub   { color:rgba(226,232,240,0.72); font-size:13px; margin-bottom:20px; }
        .aa-kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
        .aa-kpi-card { background:rgba(255,255,255,0.09); border:1px solid rgba(255,255,255,0.13); border-radius:16px; padding:16px 18px; }
        .aa-kpi-label { color:#93c5fd; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:6px; }
        .aa-kpi-value { color:#ffffff; font-size:26px; font-weight:900; letter-spacing:-0.04em; }
        .aa-kpi-note  { color:rgba(226,232,240,0.68); font-size:11px; margin-top:3px; }

        /* Highlight cards */
        .highlight-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:18px; margin-bottom:28px; }
        .highlight-card { border-radius:20px; padding:22px 26px; border:1px solid transparent; }
        .highlight-card-best    { background:linear-gradient(135deg,#ecfdf5,#d1fae5); border-color:rgba(22,163,74,0.22); }
        .highlight-card-weakest { background:linear-gradient(135deg,#fef2f2,#fee2e2); border-color:rgba(220,38,38,0.18); }
        .highlight-card-label   { font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:8px; }
        .highlight-card-best .highlight-card-label    { color:#16a34a; }
        .highlight-card-weakest .highlight-card-label { color:#dc2626; }
        .highlight-card-name  { font-size:24px; font-weight:900; color:#0f172a; letter-spacing:-0.03em; margin-bottom:4px; }
        .highlight-card-note  { font-size:14px; color:#64748b; }

        /* KK navigation grid */
        .kk-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:32px; }
        .kk-nav-card { background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.75); border-radius:18px; padding:18px 16px; box-shadow:0 12px 28px rgba(15,23,42,0.07); text-align:center; cursor:pointer; transition:all 0.22s ease; }
        .kk-nav-card:hover { box-shadow:0 20px 42px rgba(15,23,42,0.13); border-color:rgba(59,130,246,0.35); transform:translateY(-3px); }
        .kk-nav-name  { font-size:17px; font-weight:800; color:#0f172a; letter-spacing:-0.02em; margin-bottom:4px; }
        .kk-nav-avg   { font-size:13px; font-weight:700; color:#0f4c81; }
        .kk-nav-badge { display:inline-block; margin-top:8px; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; }
        .kk-nav-badge-high { background:rgba(22,163,74,0.12); color:#16a34a; border:1px solid rgba(22,163,74,0.22); }
        .kk-nav-badge-mid  { background:rgba(59,130,246,0.10); color:#1d4ed8; border:1px solid rgba(59,130,246,0.20); }
        .kk-nav-badge-low  { background:rgba(239,68,68,0.10);  color:#dc2626; border:1px solid rgba(239,68,68,0.20); }

        /* Wereda cards in KK detail view */
        .wereda-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:18px; margin-bottom:24px; }
        .wereda-card { background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.75); border-radius:20px; padding:20px 22px; box-shadow:0 16px 36px rgba(15,23,42,0.08); }
        .wereda-name  { font-size:18px; font-weight:800; color:#0f172a; letter-spacing:-0.02em; margin-bottom:12px; }
        .wereda-kpi-row { display:flex; gap:18px; flex-wrap:wrap; }
        .wereda-kpi-item { flex:1; min-width:90px; }
        .wereda-kpi-lbl { font-size:11px; font-weight:800; color:#0f4c81; text-transform:uppercase; letter-spacing:0.1em; }
        .wereda-kpi-val { font-size:20px; font-weight:900; color:#0f172a; letter-spacing:-0.03em; }

        /* Focus chips */
        .chip-focus   { display:inline-block; padding:5px 12px; border-radius:999px; font-size:12px; font-weight:700; background:rgba(239,68,68,0.11); color:#dc2626; border:1px solid rgba(239,68,68,0.24); margin:3px 4px 3px 0; }
        .chip-warning { display:inline-block; padding:5px 12px; border-radius:999px; font-size:12px; font-weight:700; background:rgba(234,88,12,0.10); color:#ea580c; border:1px solid rgba(234,88,12,0.22); margin:3px 4px 3px 0; }

        /* Prediction / insight boxes */
        .insight-box { background:linear-gradient(180deg,#f0f9ff,#f8fbff); border:1px solid rgba(56,189,248,0.22); border-radius:20px; padding:20px 24px; box-shadow:0 16px 36px rgba(15,23,42,0.08); border-left:5px solid #0f4c81; margin:20px 0 28px; }
        .insight-title { font-size:17px; font-weight:800; color:#0f172a; margin-bottom:8px; }
        .insight-text  { font-size:15px; color:#334155; line-height:1.65; }

        /* Badge */
        .badge { display:inline-flex; align-items:center; padding:5px 12px; border-radius:999px; font-size:13px; font-weight:800; letter-spacing:0.05em; }
        .badge-gold   { background:linear-gradient(180deg,#fef3c7,#fef9e7); color:#b45309; border:1px solid rgba(212,175,55,0.30); }
        .badge-silver { background:linear-gradient(180deg,#f1f5f9,#f8fafc); color:#475569; border:1px solid rgba(168,169,173,0.30); }
        .badge-bronze { background:linear-gradient(180deg,#fed7aa,#fff7ed); color:#9a3412; border:1px solid rgba(205,127,50,0.30); }

        .stButton > button { width:100%; background:#ffffff !important; border:1px solid #e2e8f0 !important; border-radius:10px !important; padding:14px 20px !important; font-size:15px !important; font-weight:600 !important; color:#334155 !important; transition:all 0.2s ease !important; box-shadow:0 1px 2px rgba(0,0,0,0.05) !important; }
        .stButton > button:hover { background:#f8fafc !important; border-color:#94a3b8 !important; color:#0f4c81 !important; transform:translateY(-1px) !important; }

        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
            background:rgba(255,255,255,0.94) !important;
            border:1px solid rgba(203,213,225,0.75) !important;
            border-radius:22px !important;
            box-shadow:0 20px 42px rgba(15,23,42,0.09) !important;
            padding:18px 20px !important;
        }
        @media (max-width:1100px) { .aa-kpi-grid, .stat-cards { grid-template-columns:1fr 1fr !important; } .kk-grid { grid-template-columns:1fr 1fr 1fr !important; } }
        @media (max-width:768px)  { .aa-kpi-grid, .stat-cards, .kk-grid { grid-template-columns:1fr !important; } }
    </style>
    """, unsafe_allow_html=True)


# navigate to
def navigate_to(page):
    st.session_state.aa_page = page
    st.rerun()


# navigate to kk
def navigate_to_kk(kk_name):
    st.session_state.aa_page = "kk"
    st.session_state.aa_kk   = kk_name
    st.rerun()


if "aa_page" not in st.session_state:
    st.session_state.aa_page = "home"


# bar
def _bar(color, pct):
    w = min(max(float(pct), 0), 100)
    return (f'<div class="kpi-bar-bg">'
            f'<div class="kpi-bar-fill" style="background:{color};width:{w}%;"></div>'
            f'</div>')


# pass color
def _pass_color(v):
    if v >= 85: return "linear-gradient(90deg,#16a34a,#22c55e)"
    if v >= 70: return "linear-gradient(90deg,#ca8a04,#facc15)"
    return "linear-gradient(90deg,#dc2626,#f87171)"


# level badge
def _level_badge(avg):
    if avg >= 78:
        return '<span class="kk-nav-badge kk-nav-badge-high">High</span>'
    if avg >= 73:
        return '<span class="kk-nav-badge kk-nav-badge-mid">Average</span>'
    return '<span class="kk-nav-badge kk-nav-badge-low">Needs Focus</span>'


# show home
def show_home():
    st.markdown('<div class="page-title">Addis Ababa Educational Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">City-wide academic overview across all 11 Kifle Ketemas. Click a Kifle Ketema to explore Wereda-level performance.</div>', unsafe_allow_html=True)

    aa   = get_aa_overall_kpis()
    df   = get_aa_kpi_df()

    st.markdown(f"""
    <div class="aa-banner">
        <div class="aa-banner-title">Addis Ababa — City Academic Dashboard</div>
        <div class="aa-banner-sub">Aggregated across all 11 Kifle Ketemas, {len(KK_WEREDAS)} Weredas, and constituent schools</div>
        <div class="aa-kpi-grid">
            <div class="aa-kpi-card">
                <div class="aa-kpi-label">Overall Avg Score</div>
                <div class="aa-kpi-value">{aa['overall_avg']}%</div>
                <div class="aa-kpi-note">All KKs combined</div>
            </div>
            <div class="aa-kpi-card">
                <div class="aa-kpi-label">Pass Rate</div>
                <div class="aa-kpi-value">{aa['pass_rate']}%</div>
                <div class="aa-kpi-note">Students ≥ 60% avg</div>
            </div>
            <div class="aa-kpi-card">
                <div class="aa-kpi-label">Distinction Rate</div>
                <div class="aa-kpi-value">{aa['distinction_rate']}%</div>
                <div class="aa-kpi-note">Students ≥ 75% avg</div>
            </div>
            <div class="aa-kpi-card">
                <div class="aa-kpi-label">At-Risk Students</div>
                <div class="aa-kpi-value">{aa['at_risk']}%</div>
                <div class="aa-kpi-note">Below pass threshold</div>
            </div>
            <div class="aa-kpi-card">
                <div class="aa-kpi-label">Top Performer Rate</div>
                <div class="aa-kpi-value">{aa['top_performer_rate']}%</div>
                <div class="aa-kpi-note">Students ≥ 85% avg</div>
            </div>
            <div class="aa-kpi-card">
                <div class="aa-kpi-label">Term Improvement</div>
                <div class="aa-kpi-value">+{aa['improvement']}%</div>
                <div class="aa-kpi-note">Q1 → Q2 city average</div>
            </div>
            <div class="aa-kpi-card">
                <div class="aa-kpi-label">Kifle Ketemas</div>
                <div class="aa-kpi-value">{aa['total_kks']}</div>
                <div class="aa-kpi-note">Administrative divisions</div>
            </div>
            <div class="aa-kpi-card">
                <div class="aa-kpi-label">Total Weredas</div>
                <div class="aa-kpi-value">{sum(len(v) for v in KK_WEREDAS.values())}</div>
                <div class="aa-kpi-note">Sub-districts monitored</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    best_row = df.loc[df["overall_avg"].idxmax()]
    weak_row = df.loc[df["overall_avg"].idxmin()]
    st.markdown(f"""
    <div class="highlight-grid">
        <div class="highlight-card highlight-card-best">
            <div class="highlight-card-label">🏆 Top Performing Kifle Ketema</div>
            <div class="highlight-card-name">{best_row['Kifle Ketema']}</div>
            <div class="highlight-card-note">Average: {best_row['overall_avg']}% &nbsp;|&nbsp; Pass Rate: {best_row['pass_rate']}% &nbsp;|&nbsp; Distinction: {best_row['distinction_rate']}%</div>
        </div>
        <div class="highlight-card highlight-card-weakest">
            <div class="highlight-card-label">⚠️ Needs Immediate Attention</div>
            <div class="highlight-card-name">{weak_row['Kifle Ketema']}</div>
            <div class="highlight-card-note">Average: {weak_row['overall_avg']}% &nbsp;|&nbsp; At-Risk: {weak_row['at_risk']}% &nbsp;|&nbsp; Pass Rate: {weak_row['pass_rate']}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Select a Kifle Ketema</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:15px;margin:-8px 0 20px;">Click any Kifle Ketema to view detailed Wereda-level performance analytics.</p>', unsafe_allow_html=True)

    kk_avgs = dict(zip(df["Kifle Ketema"], df["overall_avg"]))
    kk_pass = dict(zip(df["Kifle Ketema"], df["pass_rate"]))

    rows_of_kks = [ADDIS_ABABA_KKS[i:i+4] for i in range(0, len(ADDIS_ABABA_KKS), 4)]
    for row_kks in rows_of_kks:
        cols = st.columns(len(row_kks))
        for col, kk in zip(cols, row_kks):
            avg = kk_avgs.get(kk, 0)
            badge = "High" if avg >= 78 else ("Average" if avg >= 73 else "Needs Focus")
            badge_color = "#16a34a" if avg >= 78 else ("#1d4ed8" if avg >= 73 else "#dc2626")
            with col:
                st.markdown(f"""
                <div class="kk-nav-card" style="margin-bottom:0;">
                    <div class="kk-nav-name">{kk}</div>
                    <div class="kk-nav-avg">Avg: {avg}%</div>
                    <div style="margin-top:8px;">
                        <span class="kk-nav-badge" style="color:{badge_color};background:rgba(0,0,0,0.04);border:1px solid {badge_color}44;">{badge}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Open {kk}", key=f"aa_kk_{kk}", use_container_width=True):
                    navigate_to_kk(kk)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:36px 0;'>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Overall Score Comparison — All Kifle Ketemas</div>', unsafe_allow_html=True)

    chart_df = df[["Kifle Ketema", "overall_avg", "pass_rate", "at_risk"]].sort_values("overall_avg", ascending=False)
    fig_bar = px.bar(
        chart_df, x="Kifle Ketema", y="overall_avg",
        color="overall_avg", color_continuous_scale="Blues",
        text="overall_avg", title="Average Academic Score per Kifle Ketema",
    )
    fig_bar.update_layout(
        yaxis_range=[60, 92], plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#334155"), coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown('<div class="section-title">Pass Rate & At-Risk Comparison</div>', unsafe_allow_html=True)
    fig_multi = go.Figure()
    fig_multi.add_bar(name="Pass Rate (%)",   x=chart_df["Kifle Ketema"], y=chart_df["pass_rate"],
                      marker_color="#3b82f6", text=chart_df["pass_rate"],
                      texttemplate="%{text:.1f}%", textposition="outside")
    fig_multi.add_bar(name="At-Risk (%)",     x=chart_df["Kifle Ketema"], y=chart_df["at_risk"],
                      marker_color="#f87171",  text=chart_df["at_risk"],
                      texttemplate="%{text:.1f}%", textposition="outside")
    fig_multi.update_layout(
        barmode="group", yaxis_range=[0, 110],
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#334155"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=20, r=20, t=50, b=20),
        title="Pass Rate vs At-Risk Students by Kifle Ketema",
    )
    st.plotly_chart(fig_multi, use_container_width=True)

    st.markdown('<div class="section-title">Subject Performance Heatmap (Kifle Ketema × Subject)</div>', unsafe_allow_html=True)
    heat_df = get_aa_heatmap_df().set_index("Kifle Ketema")
    fig_heat = px.imshow(
        heat_df, color_continuous_scale="RdYlGn", text_auto=True,
        title="Average Subject Score per Kifle Ketema",
        labels=dict(x="Subject", y="Kifle Ketema", color="Score"),
        aspect="auto", zmin=60, zmax=93,
    )
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#334155"),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('<div class="section-title">Kifle Ketema KPI Comparison Table</div>', unsafe_allow_html=True)
    cmp_df = get_aa_kpi_comparison_df()
    st.dataframe(cmp_df, use_container_width=True, hide_index=True)

    st.markdown("""
    <div style='margin-top:40px; padding-top:20px; border-top:1px solid rgba(203,213,225,0.5);
                text-align:center; color:#94a3b8; font-size:13px;'>
        Addis Ababa City Education Analytics · Data is deterministic and realistic · Drill-down stops at Wereda level
    </div>
    """, unsafe_allow_html=True)


# show kk overview
def show_kk_overview(kk_name: str):
    st.markdown('<div class="back-button-area">', unsafe_allow_html=True)
    if st.button("← Back to Addis Ababa Dashboard", key="aa_back_btn"):
        navigate_to("home")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="page-title">{kk_name} Kifle Ketema</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">Wereda-level performance overview within {kk_name}. Data stops at Wereda level — school and class analytics are available through the Wereda role.</div>', unsafe_allow_html=True)

    kpis = get_kk_summary_kpis(kk_name)
    focus_subjects = get_kk_subjects_focus(kk_name)
    focus_chips = "".join(f'<span class="chip-focus">{s}</span>' for s in focus_subjects)

    st.markdown(f"""
    <div class="stat-cards">
        <div class="stat-card">
            <div class="stat-label">KK Average Score</div>
            <div class="stat-value">{kpis.get('overall_avg', 0)}%</div>
            <div class="stat-note">Across all Weredas</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Pass Rate</div>
            <div class="stat-value" style="color:#16a34a;">{kpis.get('pass_rate', 0)}%</div>
            {_bar(_pass_color(kpis.get('pass_rate', 0)), kpis.get('pass_rate', 0))}
            <div class="stat-note">Students ≥ 60% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Distinction Rate</div>
            <div class="stat-value" style="color:#7c3aed;">{kpis.get('distinction_rate', 0)}%</div>
            {_bar("linear-gradient(90deg,#7c3aed,#a855f7)", kpis.get('distinction_rate', 0))}
            <div class="stat-note">Students ≥ 75% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">At-Risk Students</div>
            <div class="stat-value" style="color:#ea580c;">{kpis.get('at_risk', 0)}%</div>
            {_bar("linear-gradient(90deg,#ea580c,#fb923c)", kpis.get('at_risk', 0))}
            <div class="stat-note">Below pass threshold</div>
        </div>
    </div>
    <div class="stat-cards" style="grid-template-columns:repeat(3,minmax(0,1fr));">
        <div class="stat-card">
            <div class="stat-label">Top Performer Rate</div>
            <div class="stat-value" style="color:#0f4c81;">{kpis.get('top_performer_rate', 0)}%</div>
            {_bar("linear-gradient(90deg,#0f4c81,#3b82f6)", kpis.get('top_performer_rate', 0))}
            <div class="stat-note">Students ≥ 85% avg</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Term Improvement</div>
            <div class="stat-value" style="color:#0891b2;">+{kpis.get('improvement', 0)}%</div>
            <div class="stat-note">Q1 → Q2 average change</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Subjects Needing Focus</div>
            <div style="margin-top:10px;">{focus_chips}</div>
            <div class="stat-note" style="margin-top:8px;">Lowest KK-wide averages</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    w_df = get_kk_wereda_df(kk_name)
    top_w    = w_df.loc[w_df["overall_avg"].idxmax(), "Wereda"]
    weak_w   = w_df.loc[w_df["overall_avg"].idxmin(), "Wereda"]
    top_avg  = w_df["overall_avg"].max()
    weak_avg = w_df["overall_avg"].min()

    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">Wereda Performance Insight — {kk_name}</div>
        <div class="insight-text">
            The highest performing Wereda in {kk_name} is <b>{top_w}</b> with an average of <b>{top_avg:.1f}%</b>.
            <b>{weak_w}</b> is underperforming at <b>{weak_avg:.1f}%</b> and requires focused academic support,
            additional teacher training resources, and targeted student intervention plans.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Wereda Performance Comparison</div>', unsafe_allow_html=True)
    chart_w = w_df[["Wereda", "overall_avg", "pass_rate", "at_risk"]].sort_values("overall_avg", ascending=False)

    fig_w = px.bar(
        chart_w, x="Wereda", y="overall_avg", color="overall_avg",
        color_continuous_scale="Teal", text="overall_avg",
        title=f"Average Score per Wereda — {kk_name}",
    )
    fig_w.update_layout(
        yaxis_range=[55, 95], plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#334155"), coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig_w.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
    st.plotly_chart(fig_w, use_container_width=True)

    st.markdown('<div class="section-title">Pass Rate & At-Risk Per Wereda</div>', unsafe_allow_html=True)
    fig_w2 = go.Figure()
    fig_w2.add_bar(name="Pass Rate (%)", x=chart_w["Wereda"], y=chart_w["pass_rate"],
                   marker_color="#3b82f6", text=chart_w["pass_rate"],
                   texttemplate="%{text:.1f}%", textposition="outside")
    fig_w2.add_bar(name="At-Risk (%)", x=chart_w["Wereda"], y=chart_w["at_risk"],
                   marker_color="#f87171", text=chart_w["at_risk"],
                   texttemplate="%{text:.1f}%", textposition="outside")
    fig_w2.update_layout(
        barmode="group", yaxis_range=[0, 115],
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#334155"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=20, r=20, t=50, b=20),
        title=f"Pass Rate vs At-Risk Students — {kk_name} Weredas",
    )
    st.plotly_chart(fig_w2, use_container_width=True)

    st.markdown('<div class="section-title">Subject Performance Heatmap (Wereda × Subject)</div>', unsafe_allow_html=True)
    heat_df = get_kk_wereda_heatmap_df(kk_name).set_index("Wereda")
    fig_heat = px.imshow(
        heat_df, color_continuous_scale="RdYlGn", text_auto=True,
        title=f"Average Subject Score per Wereda — {kk_name}",
        labels=dict(x="Subject", y="Wereda", color="Score"),
        aspect="auto", zmin=60, zmax=95,
    )
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#334155"),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('<div class="section-title">Wereda-Level KPI Comparison Table</div>', unsafe_allow_html=True)
    table_df = w_df[[
        "Wereda", "overall_avg", "pass_rate", "distinction_rate",
        "at_risk", "top_performer_rate", "improvement", "Subjects Needing Focus"
    ]].rename(columns={
        "overall_avg":        "Avg Score",
        "pass_rate":          "Pass Rate (%)",
        "distinction_rate":   "Distinction (%)",
        "at_risk":            "At-Risk (%)",
        "top_performer_rate": "Top Performer (%)",
        "improvement":        "Improvement (%)",
    }).sort_values("Avg Score", ascending=False).reset_index(drop=True)
    st.dataframe(table_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Top 3 Performing Weredas</div>', unsafe_allow_html=True)
    top3_w = w_df.nlargest(3, "overall_avg").reset_index(drop=True)
    pod_cols = st.columns(3)
    for i, (col, (_, row)) in enumerate(zip(pod_cols, top3_w.iterrows())):
        with col:
            rank = i + 1
            badge_cls, badge_txt = (
                ("badge-gold",   "🥇 1st Place") if rank == 1 else
                ("badge-silver", "🥈 2nd Place") if rank == 2 else
                ("badge-bronze", "🥉 3rd Place")
            )
            st.markdown(f"""
            <div class="stat-card" style="text-align:center;min-height:auto;padding:24px;">
                <span class="badge {badge_cls}" style="margin-bottom:12px;">{badge_txt}</span>
                <div style="font-size:22px;font-weight:900;color:#0f172a;margin:10px 0 6px;">{row['Wereda']}</div>
                <div style="font-size:28px;font-weight:900;color:#0f4c81;letter-spacing:-0.04em;">{row['overall_avg']:.1f}%</div>
                <div style="color:#64748b;font-size:14px;margin-top:4px;">Pass: {row['pass_rate']:.1f}% &nbsp;|&nbsp; Dist: {row['distinction_rate']:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style='margin-top:40px; padding-top:20px; border-top:1px solid rgba(203,213,225,0.5);
                text-align:center; color:#94a3b8; font-size:13px;'>
        Drill-down stops here. Access individual school and class analytics through the Wereda or School Administration role.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    inject_aa_css()
    if "aa_page" not in st.session_state:
        st.session_state.aa_page = "home"
    page = st.session_state.aa_page
    if page == "home":
        show_home()
    elif page == "kk":
        show_kk_overview(st.session_state.get("aa_kk", ADDIS_ABABA_KKS[0]))
    else:
        show_home()
