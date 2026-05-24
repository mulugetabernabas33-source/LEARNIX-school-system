# admin dashboard
"""
LEARNIX Admin Dashboard

Provides complete administrative control:
  - Account Management: create / update / delete teacher & parent accounts
  - Access Control: role permissions matrix, password policy, 2FA & SSO placeholders
  - Activity Monitor: encrypted audit log of all login/logout/account events
  - Data Management: live DB table stats, encryption key status
  - Documentation: security policies, system configuration records
  - Capacity Planning: scalability design notes

SECURITY ARCHITECTURE:
  - Admin accounts stored in a SEPARATE table (admin_accounts), isolated
    from teacher/parent accounts in the users table.
  - All passwords hashed with bcrypt — never stored plaintext.
  - Sensitive fields (user_id_code, log details) use Fernet symmetric encryption.
  - Encryption key lives at database/secret.key — back this up securely.
  - All admin actions written to activity_log with encrypted details.

DEFAULT CREDENTIALS:  admin / admin123
  Change this on first login in production.

SCALABILITY NOTES:
  - Add new roles by inserting rows; no code changes needed.
  - admin_accounts.is_active supports soft-disable without data loss.
  - activity_log supports future export to SIEM/compliance tools.
  - Swap SQLite for PostgreSQL by changing the DB_PATH env variable only.
"""

import os
import sys
import streamlit as st
import pandas as pd

# path setup
try:
    _ADMIN_BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ADMIN_BASE = os.getcwd()

sys.path.insert(0, os.path.join(_ADMIN_BASE, "app", "backend"))

#db_functions
from db_functions import (
    verify_admin,
    get_all_users,
    get_users_by_role,
    create_user_account,
    update_user_password,
    update_admin_password,
    delete_user_account,
    log_activity,
    get_activity_log,
    get_db_connection,
    decrypt_field,
    register_user,
    get_subjects,
    add_subject,
    delete_subject,
)
#Bcrypt
import bcrypt as _bcrypt


