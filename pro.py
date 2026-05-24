import streamlit as st
import base64
import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px


try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()

_DB_FILE = os.path.join(BASE_DIR, "database", "school_data.db")
os.environ.setdefault("SCHOOL_DB_PATH", _DB_FILE)

sys.path.insert(0, os.path.join(BASE_DIR, "app", "backend"))

from db_functions import (
    init_db as _backend_init_db,
    get_db_connection,
    get_or_create_student,
    get_or_create_subject,
    get_or_create_term,
    get_students,
    get_subjects,
    upload_grades_from_excel,
    register_user,
    verify_user,
    log_activity,
    seed_default_admin,
    migrate_plaintext_passwords,
    decrypt_field,
    encrypt_field,
)


# page configuration
st.set_page_config(
    page_title="LEARNIX - Academic Portals",
    page_icon="LEARNIX",
    layout="wide",
    initial_sidebar_state="expanded",
)


REGIONS = [
    "Select Region",
    "Addis Ababa",
    "Oromia",
    "Amhara",
    "Tigray",
    "Sidama",
    "Afar",
    "Somali",
    "Benshangul-Gumuuz",
    "Harari",
    "SNNPR",
    "Gambela",
]
KIFLE_KETEMAS = [
    "Select Kifle Ketema",
    "Bole",
    "Arada",
    "Yeka",
    "Kirkos",
    "Lideta",
    "Addis Ketema",
    "Akaki Kality",
    "Kolfe Keranio",
    "Nifas Silk-Lafto",
    "Gulele",
    "Lemi Kura",
]
WEREDAS = [
    "Select Wereda",
    "Wereda 01",
    "Wereda 02",
    "Wereda 03",
    "Wereda 04",
    "Wereda 05",
    "Wereda 06",
    "Wereda 07",
    "Wereda 08",
    "Wereda 09",
    "Wereda 10",
]
SCHOOLS = [
    "Select School",
    "NEPS",
    "OMEGA",
    "CRUISE",
    "EWIKET LE FIRE",
    "YANTETA",
    "FUTURE",
    "STANDFORD",
    "SOUTH WEST",
    "EVEREST YOUTH ACADEMY",
    "BISRATE GEBIREL",
]

TEACHER_CREDENTIALS = {"tafesse": {"id": "neps-t-4567", "pass": "1234"}}
PARENT_CREDENTIALS = {"jallel million": {"id": "neps-s-8903", "pass": "1234"}}

# School logo image mapping — filenames relative to BASE_DIR
# Used to display school branding images in the school selection UI.
# Scalability: add new entries here when new schools are added.
SCHOOL_IMAGE_MAP = {
    "NEPS":               "download.png",
    "BGIS":               "bgis.png",
    "CRUISE":             "cruise.jfif",
    "OMEGA":              "omega.jfif",
    "SCHOOL OF TOMORROW": "schoolof.jfif",
    "FUTURE":             "future.jfif",
    "SOUTH WEST":         "south_west.jfif",
    "STANDFORD":          "standford.png",
}

CLASSROOMS = [
    "9A",
    "9B",
    "9C",
    "9D",
    "10A",
    "10B",
    "10C",
    "10D",
    "11A",
    "11B",
    "11C",
    "11D",
    "12A",
    "12B",
    "12C",
    "12D",
]

COMPONENTS = {
    "Worksheet (0-10)": 10,
    "Test (0-10)": 10,
    "Mid Exam (0-30)": 30,
    "Final Exam (0-40)": 40,
    "Assignment (0-10)": 10,
}
ATTENDANCE_ROW = "Attendance"
ALL_ROWS = list(COMPONENTS.keys()) + [ATTENDANCE_ROW]


COMPONENT_AXIS = {
    "Worksheet (0-10)": {"range": [0, 10], "dtick": 2},
    "Test (0-10)": {"range": [0, 10], "dtick": 2},
    "Assignment (0-10)": {"range": [0, 10], "dtick": 2},
    "Mid Exam (0-30)": {"range": [0, 30], "dtick": 5},
    "Final Exam (0-40)": {"range": [0, 40], "dtick": 10},
}


COMPONENT_DISPLAY = {
    "Worksheet (0-10)": "Worksheet",
    "Test (0-10)": "Test",
    "Assignment (0-10)": "Assignment",
    "Mid Exam (0-30)": "Mid Exam",
    "Final Exam (0-40)": "Final Exam",
}
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
DASH_MENU = {
    "Dashboard": "Dashboard",
    "1st Quarter": "1st Quarter",
    "2nd Quarter": "2nd Quarter",
    "3rd Quarter": "3rd Quarter",
    "4th Quarter": "4th Quarter",
    "Teacher Notes": "Teacher's Notes & Concerns",
    "System Initialization": "System Initialization",
}


# init app tables
def init_app_tables():

    conn = get_db_connection()
    if conn is None:
        return
    try:
        c = conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS component_grades (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                term_id    INTEGER NOT NULL,
                component  TEXT    NOT NULL,
                score      REAL,
                UNIQUE (student_id, subject_id, term_id, component),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (term_id)    REFERENCES terms(id)    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS teacher_notes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id    INTEGER NOT NULL,
                note          TEXT    NOT NULL,
                date_recorded DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
        """)

        for q in QUARTERS:
            c.execute("INSERT OR IGNORE INTO terms (name) VALUES (?)", (q,))
        conn.commit()
    finally:
        conn.close()


# app init db
def app_init_db():
    _backend_init_db()
    init_app_tables()
# seed default admin account and migrate any plaintext passwords
    seed_default_admin()
    migrate_plaintext_passwords()


# is blank markbook value
def _is_blank_markbook_value(val) -> bool:
    if val is None:
        return True
    if isinstance(val, (float, np.floating)) and np.isnan(val):
        return True
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return True
    if s == "-":
        return True
    return False


# parse component score
def _parse_component_score(raw):
    if _is_blank_markbook_value(raw):
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


# parent component value for analytics
def _parent_component_value_for_analytics(raw):

    if raw is None:
        return None
    try:
        if isinstance(raw, (float, np.floating)) and np.isnan(raw):
            return None
        fv = float(raw)
    except (TypeError, ValueError):
        return None
    if fv == 0.0:
        return None
    return fv


# save component scores
def save_component_scores(
    student_id: int, subject_id: int, term_id: int, component_scores: dict
):
    conn = get_db_connection()
    if conn is None:
        return
    try:
        c = conn.cursor()
        total = 0.0
        recorded = 0
        for component, raw in component_scores.items():
            max_val = COMPONENTS.get(component, 100)
            parsed = _parse_component_score(raw)
            if parsed is None:
                c.execute(
                    """
                    DELETE FROM component_grades
                    WHERE student_id = ? AND subject_id = ? AND term_id = ? AND component = ?
                """,
                    (student_id, subject_id, term_id, component),
                )
                continue
            score = max(0.0, min(float(parsed), float(max_val)))
            total += score
            recorded += 1
            c.execute(
                """
                INSERT OR REPLACE INTO component_grades
                    (student_id, subject_id, term_id, component, score)
                VALUES (?, ?, ?, ?, ?)
            """,
                (student_id, subject_id, term_id, component, score),
            )
        if recorded == 0:
            c.execute(
                """
                DELETE FROM grades
                WHERE student_id = ? AND subject_id = ? AND term_id = ?
            """,
                (student_id, subject_id, term_id),
            )
        else:
            c.execute(
                """
                INSERT OR REPLACE INTO grades (student_id, subject_id, term_id, score)
                VALUES (?, ?, ?, ?)
            """,
                (student_id, subject_id, term_id, total),
            )
        conn.commit()
    finally:
        conn.close()


# load component scores
def load_component_scores(student_id: int, subject_id: int, term_id: int) -> dict:
    conn = get_db_connection()
    if conn is None:
        return {}
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT component, score
            FROM component_grades
            WHERE student_id = ? AND subject_id = ? AND term_id = ?
        """,
            (student_id, subject_id, term_id),
        )
        return {row["component"]: row["score"] for row in c.fetchall()}
    finally:
        conn.close()


# save student attendance
def save_student_attendance(student_id: int, term_id: int, code: str):

    mapping = {"P": 100.0, "L": 50.0, "A": 0.0}
    pct = mapping.get(str(code).upper().strip(), 0.0)
    conn = get_db_connection()
    if conn is None:
        return
    try:
        c = conn.cursor()

        c.execute("INSERT OR IGNORE INTO subjects (name) VALUES ('__TERM_ATT__')")
        c.execute("SELECT id FROM subjects WHERE name = '__TERM_ATT__'")
        sentinel_id = c.fetchone()["id"]
        c.execute(
            """
            INSERT OR REPLACE INTO attendance
                (student_id, subject_id, attendance_percentage)
            VALUES (?, ?, ?)
        """,
            (student_id, sentinel_id, pct),
        )
        conn.commit()
    finally:
        conn.close()


# load student attendance code
def load_student_attendance_code(student_id: int) -> str:
    conn = get_db_connection()
    if conn is None:
        return "P"
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM subjects WHERE name = '__TERM_ATT__'")
        row = c.fetchone()
        if row is None:
            return "P"
        c.execute(
            """
            SELECT attendance_percentage FROM attendance
            WHERE student_id = ? AND subject_id = ?
        """,
            (student_id, row["id"]),
        )
        res = c.fetchone()
        if res is None:
            return "P"
        pct = res["attendance_percentage"]
        if pct >= 80:
            return "P"
        if pct >= 40:
            return "L"
        return "A"
    finally:
        conn.close()


# get all grades df
def get_all_grades_df() -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(
            """
            SELECT s.name AS Student, sub.name AS Subject,
                   t.name AS Quarter, g.score
            FROM grades g
            JOIN students s   ON g.student_id = s.id
            JOIN subjects sub ON g.subject_id = sub.id
            JOIN terms t      ON g.term_id    = t.id
            WHERE sub.name != '__TERM_ATT__'
        """,
            conn,
        )
    finally:
        conn.close()


# get all attendance df
def get_all_attendance_df() -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(
            """
            SELECT s.name AS Student, a.attendance_percentage
            FROM attendance a
            JOIN students s   ON a.student_id = s.id
            JOIN subjects sub ON a.subject_id = sub.id
            WHERE sub.name = '__TERM_ATT__'
        """,
            conn,
        )
    finally:
        conn.close()


# compute dashboard data
def compute_dashboard_data():
    df_grades = get_all_grades_df()
    df_att = get_all_attendance_df()

    empty_ranking = pd.DataFrame(
        columns=[
            "Student",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "Q1 Rank",
            "Q2 Rank",
            "Q3 Rank",
            "Q4 Rank",
            "Overall Avg",
            "Overall Rank",
        ]
    )
    empty_att = pd.DataFrame(columns=["Student", "Attendance %"])

    if df_grades.empty:
        return (
            pd.Series(dtype=float),
            pd.DataFrame(columns=["Quarter", "Average Score"]),
            [],
            empty_ranking,
            empty_att,
            pd.DataFrame(),
            pd.DataFrame(columns=["Student", "Quarter", "Average"]),
        )

    avg_subject = (
        df_grades.groupby("Subject")["score"].mean().sort_values(ascending=False)
    )
    weak_subjects = avg_subject[avg_subject < 60].index.tolist()

    perf = (
        df_grades.groupby(["Student", "Quarter"])["score"]
        .mean()
        .reset_index()
        .rename(columns={"score": "Average"})
    )

    quarterly_trend = (
        perf.groupby("Quarter")["Average"]
        .mean()
        .reset_index()
        .rename(columns={"Average": "Average Score"})
    )

    ranking_table = perf.pivot(
        index="Student", columns="Quarter", values="Average"
    ).reset_index()
    for q in QUARTERS:
        if q not in ranking_table.columns:
            ranking_table[q] = np.nan
    ranking_table["Overall Avg"] = ranking_table[QUARTERS].mean(axis=1)
    for q in QUARTERS:
        ranking_table[f"{q} Rank"] = ranking_table[q].rank(
            ascending=False, na_option="bottom"
        )
    ranking_table["Overall Rank"] = ranking_table["Overall Avg"].rank(ascending=False)

    if not df_att.empty:
        attendance_pct = (
            df_att.groupby("Student")["attendance_percentage"]
            .mean()
            .reset_index()
            .rename(columns={"attendance_percentage": "Attendance %"})
        )
        q_att_pivot = pd.DataFrame(index=df_grades["Student"].unique())
    else:
        attendance_pct = empty_att
        q_att_pivot = pd.DataFrame()

    return (
        avg_subject,
        quarterly_trend,
        weak_subjects,
        ranking_table,
        attendance_pct,
        q_att_pivot,
        perf,
    )


# build student markbook df
def build_student_markbook_df(
    student_id: int, term_id: int, subjects: list
) -> pd.DataFrame:
    data = {"Components": ALL_ROWS}
    for subj in subjects:
        data[subj] = [""] * len(ALL_ROWS)
    df = pd.DataFrame(data).set_index("Components")

    for subj in subjects:
        sub_row = get_subject_row(subj)
        if sub_row is None:
            continue
        subject_id = sub_row["id"]
        scores = load_component_scores(student_id, subject_id, term_id)
        for comp in COMPONENTS:
            if comp in scores and scores[comp] is not None:
                v = scores[comp]
                df.at[comp, subj] = str(int(v)) if float(v) == int(float(v)) else str(v)

    att_code = load_student_attendance_code(student_id)
    for subj in subjects:
        df.at[ATTENDANCE_ROW, subj] = att_code

    return df


# get subject row
def get_subject_row(name: str):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        c = conn.cursor()
        c.execute("SELECT id, name FROM subjects WHERE name = ?", (name,))
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# get student row
def get_student_row(name: str):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        c = conn.cursor()
        c.execute("SELECT id, name FROM students WHERE name = ?", (name,))
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# get term row
def get_term_row(name: str):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        c = conn.cursor()
        c.execute("SELECT id, name FROM terms WHERE name = ?", (name,))
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# compute student totals
def compute_student_totals(df: pd.DataFrame) -> pd.Series:
    numeric = df.drop(index=ATTENDANCE_ROW, errors="ignore").copy()
    totals = {}
    for col in numeric.columns:
        s = 0.0
        for comp in COMPONENTS:
            if comp not in numeric.index:
                continue
            raw = numeric.at[comp, col]
            if _is_blank_markbook_value(raw):
                continue
            try:
                s += float(raw)
            except (ValueError, TypeError):
                continue
        totals[col] = s
    return pd.Series(totals)


# get student grades df
def get_student_grades_df(student_name: str) -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            SELECT sub.name AS Subject, t.name AS Quarter, g.score
            FROM grades g
            JOIN students s   ON g.student_id = s.id
            JOIN subjects sub ON g.subject_id = sub.id
            JOIN terms t      ON g.term_id    = t.id
            WHERE (s.name = ? OR s.name = ? OR s.name = ?)
              AND sub.name != '__TERM_ATT__'
        """
        alt_name1 = student_name.replace(" ", ".")
        alt_name2 = student_name.replace(".", " ")
        df = pd.read_sql_query(query, conn, params=(student_name, alt_name1, alt_name2))
        return df
    finally:
        conn.close()


# get student notes df
def get_student_notes_df(student_name: str) -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            SELECT t.note, t.date_recorded
            FROM teacher_notes t
            JOIN students s ON t.student_id = s.id
            WHERE (s.name = ? OR s.name = ? OR s.name = ?)
            ORDER BY t.date_recorded DESC
        """
        alt_name1 = student_name.replace(" ", ".")
        alt_name2 = student_name.replace(".", " ")
        df = pd.read_sql_query(query, conn, params=(student_name, alt_name1, alt_name2))
        return df
    finally:
        conn.close()


# get student component grades df
def get_student_component_grades_df(student_name: str, quarter: str) -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        query = """
            SELECT sub.name AS Subject, cg.component AS Component, cg.score
            FROM component_grades cg
            JOIN students s   ON cg.student_id = s.id
            JOIN subjects sub ON cg.subject_id = sub.id
            JOIN terms t      ON cg.term_id    = t.id
            WHERE (s.name = ? OR s.name = ? OR s.name = ?)
              AND t.name = ?
              AND sub.name != '__TERM_ATT__'
        """
        alt_name1 = student_name.replace(" ", ".")
        alt_name2 = student_name.replace(".", " ")
        df = pd.read_sql_query(
            query, conn, params=(student_name, alt_name1, alt_name2, quarter)
        )
        return df
    finally:
        conn.close()


# get total subjects count
def get_total_subjects_count() -> int:
    conn = get_db_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM subjects WHERE name != '__TERM_ATT__'")
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        conn.close()


# resolve student id
def resolve_student_id(student_name: str):
    for nm in (
        student_name,
        student_name.replace(" ", "."),
        student_name.replace(".", " "),
    ):
        r = get_student_row(nm)
        if r:
            return r["id"]
    return None


# subject has all components
def subject_has_all_components(student_id: int, term_id: int, subject_id: int) -> bool:
    loaded = load_component_scores(student_id, subject_id, term_id)
    for comp in COMPONENTS:
        if _parent_component_value_for_analytics(loaded.get(comp)) is None:
            return False
    return True


# is quarter complete for student
def is_quarter_complete_for_student(student_name: str, quarter: str) -> bool:
    sid = resolve_student_id(student_name)
    if sid is None:
        return False
    trow = get_term_row(quarter)
    if not trow:
        return False
    term_id = trow["id"]
    subs = [s for s in get_subjects() if s["name"] != "__TERM_ATT__"]
    if not subs:
        return False
    for sub in subs:
        if not subject_has_all_components(sid, term_id, sub["id"]):
            return False
    return True


# get student term subject scores df
def get_student_term_subject_scores_df(student_name: str) -> pd.DataFrame:
    sid = resolve_student_id(student_name)
    if sid is None:
        return pd.DataFrame(columns=["Subject", "Quarter", "score"])
    rows = []
    for q in QUARTERS:
        trow = get_term_row(q)
        if not trow:
            continue
        term_id = trow["id"]
        for sub in get_subjects():
            if sub["name"] == "__TERM_ATT__":
                continue
            if not subject_has_all_components(sid, term_id, sub["id"]):
                rows.append({"Subject": sub["name"], "Quarter": q, "score": np.nan})
                continue
            loaded = load_component_scores(sid, sub["id"], term_id)
            total = sum(
                _parent_component_value_for_analytics(loaded[c]) for c in COMPONENTS
            )
            rows.append({"Subject": sub["name"], "Quarter": q, "score": total})
    return pd.DataFrame(rows)


# build full component pivot
def build_full_component_pivot(student_name: str, quarter: str) -> pd.DataFrame:
    sid = resolve_student_id(student_name)
    trow = get_term_row(quarter)
    if sid is None or not trow:
        return pd.DataFrame()
    term_id = trow["id"]
    subs = [s for s in get_subjects() if s["name"] != "__TERM_ATT__"]
    records = []
    for sub in subs:
        loaded = load_component_scores(sid, sub["id"], term_id)
        row = {"Subject": sub["name"]}
        vals = []
        all_filled = True
        for comp in COMPONENTS:
            av = _parent_component_value_for_analytics(loaded.get(comp))
            if av is None:
                row[comp] = np.nan
                all_filled = False
            else:
                row[comp] = av
                vals.append(av)
        if all_filled and len(vals) == len(COMPONENTS):
            row["Total Output"] = sum(vals)
        else:
            row["Total Output"] = np.nan
        records.append(row)
    return pd.DataFrame(records)


# build component subject frame for parent
def build_component_subject_frame_for_parent(
    student_name: str, quarter: str, component_key: str
) -> pd.DataFrame:
    sid = resolve_student_id(student_name)
    trow = get_term_row(quarter)
    if sid is None or not trow:
        return pd.DataFrame(columns=["Subject", "score"])
    term_id = trow["id"]
    subs = [s for s in get_subjects() if s["name"] != "__TERM_ATT__"]
    rows = []
    for sub in subs:
        loaded = load_component_scores(sid, sub["id"], term_id)
        av = _parent_component_value_for_analytics(loaded.get(component_key))
        rows.append({"Subject": sub["name"], "score": np.nan if av is None else av})
    return pd.DataFrame(rows)


# count parent filled component slots
def count_parent_filled_component_slots(student_name: str, quarter: str) -> int:
    sid = resolve_student_id(student_name)
    trow = get_term_row(quarter)
    if sid is None or not trow:
        return 0
    term_id = trow["id"]
    n = 0
    for sub in get_subjects():
        if sub["name"] == "__TERM_ATT__":
            continue
        loaded = load_component_scores(sid, sub["id"], term_id)
        for comp in COMPONENTS:
            if _parent_component_value_for_analytics(loaded.get(comp)) is not None:
                n += 1
    return n


# get base64 image
def get_base64_image(image_path):
    try:
        if not os.path.exists(image_path):
            return ""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


# get school logo b64
def get_school_logo_b64(school_name: str) -> str:
    """Return base64-encoded image for a school name, or empty string if not found."""
    filename = SCHOOL_IMAGE_MAP.get(school_name.upper(), "")
    if not filename:
        return ""
    path = os.path.join(BASE_DIR, filename)
    return get_base64_image(path)


def _school_img_html(school_name: str, size: str = "28px") -> str:
    """Return an inline <img> HTML tag for a school logo, or empty string."""
    b64 = get_school_logo_b64(school_name)
    if not b64:
        return ""
    ext = SCHOOL_IMAGE_MAP.get(school_name.upper(), ".png").rsplit(".", 1)[-1].lower()
    mime = "image/jpeg" if ext in ("jfif", "jpg", "jpeg") else "image/png"
    return (f'<img src="data:{mime};base64,{b64}" '
            f'style="height:{size};width:{size};object-fit:contain;'
            f'border-radius:4px;vertical-align:middle;margin-right:6px;">')