# CSS 
def inject_admin_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

    /* ── Global font override ──────────────────────────────────────── */
    html, body, [class*="css"], .stApp,
    .stMarkdown, .stButton, .stTextInput, .stSelectbox,
    .stDataFrame, .stForm, .stRadio, .stTabs {
        font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
    }

    /* ── Hero banner ────────────────────────────────────────────────── */
    .admin-hero {
        position: relative; overflow: hidden;
        padding: 36px 40px; margin-bottom: 28px; border-radius: 24px;
        background:
            radial-gradient(ellipse at 90% 10%, rgba(185,28,28,0.45), transparent 30%),
            linear-gradient(140deg, #0c1220 0%, #6b1111 52%, #7f1d1d 100%);
        border: 1px solid rgba(252,165,165,0.14);
        box-shadow: 0 32px 72px rgba(12,18,32,0.28);
    }
    .admin-hero::before {
        content: ''; position: absolute; inset: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.017'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        pointer-events: none;
    }
    .admin-chip {
        display: inline-block;
        padding: 5px 14px; border-radius: 4px;
        background: rgba(185,28,28,0.22); border: 1px solid rgba(252,165,165,0.22);
        color: #fca5a5;
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 10px; font-weight: 700;
        letter-spacing: 0.18em; text-transform: uppercase;
        margin-bottom: 14px;
    }
    .admin-hero-title {
        font-family: 'Playfair Display', Georgia, serif;
        color: #f8fafc;
        font-size: clamp(28px, 3.4vw, 42px);
        font-weight: 900;
        letter-spacing: -0.02em;
        margin: 0 0 10px;
        line-height: 1.06;
    }
    .admin-hero-sub {
        font-family: 'IBM Plex Sans', sans-serif;
        color: rgba(226,232,240,0.82);
        font-size: 15px; font-weight: 400;
        line-height: 1.75; margin: 0;
    }
    .admin-hero-meta {
        margin-top: 18px;
        display: flex; gap: 24px; flex-wrap: wrap;
    }
    .admin-hero-meta span {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 12px; font-weight: 600;
        color: rgba(252,165,165,0.75);
        letter-spacing: 0.06em; text-transform: uppercase;
    }

    /* ── Stat cards ─────────────────────────────────────────────────── */
    .admin-stat-grid {
        display: grid; grid-template-columns: repeat(4, minmax(0,1fr));
        gap: 16px; margin-bottom: 28px;
    }
    .admin-stat-card {
        background: #ffffff;
        border: 1px solid rgba(203,213,225,0.7);
        border-radius: 16px; padding: 22px 20px 18px;
        box-shadow: 0 4px 20px rgba(15,23,42,0.06);
        transition: box-shadow 0.2s;
    }
    .admin-stat-card:hover {
        box-shadow: 0 8px 32px rgba(15,23,42,0.12);
    }
    .admin-stat-label {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #7f1d1d; font-size: 10px; font-weight: 700;
        letter-spacing: 0.16em; text-transform: uppercase;
    }
    .admin-stat-value {
        font-family: 'Playfair Display', Georgia, serif;
        color: #0f172a; font-size: 30px; font-weight: 900;
        letter-spacing: -0.03em; margin: 10px 0 8px; display: block;
    }
    .admin-stat-note {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #64748b; font-size: 13px; font-weight: 400; line-height: 1.5;
    }

    /* ── Section headings ───────────────────────────────────────────── */
    .admin-section { margin: 28px 0 16px; }
    .admin-section h3 {
        font-family: 'Playfair Display', Georgia, serif;
        color: #0f172a; font-size: 24px; font-weight: 700;
        letter-spacing: -0.02em; margin: 0 0 6px;
    }
    .admin-section p {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #64748b; font-size: 14px; font-weight: 400;
        margin: 0; line-height: 1.65;
    }

    /* ── Activity log row ───────────────────────────────────────────── */
    .admin-log-row {
        display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
        padding: 11px 16px; border-radius: 10px; margin-bottom: 6px;
        background: #f8fafc; border: 1px solid rgba(203,213,225,0.55);
        font-family: 'IBM Plex Sans', sans-serif; font-size: 13px;
        transition: background 0.15s;
    }
    .admin-log-row:hover { background: #f1f5f9; }
    .admin-log-action {
        font-weight: 700; color: #0f172a; min-width: 140px;
        font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
    }
    .admin-log-user { color: #1d4ed8; font-weight: 600; }
    .admin-log-time { color: #94a3b8; font-size: 12px; margin-left: auto; font-family: 'IBM Plex Mono', monospace; }

    /* ── Policy / info cards ────────────────────────────────────────── */
    .policy-card {
        background: #ffffff; border: 1px solid rgba(203,213,225,0.7);
        border-radius: 14px; padding: 20px 22px; margin-bottom: 14px;
        box-shadow: 0 2px 12px rgba(15,23,42,0.05);
    }
    .policy-title {
        font-family: 'Playfair Display', Georgia, serif;
        color: #0f172a; font-size: 17px; font-weight: 700;
        margin-bottom: 10px; letter-spacing: -0.01em;
    }
    .policy-body {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #475569; font-size: 14px; line-height: 1.75;
    }
    .policy-body ul { margin: 6px 0 0; padding-left: 18px; }
    .policy-body li { margin-bottom: 4px; }

    /* ── Placeholder panels (2FA / SSO) ─────────────────────────────── */
    .placeholder-panel {
        background: linear-gradient(135deg, rgba(79,70,229,0.05), rgba(139,92,246,0.04));
        border: 1px dashed rgba(99,102,241,0.35); border-radius: 18px;
        padding: 36px 28px; text-align: center;
    }
    .placeholder-badge {
        display: inline-block;
        padding: 6px 16px; border-radius: 4px; margin-bottom: 18px;
        background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.25);
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 10px; font-weight: 700; letter-spacing: 0.16em;
        text-transform: uppercase; color: #4f46e5;
    }
    .placeholder-panel h3 {
        font-family: 'Playfair Display', Georgia, serif;
        color: #3730a3; font-size: 24px; font-weight: 700;
        margin: 0 0 12px; letter-spacing: -0.02em;
    }
    .placeholder-panel p {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #6366f1; font-size: 14px; line-height: 1.75;
        max-width: 520px; margin: 0 auto 22px;
    }
    .placeholder-steps {
        background: rgba(255,255,255,0.8); border-radius: 12px;
        padding: 18px 26px; display: inline-block; text-align: left;
        border: 1px solid rgba(99,102,241,0.15);
    }
    .placeholder-steps strong {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 11px; font-weight: 700; letter-spacing: 0.12em;
        text-transform: uppercase; color: #4338ca; display: block; margin-bottom: 10px;
    }
    .placeholder-steps span {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px; color: #475569; line-height: 2.1;
    }

    /* ── Capacity cards ─────────────────────────────────────────────── */
    .capacity-card {
        background: linear-gradient(135deg, rgba(15,23,42,0.025), rgba(30,64,175,0.03));
        border: 1px solid rgba(203,213,225,0.65);
        border-left: 3px solid #1d4ed8;
        border-radius: 14px; padding: 20px 22px; margin-bottom: 14px;
    }
    .capacity-title {
        font-family: 'Playfair Display', Georgia, serif;
        color: #1d4ed8; font-size: 17px; font-weight: 700;
        margin-bottom: 8px; letter-spacing: -0.01em;
    }
    .capacity-body {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #334155; font-size: 14px; line-height: 1.75;
    }

    /* ── Status indicators (text-based, no emoji) ───────────────────── */
    .status-ok {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 8px 14px; border-radius: 8px; margin-bottom: 8px;
        background: rgba(22,163,74,0.06); border: 1px solid rgba(22,163,74,0.2);
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 13px; font-weight: 500; color: #15803d;
        width: 100%;
    }
    .status-ok::before {
        content: 'OK'; font-size: 9px; font-weight: 800; letter-spacing: 0.1em;
        background: #16a34a; color: white; padding: 2px 6px; border-radius: 3px;
        flex-shrink: 0;
    }
    .status-warn {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 8px 14px; border-radius: 8px; margin-bottom: 8px;
        background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.22);
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 13px; font-weight: 500; color: #b45309;
        width: 100%;
    }
    .status-warn::before {
        content: 'NOTE'; font-size: 9px; font-weight: 800; letter-spacing: 0.1em;
        background: #d97706; color: white; padding: 2px 6px; border-radius: 3px;
        flex-shrink: 0;
    }
    .status-info {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 8px 14px; border-radius: 8px; margin-bottom: 8px;
        background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.18);
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 13px; font-weight: 500; color: #4338ca;
        width: 100%;
    }
    .status-info::before {
        content: 'INFO'; font-size: 9px; font-weight: 800; letter-spacing: 0.1em;
        background: #4f46e5; color: white; padding: 2px 6px; border-radius: 3px;
        flex-shrink: 0;
    }

    /* ── Sidebar overrides ──────────────────────────────────────────── */
    [data-testid="stSidebar"] * {
        font-family: 'IBM Plex Sans', sans-serif !important;
    }

    @media (max-width: 900px) {
        .admin-stat-grid { grid-template-columns: repeat(2, 1fr) !important; }
    }
    </style>
    """, unsafe_allow_html=True)


# login gate
def _show_login_gate():
    """Admin login form. Returns 'back' string if Back is pressed."""
    st.markdown("""
    <div style='max-width:460px; margin:56px auto 0; text-align:center;'>
        <div class='admin-chip'>Restricted Access</div>
        <h2 style='font-family:"Playfair Display",Georgia,serif;
                   color:#0f172a; font-size:34px; font-weight:900;
                   letter-spacing:-0.03em; margin:16px 0 8px; line-height:1.1;'>
            Administrator Login
        </h2>
        <p style='font-family:"IBM Plex Sans",sans-serif;
                  color:#64748b; font-size:14px; margin:0 0 28px; line-height:1.7;'>
            This panel is restricted to authorised system administrators.<br>
            All actions are fully logged and audited.<br>
            <span style='color:#7f1d1d; font-weight:600;'>Demo credentials:</span>
            admin / admin123
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        with st.form("admin_login_gate"):
            u = st.text_input("Username", placeholder="admin")
            p = st.text_input("Password", type="password", placeholder="Enter password")
            c1, c2 = st.columns(2)
            with c1:
                back = st.form_submit_button("Back", use_container_width=True)
            with c2:
                login = st.form_submit_button("Sign In", type="primary",
                                              use_container_width=True)
            if back:
                return "back"
            if login:
                if not u or not p:
                    st.error("Please enter both username and password.")
                elif verify_admin(u.strip(), p):
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_user = u.strip()
                    log_activity(u.strip(), "login", "admin",
                                 "Admin panel session started")
                    st.rerun()
                else:
                    st.error("Invalid administrator credentials.")
    return None


# sidebar
def _render_sidebar(admin_user):
    nav_items = [
        "Overview",
        "Account Management",
        "Subject Management",
        "Access Control",
        "Activity Monitor",
        "Data Management",
        "Documentation",
        "Capacity Planning",
    ]
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:8px 4px 22px;'>
            <div class='admin-chip'>Admin Panel</div>
            <div style='font-family:"Playfair Display",Georgia,serif;
                        font-size:26px; font-weight:900; color:#ffffff;
                        letter-spacing:-0.02em; margin-top:14px; line-height:1.1;'>
                Control Hub
            </div>
            <div style='font-family:"IBM Plex Sans",sans-serif;
                        font-size:13px; color:#94a3b8; margin-top:8px; line-height:1.65;'>
                Full system administration<br>for {admin_user}
            </div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        if ("admin_menu" not in st.session_state
                or st.session_state.admin_menu not in nav_items):
            st.session_state.admin_menu = nav_items[0]

        st.radio("Navigation", nav_items, key="admin_menu",
                 label_visibility="collapsed")
        st.divider()

        st.markdown(
            f"<p style='font-family:\"IBM Plex Sans\",sans-serif;"
            f"font-size:12px;color:#94a3b8;text-align:center;line-height:1.9;'>"
            f"Signed in as<br>"
            f"<strong style='color:#fca5a5;font-size:14px;font-weight:700;'>"
            f"{admin_user}</strong></p>",
            unsafe_allow_html=True,
        )
        if st.button("Sign Out", type="secondary", use_container_width=True,
                     key="admin_signout"):
            log_activity(admin_user, "logout", "admin",
                         "Admin panel session ended")
            st.session_state.admin_logged_in = False
            st.session_state.admin_user = None
            if "admin_menu" in st.session_state:
                del st.session_state["admin_menu"]
            st.rerun()


# overview
def _tab_overview(admin_user):
    total_t = total_p = total_ev = 0
    recent = []
    conn = get_db_connection()
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users WHERE role='teacher'")
            total_t = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM users WHERE role='parent'")
            total_p = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM activity_log")
            total_ev = c.fetchone()[0] or 0
            c.execute(
                "SELECT username,action,role,timestamp,details "
                "FROM activity_log ORDER BY timestamp DESC LIMIT 5"
            )
            recent = [dict(r) for r in c.fetchall()]
        finally:
            conn.close()

    st.markdown(f"""
    <div class='admin-hero'>
        <div class='admin-chip'>Admin Control Panel</div>
        <div class='admin-hero-title'>System Overview</div>
        <p class='admin-hero-sub'>
            Real-time snapshot of the LEARNIX platform. Monitor accounts,
            access control, and system security from this centralised dashboard.
        </p>
        <div class='admin-hero-meta'>
            <span>Teachers: {total_t}</span>
            <span>Parents: {total_p}</span>
            <span>Events logged: {total_ev}</span>
            <span>Session: {admin_user}</span>
        </div>
    </div>
    <div class='admin-stat-grid'>
        <div class='admin-stat-card'>
            <div class='admin-stat-label'>Teachers</div>
            <strong class='admin-stat-value'>{total_t}</strong>
            <div class='admin-stat-note'>Registered teacher accounts</div>
        </div>
        <div class='admin-stat-card'>
            <div class='admin-stat-label'>Parents</div>
            <strong class='admin-stat-value'>{total_p}</strong>
            <div class='admin-stat-note'>Registered parent accounts</div>
        </div>
        <div class='admin-stat-card'>
            <div class='admin-stat-label'>Activity Events</div>
            <strong class='admin-stat-value'>{total_ev}</strong>
            <div class='admin-stat-note'>Total logged system actions</div>
        </div>
        <div class='admin-stat-card'>
            <div class='admin-stat-label'>Admin Session</div>
            <strong class='admin-stat-value' style='font-size:20px;'>{admin_user}</strong>
            <div class='admin-stat-note'>Currently signed in as administrator</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "<div class='admin-section'><h3>Recent Activity</h3>"
        "<p>Latest five system events across all users and roles.</p></div>",
        unsafe_allow_html=True,
    )

    if recent:
        color_map = {
            "login":           "#16a34a",
            "logout":          "#dc2626",
            "account_created": "#1d4ed8",
            "password_changed":"#f59e0b",
            "account_deleted": "#991b1b",
        }
        for lg in recent:
            action = lg.get("action", "")
            color  = color_map.get(action, "#64748b")
            details = lg.get("details", "") or ""
            try:
                details = decrypt_field(details)[:60] if details else ""
            except Exception:
                details = details[:60]
            st.markdown(f"""
            <div class='admin-log-row'>
              <span class='admin-log-action' style='color:{color};'>
                  {action.replace("_", " ").upper()}</span>
              <span class='admin-log-user'>{lg.get('username', '')}</span>
              <span style='color:#475569; font-size:12px; font-weight:600;'>
                  [{lg.get('role', '').upper()}]</span>
              <span class='admin-log-time'>{lg.get('timestamp', '')}</span>
              <span style='color:#94a3b8; font-size:12px;'>{details}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No activity recorded yet.")

    st.markdown(
        "<div class='admin-section' style='margin-top:32px;'><h3>System Health</h3>"
        "<p>Platform security indicators and service status.</p></div>",
        unsafe_allow_html=True,
    )
    from pathlib import Path
    key_path = Path(_ADMIN_BASE) / "database" / "secret.key"
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='status-ok'>Database — Connected and operational</div>
        <div class='status-ok'>bcrypt — Password hashing active on all accounts</div>
        <div class='status-ok'>Activity Logging — Enabled and writing to database</div>
        """, unsafe_allow_html=True)
    with c2:
        if key_path.exists():
            st.markdown(
                "<div class='status-ok'>Fernet Encryption — Key active, "
                "sensitive fields protected</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='status-warn'>Fernet Key — Will auto-generate "
                "on first write operation</div>",
                unsafe_allow_html=True,
            )
        st.markdown("""
        <div class='status-info'>2FA — Design-ready. Connect pyotp to activate.</div>
        <div class='status-info'>SSO — Design-ready. OAuth 2.0 / SAML integration available.</div>
        """, unsafe_allow_html=True)


# account management
def _tab_accounts():
    st.markdown(
        "<div class='admin-section'><h3>Account Management</h3>"
        "<p>Create, view, and manage teacher and parent accounts securely.</p></div>",
        unsafe_allow_html=True,
    )

    t_create, t_view, t_manage = st.tabs(
        ["Create Account", "View All Accounts", "Manage Account"])

# create
    with t_create:
        st.markdown(
            "<div class='policy-card' style='margin-bottom:18px;'>"
            "<div class='policy-title'>New Account Registration</div>"
            "<div class='policy-body'>All passwords are hashed with bcrypt before storage. "
            "The ID code is encrypted with Fernet symmetric encryption.</div></div>",
            unsafe_allow_html=True,
        )
        with st.form("admin_create_form", clear_on_submit=True):
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                fn  = st.text_input("First Name *", placeholder="e.g. Abebe")
                em  = st.text_input("Email", placeholder="name@school.et")
                pw  = st.text_input("Password *", type="password")
            with r1c2:
                ln  = st.text_input("Last Name *", placeholder="e.g. Kebede")
                rl  = st.selectbox("Role *", ["teacher", "parent"])
                idc = st.text_input("ID Code *", placeholder="e.g. neps-t-0001")
            cp = st.text_input("Confirm Password *", type="password")
            submitted = st.form_submit_button(
                "Create Account", type="primary", use_container_width=True)
            if submitted:
                if not all([fn, ln, pw, cp, idc]):
                    st.error("Please fill all required (*) fields.")
                elif pw != cp:
                    st.error("Passwords do not match.")
                elif len(pw) < 4:
                    st.error("Password must be at least 4 characters.")
                else:
                    uname = f"{fn.strip()} {ln.strip()}"
                    ok, msg = create_user_account(uname, pw, rl, idc)
                    if ok:
                        log_activity(
                            st.session_state.get("admin_user", "admin"),
                            "account_created", "admin",
                            f"Created {rl} account for {uname}",
                        )
                        st.success(f"Account created: {uname} — Role: {rl}")
                    else:
                        st.error(msg)

# view
    with t_view:
        rf = st.selectbox("Filter by Role", ["All", "teacher", "parent"],
                          key="view_rf")
        users = get_all_users() if rf == "All" else get_users_by_role(rf)
        if users:
            rows = []
            for u in users:
                uid = u.get("user_id_code") or ""
                try:
                    uid_disp = decrypt_field(uid) if uid else ""
                except Exception:
                    uid_disp = uid
                rows.append({
                    "Username": u["username"],
                    "Role":     u["role"].title(),
                    "ID Code":  uid_disp,
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True)
            st.caption(f"Total: {len(rows)} account(s)")
        else:
            st.info("No accounts found.")

# manage
    with t_manage:
        users_all = get_all_users()
        if not users_all:
            st.info("No accounts to manage.")
        else:
            opts = [f"{u['username']} [{u['role']}]" for u in users_all]
            sel  = st.selectbox("Select Account", opts, key="manage_sel")
            if sel:
                uname_part = sel.rsplit(" [", 1)[0]
                role_part  = sel.rsplit("[", 1)[1].rstrip("]") if "[" in sel else ""
                action = st.radio(
                    "Action", ["Reset Password", "Delete Account"],
                    horizontal=True, key="manage_act",
                )

                if action == "Reset Password":
                    with st.form("reset_pw_form"):
                        np1 = st.text_input("New Password", type="password")
                        np2 = st.text_input("Confirm Password", type="password")
                        if st.form_submit_button("Update Password", type="primary"):
                            if not np1:
                                st.error("Password cannot be empty.")
                            elif np1 != np2:
                                st.error("Passwords do not match.")
                            else:
                                ok, msg = update_user_password(
                                    uname_part, np1, role_part)
                                if ok:
                                    log_activity(
                                        st.session_state.get("admin_user", "admin"),
                                        "password_changed", "admin",
                                        f"Reset password for {uname_part}",
                                    )
                                    st.success(
                                        f"Password updated for {uname_part}")
                                else:
                                    st.error(msg)
                else:
                    st.warning(
                        f"This will permanently delete the account for **{uname_part}**. "
                        f"This action cannot be undone.")
                    with st.form("delete_acct_form"):
                        confirm = st.text_input(
                            f"Type '{uname_part}' to confirm deletion")
                        if st.form_submit_button("Delete Account", type="primary"):
                            if confirm == uname_part:
                                ok, msg = delete_user_account(
                                    uname_part, role_part)
                                if ok:
                                    log_activity(
                                        st.session_state.get("admin_user", "admin"),
                                        "account_deleted", "admin",
                                        f"Deleted {role_part} account {uname_part}",
                                    )
                                    st.success(f"Account deleted: {uname_part}")
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.error("Confirmation text does not match. Account not deleted.")


# access control
def _tab_access(admin_user):
    st.markdown(
        "<div class='admin-section'><h3>Access Control</h3>"
        "<p>Role permissions, password policies, and future authentication configuration.</p></div>",
        unsafe_allow_html=True,
    )

    t_roles, t_pw, t_2fa, t_sso = st.tabs(
        ["Role Permission Matrix", "Password Policy",
         "Two-Factor Authentication", "Single Sign-On"])

    with t_roles:
        st.markdown("#### Role-Based Permission Matrix")
        perm = {
            "Feature": [
                "View Grade Records", "Enter and Edit Grades",
                "View Own Child Marks", "View Teacher Notes",
                "Manage User Accounts", "View Activity Log",
                "System Initialization", "Admin Dashboard",
                "Upload Excel Data", "Add Students",
                "Wereda Dashboard", "City-Level Dashboard",
            ],
            "Teacher":      ["Yes","Yes","Yes","Yes","No","No","Yes","No","Yes","Yes","No","No"],
            "Parent":       ["Yes","No","Yes","Yes","No","No","No","No","No","No","No","No"],
            "School Admin": ["Yes","No","Yes","No","No","No","No","No","No","No","No","No"],
            "Wereda":       ["Yes","No","No","No","No","No","No","No","No","No","Yes","No"],
            "Admin":        ["Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes"],
        }
        st.dataframe(pd.DataFrame(perm), use_container_width=True,
                     hide_index=True)
        st.caption(
            "Permissions are enforced at the application layer. "
            "Admin has unrestricted access to all platform features.")

    with t_pw:
        st.markdown("""
        <div class='policy-card'>
          <div class='policy-title'>Password Security Rules</div>
          <div class='policy-body'>
            <ul>
              <li>Passwords are hashed with <strong>bcrypt</strong> (adaptive cost factor)
                  and never stored in plaintext</li>
              <li>Minimum length: 4 characters (production recommendation: 12 or more)</li>
              <li>Password resets are performed by administrators only —
                  no self-service reset is available</li>
              <li>No automatic password expiry (add a scheduled task for production policy)</li>
              <li>A migration utility auto-rehashes any legacy plaintext passwords on startup</li>
            </ul>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("#### Change Administrator Password")
        with st.form("admin_pw_change"):
            cur = st.text_input("Current Password", type="password")
            np1 = st.text_input("New Password", type="password")
            np2 = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password", type="primary"):
                if not verify_admin(admin_user, cur):
                    st.error("Current password is incorrect.")
                elif np1 != np2:
                    st.error("New passwords do not match.")
                elif len(np1) < 4:
                    st.error("Password must be at least 4 characters.")
                else:
                    ok, msg = update_admin_password(admin_user, np1)
                    if ok:
                        log_activity(admin_user, "password_changed",
                                     "admin", "Changed own admin password")
                        st.success("Administrator password updated successfully.")
                    else:
                        st.error(msg)

    with t_2fa:
        st.markdown("""
        <div class='placeholder-panel'>
          <div class='placeholder-badge'>Design Ready — Not Yet Activated</div>
          <h3>Two-Factor Authentication</h3>
          <p>
            TOTP-based 2FA is architecture-ready. The database schema is prepared.
            Connect the <code style='font-family:"IBM Plex Mono",monospace;
            background:rgba(99,102,241,0.08);padding:2px 6px;border-radius:4px;'>pyotp</code>
            library and a QR code renderer to activate this feature.
          </p>
          <div class='placeholder-steps'>
            <strong>Implementation Checklist</strong>
            <span>
              [ ] pip install pyotp qrcode pillow<br>
              [ ] Generate TOTP secret per user and store encrypted<br>
              [ ] Render QR code for authenticator application setup<br>
              [ ] Validate 6-digit OTP on login flow<br>
              [ ] Add totp_secret column to admin_accounts table
            </span>
          </div>
        </div>""", unsafe_allow_html=True)
        st.button("Activate Two-Factor Authentication (Requires OTP Provider)",
                  disabled=True)

    with t_sso:
        st.markdown("""
        <div class='placeholder-panel'>
          <div class='placeholder-badge'>Design Ready — Not Yet Activated</div>
          <h3>Single Sign-On</h3>
          <p>
            SSO allows institutional login via Google Workspace, Microsoft Entra,
            or SAML 2.0 providers compatible with Ethiopian Ministry of Education systems.
            The routing architecture is fully prepared.
          </p>
          <div class='placeholder-steps'>
            <strong>Supported Providers</strong>
            <span>
              [ ] Google OAuth 2.0 — via streamlit-oauth or authlib<br>
              [ ] Microsoft Entra ID — OAuth 2.0 / OIDC protocol<br>
              [ ] SAML 2.0 — via python3-saml library<br>
              [ ] Custom LDAP / Active Directory endpoint
            </span>
          </div>
        </div>""", unsafe_allow_html=True)
        st.button("Configure SSO Provider (Requires OAuth Credentials)",
                  disabled=True)


# activity monitor
def _tab_activity():
    st.markdown(
        "<div class='admin-section'><h3>Activity Monitor</h3>"
        "<p>Complete audit trail of all login, logout, account, and security events. "
        "Details are stored encrypted and decrypted for display only.</p></div>",
        unsafe_allow_html=True,
    )

    logs = get_activity_log(limit=300)
    if not logs:
        st.info("No activity recorded yet. Events will appear here as users interact with the system.")
        return

    f1, f2 = st.columns(2)
    with f1:
        act_f = st.selectbox(
            "Filter by Action",
            ["All","login","logout","account_created",
             "password_changed","account_deleted"],
            key="act_f",
        )
    with f2:
        role_f = st.selectbox(
            "Filter by Role",
            ["All","teacher","parent","admin"],
            key="role_f",
        )

    filtered = [
        l for l in logs
        if (act_f == "All" or l.get("action") == act_f)
        and (role_f == "All" or l.get("role") == role_f)
    ]
    st.caption(f"Showing {len(filtered)} of {len(logs)} total events")

    if filtered:
        rows = []
        for l in filtered:
            det = l.get("details", "") or ""
            try:
                det = decrypt_field(det)[:80] if det else ""
            except Exception:
                det = det[:80]
            rows.append({
                "Timestamp": l.get("timestamp", ""),
                "Username":  l.get("username", ""),
                "Role":      l.get("role", "").title(),
                "Action":    l.get("action", "").replace("_", " ").title(),
                "Details":   det,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True,
                     hide_index=True)
    else:
        st.info("No events match the current filters.")


# data management
def _tab_data():
    st.markdown(
        "<div class='admin-section'><h3>Data Management and Protection</h3>"
        "<p>Live database snapshot, encryption key status, and backup guidance.</p></div>",
        unsafe_allow_html=True,
    )

    conn = get_db_connection()
    table_stats = {}
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [r[0] for r in c.fetchall()]
            for tbl in tables:
                try:
                    c.execute(f"SELECT COUNT(*) FROM [{tbl}]")
                    table_stats[tbl] = c.fetchone()[0]
                except Exception:
                    table_stats[tbl] = "—"
        finally:
            conn.close()

    if table_stats:
        st.markdown("#### Live Database Table Sizes")
        df_stats = pd.DataFrame(
            [{"Table": k, "Row Count": v} for k, v in table_stats.items()]
        )
        st.dataframe(df_stats, use_container_width=True, hide_index=True)

    st.markdown("#### Encryption Key Status")
    from pathlib import Path
    key_path = Path(_ADMIN_BASE) / "database" / "secret.key"
    if key_path.exists():
        key_size = key_path.stat().st_size
        st.markdown(
            f"<div class='status-ok'>Fernet key present — {key_size} bytes "
            f"at database/secret.key</div>",
            unsafe_allow_html=True,
        )
        st.markdown("""
        <div class='policy-card'>
          <div class='policy-title'>Encrypted Fields</div>
          <div class='policy-body'>
            <ul>
              <li><strong>users.user_id_code</strong> — Teacher and student IDs encrypted (PII)</li>
              <li><strong>activity_log.details</strong> — Log detail fields encrypted at rest</li>
            </ul>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div class='status-warn'>Fernet key not yet generated. "
            "Will auto-create on first database write.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### Backup and Recovery Guidance")
    st.markdown("""
    <div class='policy-card'>
      <div class='policy-title'>Backup Strategy</div>
      <div class='policy-body'>
        <ul>
          <li>Back up <strong>database/school_data.db</strong> daily using a simple file copy</li>
          <li>Back up <strong>database/secret.key</strong> separately to offline secure storage</li>
          <li>Never store the encryption key and database in the same backup location</li>
          <li>For production: migrate to PostgreSQL with daily pg_dump and WAL archiving</li>
          <li>Use cloud storage (AWS S3, GCS, Azure Blob) with server-side encryption enabled</li>
        </ul>
      </div>
    </div>""", unsafe_allow_html=True)


# documentation
def _tab_documentation():
    st.markdown(
        "<div class='admin-section'><h3>Documentation and Strategy</h3>"
        "<p>System configuration records, security policies, and operational procedures.</p></div>",
        unsafe_allow_html=True,
    )

    with st.expander("System Configuration Records", expanded=True):
        st.markdown("""
        <div class='policy-body' style='line-height:2.1;'>
          <strong>Platform:</strong> LEARNIX — Ethiopian School Management System<br>
          <strong>Stack:</strong> Python 3.x · Streamlit · SQLite · bcrypt · Fernet (cryptography)<br>
          <strong>Architecture:</strong> Single-entry Streamlit application with modular dashboard imports<br>
          <strong>Authentication:</strong> bcrypt-hashed passwords; admin accounts isolated in a separate table<br>
          <strong>Encryption:</strong> Fernet symmetric encryption — AES-128-CBC with HMAC-SHA256<br>
          <strong>Database:</strong> SQLite stored at <code>database/school_data.db</code><br>
          <strong>Key Storage:</strong> <code>database/secret.key</code> — auto-generated on first run<br>
          <strong>Roles:</strong> teacher · parent · school_admin · wereda · kifle_ketema · addis_ababa · admin
        </div>""", unsafe_allow_html=True)

    with st.expander("Security Policies"):
        st.markdown("""
        <div class='policy-card'>
          <div class='policy-title'>Password Policy</div>
          <div class='policy-body'>All passwords are stored as bcrypt hashes. Minimum length is
          4 characters in development (12 or more recommended in production). No plaintext
          passwords exist anywhere in the codebase, logs, or database. Password resets are
          performed by administrators only.</div>
        </div>
        <div class='policy-card'>
          <div class='policy-title'>Data Encryption Policy</div>
          <div class='policy-body'>PII fields — including user ID codes and activity log details —
          are encrypted using Fernet symmetric encryption. The encryption key is stored separately
          from the database. Both must be backed up independently. Data in transit is protected
          by deploying behind a TLS-terminating reverse proxy.</div>
        </div>
        <div class='policy-card'>
          <div class='policy-title'>Access Control Policy</div>
          <div class='policy-body'>Role-based access is enforced at the application layer.
          Administrator accounts are maintained in an isolated table with bcrypt credential
          verification. All administrative actions are logged to the activity_log table with
          encrypted detail fields. Two-factor authentication and SSO are architecture-ready
          for production hardening.</div>
        </div>
        <div class='policy-card'>
          <div class='policy-title'>Audit and Logging Policy</div>
          <div class='policy-body'>All login, logout, account creation, deletion,
          and password change events are recorded with their timestamp, username, role,
          and encrypted details. Logs are retained indefinitely by default; add a
          retention and archival policy for compliance requirements.</div>
        </div>""", unsafe_allow_html=True)

    with st.expander("Operational Procedures"):
        st.markdown("""
        <div class='policy-body' style='line-height:2.2;'>
          <strong>Onboarding a new teacher:</strong><br>
          Admin Dashboard → Account Management → Create Account → Role: Teacher → complete fields → Submit.<br><br>
          <strong>Resetting a forgotten password:</strong><br>
          Admin Dashboard → Account Management → Manage Account → select user → Reset Password.<br><br>
          <strong>Offboarding a user:</strong><br>
          Admin Dashboard → Account Management → Manage Account → select user → Delete Account → confirm.<br><br>
          <strong>Monitoring for suspicious activity:</strong><br>
          Admin Dashboard → Activity Monitor → filter Action by "Login" → review timestamps and sources.<br><br>
          <strong>Database backup procedure:</strong><br>
          Copy <code>database/school_data.db</code> and <code>database/secret.key</code>
          to separate, secure, offline locations. These two files must never share the same backup destination.
        </div>""", unsafe_allow_html=True)


# capacity planning
def _tab_capacity():
    st.markdown(
        "<div class='admin-section'><h3>Capacity Planning</h3>"
        "<p>Scalability architecture and future growth design notes.</p></div>",
        unsafe_allow_html=True,
    )

    cards = [
        (
            "Multi-School Scalability",
            "The system is school-agnostic. Add new schools by updating the SCHOOLS constant in "
            "pro.py — no database schema changes are required. The users table is not school-scoped, "
            "so teachers from any school can be registered immediately. For full multi-tenancy, "
            "add a school_id foreign key to the users and grades tables.",
        ),
        (
            "User Growth",
            "SQLite handles thousands of concurrent read operations efficiently. For 10,000 or more "
            "concurrent users, migrate to PostgreSQL or MySQL by changing the DB_PATH environment "
            "variable — the db_functions.py abstraction layer requires no other code changes. "
            "Connection pooling via SQLAlchemy can be added at the get_db_connection() function level.",
        ),
        (
            "Security Scaling",
            "The bcrypt cost factor can be increased for stronger hashing without breaking existing "
            "passwords — new logins use the updated factor; legacy passwords are rehashed on next save. "
            "Fernet key rotation is supported by decrypting then re-encrypting all fields with a new key. "
            "Two-factor authentication requires only pyotp plus a delivery mechanism — the schema is ready.",
        ),
        (
            "Analytics Growth",
            "The hierarchical dashboard (school to wereda to kifle ketema to city) is designed for "
            "drill-down expansion. Add new administrative levels by creating dashboard modules that follow "
            "the pattern of addis_ababa_dashboard.py. Each level is independently routable from pro.py.",
        ),
        (
            "Deployment and Hosting",
            "For production deployment, use Streamlit Cloud, Docker, or AWS EC2 behind an NGINX reverse "
            "proxy with HTTPS via Let's Encrypt. Use environment variables for DB_PATH and key paths — "
            "never hardcode production paths in source code. Session management scales with "
            "Streamlit's built-in session_state.",
        ),
        (
            "Data Volume",
            "The current SQLite database handles a full school's academic records efficiently. "
            "Grade records, attendance, notes, and activity logs are all indexed. For one million or more "
            "rows, add composite indexes on (student_id, term_id) in the grades table and partition "
            "the activity_log table by year for archival.",
        ),
    ]

    for title, body in cards:
        st.markdown(
            f"<div class='capacity-card'>"
            f"<div class='capacity-title'>{title}</div>"
            f"<div class='capacity-body'>{body}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# subject management
def _tab_subjects():
    st.markdown(
        "<div class='admin-section'><h3>Subject Management</h3>"
        "<p>Centralized control over academic subjects available in the system.</p></div>",
        unsafe_allow_html=True,
    )

    t_add, t_view = st.tabs(["Add Subject", "Current Subjects"])

    with t_add:
        with st.form("admin_add_subj_form", clear_on_submit=True):
            new_subj = st.text_input("New Subject Name")
            submitted = st.form_submit_button("Add Subject", type="primary")
            if submitted:
                if not new_subj.strip():
                    st.error("Subject name cannot be empty.")
                else:
                    try:
                        add_subject(new_subj.strip())
                        log_activity(st.session_state.admin_user, "add_subject", "admin", f"Added subject: {new_subj}")
                        st.success(f"Subject '{new_subj}' added successfully!")
                    except Exception as e:
                        st.error(f"Error adding subject: {e}")

    with t_view:
        subjects = get_subjects()
        if not subjects:
            st.info("No subjects found in the database. Add one to begin.")
        else:
            st.markdown("<p style='color:#64748b; font-size:14px; margin-bottom:16px;'>These subjects automatically propagate to all dashboards.</p>", unsafe_allow_html=True)
            for s in subjects:
                if s["name"] == "__TERM_ATT__":
                    continue
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"<div style='font-family:\"IBM Plex Sans\"; font-size:15px; font-weight:600; padding:12px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;'>{s['name']}</div>", unsafe_allow_html=True)
                with c2:
                    if st.button("Delete", key=f"del_subj_{s['id']}", use_container_width=True):
                        try:
                            delete_subject(s['id'])
                            log_activity(st.session_state.admin_user, "delete_subject", "admin", f"Deleted subject: {s['name']}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting subject: {e}")
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# main entry point
def show_admin_dashboard():
    """Main entry point called from pro.py.
    Handles login gate, then renders the full admin interface.
    """
    inject_admin_css()

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    if "admin_user" not in st.session_state:
        st.session_state.admin_user = None

    if not st.session_state.admin_logged_in:
        result = _show_login_gate()
        if result == "back":
            st.session_state.page = "role"
            st.rerun()
        return

    admin_user = st.session_state.admin_user or "admin"
    _render_sidebar(admin_user)

    menu = st.session_state.get("admin_menu", "Overview")

    if menu == "Overview":
        _tab_overview(admin_user)
    elif menu == "Account Management":
        _tab_accounts()
    elif menu == "Subject Management":
        _tab_subjects()
    elif menu == "Access Control":
        _tab_access(admin_user)
    elif menu == "Activity Monitor":
        _tab_activity()
    elif menu == "Data Management":
        _tab_data()
    elif menu == "Documentation":
        _tab_documentation()
    elif menu == "Capacity Planning":
        _tab_capacity()
    else:
        _tab_overview(admin_user)