# load global css
def load_global_css():
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@700;800&family=Orbitron:wght@700;900&display=swap');

    html, body, [data-testid="stApp"], .stMarkdown, .stText { font-family: 'Inter', sans-serif !important; }
    #MainMenu, footer { visibility: hidden; }

    header[data-testid="stHeader"] {
        visibility: visible !important;
        background: transparent !important;
        z-index: 100000 !important;
        pointer-events: none !important;
    }
    header[data-testid="stHeader"] * { pointer-events: none !important; }
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] *,
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] * { pointer-events: auto !important; }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
        padding: 10px 16px !important;
        margin-bottom: 6px !important;
        border-radius: 10px !important;
        transition: all 0.2s ease-in-out !important;
        cursor: pointer !important;
        background-color: transparent !important;
        display: flex !important;
        align-items: center !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] p,
    [data-testid="stSidebar"] [data-testid="stRadio"] span {
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 15px !important;
        transition: color 0.2s ease !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover { background-color: rgba(255,255,255,0.05) !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover p,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover span { color: #ffffff !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked),
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(div[aria-checked="true"]) {
        background-color: rgba(255,255,255,0.12) !important;
        box-shadow: inset 4px 0 0 0 #60a5fa !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) span,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(div[aria-checked="true"]) p,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(div[aria-checked="true"]) span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    div[data-testid="stCheckbox"] label span { color: #0f172a !important; font-weight: 500 !important; }

    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        color: transparent !important;
        font-size: 0px !important;
        font-family: Arial, sans-serif !important;
    }
    [data-testid="stSidebarCollapseButton"] > *,
    [data-testid="collapsedControl"] > * { display: none !important; }
    [data-testid="stSidebarCollapseButton"]::before {
        content: "<";
        font-size: 20px !important;
        color: #cbd5e1 !important;
        font-weight: bold !important;
        display: block !important;
        visibility: visible !important;
    }
    [data-testid="collapsedControl"]::before {
        content: ">";
        font-size: 22px !important;
        color: #0f172a !important;
        font-weight: bold !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 6px 14px !important;
        background: #ffffff !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
        margin-top: 10px !important;
        margin-left: 10px !important;
        border: 1px solid #cbd5e1 !important;
        cursor: pointer !important;
        visibility: visible !important;
    }
    [data-testid="collapsedControl"]:hover::before {
        background: #f8fafc !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
    }

    /* Primary / secondary: strong, clean hover (forms, sign-in, dashboards) */
    @keyframes et-btn-shine {
        0% { transform: translateX(-140%) skewX(-12deg); }
        100% { transform: translateX(220%) skewX(-12deg); }
    }
    button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(165deg, #1e40af 0%, #1d4ed8 40%, #1e3a8a 100%) !important;
        border: 1px solid rgba(30, 64, 175, 0.95) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 4px 16px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        letter-spacing: 0.06em !important;
        min-height: 42px !important;
        height: 42px !important;
        text-transform: uppercase !important;
        position: relative !important;
        overflow: hidden !important;
        z-index: 1 !important;
        isolation: isolate !important;
        transition:
            background 0.38s cubic-bezier(0.34, 1.2, 0.64, 1),
            border-color 0.38s ease,
            box-shadow 0.38s cubic-bezier(0.34, 1.2, 0.64, 1),
            transform 0.38s cubic-bezier(0.34, 1.2, 0.64, 1),
            filter 0.38s ease !important;
        box-shadow:
            0 4px 14px rgba(30, 64, 175, 0.35),
            0 1px 0 rgba(255, 255, 255, 0.12) inset !important;
    }
    button[kind="primary"]::before,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(255,255,255,0.18) 0%, transparent 48%);
        opacity: 0.85;
        pointer-events: none;
        z-index: 0;
        transition: opacity 0.35s ease;
    }
    button[kind="primary"]::after,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 45%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.28), transparent);
        pointer-events: none;
        z-index: 0;
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    button[kind="primary"] p, button[kind="primary"] span,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] p,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] span {
        color: #ffffff !important;
        position: relative !important;
        z-index: 2 !important;
        text-shadow: 0 1px 2px rgba(15, 23, 42, 0.2);
    }
    button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
        background: linear-gradient(145deg, #3b82f6 0%, #2563eb 45%, #1d4ed8 100%) !important;
        border-color: #93c5fd !important;
        box-shadow:
            0 16px 42px rgba(37, 99, 235, 0.55),
            0 0 0 1px rgba(147, 197, 253, 0.45),
            0 0 28px rgba(59, 130, 246, 0.35),
            inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
        transform: translateY(-4px) scale(1.03) !important;
        filter: brightness(1.05) saturate(1.05);
    }
    button[kind="primary"]:hover::after,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover::after {
        opacity: 1;
        animation: et-btn-shine 0.85s ease-out forwards;
    }
    button[kind="primary"]:hover::before,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover::before {
        opacity: 1;
    }
    button[kind="primary"]:active,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:active {
        background: linear-gradient(165deg, #1e3a8a 0%, #1d4ed8 100%) !important;
        border-color: #1e40af !important;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.45) !important;
        transform: translateY(-1px) scale(1.01) !important;
        filter: brightness(0.98);
    }

    button[kind="secondary"],
    div[data-testid="stFormSubmitButton"] > button:not([kind="primary"]) {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 4px 16px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        letter-spacing: 0.06em !important;
        min-height: 42px !important;
        height: 42px !important;
        text-transform: uppercase !important;
        position: relative !important;
        overflow: hidden !important;
        z-index: 1 !important;
        isolation: isolate !important;
        transition:
            background 0.38s cubic-bezier(0.34, 1.2, 0.64, 1),
            border-color 0.38s ease,
            color 0.38s ease,
            box-shadow 0.38s cubic-bezier(0.34, 1.2, 0.64, 1),
            transform 0.38s cubic-bezier(0.34, 1.2, 0.64, 1) !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.07), 0 1px 0 rgba(255,255,255,0.9) inset !important;
    }
    button[kind="secondary"] p, button[kind="secondary"] span,
    div[data-testid="stFormSubmitButton"] > button:not([kind="primary"]) p,
    div[data-testid="stFormSubmitButton"] > button:not([kind="primary"]) span {
        color: #1e293b !important;
        position: relative !important;
        z-index: 2 !important;
        transition: color 0.35s ease !important;
    }
    button[kind="secondary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:not([kind="primary"]):hover {
        background: linear-gradient(180deg, #ffffff 0%, #eff6ff 55%, #dbeafe 100%) !important;
        border: 2px solid #3b82f6 !important;
        box-shadow:
            0 12px 36px rgba(59, 130, 246, 0.22),
            0 0 0 1px rgba(59, 130, 246, 0.15),
            0 4px 16px rgba(15, 23, 42, 0.08) !important;
        transform: translateY(-4px) scale(1.03) !important;
    }
    button[kind="secondary"]:hover p, button[kind="secondary"]:hover span,
    div[data-testid="stFormSubmitButton"] > button:not([kind="primary"]):hover p,
    div[data-testid="stFormSubmitButton"] > button:not([kind="primary"]):hover span {
        color: #0f172a !important;
    }
    button[kind="secondary"]:active,
    div[data-testid="stFormSubmitButton"] > button:not([kind="primary"]):active {
        background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%) !important;
        border: 2px solid #2563eb !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1) !important;
        transform: translateY(-1px) scale(1.01) !important;
    }

    .stSelectbox div[data-baseweb="select"],
    .stTextInput input,
    .stTextArea textarea {
        border-radius: 6px !important;
        border: 1px solid #cbd5e1 !important;
        padding: 6px 12px !important;
        font-size: 14px !important;
        color: #0f172a !important;
        background-color: #ffffff !important;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.02) !important;
        min-height: 40px !important;
    }
    .stSelectbox div[data-baseweb="select"]:hover,
    .stTextInput input:hover,
    .stTextArea textarea:hover { border-color: #94a3b8 !important; }
    .stSelectbox div[data-baseweb="select"]:focus-within,
    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 1px #2563eb !important;
    }
    .stTextInput label, .stSelectbox label, .stRadio label, .stTextArea label {
        font-size: 13px !important;
        color: #1e293b !important;
        font-weight: 600 !important;
        margin-bottom: 4px !important;
    }
    ul[data-baseweb="menu"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; }
    ul[data-baseweb="menu"] li,
    ul[data-baseweb="menu"] li span { color: #0f172a !important; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important;
        border-right: 1px solid #334155 !important;
    }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] h3 { color: #f8fafc !important; font-size: 16px !important; }
    [data-testid="stSidebarContent"] { padding: 20px 16px !important; }
    </style>
    """,
        unsafe_allow_html=True,
    )


# inject page layout
def inject_page_layout():
    if st.session_state.page in [
        "teacher_dashboard", "parent_dashboard", "admin_dashboard"
    ]:
        st.markdown(
            """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(191,219,254,0.45), transparent 28%),
                radial-gradient(circle at top right, rgba(125,211,252,0.28), transparent 24%),
                linear-gradient(180deg, #f8fbff 0%, #eef4fb 52%, #e8eff8 100%) !important;
        }
        header { display: flex !important; visibility: visible !important; background-color: transparent !important; }
        [data-testid="collapsedControl"] { z-index: 999999 !important; display: flex !important; }
        [data-testid="block-container"] {
            max-width: 100% !important;
            padding: 72px 36px 40px 36px !important;
            margin: 0 !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #111827 50%, #0b1120 100%) !important;
            border-right: 1px solid rgba(148,163,184,0.16) !important;
            box-shadow: 18px 0 40px rgba(15,23,42,0.18) !important;
        }
        [data-testid="stSidebarContent"] { padding: 22px 16px !important; }
        [data-testid="stSidebar"] [data-testid="stButton"] button { min-height: 46px !important; }
        [data-testid="stSidebar"] [data-testid="stRadio"] p,
        [data-testid="stSidebar"] [data-testid="stRadio"] span {
            font-size: 16px !important;
            line-height: 1.45 !important;
        }

        .staff-chip {
            display: inline-flex !important; align-items: center !important; gap: 8px !important;
            padding: 7px 12px !important; border-radius: 999px !important;
            background: rgba(12,74,110,0.10) !important; border: 1px solid rgba(56,189,248,0.22) !important;
            color: #0c4a6e !important; font-size: 12px !important; font-weight: 800 !important;
            letter-spacing: 0.12em !important; text-transform: uppercase !important;
        }
        .dashboard-hero {
            position: relative !important; overflow: hidden !important;
            padding: 28px 30px !important; margin-bottom: 22px !important;
            border-radius: 28px !important;
            background: radial-gradient(circle at 85% 18%, rgba(191,219,254,0.42), transparent 22%),
                        linear-gradient(135deg, #0f172a 0%, #0f4c81 48%, #1d4ed8 100%) !important;
            border: 1px solid rgba(191,219,254,0.24) !important;
            box-shadow: 0 28px 60px rgba(15,23,42,0.20) !important;
        }
        .dashboard-hero::after {
            content: ""; position: absolute; inset: auto -80px -120px auto;
            width: 260px; height: 260px; border-radius: 50%;
            background: radial-gradient(circle, rgba(125,211,252,0.28), transparent 68%);
            pointer-events: none;
        }
        .dashboard-hero-grid {
            display: grid !important; grid-template-columns: 1.7fr 1fr !important;
            gap: 22px !important; align-items: stretch !important; position: relative !important; z-index: 1 !important;
        }
        .dashboard-hero-title {
            margin: 16px 0 10px 0 !important; color: #f8fafc !important;
            font-size: clamp(32px,4vw,42px) !important; font-weight: 900 !important;
            letter-spacing: -0.04em !important; line-height: 1.02 !important;
        }
        .dashboard-hero-subtitle {
            margin: 0 !important; color: rgba(226,232,240,0.92) !important;
            font-size: 16px !important; line-height: 1.75 !important; max-width: 720px !important;
        }
        .dashboard-hero-meta { display: flex !important; flex-wrap: wrap !important; gap: 10px !important; margin-top: 18px !important; }
        .dashboard-hero-meta span {
            display: inline-flex !important; align-items: center !important;
            padding: 8px 12px !important; border-radius: 999px !important;
            background: rgba(255,255,255,0.08) !important; border: 1px solid rgba(255,255,255,0.10) !important;
            color: #dbeafe !important; font-size: 13px !important; font-weight: 700 !important;
        }
        .dashboard-hero-panel {
            display: flex !important; flex-direction: column !important;
            justify-content: space-between !important; gap: 14px !important;
            padding: 18px !important; border-radius: 22px !important;
            background: rgba(255,255,255,0.08) !important; border: 1px solid rgba(255,255,255,0.12) !important;
            backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important;
        }
        .dashboard-hero-panel-label { color: #93c5fd !important; font-size: 12px !important; font-weight: 700 !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; }
        .dashboard-hero-panel-value { color: #f8fafc !important; font-size: 26px !important; font-weight: 900 !important; line-height: 1.1 !important; }
        .dashboard-hero-panel-note { color: rgba(226,232,240,0.80) !important; font-size: 13px !important; line-height: 1.6 !important; }

        .dashboard-stats {
            display: grid !important; grid-template-columns: repeat(4,minmax(0,1fr)) !important;
            gap: 18px !important; margin-bottom: 26px !important;
        }
        .dashboard-stat-card {
            background: rgba(255,255,255,0.94) !important; border: 1px solid rgba(203,213,225,0.78) !important;
            border-radius: 22px !important; padding: 22px 22px 18px !important;
            box-shadow: 0 18px 40px rgba(15,23,42,0.09) !important; min-height: 148px !important;
        }
        .dashboard-stat-card strong {
            display: block !important; color: #0f172a !important; font-size: 31px !important;
            line-height: 1.08 !important; margin: 10px 0 12px !important;
            font-weight: 900 !important; letter-spacing: -0.04em !important;
        }
        .dashboard-stat-label { color: #0f4c81 !important; font-size: 13px !important; font-weight: 800 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; }
        .dashboard-stat-note { color: #64748b !important; font-size: 15px !important; line-height: 1.6 !important; }

        .dashboard-section { margin: 28px 0 16px 0 !important; }
        .dashboard-section h3 { margin: 0 !important; color: #0f172a !important; font-size: 26px !important; font-weight: 800 !important; letter-spacing: -0.03em !important; }
        .dashboard-section p { margin: 10px 0 0 0 !important; color: #64748b !important; font-size: 16px !important; line-height: 1.65 !important; }

        [data-testid="stPlotlyChart"],
        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"],
        [data-testid="stExpander"],
        div[data-testid="stAlert"],
        div[data-testid="stForm"] {
            background: rgba(255,255,255,0.94) !important;
            border: 1px solid rgba(203,213,225,0.75) !important;
            border-radius: 22px !important;
            box-shadow: 0 20px 42px rgba(15,23,42,0.09) !important;
        }
        [data-testid="stPlotlyChart"],
        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"],
        div[data-testid="stForm"] { padding: 18px 20px !important; }
        [data-testid="stExpander"] { padding: 6px !important; overflow: hidden !important; }
        [data-testid="stExpander"] details summary {
            padding: 16px 20px !important;
            min-height: 54px !important;
            cursor: pointer !important;
        }
        [data-testid="stExpander"] details summary:hover { background: rgba(248,250,252,0.95) !important; }
        [data-testid="stExpander"] details summary p { color: #0f172a !important; font-weight: 700 !important; font-size: 17px !important; line-height: 1.35 !important; }
        div[data-testid="stAlert"] { padding: 16px 20px !important; }
        div[data-testid="stAlert"] p { color: #0f172a !important; font-size: 15px !important; line-height: 1.65 !important; }

        .dashboard-mini-heading { margin: 0 0 12px 4px !important; color: #0f172a !important; font-size: 18px !important; font-weight: 800 !important; letter-spacing: -0.02em !important; }
        .dashboard-notice {
            padding: 18px 22px !important; border-radius: 18px !important;
            margin-bottom: 14px !important; border: 1px solid transparent !important;
            box-shadow: 0 16px 34px rgba(15,23,42,0.07) !important;
        }
        .dashboard-notice strong { display: block !important; font-size: 16px !important; margin-bottom: 6px !important; }
        .dashboard-notice span { font-size: 15px !important; line-height: 1.65 !important; }
        .dashboard-notice-critical { background: linear-gradient(180deg,#fef2f2,#fff7f7) !important; border-color: rgba(220,38,38,0.14) !important; color: #991b1b !important; }
        .dashboard-notice-warning  { background: linear-gradient(180deg,#fffbeb,#fffdf5) !important; border-color: rgba(202,138,4,0.18) !important; color: #854d0e !important; }
        .dashboard-notice-positive { background: linear-gradient(180deg,#ecfdf5,#f3fff8) !important; border-color: rgba(22,163,74,0.18) !important; color: #166534 !important; }
        .dashboard-note-item {
            padding: 14px 16px !important; border-radius: 14px !important;
            background: #f8fbff !important; border: 1px solid #dbeafe !important;
            color: #334155 !important; font-size: 15px !important;
            line-height: 1.65 !important; margin-bottom: 12px !important;
        }
        [data-testid="stDataFrame"] table,
        [data-testid="stDataFrame"] [role="grid"] { font-size: 15px !important; }
        [data-testid="stDataFrame"] th { font-size: 14px !important; font-weight: 700 !important; }
        [data-testid="stDataFrame"] td { padding: 10px 12px !important; line-height: 1.45 !important; }
        @media (max-width: 1100px) {
            .dashboard-hero-grid, .dashboard-stats { grid-template-columns: 1fr !important; }
        }
        </style>
        """,
            unsafe_allow_html=True,
        )
        return

    bg_path = os.path.join(BASE_DIR, "background.jpg")
    bg_base64 = get_base64_image(bg_path)
    bg_css = (
        f"background-image: linear-gradient(rgba(15,23,42,0.82), rgba(15,23,42,0.94)), url('data:image/jpeg;base64,{bg_base64}') !important;"
        if bg_base64
        else "background-color: #0f172a !important;"
    )

    if st.session_state.page == "welcome":
        st.markdown(
            f"""
        <style>
        header[data-testid="stHeader"] {{ display: none !important; }}
        .stApp {{ {bg_css} background-size: cover !important; background-position: center !important; background-attachment: fixed !important; }}
        [data-testid="stSidebar"] {{ display: none !important; }}
        [data-testid="block-container"] {{
            max-width: 100% !important; padding: 0 !important; margin: 0 !important;
            background-color: transparent !important; border: none !important;
            box-shadow: none !important; border-radius: 0 !important;
        }}
        .main .block-container {{ padding: 0 !important; }}
        </style>
        """,
            unsafe_allow_html=True,
        )
        return

    card_width = (
        "680px"
        if st.session_state.page in ["register_teacher", "register_parent"]
        else ("980px" if st.session_state.page == "role" else "560px")
    )

    st.markdown(
        f"""
    <style>
    .stApp {{ {bg_css} background-size: cover !important; background-position: center !important; background-attachment: fixed !important; }}
    [data-testid="stSidebar"] {{ display: none !important; }}
    @keyframes cardSlideUp {{ from {{ opacity: 0; transform: translateY(36px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    [data-testid="block-container"], .main .block-container {{
        background: linear-gradient(180deg, rgba(15,23,42,0.84), rgba(15,23,42,0.76)) !important;
        backdrop-filter: blur(22px) !important; -webkit-backdrop-filter: blur(22px) !important;
        border-radius: 20px !important; border: 1px solid rgba(148,163,184,0.24) !important;
        box-shadow: 0 32px 80px rgba(0,0,0,0.58), inset 0 1px 0 rgba(255,255,255,0.10) !important;
        width: calc(100% - 32px) !important; max-width: {card_width} !important;
        position: relative !important; padding: 44px !important;
        margin-top: 6vh !important; margin-bottom: 6vh !important;
        margin-left: auto !important; margin-right: auto !important;
        animation: cardSlideUp 0.45s cubic-bezier(0.16,1,0.3,1) both !important;
    }}
    [data-testid="block-container"] p,
    [data-testid="block-container"] span,
    [data-testid="block-container"] label,
    [data-testid="block-container"] h2,
    [data-testid="stCheckbox"] label span,
    .stTextInput label, .stSelectbox label, .stRadio label, .stTextArea label {{ color: #e2e8f0 !important; }}
    .form-page-heading {{ margin-bottom: 24px !important; }}
    .form-page-heading-center {{ text-align: center !important; }}
    .form-page-chip {{
        display: inline-flex !important; align-items: center !important; gap: 8px !important;
        padding: 6px 12px !important; margin-bottom: 14px !important; border-radius: 999px !important;
        background: rgba(56,189,248,0.14) !important; border: 1px solid rgba(125,211,252,0.28) !important;
        color: #bae6fd !important; font-size: 12px !important; font-weight: 700 !important;
        letter-spacing: 0.08em !important; text-transform: uppercase !important;
    }}
    .form-page-heading h2 {{
        margin: 0 0 8px 0 !important; color: #f8fafc !important;
        font-size: clamp(26px,4vw,34px) !important; font-weight: 800 !important;
        letter-spacing: -0.02em !important; line-height: 1.1 !important;
        text-shadow: 0 4px 24px rgba(15,23,42,0.48) !important;
    }}
    .form-page-heading p {{ margin: 0 !important; color: #cbd5e1 !important; font-size: 14px !important; line-height: 1.65 !important; }}
    .form-page-heading strong, .form-page-heading em {{ color: #f8fafc !important; }}
    .form-page-note {{
        background: rgba(255,255,255,0.08) !important; border: 1px dashed rgba(191,219,254,0.24) !important;
        padding: 12px 14px !important; border-radius: 10px !important;
        font-size: 12px !important; color: #cbd5e1 !important; margin-bottom: 20px !important; text-align: center !important;
    }}
    .form-page-note strong {{ color: #f8fafc !important; }}
    .form-page-links {{ margin-top: 15px !important; text-align: left !important; font-size: 13px !important; font-weight: 500 !important; }}
    .form-page-links a {{ color: #7dd3fc !important; text-decoration: none !important; }}
    .form-page-links a:hover {{ color: #e0f2fe !important; text-decoration: underline !important; }}
    .stSelectbox div[data-baseweb="select"],
    .stTextInput input, .stTextArea textarea {{
        background-color: rgba(255,255,255,0.96) !important; border: 1px solid rgba(191,219,254,0.9) !important;
        color: #0f172a !important; border-radius: 8px !important;
        box-shadow: 0 10px 30px rgba(15,23,42,0.16) !important;
    }}
    .stSelectbox div[data-baseweb="select"] *, .stTextInput input, .stTextArea textarea {{ color: #0f172a !important; }}
    .stSelectbox div[data-baseweb="select"] svg {{ fill: #0f172a !important; color: #0f172a !important; }}
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color: #64748b !important; }}
    ul[data-baseweb="menu"] {{ background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; }}
    ul[data-baseweb="menu"] li, ul[data-baseweb="menu"] li span {{ color: #0f172a !important; }}
    ul[data-baseweb="menu"] li:hover {{ background-color: #e0f2fe !important; }}
    div[data-testid="stAlert"] p {{ color: #0f172a !important; }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    import streamlit.components.v1 as components

    components.html(
        """<script>
    const observer = new MutationObserver(() => {
        const buttons = window.parent.document.querySelectorAll('button');
        buttons.forEach(btn => {
            const text = btn.innerText || btn.textContent;
            if (text.includes('Continue'))       btn.classList.add('btn-continue');
            else if (text.includes('Demo Fill')) btn.classList.add('btn-demo');
            else if (text.includes('Create Account')) btn.classList.add('btn-create-account');
            else if (text.includes('Back to Role'))   btn.classList.add('btn-back-role');
        });
    });
    observer.observe(window.parent.document.body, {childList: true, subtree: true});
    </script>""",
        height=0,
    )


# inject page transitions
def inject_page_transitions():
    import streamlit.components.v1 as components

    components.html(
        """
<style>
#et-page-overlay { position: fixed; inset: 0; z-index: 9999998; background: #080f1e; pointer-events: none; opacity: 0; }
#et-page-overlay.et-reveal { animation: etReveal 0.42s cubic-bezier(0.4,0,0.2,1) forwards; }
@keyframes etReveal { 0% { opacity: 1; } 100% { opacity: 0; } }
</style>
<script>
(function(){
    var doc = window.parent.document;
    function getOverlay(){
        var el = doc.getElementById('et-page-overlay');
        if(!el){ el = doc.createElement('div'); el.id='et-page-overlay'; doc.body.appendChild(el); }
        return el;
    }
    function triggerReveal(){ var o=getOverlay(); o.classList.remove('et-reveal'); o.style.opacity='1'; void o.offsetWidth; o.classList.add('et-reveal'); }
    function attachListeners(){ doc.querySelectorAll('button').forEach(function(btn){ if(btn.dataset.etDone) return; btn.dataset.etDone='1'; btn.addEventListener('click',triggerReveal); }); }
    triggerReveal();
    var mo = new MutationObserver(attachListeners);
    mo.observe(doc.body,{childList:true,subtree:true});
    attachListeners();
})();
</script>""",
        height=0,
    )


# init session state
def init_session_state():
    defaults = {
        "page": "welcome",
        "logged_in": False,
        "user_name": None,
        "selected_region": None,
        "selected_kifle_ketema": None,
        "selected_wereda": None,
        "selected_classroom": "11A",
        "is_homeroom": False,
        "dashboard_menu": "Dashboard",
        # Admin session state
        "admin_logged_in": False,
        "admin_user": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# navigate to
def navigate_to(page):
    st.session_state.page = page
    st.rerun()


# go back
def go_back():
    back_routes = {
        "region": "welcome",
        "kifle_ketema": "region",
        "wereda": "kifle_ketema",
        "school": "wereda",
        "role": "school",
        "register_teacher": "role",
        "register_parent": "role",
        "classroom_selection": "register_teacher",
        "login_teacher": "classroom_selection",
        "login_parent": "register_parent",
        "teacher_dashboard": "login_teacher",
        "parent_dashboard": "login_parent",
        "school_admin_dashboard": "role",
        "wereda_dashboard": "role",
        "addis_ababa_dashboard": "role",
        "admin_dashboard": "role",
    }
    if st.session_state.page in back_routes:
        st.session_state.page = back_routes[st.session_state.page]
        st.rerun()


# render form header
def render_form_header(title, subtitle, chip=None, centered=False):
    chip_html = f"<div class='form-page-chip'>{chip}</div>" if chip else ""
    centered_class = " form-page-heading-center" if centered else ""
    st.markdown(
        f"""
    <div class="form-page-heading{centered_class}">
        {chip_html}
        <h2>{title}</h2>
        <p>{subtitle}</p>
    </div>""",
        unsafe_allow_html=True,
    )


# render dashboard banner
def render_dashboard_banner(
    title,
    subtitle,
    panel_label,
    panel_value,
    panel_note,
    chip="Staff Portal",
    meta=None,
):
    meta_html = ""
    if meta:
        meta_html = (
            "<div class='dashboard-hero-meta'>"
            + "".join(f"<span>{i}</span>" for i in meta)
            + "</div>"
        )
    st.markdown(
        f"""
<div class="dashboard-hero">
<div class="dashboard-hero-grid">
<div>
<div class="staff-chip">{chip}</div>
<div class="dashboard-hero-title">{title}</div>
<p class="dashboard-hero-subtitle">{subtitle}</p>
{meta_html}
</div>
<div class="dashboard-hero-panel">
<div>
<div class="dashboard-hero-panel-label">{panel_label}</div>
<div class="dashboard-hero-panel-value">{panel_value}</div>
</div>
<div class="dashboard-hero-panel-note">{panel_note}</div>
</div>
</div>
</div>""",
        unsafe_allow_html=True,
    )


# render dashboard stats
def render_dashboard_stats(cards):
    stat_html = "".join(
        f"<div class='dashboard-stat-card'>"
        f"<div class='dashboard-stat-label'>{c['label']}</div>"
        f"<strong>{c['value']}</strong>"
        f"<div class='dashboard-stat-note'>{c['note']}</div>"
        f"</div>"
        for c in cards
    )
    st.markdown(
        f"<div class='dashboard-stats'>{stat_html}</div>", unsafe_allow_html=True
    )


# render dashboard section
def render_dashboard_section(title, subtitle):
    st.markdown(
        f"""
    <div class="dashboard-section">
        <h3>{title}</h3>
        <p>{subtitle}</p>
    </div>""",
        unsafe_allow_html=True,
    )


# render dashboard notice
def render_dashboard_notice(title, message, tone="warning"):
    tone_class = {
        "critical": "dashboard-notice-critical",
        "warning": "dashboard-notice-warning",
        "positive": "dashboard-notice-positive",
    }.get(tone, "dashboard-notice-warning")
    st.markdown(
        f"""
    <div class="dashboard-notice {tone_class}">
        <strong>{title}</strong>
        <span>{message}</span>
    </div>""",
        unsafe_allow_html=True,
    )


# style dashboard figure
def style_dashboard_figure(fig, title):
    fig.update_layout(
        title=dict(
            text=title,
            x=0.02,
            xanchor="left",
            font=dict(size=22, color="#0f172a", family="Inter, sans-serif"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.82)",
        margin=dict(l=28, r=28, t=78, b=36),
        font=dict(family="Inter, sans-serif", color="#334155", size=15),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,0.78)",
            font=dict(size=14, family="Inter, sans-serif"),
        ),
        coloraxis_colorbar=dict(
            thickness=16,
            outlinewidth=0,
            bgcolor="rgba(255,255,255,0.65)",
            tickfont=dict(size=13),
        ),
        hoverlabel=dict(font_size=14, font_family="Inter, sans-serif"),
        bargap=0.3,
        bargroupgap=0.14,
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor="rgba(148,163,184,0.35)",
        tickfont=dict(color="#475569", size=14),
        title_font=dict(color="#475569", size=15, family="Inter, sans-serif"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.20)",
        zeroline=False,
        tickfont=dict(color="#475569", size=14),
        title_font=dict(color="#475569", size=15, family="Inter, sans-serif"),
    )
    return fig


# show welcome
def show_welcome():
    st.markdown(
        """
    <style>
    html, body, [data-testid="stAppViewContainer"], .main { scroll-behavior: smooth !important; }
    .futuristic-header {
        position: fixed; top: 0; left: 0; right: 0; height: 80px;
        background-color: #000000; display: flex; justify-content: space-between;
        align-items: center; padding-left: 50px; padding-right: 150px;
        z-index: 100001; box-shadow: 0 4px 15px rgba(0,0,0,0.8);
    }
    .header-left { display: flex; align-items: center; gap: 15px; }
    .header-logo { height: 65px; object-fit: contain; }
    .header-title { color: #ffffff; font-family: 'Orbitron', sans-serif; font-size: 26px; font-weight: 900; margin: 0; letter-spacing: 2px; }
    .header-nav { display: flex; gap: 40px; }
    .header-nav button { color: #ffffff !important; background: transparent; border: none; padding: 0; font-size: 16px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; transition: color 0.3s ease, transform 0.3s ease; cursor: pointer; font-family: 'Inter', sans-serif; }
    .header-nav button:hover { color: #93c5fd !important; transform: translateY(-2px); }
    .welcome-container { position: relative; z-index: 10; width: 100%; color: white; display: flex; flex-direction: column; align-items: center; }
    .section { width: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 80px 40px; text-align: center; scroll-margin-top: 100px; }
    #home { min-height: 40vh; background: radial-gradient(circle at center, rgba(30,27,75,0.4) 0%, transparent 70%); padding-bottom: 20px !important; }
    .home-title { font-family: 'Orbitron', sans-serif; font-size: clamp(50px,8vw,100px); font-weight: 900; text-transform: uppercase; background: linear-gradient(90deg, #ffffff, #a855f7, #ffffff); background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: gradientShine 4s linear infinite; margin-bottom: 20px; letter-spacing: 6px; }
    #about { min-height: 80vh; background: rgba(15,23,42,0.6); border-top: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05); }
    .about-title { font-family: 'Montserrat', sans-serif; font-size: 50px; font-weight: 800; margin-bottom: 40px; color: #ffffff; letter-spacing: 2px; }
    .about-text { font-size: 18px; line-height: 1.8; max-width: 900px; color: #cbd5e1; text-align: justify; font-weight: 400; }
    .about-text p { margin: 0 0 24px 0; }
    .about-subtitle { font-family: 'Montserrat', sans-serif; font-size: 28px; font-weight: 800; color: #f8fafc; margin: 0 0 18px 0; letter-spacing: 0.5px; text-align: left; }
    .about-subheading { font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 800; color: #93c5fd; margin: 28px 0 12px 0; text-align: left; }
    .about-team-note { margin-top: 28px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.12); color: #e2e8f0; font-weight: 500; }
    #developers { min-height: 100vh; background: radial-gradient(circle at bottom, rgba(30,27,75,0.3) 0%, transparent 100%); }
    .dev-title { font-family: 'Montserrat', sans-serif; font-size: 50px; font-weight: 800; margin-bottom: 60px; color: #ffffff; letter-spacing: 2px; }
    .dev-cards { display: flex; flex-wrap: wrap; gap: 30px; justify-content: center; max-width: 1200px; }
    .dev-card-main { background: linear-gradient(135deg, #1e293b, #0f172a); color: #ffffff; width: 100%; max-width: 650px; padding: 50px 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 15px 40px rgba(0,0,0,0.6); transition: transform 0.4s cubic-bezier(0.175,0.885,0.32,1.275); display: flex; flex-direction: column; align-items: center; text-align: center; margin: 0 auto; }
    .dev-card-main:hover { transform: translateY(-10px) scale(1.02); box-shadow: 0 25px 50px rgba(96,165,250,0.3); }
    .dev-name-main { font-size: 32px; font-weight: 900; margin-bottom: 12px; color: #60a5fa; font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
    .dev-desc-main { font-size: 16px; color: #94a3b8; }
    .dev-card { background: #ffffff; color: #0f172a; width: 280px; padding: 35px 25px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); transition: transform 0.4s cubic-bezier(0.175,0.885,0.32,1.275), box-shadow 0.4s ease; display: flex; flex-direction: column; align-items: center; text-align: center; }
    .dev-card:hover { transform: translateY(-15px); box-shadow: 0 20px 40px rgba(147,51,234,0.3); }
    .dev-name { font-size: 22px; font-weight: 800; margin-bottom: 12px; font-family: 'Inter', sans-serif; color: #0f172a; }
    .dev-desc { font-size: 15px; color: #475569; font-weight: 500; line-height: 1.5; }
    .welcome-footer { padding: 30px; text-align: center; font-size: 15px; color: #64748b; width: 100%; font-weight: 500; letter-spacing: 1px; }
    .stButton { display: flex; justify-content: center; margin-top: 10px; margin-bottom: 60px; z-index: 20; }
    .stButton > button { background-color: #1d4ed8 !important; border: 1px solid #1e40af !important; border-radius: 50px !important; padding: 18px 50px !important; height: auto !important; min-height: 60px !important; font-size: 20px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 2px !important; color: #ffffff !important; transition: background-color 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease !important; position: relative; overflow: hidden; box-shadow: 0 0 20px rgba(30, 64, 175, 0.45) !important; }
    .stButton > button::before { display: none !important; }
    .stButton > button:hover { background-color: #2563eb !important; border-color: #3b82f6 !important; box-shadow: 0 8px 28px rgba(37, 99, 235, 0.45) !important; transform: translateY(-2px) !important; }
    .stButton > button {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
    }
    .stButton > button *,
    .stButton > button p,
    .stButton > button span,
    .stButton > button div,
    .stButton > button [data-testid="stMarkdownContainer"],
    .stButton > button [data-testid="stMarkdownContainer"] * {
        position: relative;
        z-index: 2 !important;
        margin: 0 !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    logo_path = os.path.join(BASE_DIR, "lognn.png")
    logo_base64 = get_base64_image(logo_path)
    logo_html = (
        f'<img src="data:image/png;base64,{logo_base64}" class="header-logo">'
        if logo_base64
        else '<div style="color:white;font-size:30px;font-weight:bold;">◎</div>'
    )

    st.markdown(
        f"""
    <div class="futuristic-header">
        <div class="header-left">{logo_html}<div class="header-title">LEARNIX</div></div>
        <div class="header-nav">
            <button type="button" data-target="home">Home</button>
            <button type="button" data-target="about">About</button>
            <button type="button" data-target="developers">Developers</button>
        </div>
    </div>
    <div style="height: 120px;"></div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="welcome-container">
        <div id="home" class="section">
            <div class="home-title">WELCOME TO LEARNIX</div>
            <div style="text-align: center; font-size: 21px; color: #94a3b8; font-weight: 500; margin-top: 12px; letter-spacing: 0.5px; font-family: 'IBM Plex Sans', sans-serif;">Smart Learning Analytics and Early Warning System</div>
        </div>
    </div>""",
        unsafe_allow_html=True,
    )

    _, c2, _ = st.columns([1, 1, 1])
    with c2:
        if st.button("Get Started", key="get_started_btn", use_container_width=True):
            navigate_to("region")

    st.markdown(
        """
<div class="welcome-container">
<div style="height: 80px;"></div>
<div id="about" class="section">
<div class="about-title">About</div>
<div class="about-text">
<div class="about-subtitle">Transforming Ethiopian Education Through Digital Innovation</div>
<p>Ethiopia's education system stands at a pivotal moment, one that calls for bold, purposeful reform. This platform was developed to meet that moment: a comprehensive digital ecosystem designed to bring transparency, efficiency, and data-informed decision-making to every level of the country's educational landscape.</p>
<div class="about-subheading">Empowering Every Stakeholder</div>
<p>At its core, this platform is about visibility and trust. Teachers gain the tools to monitor student progress with greater precision and deliver feedback that is consistent, timely, and meaningful. Parents now have direct access to attendance records, performance data, and real-time updates.</p>
<div class="about-subheading">Bridging Schools and Government</div>
<p>Beyond the individual classroom, this platform serves a broader national purpose by providing the Ethiopian Ministry of Education with structured, real-time access to school-level data, fundamentally improving how educational policy is shaped and implemented.</p>
<div class="about-subheading">Built for the Future</div>
<p>The platform has been deliberately designed with scalability in mind, with capacity for future integration of advanced analytics, predictive modelling, and optimization tools.</p>
<div class="about-subheading">Development Team</div>
<p class="about-team-note">This platform was designed and developed by Ethiopian high school students with a shared commitment to improving the future of education in their country.</p>
</div>
</div>
<div style="height: 150px;"></div>
<div id="developers" class="section">
<div class="dev-title">Developer</div>
<div style="display: flex; justify-content: center; width: 100%;">
<div class="dev-card-main">
<div class="dev-name-main">Bernabas.Mulugeta</div>
<div class="dev-desc-main">Grade 11 Student at New English Private School</div>
</div>
</div>
</div>
<div style="height: 100px;"></div>
<div id="others" class="section">
<div class="dev-title">Others</div>
<div class="dev-cards">
<div class="dev-card"><div class="dev-name">Jallel.Million</div><div class="dev-desc">Grade 11 Student at New English Private School</div></div>
<div class="dev-card"><div class="dev-name">Barkot.Daniel</div><div class="dev-desc">Grade 11 Student at New English Private School</div></div>
<div class="dev-card"><div class="dev-name">Eyeole.Yirga</div><div class="dev-desc">Grade 11 Student at New English Private School</div></div>
<div class="dev-card"><div class="dev-name">Henos</div><div class="dev-desc">Grade 11 Student at New English Private School</div></div>
</div>
</div>
<div style="height: 100px;"></div>
<div class="welcome-footer">© LEARNIX 2026</div>
</div>""",
        unsafe_allow_html=True,
    )

    import streamlit.components.v1 as components

    components.html(
        """<script>
    (function(){
        const doc = window.parent.document;
        const headerOffset = 96;
        function getScrollTargets(){ return [window.parent,doc.scrollingElement,doc.documentElement,doc.body,doc.querySelector('[data-testid="stAppViewContainer"]'),doc.querySelector('section[data-testid="stMain"]'),doc.querySelector('.main')].filter(Boolean); }
        function getAbsoluteTop(el){ const pageTop = window.parent.pageYOffset||doc.documentElement.scrollTop||doc.body.scrollTop||0; return el.getBoundingClientRect().top+pageTop; }
        function scrollToSection(id,extra){
            const el = doc.getElementById(id); if(!el) return false;
            const top = Math.max(getAbsoluteTop(el)-headerOffset+(extra||0),0);
            el.scrollIntoView({behavior:'smooth',block:'start'});
            getScrollTargets().forEach(function(t){ try{ if(typeof t.scrollTo==='function') t.scrollTo({top,behavior:'smooth'}); else t.scrollTop=top; }catch(e){} });
            window.setTimeout(function(){ try{ window.parent.scrollTo({top,behavior:'smooth'}); }catch(e){} },120);
            return true;
        }
        function bindNav(){
            if(doc.body.dataset.etWelcomeNavBound==='1') return;
            doc.body.dataset.etWelcomeNavBound='1';
            doc.addEventListener('click',function(e){
                const t=e.target.closest('.header-nav [data-target]'); if(!t) return;
                e.preventDefault(); e.stopPropagation();
                window.requestAnimationFrame(function(){ scrollToSection(t.getAttribute('data-target'),Number(t.getAttribute('data-extra-offset')||0)); });
            },true);
        }
        bindNav();
    })();
    </script>""",
        height=0,
    )


# show region
def show_region():
    render_form_header(
        "Select Region", "Choose your administrative region.", chip="School Setup"
    )
    selected = st.selectbox("Region", REGIONS, label_visibility="collapsed")
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back", use_container_width=True, type="secondary"):
            go_back()
    with c2:
        if st.button("Continue", use_container_width=True, type="primary"):
            if selected == "Select Region":
                st.error("Please select a region.")
            elif selected != "Addis Ababa":
                st.error("For this prototype, only 'Addis Ababa' is available.")
            else:
                st.session_state.selected_region = selected
                navigate_to("kifle_ketema")


# show kifle ketema
def show_kifle_ketema():
    render_form_header(
        "Select Kifle Ketema",
        f"Kifle Ketemas in {st.session_state.selected_region}.",
        chip="School Setup",
    )
    selected = st.selectbox("Kifle Ketema", KIFLE_KETEMAS, label_visibility="collapsed")
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back", use_container_width=True, type="secondary"):
            go_back()
    with c2:
        if st.button("Continue", use_container_width=True, type="primary"):
            if selected == "Select Kifle Ketema":
                st.error("Please select a Kifle Ketema.")
            else:
                st.session_state.selected_kifle_ketema = selected
                navigate_to("wereda")


# show wereda
def show_wereda():
    render_form_header(
        "Select Wereda",
        f"Weredas in {st.session_state.selected_kifle_ketema}.",
        chip="School Setup",
    )
    selected = st.selectbox("Wereda", WEREDAS, label_visibility="collapsed")
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back", use_container_width=True, type="secondary"):
            go_back()
    with c2:
        if st.button("Continue", use_container_width=True, type="primary"):
            if selected == "Select Wereda":
                st.error("Please select a Wereda.")
            else:
                st.session_state.selected_wereda = selected
                navigate_to("school")


# show school
def show_school():
    wereda = st.session_state.get("selected_wereda", "the selected area")
    render_form_header("Select School", f"Schools in {wereda}.", chip="School Setup")

    from helpers.ui_components import inject_school_card_css, render_clickable_school_card
    inject_school_card_css()

    known_schools = [s for s in SCHOOLS if s != "Select School"]
    
    cols = st.columns(4)
    for idx, school in enumerate(known_schools):
        with cols[idx % 4]:
            if render_clickable_school_card(school, key=f"pro_btn_{school}"):
                st.session_state.selected_school = school
                navigate_to("role")

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Back", use_container_width=True, type="secondary"):
            go_back()


# show role
def show_role():
    st.markdown(
        """
    <style>
    div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child { display: none !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 22px !important;
        width: 100% !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background: linear-gradient(180deg, rgba(15,23,42,0.92), rgba(30,41,59,0.88)) !important;
        border: 1px solid rgba(125,211,252,0.22) !important;
        border-radius: 20px !important;
        padding: 28px 26px !important;
        min-height: 152px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        cursor: pointer !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease, background 0.25s ease !important;
        box-shadow: 0 16px 40px rgba(2,6,23,0.32), inset 0 1px 0 rgba(255,255,255,0.05) !important;
        position: relative !important;
        overflow: hidden !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:focus-within {
        outline: 2px solid rgba(56,189,248,0.55) !important;
        outline-offset: 2px !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"] > div {
        width: 100% !important;
        min-height: 96px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"] p {
        color: #f8fafc !important;
        font-size: clamp(20px, 2.1vw, 26px) !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: -0.02em !important;
        text-align: left !important;
        line-height: 1.25 !important;
        transition: color 0.25s ease !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:nth-child(3) p,
    div[data-testid="stRadio"] label[data-baseweb="radio"]:nth-child(4) p,
    div[data-testid="stRadio"] label[data-baseweb="radio"]:nth-child(5) p,
    div[data-testid="stRadio"] label[data-baseweb="radio"]:nth-child(6) p {
        font-size: clamp(17px, 1.8vw, 22px) !important;
        max-width: 100% !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        border-color: rgba(125,211,252,0.5) !important;
        box-shadow: 0 22px 50px rgba(14,165,233,0.18), 0 12px 28px rgba(2,6,23,0.35) !important;
        transform: translateY(-4px) !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(div[aria-checked="true"]) {
        background: linear-gradient(135deg, rgba(8,47,73,0.96), rgba(29,78,216,0.72), rgba(15,23,42,0.95)) !important;
        border-color: rgba(186,230,253,0.65) !important;
        box-shadow: 0 24px 56px rgba(29,78,216,0.28), inset 0 1px 0 rgba(255,255,255,0.1) !important;
        transform: translateY(-2px) !important;
    }
    </style>""",
        unsafe_allow_html=True,
    )

    render_form_header(
        "Account Type", "Select your access level to sign in.", chip="Access Portal"
    )
    role = st.radio(
        "Role",
        [
            "Teacher",
            "Parent",
            "School Administration",
            "Wereda",
            "Kifle Ketema",
            "Addis Ababa",
            "Admin",
        ],
        label_visibility="collapsed",
    )
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back", use_container_width=True, type="secondary"):
            go_back()
    with c2:
        if st.button("Continue", use_container_width=True, type="primary"):
            if role == "School Administration":
                navigate_to("school_admin_dashboard")
            elif role == "Wereda":
                navigate_to("wereda_dashboard")
            elif role == "Kifle Ketema":
                navigate_to("kifle_ketema_dashboard")
            elif role == "Addis Ababa":
                navigate_to("addis_ababa_dashboard")
            elif role == "Admin":
                navigate_to("admin_dashboard")
            else:
                navigate_to(
                    "register_teacher" if role == "Teacher" else "register_parent"
                )


# show register
def show_register(role_type):
    title = (
        "Teacher Registration Form"
        if role_type == "teacher"
        else "Parent Registration Form"
    )
    render_form_header(
        title,
        "<em>Not a registered user?</em> Create an account below.",
        chip="Create Account",
    )

    form_keys = [
        "reg_fname",
        "reg_lname",
        "reg_email",
        "reg_address",
        "reg_id",
        "reg_pass",
        "reg_cpass",
    ]
    for k in form_keys:
        if k not in st.session_state:
            st.session_state[k] = ""

    demo_hint = "Teacher Demo" if role_type == "teacher" else "Parent Demo"
    st.markdown(
        f"<div class='form-page-note'><strong>{demo_hint}:</strong> Click Demo Fill to auto-fill.</div>",
        unsafe_allow_html=True,
    )

    if st.button(f"Demo Fill ({role_type.capitalize()})", type="secondary"):
        if role_type == "teacher":
            st.session_state.update(
                reg_fname="Tafesse",
                reg_lname="Tamirat",
                reg_email="tafessetamirat@gmail.com",
                reg_address="Ayer Tena",
                reg_id="neps-t-4567",
                reg_pass="1234",
                reg_cpass="1234",
            )
        else:
            st.session_state.update(
                reg_fname="Jallel",
                reg_lname="Million",
                reg_email="jallel.million@example.com",
                reg_address="Addis Ababa",
                reg_id="neps-s-8903",
                reg_pass="1234",
                reg_cpass="1234",
            )
        st.rerun()

    with st.form(f"register_{role_type}_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            fname = st.text_input(
                "First Name",
                value=st.session_state["reg_fname"],
                placeholder="e.g. Abebe",
            )
        with c2:
            lname = st.text_input(
                "Last Name",
                value=st.session_state["reg_lname"],
                placeholder="e.g. Kebede",
            )
        email = st.text_input(
            "Email Address",
            value=st.session_state["reg_email"],
            placeholder="name@example.com",
        )
        address = st.text_input(
            "Address",
            value=st.session_state["reg_address"],
            placeholder="e.g. Bole, Addis Ababa",
        )
        id_label = "Teacher ID" if role_type == "teacher" else "Student ID"
        user_id = st.text_input(id_label, value=st.session_state["reg_id"])
        c3, c4 = st.columns(2)
        with c3:
            password = st.text_input(
                "Password", value=st.session_state["reg_pass"], type="password"
            )
        with c4:
            cpassword = st.text_input(
                "Confirm Password", value=st.session_state["reg_cpass"], type="password"
            )
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            create = st.form_submit_button(
                "Create Account", type="primary", use_container_width=True
            )
        if create:
            if not all([fname, lname, email, address, user_id, password, cpassword]):
                st.error("Please fill all fields.")
            elif password != cpassword:
                st.error("Passwords do not match.")
            else:
                success, msg = register_user(
                    username=f"{fname} {lname}".strip(),
                    password=password,
                    role=role_type,
                    user_id_code=user_id
                )
                if success:
                    st.success(msg)
                    for k in form_keys:
                        st.session_state[k] = ""
                    navigate_to(
                        "classroom_selection" if role_type == "teacher" else "login_parent"
                    )
                else:
                    st.error(msg)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    if st.button("← Back to Role Selection", type="secondary"):
        for k in form_keys:
            st.session_state[k] = ""
        go_back()


# show classroom selection
def show_classroom_selection():
    render_form_header(
        "Classroom Selection",
        "Please select the classroom you are assigned to.",
        chip="Teacher Setup",
    )
    default_index = CLASSROOMS.index("11A") if "11A" in CLASSROOMS else 0
    selected = st.selectbox("Assign Classroom", CLASSROOMS, index=default_index)
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back", use_container_width=True, type="secondary"):
            go_back()
    with c2:
        if st.button("Confirm Classroom", use_container_width=True, type="primary"):
            st.session_state.selected_classroom = selected
            navigate_to("login_teacher")


# show login
def show_login(role_type):
    render_form_header(
        "Login Form", "Welcome back! Please enter your details.", chip="Secure Sign In"
    )

    login_keys = ["log_user", "log_id", "log_pass"]
    for k in login_keys:
        if k not in st.session_state:
            st.session_state[k] = ""

    demo_msg = (
        "<strong>Teacher Demo:</strong> Name: Tafesse | ID: neps-t-4567 | Pass: 1234"
        if role_type == "teacher"
        else "<strong>Parent Demo:</strong> Student: Jallel Million | ID: neps-s-8903 | Pass: 1234"
    )
    st.markdown(
        f"<div class='form-page-note'>{demo_msg}<br>Click Demo Fill below.</div>",
        unsafe_allow_html=True,
    )

    if st.button(f"Demo Fill ({role_type.capitalize()})", type="secondary"):
        if role_type == "teacher":
            st.session_state.update(
                log_user="Tafesse", log_id="neps-t-4567", log_pass="1234"
            )
        else:
            st.session_state.update(
                log_user="Jallel Million", log_id="neps-s-8903", log_pass="1234"
            )
        st.rerun()

    with st.form(f"login_{role_type}_form", clear_on_submit=False):
        label_user = "Username" if role_type == "teacher" else "Student Name"
        label_id = "Teacher ID" if role_type == "teacher" else "Student ID"
        user_input = st.text_input(label_user, value=st.session_state["log_user"])
        id_input = st.text_input(label_id, value=st.session_state["log_id"])
        password = st.text_input(
            "Password", value=st.session_state["log_pass"], type="password"
        )
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.checkbox("Remember Me")
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            back = st.form_submit_button("Back", use_container_width=True)
        with c2:
            submitted = st.form_submit_button(
                "Login", use_container_width=True, type="primary"
            )

        if submitted:
            if not all([user_input, id_input, password]):
                st.error("Please fill all required fields.")
            else:
                valid = verify_user(username=user_input, password=password, role=role_type)
                
                # Fallback to old hardcoded auth ONLY if not found in Database and to not break functionality
                if not valid:
                    if role_type == "teacher":
                        cred = TEACHER_CREDENTIALS.get(user_input.lower(), {})
                        valid = (user_input.lower() == "tafesse" and id_input == cred.get("id") and password == cred.get("pass"))
                    else:
                        cred = PARENT_CREDENTIALS.get(user_input.lower(), {})
                        valid = (user_input.lower() == "jallel million" and id_input == cred.get("id") and password == cred.get("pass"))

                if valid:
                    for k in login_keys:
                        st.session_state[k] = ""
                    st.session_state.logged_in = True
                    st.session_state.user_name = user_input
                    st.session_state.page = f"{role_type}_dashboard"
# log login event to activity_log
                    log_activity(user_input, "login", role_type,
                                 f"Logged in to {role_type} dashboard")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        if back:
            for k in login_keys:
                st.session_state[k] = ""
            go_back()

    st.markdown(
        """
    <div class='form-page-links'>
        <a href='#'>Register</a><br>
        <a href='#'>Stop forgetting your password</a>
    </div>""",
        unsafe_allow_html=True,
    )


# show teacher dashboard staff
def show_teacher_dashboard_staff():
    classroom = st.session_state.get("selected_classroom", "11A")
    teacher_name = (
        st.session_state.user_name.title() if st.session_state.user_name else "Teacher"
    )
    nav_options = list(DASH_MENU.keys())

    with st.sidebar:
        st.markdown(
            f"""
<div style='padding: 8px 4px 22px;'>
    <div class='staff-chip' style='background: rgba(96,165,250,0.12); color:#bfdbfe; border-color: rgba(191,219,254,0.14);'>Staff Only</div>
    <div style='font-size:32px; font-weight:900; color:#ffffff; letter-spacing:-0.03em; margin-top:14px;'>Class {classroom}</div>
    <div style='font-size:14px; color:#94a3b8; margin-top:8px; line-height:1.7;'>Academic staff workspace for {teacher_name}</div>
</div>""",
            unsafe_allow_html=True,
        )
        st.divider()

        if (
            "dashboard_menu" not in st.session_state
            or st.session_state.dashboard_menu not in nav_options
        ):
            st.session_state.dashboard_menu = "Dashboard"

        st.sidebar.radio(
            "Navigation",
            nav_options,
            key="dashboard_menu",
            label_visibility="collapsed",
        )
        st.divider()

        st.markdown(
            f"<p style='font-size:12px; color:#94a3b8; text-align:center; line-height:1.8;'>Signed in as<br><strong style='color:#dbeafe; font-size:14px;'>{teacher_name}</strong></p>",
            unsafe_allow_html=True,
        )
        if st.button("Sign Out", type="secondary", use_container_width=True):
            log_activity(st.session_state.user_name, "logout", "teacher", "Logged out from teacher dashboard")
            st.session_state.logged_in = False
            st.session_state.user_name = None
            if "dashboard_menu" in st.session_state:
                del st.session_state["dashboard_menu"]
            navigate_to("role")

    menu = st.session_state.dashboard_menu

    if menu == "Dashboard":
        _show_overview_dashboard(classroom, teacher_name)

    elif menu in ["1st Quarter", "2nd Quarter", "3rd Quarter", "4th Quarter"]:
        q_map = {
            "1st Quarter": "Q1",
            "2nd Quarter": "Q2",
            "3rd Quarter": "Q3",
            "4th Quarter": "Q4",
        }
        quarter = q_map[menu]
        _show_quarter_markbook(menu, quarter, classroom, teacher_name)
    elif menu == "Teacher Notes":
        _show_teacher_notes(classroom)
    elif menu == "System Initialization":
        _show_system_init()


# show overview dashboard
def _show_overview_dashboard(classroom, teacher_name):
    (
        avg_subject,
        quarterly_trend,
        weak_subjects,
        ranking_table,
        attendance_pct,
        q_att_pivot,
        perf,
    ) = compute_dashboard_data()

    student_count = len(get_students())
    has_data = not perf.empty

    class_average = perf["Average"].mean() if has_data else 0.0
    attendance_avg = (
        attendance_pct["Attendance %"].mean() if not attendance_pct.empty else 0.0
    )
    top_student_name = "No data"
    top_student_score = 0.0
    strongest_subject = "No data"
    strongest_score = 0.0

    if has_data and not ranking_table.empty:
        top_row = ranking_table.sort_values("Overall Avg", ascending=False).iloc[0]
        top_student_name = top_row["Student"].replace(".", " ")
        top_student_score = top_row["Overall Avg"]
    if not avg_subject.empty:
        strongest_subject = avg_subject.index[0]
        strongest_score = avg_subject.iloc[0]

    render_dashboard_banner(
        "Academic Staff Dashboard",
        f"Review performance, rankings, attendance, and academic concerns for Class {classroom}.",
        "Access Scope",
        f"Class {classroom}",
        "Internal view for marks, attendance, and note management.",
        chip="Staff Portal",
        meta=[
            f"Teacher: {teacher_name}",
            f"Students: {student_count}",
            "Live academic tracking",
        ],
    )
    render_dashboard_stats(
        [
            {
                "label": "Class Average",
                "value": f"{class_average:.1f}",
                "note": "Average score across all recorded quarters and subjects.",
            },
            {
                "label": "Strongest Subject",
                "value": strongest_subject,
                "note": f"Current leading subject avg: {strongest_score:.1f}.",
            },
            {
                "label": "Attendance",
                "value": f"{attendance_avg:.1f}%",
                "note": "Yearly attendance rate.",
            },
            {
                "label": "Top Student",
                "value": top_student_name,
                "note": f"Highest overall avg: {top_student_score:.1f}.",
            },
        ]
    )

    if not has_data:
        st.info(
            "No grade data yet. Go to a Quarter markbook or System Initialization to add records."
        )
        return

    fig_bar = px.bar(
        x=avg_subject.index,
        y=avg_subject.values,
        labels={"x": "Subject", "y": "Average Score"},
        color=avg_subject.values,
        color_continuous_scale=[[0.0, "#bfdbfe"], [0.55, "#38bdf8"], [1.0, "#0f4c81"]],
    )
    fig_bar.update_traces(
        marker=dict(line=dict(color="rgba(15,23,42,0.18)", width=1.2)),
        hovertemplate="<b>%{x}</b><br>Avg: %{y:.1f}<extra></extra>",
    )
    fig_bar.update_layout(coloraxis_showscale=False)
    fig_bar.update_xaxes(tickangle=-25)
    style_dashboard_figure(fig_bar, "Average Score per Subject")

    fig_line = px.line(quarterly_trend, x="Quarter", y="Average Score", markers=True)
    fig_line.update_traces(
        line=dict(color="#0f4c81", width=4),
        marker=dict(size=10, color="#38bdf8", line=dict(color="#ffffff", width=2)),
        hovertemplate="<b>%{x}</b><br>Avg: %{y:.1f}<extra></extra>",
    )
    style_dashboard_figure(fig_line, "Class Average Trend")

    render_dashboard_section(
        "Performance Overview", "Class trend and subject distribution."
    )
    col1, col2 = st.columns([1.15, 0.85])
    with col1:
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        st.plotly_chart(fig_line, use_container_width=True)

    sem1 = (
        perf[perf["Quarter"].isin(["Q1", "Q2"])]
        .groupby("Student")["Average"]
        .mean()
        .reset_index()
        .rename(columns={"Average": "Semester Average"})
    )
    sem2 = (
        perf[perf["Quarter"].isin(["Q3", "Q4"])]
        .groupby("Student")["Average"]
        .mean()
        .reset_index()
        .rename(columns={"Average": "Semester Average"})
    )
    yearly = ranking_table[["Student", "Overall Avg"]].copy()

    render_dashboard_section(
        "Recognition Snapshot", "Top performers by semester and full year."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "<div class='dashboard-mini-heading'>Top 5: 1st Semester</div>",
            unsafe_allow_html=True,
        )
        st.dataframe(
            sem1.sort_values("Semester Average", ascending=False)
            .head(5)
            .reset_index(drop=True)
            .style.format({"Semester Average": "{:.1f}"}),
            use_container_width=True,
        )
    with c2:
        st.markdown(
            "<div class='dashboard-mini-heading'>Top 5: 2nd Semester</div>",
            unsafe_allow_html=True,
        )
        st.dataframe(
            sem2.sort_values("Semester Average", ascending=False)
            .head(5)
            .reset_index(drop=True)
            .style.format({"Semester Average": "{:.1f}"}),
            use_container_width=True,
        )
    with c3:
        st.markdown(
            "<div class='dashboard-mini-heading'>Top 5: Full Year</div>",
            unsafe_allow_html=True,
        )
        st.dataframe(
            yearly.sort_values("Overall Avg", ascending=False)
            .head(5)
            .reset_index(drop=True)
            .style.format({"Overall Avg": "{:.1f}"}),
            use_container_width=True,
        )

    render_dashboard_section(
        "Class Rankings", "Quarter-by-quarter comparison and overall standing."
    )
    fmt = {c: "{:.1f}" for c in ["Q1", "Q2", "Q3", "Q4", "Overall Avg"]}
    fmt.update(
        {
            c: "{:.0f}"
            for c in ["Q1 Rank", "Q2 Rank", "Q3 Rank", "Q4 Rank", "Overall Rank"]
        }
    )
    st.dataframe(ranking_table.style.format(fmt, na_rep="—"), use_container_width=True)

    if not attendance_pct.empty:
        render_dashboard_section(
            "Attendance Review", "Yearly attendance rate per student."
        )
        fig_att = px.bar(
            attendance_pct,
            x="Student",
            y="Attendance %",
            color="Attendance %",
            color_continuous_scale=[
                [0.0, "#dc2626"],
                [0.55, "#f59e0b"],
                [1.0, "#16a34a"],
            ],
            range_color=[0, 100],
        )
        fig_att.update_traces(
            marker=dict(line=dict(color="rgba(15,23,42,0.16)", width=0.8)),
            hovertemplate="<b>%{x}</b><br>Attendance: %{y:.1f}%<extra></extra>",
        )
        fig_att.update_layout(coloraxis_showscale=False)
        fig_att.update_xaxes(tickangle=-35)
        fig_att.update_yaxes(range=[0, 100])
        style_dashboard_figure(fig_att, "Yearly Attendance by Student")
        st.plotly_chart(fig_att, use_container_width=True)

    render_dashboard_section("Subject Alerts", "Subjects needing intervention.")
    if weak_subjects:
        render_dashboard_notice(
            "Weak subjects detected",
            f"Average below 60 in: {', '.join(weak_subjects)}.",
            tone="warning",
        )
    else:
        render_dashboard_notice(
            "Healthy subject performance",
            "All subjects are currently above the 60-point monitoring threshold.",
            tone="positive",
        )


# show quarter markbook
def _show_quarter_markbook(menu, quarter, classroom, teacher_name):
    db_students = [s["name"] for s in get_students()]
    db_subjects = [s["name"] for s in get_subjects() if s["name"] != "__TERM_ATT__"]

    render_dashboard_banner(
        f"{menu} Markbook",
        f"Review and update marks for Class {classroom}. Changes save automatically.",
        "Quarter Code",
        quarter,
        "Expand a student record to edit component scores and attendance.",
        chip="Staff Workspace",
        meta=[
            f"Teacher: {teacher_name}",
            f"Students: {len(db_students)}",
            "Scores and attendance",
        ],
    )
    render_dashboard_stats(
        [
            {
                "label": "Students",
                "value": str(len(db_students)),
                "note": "Student records in this classroom.",
            },
            {
                "label": "Subjects",
                "value": str(len(db_subjects)),
                "note": "Subjects in each markbook.",
            },
            {
                "label": "Components",
                "value": str(len(COMPONENTS)),
                "note": "Scored components per subject.",
            },
            {
                "label": "Attendance Codes",
                "value": "P / A / L",
                "note": "Present, Absent, and Late.",
            },
        ]
    )

    if len(db_students) == 0:
        st.info(
            "No students found. Add your first student below or use System Initialization to upload an Excel file."
        )
        with st.form("inline_student_add"):
            ns = st.text_input("Student name (e.g. Abebe.Kebede)")
            if st.form_submit_button("Add Student", type="primary") and ns.strip():
                get_or_create_student(ns.strip())
                st.rerun()
        return

    if len(db_subjects) == 0:
        st.info(
            "No subjects found. Go to System Initialization to upload an Excel file "
            "with subjects included, or contact your administrator."
        )
        return

    render_dashboard_section(
        "Entry Guidance",
        "Expand a student to edit marks. Attendance: P = Present, A = Absent, L = Late.",
    )
    st.info(
        f"Showing {len(db_students)} student(s) for {quarter}. Enter scores in each component row, then save."
    )

    term_row = get_term_row(quarter)
    if term_row is None:
        get_or_create_term(quarter)
        term_row = get_term_row(quarter)

    for student_name in db_students:
        student_row = get_student_row(student_name)
        if student_row is None:
            continue
        student_id = student_row["id"]
        term_id = term_row["id"]

        df_raw = build_student_markbook_df(student_id, term_id, db_subjects)

        with st.expander(student_name.replace(".", " "), expanded=False):
            edited_df = st.data_editor(
                df_raw,
                key=f"de_{quarter}_{student_name}",
                use_container_width=True,
                num_rows="fixed",
            )

            for comp, max_val in COMPONENTS.items():
                for subj in db_subjects:
                    raw = edited_df.at[comp, subj]
                    if _is_blank_markbook_value(raw):
                        edited_df.at[comp, subj] = ""
                        continue
                    try:
                        val = max(0, min(int(float(raw)), max_val))
                        edited_df.at[comp, subj] = val
                    except (ValueError, TypeError):
                        edited_df.at[comp, subj] = ""

            totals = compute_student_totals(edited_df)
            st.markdown(
                "<div class='dashboard-mini-heading'>Subject totals (out of 100)</div>",
                unsafe_allow_html=True,
            )
            st.dataframe(
                pd.DataFrame(totals).T.style.format("{:.0f}"), use_container_width=True
            )

            if st.button(
                f"Save {student_name.replace('.', ' ')}",
                key=f"save_{quarter}_{student_name}",
                type="primary",
            ):
                for subj in db_subjects:
                    sub_row = get_subject_row(subj)
                    if sub_row is None:
                        continue
                    subject_id = sub_row["id"]

                    component_scores = {
                        comp: edited_df.at[comp, subj] for comp in COMPONENTS
                    }
                    save_component_scores(
                        student_id, subject_id, term_id, component_scores
                    )

                att_code = (
                    str(edited_df.at[ATTENDANCE_ROW, db_subjects[0]]).upper().strip()
                )
                if att_code not in ("P", "A", "L"):
                    att_code = "P"
                save_student_attendance(student_id, term_id, att_code)
                st.success(f"Saved marks for {student_name.replace('.', ' ')}!")
                st.rerun()


# show teacher notes
def _show_teacher_notes(classroom):
    students_data = get_students()
    students_list = [s["name"] for s in students_data]

    conn = get_db_connection()
    df_notes = (
        pd.read_sql_query(
            """
        SELECT s.name AS Student, t.note, t.date_recorded
        FROM teacher_notes t
        JOIN students s ON t.student_id = s.id
        ORDER BY t.date_recorded DESC
    """,
            conn,
        )
        if conn
        else pd.DataFrame()
    )
    if conn:
        conn.close()

    render_dashboard_banner(
        "Teacher Notes and Concerns",
        f"Record staff-only observations for Class {classroom}.",
        "Recorded Entries",
        str(len(df_notes)),
        "Private observation log for concerns, interventions, and communication.",
        chip="Staff Notes",
    )

    note_col, status_col = st.columns([1.2, 0.8])
    with note_col:
        render_dashboard_section("Create New Note", "Capture observations.")
        with st.form("teacher_notes_form"):
            if students_list:
                student = st.selectbox("Select Student", students_list)
                note = st.text_area("Note / Concern", height=140)
                if st.form_submit_button("Save Note", type="primary"):
                    if note.strip():
                        s_row = get_student_row(student)
                        if s_row:
                            conn = get_db_connection()
                            try:
                                c = conn.cursor()
                                c.execute(
                                    "INSERT INTO teacher_notes (student_id, note) VALUES (?, ?)",
                                    (s_row["id"], note.strip()),
                                )
                                conn.commit()
                                st.success("Note saved.")
                                st.rerun()
                            finally:
                                conn.close()
                    else:
                        st.error("Please enter a note before saving.")
            else:
                st.warning("No students in database. Add students first.")
                st.form_submit_button("Save Note", disabled=True)

    with status_col:
        render_dashboard_section("Staff Guidance", "Keep entries short and factual.")
        if len(df_notes) > 0:
            render_dashboard_notice(
                "Existing Notes", f"{len(df_notes)} notes found.", tone="positive"
            )
        else:
            render_dashboard_notice(
                "No notes yet",
                "Add the first observation from the form.",
                tone="positive",
            )

    render_dashboard_section("Logged Notes", "Review saved notes.")
    if not df_notes.empty:
        for s in df_notes["Student"].unique():
            s_notes = df_notes[df_notes["Student"] == s]
            with st.expander(
                f"{s} ({len(s_notes)} note{'s' if len(s_notes) > 1 else ''})"
            ):
                for _, row in s_notes.iterrows():
                    st.markdown(
                        f"<div class='dashboard-note-item'><strong>{row['date_recorded']}</strong><br>{row['note']}</div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.info("No saved notes found.")


# show system init
def _show_system_init():
    render_dashboard_banner(
        "System Initialization & Data Upload",
        "Upload a master Excel file to initialise or refresh the grade database.",
        "Process",
        "Data Upload",
        "Required columns: student_name, subject, score, attendance_percentage, term",
        chip="Admin Function",
        meta=["Supported format: .xlsx", "Required columns listed above"],
    )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    st.subheader("Upload Excel File")
    upload_mode = st.radio(
        "Upload Mode",
        ["Append (keep existing data)", "Overwrite (clear all data first)"],
        index=0,
        horizontal=True,
    )
    uploaded_file = st.file_uploader("Master Excel File", type=["xlsx", "xls"])

    if uploaded_file is not None:
        if st.button("Process Excel File", type="primary"):
            import tempfile
            import shutil

            with st.spinner("Processing..."):
                suffix = ".xlsx" if uploaded_file.name.endswith(".xlsx") else ".xls"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    shutil.copyfileobj(uploaded_file, tmp)
                    tmp_path = tmp.name
                clear = "Overwrite" in upload_mode
                success, msg = upload_grades_from_excel(tmp_path, clear_existing=clear)
                os.unlink(tmp_path)
                if success:
                    st.success(msg)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("<hr>", unsafe_allow_html=True)

    render_dashboard_section(
        "Manual Setup", "Add students individually without uploading an Excel file."
    )

    with st.form("manual_student_form"):
        st.write("**Add New Student**")
        new_student = st.text_input("Student Name", placeholder="e.g. Abebe.Kebede")
        if st.form_submit_button("Save Student", type="primary"):
            if new_student.strip():
                result = get_or_create_student(new_student.strip())
                if result:
                    st.success(f"Student '{new_student.strip()}' added.")
                else:
                    st.error("Failed to add student.")
            else:
                st.error("Name cannot be empty.")

    st.markdown("<hr>", unsafe_allow_html=True)
    render_dashboard_section(
        "Current Database Snapshot", "Live view of what is in the database right now."
    )

    students_now = get_students()
    subjects_now = [s for s in get_subjects() if s["name"] != "__TERM_ATT__"]

    snap_c1, snap_c2 = st.columns(2)
    with snap_c1:
        st.markdown(f"**Students ({len(students_now)})**")
        if students_now:
            st.dataframe(
                pd.DataFrame(students_now)[["name"]].rename(columns={"name": "Name"}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No students yet.")

    with snap_c2:
        st.markdown(f"**Subjects ({len(subjects_now)})**")
        if subjects_now:
            st.dataframe(
                pd.DataFrame(subjects_now)[["name"]].rename(
                    columns={"name": "Subject"}
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No subjects yet.")

    with st.expander("Danger Zone — Clear All Data"):
        st.warning(
            "This will permanently delete ALL grades, students, subjects, attendance and notes from the database."
        )
        if st.button("Clear Entire Database", type="secondary"):
            conn = get_db_connection()
            if conn:
                try:
                    c = conn.cursor()
                    for tbl in [
                        "component_grades",
                        "teacher_notes",
                        "grades",
                        "attendance",
                        "students",
                        "subjects",
                        "terms",
                    ]:
                        c.execute(f"DELETE FROM {tbl}")
                    conn.commit()
                    st.success("Database cleared. Quarter terms have been re-seeded.")
                    for q in QUARTERS:
                        c.execute("INSERT OR IGNORE INTO terms (name) VALUES (?)", (q,))
                    conn.commit()
                    st.rerun()
                finally:
                    conn.close()


# generate ai insight
def generate_ai_insight(current_avg, prev_avg):
    if prev_avg is None:
        return "Stable early performance baseline."
    diff = current_avg - prev_avg
    if diff >= 3:
        return "Performance has improved compared to last quarter."
    elif diff <= -3:
        return "Performance has declined in recent quarters."
    else:
        return "Performance remains stable."


# show parent overview
def _show_parent_overview(student_name, df_grades):
    if df_grades.empty:
        st.info("No academic records available yet.")
        return

    total_subjects = get_total_subjects_count()
    if total_subjects == 0:
        st.info("System configuration error: No valid subjects defined.")
        return

    completed_quarters_list = [
        q for q in QUARTERS if is_quarter_complete_for_student(student_name, q)
    ]
    num_complete = len(completed_quarters_list)
    all_complete = num_complete == 4

    if all_complete:
        df_comp = df_grades[df_grades["score"].notna()].copy()
        subject_avgs = df_comp.groupby("Subject")["score"].mean()
        overall_avg = df_comp["score"].mean()
        best_sub = subject_avgs.idxmax()
        best_sco = subject_avgs.max()
        weak_sub = subject_avgs.idxmin()
        weak_sco = subject_avgs.min()
        render_dashboard_stats(
            [
                {
                    "label": "Overall Average",
                    "value": f"{overall_avg:.1f}",
                    "note": "All 4 quarters complete",
                },
                {
                    "label": "Best Subject",
                    "value": best_sub,
                    "note": f"Avg: {best_sco:.1f}",
                },
                {
                    "label": "Weakest Subject",
                    "value": weak_sub,
                    "note": f"Avg: {weak_sco:.1f}",
                },
                {
                    "label": "Performance Status",
                    "value": "Complete",
                    "note": "Full analytics available",
                },
            ]
        )
        weak_list = subject_avgs[subject_avgs < 60].index.tolist()
        if len(weak_list) >= 2:
            render_dashboard_notice(
                "Immediate Attention Required",
                f"Multiple subjects average below 60: {', '.join(weak_list)}.",
                tone="critical",
            )
        elif len(weak_list) == 1:
            render_dashboard_notice(
                "Performance Improvement Required",
                f"{weak_list[0]} averages below 60 and needs attention.",
                tone="warning",
            )
    else:
        completed_qs_str = (
            ", ".join(completed_quarters_list) if completed_quarters_list else "None"
        )
        render_dashboard_stats(
            [
                {
                    "label": "Overall Average",
                    "value": "Incomplete",
                    "note": "Awaiting all quarters",
                },
                {"label": "Best Subject", "value": "Incomplete", "note": "-"},
                {"label": "Weakest Subject", "value": "Incomplete", "note": "-"},
                {
                    "label": "Performance Status",
                    "value": "Incomplete",
                    "note": f"{num_complete}/4 quarters complete ({completed_qs_str})",
                },
            ]
        )
        render_dashboard_notice(
            "Yearly Insights Locked Until All Quarters Are Submitted",
            f"Full yearly analysis and predictions will unlock once all 4 quarters are completely recorded. "
            f"Currently {num_complete} of 4 quarters fully complete.",
            tone="warning",
        )

    st.markdown(
        "<hr style='margin: 32px 0; border-color: rgba(203,213,225,0.4);'>",
        unsafe_allow_html=True,
    )

    if not all_complete:
        st.markdown(
            """
        <div style='background:rgba(245,158,11,0.08); border:1px solid #f59e0b; border-radius:12px;
                    padding:14px 20px; margin-bottom:20px;'>
            <span style='color:#92400e; font-weight:700; font-size:15px; line-height:1.5;'>
                Partial Data – Full Analysis Locked
            </span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    render_dashboard_section(
        "Component Trend Overview",
        "Cross-quarter trends per assessment type. Available regardless of overall completeness.",
    )

    all_comps_rows = []
    for q in QUARTERS:
        df_c = get_student_component_grades_df(student_name, q)
        if not df_c.empty:
            mask = df_c["score"].apply(
                lambda s: _parent_component_value_for_analytics(s) is not None
            )
            df_c = df_c[mask]
        if not df_c.empty:
            df_c["Quarter"] = q
            all_comps_rows.append(df_c)

    if all_comps_rows:
        df_all_comps = pd.concat(all_comps_rows, ignore_index=True)
        mask2 = df_all_comps["score"].apply(
            lambda s: _parent_component_value_for_analytics(s) is not None
        )
        df_all_comps = df_all_comps[mask2]
        comp_trend = (
            df_all_comps.groupby(["Quarter", "Component"])["score"].mean().reset_index()
        )
        q_order = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
        comp_trend["Q_idx"] = comp_trend["Quarter"].map(q_order)
        comp_trend = comp_trend.sort_values("Q_idx")

        fig_comp_trend = px.line(
            comp_trend,
            x="Quarter",
            y="score",
            color="Component",
            markers=True,
            color_discrete_sequence=[
                "#9333ea",
                "#3b82f6",
                "#f59e0b",
                "#ef4444",
                "#10b981",
            ],
        )
        fig_comp_trend.update_traces(line=dict(width=3), marker=dict(size=9))
        style_dashboard_figure(fig_comp_trend, "Component Score Trends Across Quarters")
        st.plotly_chart(fig_comp_trend, use_container_width=True)
    else:
        st.info("No component data recorded yet to build trend graphs.")

    if all_complete:
        render_dashboard_section(
            "Full Performance Journey",
            "Complete annual academic trajectory and trend predictions.",
        )
        df_comp_full = df_grades[
            (df_grades["Quarter"].isin(completed_quarters_list))
            & (df_grades["score"].notna())
        ]
        quarterly_trend = df_comp_full.groupby("Quarter")["score"].mean().reset_index()
        quarterly_trend["Q_idx"] = quarterly_trend["Quarter"].map(
            {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
        )
        quarterly_trend = quarterly_trend.sort_values("Q_idx")

        x_vals = np.arange(len(quarterly_trend))
        y_vals = quarterly_trend["score"].values
        slope, intercept = np.polyfit(x_vals, y_vals, 1)
        next_pred = slope * len(quarterly_trend) + intercept
        trend_str = (
            "Improving" if slope > 1 else ("Declining" if slope < -1 else "Stable")
        )
        badge_color = (
            "#16a34a" if slope > 1 else ("#dc2626" if slope < -1 else "#f59e0b")
        )

        fig_line = px.line(quarterly_trend, x="Quarter", y="score", markers=True)
        fig_line.update_traces(
            line=dict(color="#9333ea", width=4),
            marker=dict(size=10, color="#d8b4fe", line=dict(color="#ffffff", width=2)),
            hovertemplate="<b>%{x}</b><br>Avg: %{y:.1f}<extra></extra>",
        )
        style_dashboard_figure(fig_line, "Annual Academic Progress")

        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.plotly_chart(fig_line, use_container_width=True)
        with c2:
            st.markdown(
                f"""
            <div style='background:rgba(255,255,255,0.94); padding:24px; border-radius:24px;
                        border:1px solid rgba(203,213,225,0.75); height:100%;
                        box-shadow:0 18px 40px rgba(15,23,42,0.09);'>
                <h4 style='color:#0f172a; margin-top:0; font-size:22px; font-weight:800; font-family: Inter, system-ui, sans-serif;'>Trend analysis</h4>
                <p style='color:#64748b; font-size:16px; margin-bottom:14px; line-height:1.55;'>Based on all four complete quarters:</p>
                <div style='display:inline-block; font-size:17px; font-weight:800; color:{badge_color};
                            background:rgba(255,255,255,0.9); border:1px solid #cbd5e1;
                            padding:8px 16px; border-radius:99px;'>{trend_str}</div>
                <div style='margin-top:22px;'>
                    <p style='color:#0f172a; font-weight:700; font-size:16px; margin-bottom:6px;'>Predicted final trajectory</p>
                    <p style='color:#9333ea; font-size:34px; font-weight:900; margin:0;'>~{min(100, max(0, int(next_pred)))}</p>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown(
        "<hr style='margin: 32px 0; border-color: rgba(203,213,225,0.4);'>",
        unsafe_allow_html=True,
    )
    render_dashboard_section(
        "Detailed Breakdown", "Numerical records across all evaluated quarters."
    )
    grade_table = df_grades.pivot(
        index="Subject", columns="Quarter", values="score"
    ).reset_index()
    for q in QUARTERS:
        if q not in grade_table.columns:
            grade_table[q] = np.nan
    numeric_cols = [q for q in QUARTERS if q in grade_table.columns]
    if all_complete:
        grade_table["Yearly Avg"] = grade_table[numeric_cols].mean(axis=1)
    else:
        grade_table["Yearly Avg"] = np.nan
    fmt = {c: "{:.1f}" for c in QUARTERS + ["Yearly Avg"]}
    st.dataframe(
        grade_table.style.format(fmt, na_rep="—"),
        use_container_width=True,
        hide_index=True,
    )


# show parent quarter
def _show_parent_quarter(quarter, student_name, df_grades):
    total_subjects = get_total_subjects_count()
    if total_subjects == 0:
        st.info("System configuration error: No valid subjects defined.")
        return

    expected_components_count = total_subjects * len(COMPONENTS)
    df_q = df_grades[(df_grades["Quarter"] == quarter) & df_grades["score"].notna()]
    recorded_components_count = count_parent_filled_component_slots(
        student_name, quarter
    )
    is_quarter_complete = is_quarter_complete_for_student(student_name, quarter)

    if not is_quarter_complete:
        st.markdown(
            "<div class='dashboard-mini-heading' style='margin-top:0px; color:#ea580c;'>Status: Incomplete</div>",
            unsafe_allow_html=True,
        )
        render_dashboard_stats(
            [
                {
                    "label": "Quarter Average",
                    "value": "Incomplete",
                    "note": "Awaiting remaining marks",
                },
                {"label": "Best Subject", "value": "Incomplete", "note": "-"},
                {"label": "Weakest Subject", "value": "Incomplete", "note": "-"},
                {
                    "label": "Performance Status",
                    "value": "Incomplete",
                    "note": "Missing data",
                },
            ]
        )
        render_dashboard_notice(
            "Quarter Summary: Incomplete",
            f"Some subject–component marks are still missing, so the quarter summary stays Incomplete. "
            f"Recorded: {recorded_components_count}/{expected_components_count} component entries. "
            f"Open each assessment type below—graphs, warnings, and predictions use only subjects with real scores; missing subjects are skipped.",
            tone="warning",
        )
    else:
        current_avg = df_q["score"].mean()
        best_sub = (
            df_q.loc[df_q["score"].idxmax()]["Subject"] if not df_q.empty else "N/A"
        )
        best_sco = df_q["score"].max() if not df_q.empty else 0
        weak_sub = (
            df_q.loc[df_q["score"].idxmin()]["Subject"] if not df_q.empty else "N/A"
        )
        weak_sco = df_q["score"].min() if not df_q.empty else 0

        render_dashboard_stats(
            [
                {
                    "label": "Quarter Average",
                    "value": f"{current_avg:.1f}",
                    "note": f"Avg for {quarter}",
                },
                {
                    "label": "Best Subject",
                    "value": best_sub,
                    "note": f"Score: {best_sco:.1f}",
                },
                {
                    "label": "Weakest Subject",
                    "value": weak_sub,
                    "note": f"Score: {weak_sco:.1f}",
                },
                {
                    "label": "Performance Status",
                    "value": "Complete",
                    "note": "All components recorded",
                },
            ]
        )

        prev_q_map = {"Q2": "Q1", "Q3": "Q2", "Q4": "Q3"}
        prev_avg = None
        if quarter in prev_q_map:
            pq = prev_q_map[quarter]
            if is_quarter_complete_for_student(student_name, pq):
                prev_df = df_grades[
                    (df_grades["Quarter"] == pq) & df_grades["score"].notna()
                ]
                if not prev_df.empty:
                    prev_avg = prev_df["score"].mean()

        insight_msg = generate_ai_insight(current_avg, prev_avg)
        render_dashboard_notice(
            f"{quarter} Progress Insight",
            insight_msg,
            tone="positive"
            if "improved" in insight_msg
            else ("warning" if "declined" in insight_msg else "positive"),
        )

        fig_bar = px.bar(
            df_q.sort_values("score", ascending=False),
            x="Subject",
            y="score",
            color="score",
            color_continuous_scale=[
                [0.0, "#dc2626"],
                [0.55, "#f59e0b"],
                [1.0, "#16a34a"],
            ],
        )
        fig_bar.update_traces(
            marker=dict(line=dict(color="rgba(15,23,42,0.18)", width=1.2)),
            hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<extra></extra>",
        )
        fig_bar.update_layout(coloraxis_showscale=False)
        style_dashboard_figure(fig_bar, f"{quarter} Subject Standings")

        fig_pie = px.pie(
            df_q,
            values="score",
            names="Subject",
            hole=0.4,
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>Weight: %{value:.1f}<extra></extra>",
        )
        fig_pie.update_layout(
            title=dict(
                text="Performance Distribution",
                x=0.02,
                xanchor="left",
                font=dict(
                    size=22, color="#0f172a", family="Inter, sans-serif", weight="bold"
                ),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=24, r=24, t=76, b=32),
            font=dict(family="Inter, sans-serif", color="#334155", size=15),
            legend=dict(
                orientation="v",
                yanchor="auto",
                y=0.5,
                xanchor="left",
                x=1.0,
                font=dict(size=14),
            ),
            hoverlabel=dict(font_size=14, font_family="Inter, sans-serif"),
        )

        col1, col2 = st.columns([1.2, 0.8])
        with col1:
            st.plotly_chart(fig_bar, use_container_width=True)
        with col2:
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown(
            "<div class='dashboard-mini-heading' style='margin-top:20px;'>Performance Badges</div>",
            unsafe_allow_html=True,
        )
        badge_html = ""
        for _, row in df_q.iterrows():
            s = row["score"]
            if s >= 90:
                badge, color = "Excellent", "#15803d"
            elif s >= 80:
                badge, color = "Very Good", "#1d4ed8"
            elif s >= 70:
                badge, color = "Good", "#ca8a04"
            elif s >= 60:
                badge, color = "Average", "#ea580c"
            elif s >= 50:
                badge, color = "At Risk", "#c2410c"
            else:
                badge, color = "Below Average", "#b91c1c"
            badge_html += f"<div style='display:inline-flex; align-items:center; margin: 4px 8px 4px 0; padding: 6px 14px; border-radius:99px; background:white; border:1px solid #cbd5e1; box-shadow: 0 4px 6px rgba(15,23,42,0.05); font-weight:700; font-size:13px;'><span style='color:#0f172a;'>{row['Subject']}</span><span style='color:{color}; margin-left:8px; border-left:1px solid #e2e8f0; padding-left:8px;'>{s:.1f} - {badge}</span></div>"
        st.markdown(badge_html, unsafe_allow_html=True)

    if df_q.empty and recorded_components_count == 0:
        st.info(f"No records entered yet for {quarter}.")

    st.markdown(
        "<hr style='margin: 32px 0; border-color: rgba(203,213,225,0.4);'>",
        unsafe_allow_html=True,
    )
    render_dashboard_section(
        "Component-Level Analytics Engine",
        "Granular performance breakdown and intelligence per assessment type.",
    )

    comp_table = build_full_component_pivot(student_name, quarter)
    if not comp_table.empty:
        rename_map = {
            k: v for k, v in COMPONENT_DISPLAY.items() if k in comp_table.columns
        }
        comp_table = comp_table.rename(columns=rename_map)
        ordered_cols = (
            ["Subject"] + [COMPONENT_DISPLAY[k] for k in COMPONENTS] + ["Total Output"]
        )
        comp_table = comp_table[[c for c in ordered_cols if c in comp_table.columns]]
        fmt_cols = [c for c in comp_table.columns if c != "Subject"]
        fmt = {c: "{:.1f}" for c in fmt_cols}
        st.dataframe(
            comp_table.style.format(fmt, na_rep="—"),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.markdown(
            """
        <div style='padding:16px 18px; border-radius:12px; border:1px dashed rgba(203,213,225,0.6);
                    background:rgba(248,250,252,0.8); color:#64748b; font-size:14px; text-align:center;'>
            No component data available for this quarter yet.
        </div>
        """,
            unsafe_allow_html=True,
        )

    if not is_quarter_complete:
        st.markdown(
            """
        <div style='background:rgba(245,158,11,0.08); border:1px solid #f59e0b; border-radius:12px;
                    padding:16px 20px; margin:20px 0;'>
            <strong style='color:#92400e; font-size:15px;'>Quarter incomplete — component drill-down still active</strong><br>
            <span style='color:#78350f; font-size:15px; line-height:1.65;'>
                Summary cards above stay Incomplete until every subject has all five components recorded.
                Below, each assessment type is evaluated on its own: only subjects with real marks get charts, warnings, and predictions.
            </span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    for c_name, max_val in COMPONENTS.items():
        display_name = COMPONENT_DISPLAY.get(c_name, c_name)
        df_sub = build_component_subject_frame_for_parent(student_name, quarter, c_name)
        comp_plot = df_sub[df_sub["score"].notna()].copy()

        with st.expander(f"{display_name} (max {max_val})"):
            c1, c2 = st.columns([1.2, 0.8])
            with c1:
                if comp_plot.empty:
                    st.info("No recorded scores for this component—nothing to plot.")
                else:
                    fig_comp = px.bar(
                        comp_plot.sort_values("score", ascending=False),
                        x="Subject",
                        y="score",
                        color="score",
                        color_continuous_scale=[
                            [0.0, "#dc2626"],
                            [0.55, "#f59e0b"],
                            [1.0, "#16a34a"],
                        ],
                        color_continuous_midpoint=max_val * 0.6,
                    )
                    fig_comp.update_traces(
                        marker=dict(line=dict(color="rgba(15,23,42,0.18)", width=1.2)),
                        hovertemplate=f"<b>%{{x}}</b><br>Score: %{{y:.1f}} / {max_val}<extra></extra>",
                    )
                    fig_comp.update_layout(coloraxis_showscale=False)
                    style_dashboard_figure(fig_comp, f"{display_name} — Subject Scores")
                    ax = COMPONENT_AXIS.get(
                        c_name, {"range": [0, max_val], "dtick": max(1, max_val // 5)}
                    )
                    fig_comp.update_yaxes(
                        range=ax["range"],
                        dtick=ax["dtick"],
                        showgrid=True,
                        gridcolor="rgba(148,163,184,0.20)",
                    )
                    fig_comp.update_traces(width=0.72)
                    st.plotly_chart(fig_comp, use_container_width=True)

            with c2:
                st.markdown(
                    f"<div style='margin-top:10px; font-weight:700; font-size:16px; "
                    f"color:#0f172a; margin-bottom:10px;'>{display_name} — Raw marks</div>",
                    unsafe_allow_html=True,
                )
                if comp_plot.empty:
                    st.caption("No subjects with recorded marks for this component.")
                else:
                    st.dataframe(
                        comp_plot.rename(
                            columns={"score": f"Score (/{max_val})"}
                        ).style.format({f"Score (/{max_val})": "{:.1f}"}),
                        use_container_width=True,
                        hide_index=True,
                    )

            threshold = max_val * 0.60
            weak_comps = comp_plot[comp_plot["score"] < threshold]

            if comp_plot.empty:
                pass
            elif not weak_comps.empty:
                weak_subjects_str = ", ".join(weak_comps["Subject"].tolist())
                st.markdown(
                    f"""
                    <div style='background:rgba(220,38,38,0.05); border-left:4px solid #dc2626;
                                padding:14px 18px; margin:14px 0; border-radius:6px;'>
                        <strong style='color:#b91c1c; font-size:16px; display:block; margin-bottom:6px;'>
                            Low performance (recorded subjects): {weak_subjects_str}
                        </strong>
                        <div style='color:#7f1d1d; font-size:15px; line-height:1.55;'>
                            Requires consistent monitoring.
                        </div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"""
                    <div style='background:rgba(245,158,11,0.05); border-left:4px solid #f59e0b;
                                padding:14px 18px; margin:14px 0; border-radius:6px;'>
                        <strong style='color:#b45309; font-size:16px; display:block; margin-bottom:6px;'>Prediction</strong>
                        <div style='color:#92400e; font-size:15px; line-height:1.55;'>
                            If the current performance trend continues, the student is at risk of falling below the 60% passing threshold in {weak_subjects_str}.
                        </div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    """
                    <div style='background:#f8fafc; border:1px solid #cbd5e1;
                                padding:14px 18px; margin:14px 0; border-radius:8px;'>
                        <strong style='color:#0f172a; font-size:16px; display:block; margin-bottom:6px;'>Suggestion</strong>
                        <div style='color:#475569; font-size:15px; line-height:1.55;'>
                            Recommend additional practice, teacher support, and close monitoring
                            to prevent failure in upcoming assessments.
                        </div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style='background:rgba(22,163,74,0.05); border-left:4px solid #16a34a;
                                padding:14px 18px; margin:14px 0; border-radius:6px;'>
                        <strong style='color:#15803d; font-size:16px; display:block; margin-bottom:6px;'>Satisfactory performance</strong>
                        <div style='color:#166534; font-size:15px; line-height:1.55;'>
                            Among subjects with recorded scores for {display_name}, all met or exceeded the 60% standard.
                        </div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )


# show parent notes
def _show_parent_notes(student_name):
    df_notes = get_student_notes_df(student_name)
    render_dashboard_section(
        "Teacher Notes & Recommendations",
        f"Chronological observations for {student_name}.",
    )

    if df_notes.empty:
        st.info("No recorded notes or concerns for this student.")
        return

    for _, row in df_notes.iterrows():
        st.markdown(
            f"""
        <div style='background:rgba(255,255,255,0.94); border:1px solid rgba(203,213,225,0.85); border-radius:20px; padding:24px; margin-bottom:18px; box-shadow: 0 16px 36px rgba(15,23,42,0.07);'>
            <div style='color:#64748b; font-size:14px; font-weight:600; margin-bottom:12px;'>{row["date_recorded"]}</div>
            <div style='color:#0f172a; font-size:16px; line-height:1.7; font-weight:500;'>{row["note"]}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


# show parent dashboard
def show_parent_dashboard():
    student_name = (
        st.session_state.user_name.title() if st.session_state.user_name else "Student"
    )
    nav_options = [
        "Overview",
        "1st Quarter",
        "2nd Quarter",
        "3rd Quarter",
        "4th Quarter",
        "Teacher Notes",
    ]

    with st.sidebar:
        st.markdown(
            f"""
        <div style='padding: 8px 4px 22px;'>
            <div class='staff-chip' style='background: rgba(147,51,234,0.15); color:#e9d5ff; border-color: rgba(168,85,247,0.3);'>Parent Portal</div>
            <div style='font-size:28px; font-weight:900; color:#ffffff; letter-spacing:-0.03em; margin-top:14px; line-height:1.15;'>{student_name}</div>
            <div style='font-size:14px; color:#94a3b8; margin-top:8px; line-height:1.6;'>Academic monitoring and alerts</div>
        </div>""",
            unsafe_allow_html=True,
        )
        st.divider()

        if (
            "parent_menu" not in st.session_state
            or st.session_state.parent_menu not in nav_options
        ):
            st.session_state.parent_menu = "Overview"

        st.sidebar.radio(
            "Navigation", nav_options, key="parent_menu", label_visibility="collapsed"
        )
        st.divider()

        st.markdown(
            "<p style='font-size:12px; color:#94a3b8; text-align:center; line-height:1.8;'>Signed in as<br><strong style='color:#dbeafe; font-size:14px;'>Parent/Guardian</strong></p>",
            unsafe_allow_html=True,
        )
        if st.button("Sign Out", type="secondary", use_container_width=True):
            log_activity(st.session_state.user_name, "logout", "parent", "Logged out from parent dashboard")
            st.session_state.logged_in = False
            st.session_state.user_name = None
            if "parent_menu" in st.session_state:
                del st.session_state["parent_menu"]
            navigate_to("role")

    menu = st.session_state.parent_menu
    df_grades = get_student_term_subject_scores_df(student_name)

    st.markdown(
        """
    <div style='margin-bottom: 28px; padding-bottom: 14px; border-bottom: 2px solid rgba(203,213,225,0.4);'>
        <h1 style='color: #0f172a; font-size: 40px; font-weight: 900; letter-spacing:-0.03em; margin:0; font-family: Inter, system-ui, sans-serif;'>Welcome, Mr. Million</h1>
        <p style='color: #64748b; font-size: 17px; margin: 8px 0 0 0; font-weight:500; line-height:1.5;'>Here is your child's academic performance overview</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if menu == "Overview":
        _show_parent_overview(student_name, df_grades)
    elif menu in ["1st Quarter", "2nd Quarter", "3rd Quarter", "4th Quarter"]:
        q_map = {
            "1st Quarter": "Q1",
            "2nd Quarter": "Q2",
            "3rd Quarter": "Q3",
            "4th Quarter": "Q4",
        }
        quarter = q_map[menu]
        _show_parent_quarter(quarter, student_name, df_grades)
    elif menu == "Teacher Notes":
        _show_parent_notes(student_name)


# show admin dashboard
def show_admin_dashboard():
    """Admin Control Panel — delegates to admin_dashboard module."""
    import admin_dashboard as _adm
    _adm.show_admin_dashboard()


# show school admin dashboard
def show_school_admin_dashboard():
    """School Administration Dashboard - integrated from dashboard module."""
    import dashboard as admin_dash
    admin_dash.inject_css()

    if "dash_page" not in st.session_state:
        st.session_state.dash_page = "home"

    if st.session_state.dash_page == "home":
        if st.button("← Back to Role Selection", key="admin_back_to_role"):
            st.session_state.dash_page = "home"
            navigate_to("role")
            return

    page = st.session_state.dash_page
    if page == "home":
        admin_dash.show_home()
    elif page.startswith("class_"):
        class_name = page.replace("class_", "")
        admin_dash.show_class_page(class_name)
    elif page.startswith("grade_"):
        grade = int(page.replace("grade_", ""))
        admin_dash.show_grade_overview(grade)
    else:
        admin_dash.show_home()


# show wereda dashboard
def show_wereda_dashboard():
    """Wereda School Performance Dashboard - integrated from wereda_dashboard module."""
    import wereda_dashboard as wereda_dash
    wereda_dash.inject_wereda_css()

    if "wereda_page" not in st.session_state:
        st.session_state.wereda_page = "home"

    if st.session_state.wereda_page == "home":
        if st.button("\u2190 Back to Role Selection", key="wereda_back_to_role"):
            st.session_state.wereda_page = "home"
            navigate_to("role")
            return

    page = st.session_state.wereda_page
    if page == "home":
        wereda_dash.show_wereda_home()
    elif page == "school":
        wereda_dash.show_school_overview(st.session_state.get("wereda_school", ""))
    elif page == "grade_detail":
        wereda_dash.show_grade_detail(
            st.session_state.get("wereda_school", ""),
            st.session_state.get("wereda_grade", 9),
            st.session_state.get("wereda_track", None)
        )
    else:
        wereda_dash.show_wereda_home()


# show addis ababa dashboard
def show_addis_ababa_dashboard():
    """Addis Ababa City-Level Education Performance Dashboard."""
    import addis_ababa_dashboard as aa_dash
    aa_dash.inject_aa_css()

    if "aa_page" not in st.session_state:
        st.session_state.aa_page = "home"

    if st.session_state.aa_page == "home":
        if st.button("\u2190 Back to Role Selection", key="aa_back_to_role"):
            st.session_state.aa_page = "home"
            navigate_to("role")
            return

    page = st.session_state.aa_page
    if page == "home":
        aa_dash.show_home()
    elif page == "kk":
        aa_dash.show_kk_overview(st.session_state.get("aa_kk", ""))
    else:
        aa_dash.show_home()


# show kifle ketema dashboard
def show_kifle_ketema_dashboard():
    """Kifle Ketema Performance Dashboard."""
    import kifle_ketema_dashboard as kk_dash
    kk_dash.inject_kk_css()

    if "kk_page" not in st.session_state:
        st.session_state.kk_page = "home"

    if st.session_state.kk_page == "home":
        if st.button("\u2190 Back to Role Selection", key="kk_back_to_role"):
            st.session_state.kk_page = "home"
            navigate_to("role")
            return

    page = st.session_state.kk_page
    if page == "home":
        kk_dash.show_home()
    elif page == "wereda":
        kk_dash.show_wereda_overview(st.session_state.get("kk_wereda", ""))
    elif page == "school":
        kk_dash.show_school_overview(
            st.session_state.get("kk_wereda", ""),
            st.session_state.get("kk_school", "")
        )
    elif page == "grade":
        kk_dash.show_grade_detail(
            st.session_state.get("kk_wereda", ""),
            st.session_state.get("kk_school", ""),
            st.session_state.get("kk_grade", 9),
            st.session_state.get("kk_track", None)
        )
    else:
        kk_dash.show_home()


# main
def main():
    app_init_db()
    init_session_state()
    load_global_css()
    inject_page_layout()
    inject_page_transitions()

    pages = {
        "welcome": show_welcome,
        "region": show_region,
        "kifle_ketema": show_kifle_ketema,
        "wereda": show_wereda,
        "school": show_school,
        "role": show_role,
        "register_teacher": lambda: show_register("teacher"),
        "register_parent": lambda: show_register("parent"),
        "classroom_selection": show_classroom_selection,
        "login_teacher": lambda: show_login("teacher"),
        "login_parent": lambda: show_login("parent"),
        "teacher_dashboard": show_teacher_dashboard_staff,
        "parent_dashboard": show_parent_dashboard,
        "school_admin_dashboard": show_school_admin_dashboard,
        "wereda_dashboard": show_wereda_dashboard,
        "kifle_ketema_dashboard": show_kifle_ketema_dashboard,
        "addis_ababa_dashboard": show_addis_ababa_dashboard,
        "admin_dashboard": show_admin_dashboard,
    }

    if st.session_state.page in pages:
        pages[st.session_state.page]()
    else:
        st.session_state.page = "welcome"
        st.rerun()


if __name__ == "__main__":
    main()
