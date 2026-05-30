import streamlit as st
import sqlite3
import hashlib
import datetime

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LaundroSoft POS",
    page_icon="🫧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── DATABASE ─────────────────────────────────────────────────────────────────
DB_PATH = "laundrosoft.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            service      TEXT NOT NULL,
            weight       REAL NOT NULL,
            total        REAL NOT NULL,
            status       TEXT NOT NULL,
            date_created TEXT,
            pickup_date  TEXT
        )
    """)
    conn.commit()
    cur.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)",
                ("admin", hash_password("admin123"), "Admin"))
    conn.commit()
    cur.close()
    conn.close()

def hash_password(password, salt="laundry_secure_123"):
    return hashlib.sha256((password + salt).encode()).hexdigest()

# ─── SESSION STATE ────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "logged_in": False,
        "username": "",
        "role": "",
        "view": "dashboard",
        "auth_mode": "login",
        "ord_filter": "All",
        "rpt_period": "today",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ─── CSS ──────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300&family=Space+Mono:wght@400;700&display=swap');

    :root {
        --bg:        #080B12;
        --surf:      #0E1220;
        --surf2:     #141828;
        --surf3:     #1A1F32;
        --border:    #1E2540;
        --accent:    #4B8BFF;
        --accent2:   #8B5CF6;
        --green:     #10D9A0;
        --orange:    #F5A623;
        --red:       #F04A5E;
        --text:      #DDE3F5;
        --muted:     #6B7599;
        --dim:       #3A4060;
    }

    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background-color: var(--bg) !important;
        font-family: 'DM Sans', sans-serif !important;
        color: var(--text);
    }

    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stDecoration"] { display: none; }

    [data-testid="stSidebar"] {
        background: var(--surf) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebarContent"] { padding: 0 !important; }
    [data-testid="stSidebar"] * { font-family: 'DM Sans', sans-serif !important; }

    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: var(--muted) !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 10px 14px !important;
        width: 100% !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(75,139,255,0.1) !important;
        color: var(--accent) !important;
    }

    [data-testid="stMain"] .block-container {
        padding: 2rem 2.8rem 3rem !important;
        max-width: 1400px !important;
    }

    input, textarea {
        background-color: var(--surf2) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    input:focus, textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(75,139,255,0.12) !important;
    }
    [data-baseweb="select"] > div {
        background-color: var(--surf2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text) !important;
    }
    [data-baseweb="popover"] * {
        background-color: var(--surf3) !important;
        color: var(--text) !important;
    }
    label { color: var(--muted) !important; font-size: 12px !important; font-weight: 500 !important; }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        letter-spacing: 0.3px !important;
        transition: opacity 0.15s !important;
    }
    .stButton > button[kind="primary"]:hover { opacity: 0.85 !important; }
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: all 0.15s ease !important;
    }

    [data-testid="metric-container"] {
        background: var(--surf) !important;
        border: 1px solid var(--border) !important;
        border-radius: 18px !important;
        padding: 24px !important;
        position: relative;
        overflow: hidden;
    }
    [data-testid="metric-container"]::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent), var(--accent2));
    }
    [data-testid="metric-container"] label {
        color: var(--muted) !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        font-family: 'Space Mono', monospace !important;
    }

    .ls-card {
        background: var(--surf);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 10px;
        transition: border-color 0.2s, transform 0.15s;
    }
    .ls-card:hover { border-color: var(--dim); transform: translateY(-1px); }
    .ls-section-box {
        background: var(--surf);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 24px 28px;
        margin-bottom: 18px;
    }

    .badge-done {
        background: rgba(16,217,160,0.1); color: var(--green);
        border: 1px solid rgba(16,217,160,0.25); border-radius: 20px;
        padding: 3px 12px; font-size: 11px; font-weight: 700; letter-spacing: 0.3px;
    }
    .badge-pending {
        background: rgba(245,166,35,0.1); color: var(--orange);
        border: 1px solid rgba(245,166,35,0.25); border-radius: 20px;
        padding: 3px 12px; font-size: 11px; font-weight: 700;
    }
    .badge-admin {
        background: rgba(75,139,255,0.1); color: var(--accent);
        border: 1px solid rgba(75,139,255,0.25); border-radius: 20px;
        padding: 2px 10px; font-size: 11px; font-weight: 700;
    }
    .badge-staff {
        background: rgba(139,92,246,0.1); color: var(--accent2);
        border: 1px solid rgba(139,92,246,0.25); border-radius: 20px;
        padding: 2px 10px; font-size: 11px; font-weight: 700;
    }

    .ls-section-title {
        font-size: 15px; font-weight: 700; color: var(--text);
        margin-bottom: 6px; display: flex; align-items: center; gap: 10px;
    }
    .ls-section-title::before {
        content: ''; display: inline-block; width: 4px; height: 18px;
        background: linear-gradient(180deg, var(--accent), var(--accent2));
        border-radius: 2px; flex-shrink: 0;
    }
    .ls-page-title { font-size: 26px; font-weight: 700; color: var(--text); letter-spacing: -0.4px; }
    .ls-page-sub   { font-size: 13px; color: var(--muted); margin-bottom: 22px; margin-top: 2px; }

    .auth-wrap {
        background: var(--surf); border: 1px solid var(--border); border-radius: 22px;
        padding: 42px 46px; max-width: 440px; margin: 0 auto;
        box-shadow: 0 24px 64px rgba(0,0,0,0.5);
    }
    .auth-title { font-size: 26px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
    .auth-sub   { font-size: 13px; color: var(--muted); margin-bottom: 28px; }

    .chip-row { display: flex; gap: 20px; flex-wrap: wrap; align-items: center; }
    .chip { display: flex; align-items: center; gap: 5px; font-size: 12px; color: var(--muted); }
    .chip-val    { color: var(--text); }
    .chip-accent { color: var(--accent); font-weight: 600; }
    .chip-green  { color: var(--green); }
    .chip-orange { color: var(--orange); }
    .chip-red    { color: var(--red); }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
        border-radius: 4px !important;
    }
    .stProgress > div > div { background: var(--surf3) !important; border-radius: 4px !important; }

    [data-testid="stAlert"] { border-radius: 12px !important; border: none !important; }

    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--dim); }

    hr { border-color: var(--border) !important; margin: 14px 0 !important; }

    .avatar {
        width: 44px; height: 44px; border-radius: 50%;
        background: linear-gradient(135deg, var(--accent2), var(--accent));
        display: inline-flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 15px; color: #fff; flex-shrink: 0;
    }

    .notif-warn  { background: rgba(245,166,35,0.07); border: 1px solid rgba(245,166,35,0.2);
                   border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }
    .notif-error { background: rgba(240,74,94,0.07); border: 1px solid rgba(240,74,94,0.2);
                   border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }

    .bar-track { background: var(--surf3); border-radius: 8px; height: 28px;
                 overflow: hidden; display: flex; }
    .bar-high  { background: var(--green);  height: 100%; }
    .bar-low   { background: var(--orange); height: 100%; }
    </style>
    """, unsafe_allow_html=True)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def page_header(title, subtitle, icon=""):
    st.markdown(f"""
    <div style='margin-bottom:26px'>
        <div class='ls-page-title'>{icon}&nbsp;{title}</div>
        <div class='ls-page-sub'>{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def section_title(text):
    st.markdown(f"<div class='ls-section-title'>{text}</div>", unsafe_allow_html=True)

def brand_logo(size=36):
    s = int(size * 0.55)
    return (
        f"<div style='display:inline-flex;align-items:center;justify-content:center;"
        f"width:{size}px;height:{size}px;border-radius:10px;"
        f"background:linear-gradient(135deg,#4B8BFF,#8B5CF6);flex-shrink:0'>"
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='{s}' height='{s}'"
        f" fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
        f"<rect x='2' y='3' width='20' height='18' rx='3'/>"
        f"<circle cx='12' cy='13' r='4'/>"
        f"<circle cx='12' cy='13' r='1.5' fill='white' stroke='none'/>"
        f"<line x1='2' y1='8' x2='22' y2='8'/>"
        f"<circle cx='6' cy='5.5' r='1' fill='white' stroke='none'/>"
        f"<circle cx='9.5' cy='5.5' r='1' fill='white' stroke='none' opacity='0.6'/>"
        f"</svg></div>"
    )

def get_notifications():
    notes = []
    THRESHOLD = 1000.0
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status='Done'")
    earned = cur.fetchone()[0] or 0.0
    if earned < THRESHOLD:
        notes.append(("error", "⚠️ Low Revenue Alert",
            f"Completed revenue ₱{earned:,.2f} is below ₱{THRESHOLD:,.2f} threshold."))
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT id,name,service FROM orders WHERE pickup_date=? AND status='Pending'", (today,))
    for row in cur.fetchall():
        notes.append(("warn", "📦 Pick-up Today",
            f"Order #{row['id']} — {row['name']} ({row['service']}) is due today."))
    cur.close(); conn.close()
    return notes

def get_rates():
    return {"Wash": 50.0, "Wash & Dry": 75.0, "Full Service": 95.0}

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════
def render_auth():
    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        st.markdown("<br><br>", unsafe_allow_html=True)
        mode = st.session_state.auth_mode

        logo_html = brand_logo(48)
        st.markdown(
            "<div style='text-align:center;margin-bottom:32px'>"
            "<div style='display:inline-flex;align-items:center;gap:14px;"
            "background:var(--surf);border:1px solid var(--border);"
            "border-radius:18px;padding:16px 26px;'>"
            + logo_html +
            "<div style='text-align:left'>"
            "<div style='font-size:22px;font-weight:700;"
            "background:linear-gradient(135deg,#4B8BFF,#C084FC);"
            "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
            "letter-spacing:-0.3px'>LaundroSoft</div>"
            "<div style='font-size:11px;color:#6B7599;font-weight:500;"
            "letter-spacing:2px'>POINT OF SALE</div>"
            "</div></div></div>",
            unsafe_allow_html=True,
        )

        title    = "Create account" if mode == "register" else "Welcome back 👋"
        subtitle = "Register a new LaundroSoft account" if mode == "register" else "Sign in to your workspace"
        st.markdown(f"""
        <div class='auth-wrap'>
            <div class='auth-title'>{title}</div>
            <div class='auth-sub'>{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", key="auth_user", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="auth_pass",
                                 placeholder="Enter your password")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if mode == "login":
            if st.button("Sign In →", use_container_width=True, type="primary", key="signin_btn"):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    conn = get_connection(); cur = conn.cursor()
                    cur.execute("SELECT password,role FROM users WHERE username=?", (username,))
                    row = cur.fetchone(); cur.close(); conn.close()
                    if row and row["password"] == hash_password(password):
                        st.session_state.update({
                            "logged_in": True, "username": username,
                            "role": row["role"], "view": "dashboard"
                        })
                        st.rerun()
                    elif row: st.error("Incorrect password.")
                    else:     st.error("Username not found.")

            if st.button("Don't have an account? Register", use_container_width=True, key="go_register"):
                st.session_state.auth_mode = "register"; st.rerun()

        else:
            if st.button("Create Account →", use_container_width=True, type="primary", key="register_btn"):
                if not username or not password:
                    st.error("Please fill in all fields.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        conn = get_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                                    (username, hash_password(password), "Staff"))
                        conn.commit(); cur.close(); conn.close()
                        st.success("Account created! You can now sign in.")
                        st.session_state.auth_mode = "login"; st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username already exists.")

            if st.button("Already have an account? Sign in", use_container_width=True, key="go_login"):
                st.session_state.auth_mode = "login"; st.rerun()

        st.markdown("""
        <div style='text-align:center;margin-top:24px;color:var(--dim);font-size:11px;
                    font-family:"Space Mono",monospace'>
            default&nbsp;·&nbsp;<span style='color:var(--accent)'>admin</span>
            &nbsp;/&nbsp;<span style='color:var(--accent)'>admin123</span>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    user = st.session_state.username
    role = st.session_state.role

    with st.sidebar:
        logo_sb = brand_logo(40)
        st.markdown(
            "<div style='padding:24px 20px 12px'>"
            "<div style='display:flex;align-items:center;gap:12px;margin-bottom:22px'>"
            + logo_sb +
            "<div>"
            "<div style='font-size:15px;font-weight:700;"
            "background:linear-gradient(135deg,#4B8BFF,#C084FC);"
            "-webkit-background-clip:text;-webkit-text-fill-color:transparent'>LaundroSoft</div>"
            "<div style='font-size:9px;color:#3A4060;font-weight:600;"
            "letter-spacing:1.8px'>POS SYSTEM</div>"
            "</div></div>"
            "<div style='height:1px;background:linear-gradient(90deg,#1E2540,transparent);"
            "margin-bottom:18px'></div>"
            "<div style='font-size:9px;color:#3A4060;letter-spacing:2.5px;font-weight:700;"
            "margin-bottom:10px;padding-left:2px'>NAVIGATE</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        nav = [
            ("dashboard", "📊", "Dashboard"),
            ("orders",    "📋", "Orders"),
            ("customers", "👥", "Customers"),
            ("reports",   "📈", "Reports"),
            ("settings",  "⚙️", "Settings"),
        ]
        current = st.session_state.view
        for key, icon, label in nav:
            is_active = current == key
            if is_active:
                st.markdown(f"""
                <div style='background:rgba(75,139,255,0.1);border:1px solid rgba(75,139,255,0.22);
                            border-radius:10px;padding:10px 14px;margin:2px 16px;
                            font-size:13px;font-weight:600;color:var(--accent)'>
                    {icon}&nbsp;&nbsp;{label}
                </div>
                """, unsafe_allow_html=True)
            else:
                _, col_btn = st.columns([0.06, 0.94])
                with col_btn:
                    if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                        st.session_state.view = key; st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        badge_cls = "badge-admin" if role == "Admin" else "badge-staff"
        st.markdown(f"""
        <div style='padding:0 16px 10px'>
            <div style='height:1px;background:linear-gradient(90deg,var(--border),transparent);
                        margin-bottom:16px'></div>
            <div style='background:var(--surf2);border:1px solid var(--border);border-radius:14px;
                        padding:12px 14px;display:flex;align-items:center;gap:10px'>
                <div style='width:36px;height:36px;border-radius:50%;flex-shrink:0;
                            background:linear-gradient(135deg,var(--accent2),var(--accent));
                            display:flex;align-items:center;justify-content:center;
                            font-weight:800;font-size:14px;color:#fff'>
                    {user[0].upper() if user else "U"}
                </div>
                <div style='flex:1;min-width:0'>
                    <div style='font-size:13px;font-weight:700;color:var(--text);
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{user}</div>
                    <span class='{badge_cls}'>{role}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪  Log out", key="logout_btn", use_container_width=True):
            for k in ["logged_in", "username", "role"]:
                st.session_state[k] = False if k == "logged_in" else ""
            st.session_state.view = "dashboard"
            st.session_state.auth_mode = "login"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def render_dashboard():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders")
    total_cnt, total_rev = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
    pend = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Done'")
    done = cur.fetchone()[0]
    cur.close(); conn.close()

    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown(f"""
        <div class='ls-page-title'>Dashboard</div>
        <div class='ls-page-sub'>{datetime.datetime.now().strftime('%A, %d %B %Y')}</div>
        """, unsafe_allow_html=True)
    with h2:
        notes = get_notifications()
        lbl = f"🔔 Alerts ({len(notes)})" if notes else "🔔 No Alerts"
        if st.button(lbl, use_container_width=True, key="notif_btn"):
            st.session_state["show_notifs"] = not st.session_state.get("show_notifs", False)

    if st.session_state.get("show_notifs"):
        if not notes:
            st.success("✅ All clear — no notifications right now.")
        else:
            for kind, title, body in notes:
                cls = "notif-error" if kind == "error" else "notif-warn"
                st.markdown(f"""
                <div class='{cls}'>
                    <div style='font-size:13px;font-weight:700;color:var(--text)'>{title}</div>
                    <div style='font-size:12px;color:var(--muted);margin-top:3px'>{body}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋  Total Orders",  total_cnt or 0)
    c2.metric("⏳  Pending",        pend or 0)
    c3.metric("✅  Completed",      done or 0)
    c4.metric("💰  Revenue",        f"₱{(total_rev or 0):,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
    section_title("New Transaction")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    rates = get_rates()
    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    cust_name = f1.text_input("Customer Name", placeholder="e.g. Juan dela Cruz", key="dash_name")
    weight    = f2.text_input("Weight (kg)",   placeholder="e.g. 3.5",            key="dash_weight")
    service   = f3.selectbox("Service", list(rates.keys()),                        key="dash_service")
    pickup    = f4.date_input("Pick-up Date (Optional)", value=None,               key="dash_pickup",
                               min_value=datetime.date.today())

    if weight:
        try:
            kg = float(weight)
            est = rates.get(service, 50) * kg
            st.markdown(f"""
            <div style='font-size:12px;color:var(--muted);margin-bottom:8px'>
                Estimated total:&nbsp;
                <span style='font-size:15px;font-weight:700;color:var(--green);
                             font-family:"Space Mono",monospace'>₱{est:,.2f}</span>
            </div>""", unsafe_allow_html=True)
        except ValueError:
            pass

    if st.button("➕  Create Order", type="primary", key="dash_create"):
        if not cust_name or not weight:
            st.error("Please enter Customer Name and Weight.")
        else:
            try:
                kg    = float(weight)
                total = rates.get(service, 50) * kg
                pu    = pickup.strftime("%Y-%m-%d") if pickup else ""
                conn2 = get_connection(); cur2 = conn2.cursor()
                cur2.execute(
                    "INSERT INTO orders (name,service,weight,total,status,date_created,pickup_date)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (cust_name, service, kg, total, "Pending",
                     datetime.datetime.now().strftime("%Y-%m-%d"), pu))
                conn2.commit(); cur2.close(); conn2.close()
                st.success(f"✅ Order created for **{cust_name}** — Total: ₱{total:,.2f}")
                st.rerun()
            except ValueError:
                st.error("Invalid weight. Please enter a number.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section_title("Recent Orders")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    _render_orders_table(limit=15, show_edit=False)

# ══════════════════════════════════════════════════════════════════════════════
#  ORDERS TABLE
# ══════════════════════════════════════════════════════════════════════════════
def _render_orders_table(limit=None, show_edit=True, status_filter="All", search=""):
    conn = get_connection(); cur = conn.cursor()
    q = "SELECT id,name,service,weight,total,status,date_created,pickup_date FROM orders"
    conds, params = [], []
    if status_filter != "All": conds.append("status=?");   params.append(status_filter)
    if search:                  conds.append("name LIKE ?"); params.append(f"%{search}%")
    if conds: q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY id DESC"
    if limit: q += f" LIMIT {limit}"
    cur.execute(q, params)
    rows = cur.fetchall(); cur.close(); conn.close()

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    if not rows:
        st.markdown("""
        <div style='text-align:center;padding:48px;color:var(--dim);
                    background:var(--surf);border:1px dashed var(--border);border-radius:16px'>
            <div style='font-size:36px;margin-bottom:12px'>📭</div>
            <div style='font-size:14px;font-weight:600'>No orders found</div>
        </div>""", unsafe_allow_html=True)
        return

    for row in rows:
        oid      = row["id"];     name_v = row["name"];   svc_v  = row["service"]
        wt_v     = row["weight"]; tot_v  = row["total"];  stat_v = row["status"]
        date_v   = row["date_created"]; pick_v = row["pickup_date"]
        is_done  = stat_v == "Done"
        badge    = "<span class='badge-done'>✓ Done</span>" if is_done else "<span class='badge-pending'>⏳ Pending</span>"
        pick_color = "var(--red)" if pick_v == today and not is_done else "var(--muted)"
        pickup_str = pick_v or "—"

        st.markdown(f"""
        <div class='ls-card'>
          <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px'>
            <div style='display:flex;align-items:center;gap:10px'>
              <span style='color:var(--dim);font-size:11px;font-weight:700;
                           background:var(--surf2);border:1px solid var(--border);
                           border-radius:6px;padding:2px 8px;font-family:"Space Mono",monospace'>#{oid}</span>
              <span style='color:var(--text);font-size:15px;font-weight:700'>{name_v}</span>
              {badge}
            </div>
            <div style='font-size:17px;font-weight:700;color:var(--green);
                        font-family:"Space Mono",monospace'>₱{tot_v:,.2f}</div>
          </div>
          <div class='chip-row'>
            <span class='chip'>📅&nbsp;<span class='chip-val'>{date_v or "—"}</span></span>
            <span class='chip'>🚚&nbsp;<span style='color:{pick_color}'>{pickup_str}</span></span>
            <span class='chip'>⚖️&nbsp;<span class='chip-val'>{wt_v} kg</span></span>
            <span class='chip'>👕&nbsp;<span class='chip-accent'>{svc_v}</span></span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if not is_done:
            cols = st.columns([1, 1, 1, 5]) if show_edit else st.columns([1, 1, 6])
            if cols[0].button("✅ Done", key=f"done_{oid}_{status_filter}_{limit}"):
                conn2 = get_connection(); cur2 = conn2.cursor()
                cur2.execute("UPDATE orders SET status='Done' WHERE id=?", (oid,))
                conn2.commit(); cur2.close(); conn2.close(); st.rerun()
            if show_edit and cols[1].button("✏️ Edit", key=f"edit_{oid}_{status_filter}"):
                st.session_state[f"editing_{oid}"] = not st.session_state.get(f"editing_{oid}", False)
            del_col = cols[2] if show_edit else cols[1]
            if del_col.button("🗑️ Delete", key=f"del_{oid}_{status_filter}_{limit}"):
                st.session_state[f"confirm_del_{oid}"] = True
        else:
            if show_edit:
                b1, b2, _ = st.columns([1, 1, 6])
                if b1.button("✏️ Edit", key=f"edit_{oid}_{status_filter}"):
                    st.session_state[f"editing_{oid}"] = not st.session_state.get(f"editing_{oid}", False)
                if b2.button("🗑️ Delete", key=f"del_{oid}_{status_filter}_{limit}"):
                    st.session_state[f"confirm_del_{oid}"] = True
            else:
                b1, _ = st.columns([1, 7])
                if b1.button("🗑️ Delete", key=f"del_{oid}_{status_filter}_{limit}"):
                    st.session_state[f"confirm_del_{oid}"] = True

        if st.session_state.get(f"confirm_del_{oid}"):
            st.warning(f"⚠️ Delete Order #{oid} for **{name_v}**?")
            yc, nc, _ = st.columns([1, 1, 5])
            if yc.button("Delete", key=f"yes_del_{oid}", type="primary"):
                conn3 = get_connection(); cur3 = conn3.cursor()
                cur3.execute("DELETE FROM orders WHERE id=?", (oid,))
                conn3.commit(); cur3.close(); conn3.close()
                st.session_state.pop(f"confirm_del_{oid}", None); st.rerun()
            if nc.button("Cancel", key=f"no_del_{oid}"):
                st.session_state.pop(f"confirm_del_{oid}", None); st.rerun()

        if show_edit and st.session_state.get(f"editing_{oid}"):
            rates = get_rates()
            st.markdown(f"""
            <div style='padding:16px;background:var(--surf2);border:1px solid var(--dim);
                        border-radius:12px;margin-bottom:12px'>
                <div style='font-size:13px;font-weight:700;color:var(--accent);margin-bottom:12px'>
                    ✏️ Editing Order #{oid}
                </div>
            </div>""", unsafe_allow_html=True)
            e1, e2, e3, e4 = st.columns([2, 1, 1, 1])
            e_name   = e1.text_input("Customer Name", value=name_v,       key=f"ename_{oid}")
            e_weight = e2.text_input("Weight (kg)",   value=str(wt_v),    key=f"ewt_{oid}")
            svc_opts = list(rates.keys())
            e_svc    = e3.selectbox("Service", svc_opts,
                                    index=svc_opts.index(svc_v) if svc_v in svc_opts else 0,
                                    key=f"esvc_{oid}")
            e_pickup = e4.text_input("Pick-up Date", value=pick_v or "",
                                     placeholder="YYYY-MM-DD", key=f"epick_{oid}")
            sa, ca, _ = st.columns([1, 1, 4])
            if sa.button("💾 Save", key=f"save_{oid}", type="primary"):
                try:
                    kg    = float(e_weight)
                    total = rates.get(e_svc, 50) * kg
                    conn4 = get_connection(); cur4 = conn4.cursor()
                    cur4.execute(
                        "UPDATE orders SET name=?,service=?,weight=?,total=?,pickup_date=? WHERE id=?",
                        (e_name, e_svc, kg, total, e_pickup, oid))
                    conn4.commit(); cur4.close(); conn4.close()
                    st.session_state.pop(f"editing_{oid}", None); st.rerun()
                except ValueError:
                    st.error("Invalid weight.")
            if ca.button("✕ Cancel", key=f"cancel_edit_{oid}"):
                st.session_state.pop(f"editing_{oid}", None); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  ORDERS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_orders():
    page_header("Orders", "View and manage all laundry orders", "📋")

    sc, sf = st.columns([2, 3])
    search = sc.text_input("🔍 Search customer", placeholder="Type a name…", key="ord_search")
    with sf:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        fa, fb, fc = st.columns(3)
        if fa.button("All",     use_container_width=True, key="flt_all"):     st.session_state["ord_filter"] = "All"
        if fb.button("Pending", use_container_width=True, key="flt_pending"): st.session_state["ord_filter"] = "Pending"
        if fc.button("Done",    use_container_width=True, key="flt_done"):    st.session_state["ord_filter"] = "Done"

    flt = st.session_state.get("ord_filter", "All")
    flt_colors = {"All": "var(--accent)", "Pending": "var(--orange)", "Done": "var(--green)"}
    st.markdown(f"""
    <div style='margin:6px 0 14px;font-size:12px;color:var(--muted)'>
        Filter: <span style='color:{flt_colors.get(flt,"var(--accent)")};font-weight:700'>{flt}</span>
    </div>""", unsafe_allow_html=True)
    _render_orders_table(status_filter=flt, search=search, show_edit=True)

# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMERS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_customers():
    page_header("Customers", "All unique customers derived from orders", "👥")
    search = st.text_input("🔍 Search customer", placeholder="Type a name…", key="cust_search")

    conn = get_connection(); cur = conn.cursor()
    q = "SELECT name, COUNT(*) orders, COALESCE(SUM(total),0) spent, MAX(date_created) last FROM orders"
    p = []
    if search: q += " WHERE name LIKE ?"; p.append(f"%{search}%")
    q += " GROUP BY name ORDER BY spent DESC"
    cur.execute(q, p); data = cur.fetchall(); cur.close(); conn.close()

    if not data:
        st.markdown("""
        <div style='text-align:center;padding:48px;color:var(--dim);
                    background:var(--surf);border:1px dashed var(--border);border-radius:16px'>
            <div style='font-size:36px;margin-bottom:12px'>👥</div>
            <div style='font-size:14px;font-weight:600'>No customers found</div>
        </div>""", unsafe_allow_html=True)
        return

    for i, row in enumerate(data):
        cname = row["name"]; oc = row["orders"]; spent = row["spent"]; last = row["last"]
        initials = "".join([w[0].upper() for w in cname.split()[:2]])
        accent = "var(--accent)" if i % 2 == 0 else "var(--accent2)"
        st.markdown(f"""
        <div class='ls-card' style='display:flex;align-items:center;gap:18px'>
            <div class='avatar'>{initials}</div>
            <div style='flex:1'>
                <div style='font-size:15px;font-weight:700;color:var(--text)'>{cname}</div>
                <div style='font-size:11px;color:var(--muted);margin-top:2px'>
                    Last order: <span style='color:var(--text)'>{last or "—"}</span>
                </div>
            </div>
            <div style='text-align:center;min-width:90px'>
                <div style='font-size:16px;font-weight:700;color:{accent};
                            font-family:"Space Mono",monospace'>{oc}</div>
                <div style='font-size:10px;color:var(--muted);font-weight:600;letter-spacing:0.5px'>
                    ORDER{'S' if oc!=1 else ''}
                </div>
            </div>
            <div style='width:1px;height:36px;background:var(--border)'></div>
            <div style='text-align:right;min-width:120px'>
                <div style='font-size:17px;font-weight:700;color:var(--green);
                            font-family:"Space Mono",monospace'>₱{spent:,.2f}</div>
                <div style='font-size:10px;color:var(--muted);font-weight:600;letter-spacing:0.5px'>
                    TOTAL SPENT
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  REPORTS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_reports():
    page_header("Reports", "Business analytics and performance overview", "📈")

    pa, pb, pc, pd = st.columns(4)
    if pa.button("Today",       use_container_width=True, key="rpt_today"): st.session_state["rpt_period"] = "today"
    if pb.button("Last 7 Days", use_container_width=True, key="rpt_week"):  st.session_state["rpt_period"] = "week"
    if pc.button("This Month",  use_container_width=True, key="rpt_month"): st.session_state["rpt_period"] = "month"
    if pd.button("All Time",    use_container_width=True, key="rpt_all"):   st.session_state["rpt_period"] = "all"

    period = st.session_state.get("rpt_period", "today")
    today  = datetime.datetime.now().strftime("%Y-%m-%d")

    if period == "today":
        date_filter, date_param, lbl = "date_created=?", today, "Today"
    elif period == "week":
        ws = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        date_filter, date_param, lbl = "date_created>=?", ws, "Last 7 Days"
    elif period == "month":
        ms = datetime.datetime.now().strftime("%Y-%m-01")
        date_filter, date_param, lbl = "date_created>=?", ms, "This Month"
    else:
        date_filter, date_param, lbl = None, None, "All Time"

    st.markdown(f"""
    <div style='margin:-8px 0 20px'>
        <span style='background:rgba(75,139,255,0.1);color:var(--accent);
                     border:1px solid rgba(75,139,255,0.2);border-radius:20px;
                     padding:4px 14px;font-size:12px;font-weight:700;
                     font-family:"Space Mono",monospace'>📅 {lbl}</span>
    </div>""", unsafe_allow_html=True)

    conn = get_connection(); cur = conn.cursor()
    p    = (date_param,) if date_param else ()
    base = f"FROM orders WHERE {date_filter}" if date_param else "FROM orders"

    def qry(sql):  cur.execute(sql, p); return cur.fetchone()
    def qrys(sql): cur.execute(sql, p); return cur.fetchall()

    if date_param:
        r_tot  = qry(f"SELECT COUNT(*),COALESCE(SUM(total),0) {base}")
        r_done = qry(f"SELECT COUNT(*) {base} AND status='Done'")
        r_pend = qry(f"SELECT COUNT(*) {base} AND status='Pending'")
        by_svc = qrys(f"SELECT service,COUNT(*),COALESCE(SUM(total),0) {base} GROUP BY service ORDER BY SUM(total) DESC")
        top_c  = qrys(f"SELECT name,COUNT(*),COALESCE(SUM(total),0) {base} GROUP BY name ORDER BY SUM(total) DESC LIMIT 5")
        daily  = qrys(f"SELECT date_created,COALESCE(SUM(total),0) {base} GROUP BY date_created ORDER BY date_created DESC LIMIT 7")
        cpr    = qrys(f"SELECT name,COALESCE(SUM(total),0) {base} GROUP BY name")
    else:
        r_tot  = qry("SELECT COUNT(*),COALESCE(SUM(total),0) FROM orders")
        r_done = qry("SELECT COUNT(*) FROM orders WHERE status='Done'")
        r_pend = qry("SELECT COUNT(*) FROM orders WHERE status='Pending'")
        by_svc = qrys("SELECT service,COUNT(*),COALESCE(SUM(total),0) FROM orders GROUP BY service ORDER BY SUM(total) DESC")
        top_c  = qrys("SELECT name,COUNT(*),COALESCE(SUM(total),0) FROM orders GROUP BY name ORDER BY SUM(total) DESC LIMIT 5")
        daily  = qrys("SELECT date_created,COALESCE(SUM(total),0) FROM orders GROUP BY date_created ORDER BY date_created DESC LIMIT 7")
        cpr    = qrys("SELECT name,COALESCE(SUM(total),0) FROM orders GROUP BY name")

    cur.close(); conn.close()

    tot_ord, tot_rev = r_tot[0], r_tot[1]
    done_cnt, pend_cnt = r_done[0], r_pend[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Total Orders", tot_ord or 0)
    c2.metric("💰 Revenue",       f"₱{(tot_rev or 0):,.2f}")
    c3.metric("✅ Completed",     done_cnt or 0)
    c4.metric("⏳ Pending",       pend_cnt or 0)
    st.markdown("<br>", unsafe_allow_html=True)

    if by_svc:
        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("Revenue by Service")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        max_r = max(r[2] for r in by_svc) or 1
        for svc, cnt, rev in by_svc:
            la, lb = st.columns([3, 1])
            la.markdown(f"<span style='color:var(--text);font-size:13px;font-weight:600'>{svc}</span>"
                        f"<span style='color:var(--muted);font-size:11px'>&nbsp;({cnt} orders)</span>",
                        unsafe_allow_html=True)
            lb.markdown(f"<div style='text-align:right;color:var(--green);font-weight:700;"
                        f"font-size:13px;font-family:\"Space Mono\",monospace'>₱{rev:,.2f}</div>",
                        unsafe_allow_html=True)
            st.progress(rev / max_r)
        st.markdown("</div>", unsafe_allow_html=True)

    if top_c:
        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("Top 5 Customers")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, (cn, cc, cr) in enumerate(top_c):
            st.markdown(f"""
            <div style='background:var(--surf2);border:1px solid var(--border);border-radius:12px;
                        padding:12px 18px;display:flex;align-items:center;margin-bottom:8px'>
                <span style='font-size:18px;width:38px'>{medals[i]}</span>
                <span style='flex:1;font-size:13px;font-weight:700;color:var(--text)'>{cn}</span>
                <span style='font-size:11px;color:var(--muted);width:80px'>{cc} order{'s' if cc!=1 else ''}</span>
                <span style='font-size:14px;font-weight:700;color:var(--green);
                             font-family:"Space Mono",monospace'>₱{cr:,.2f}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if cpr:
        all_rev = [r[1] for r in cpr]
        avg     = sum(all_rev) / len(all_rev) if all_rev else 0
        high_c  = [(r[0], r[1]) for r in cpr if r[1] >= avg]
        low_c   = [(r[0], r[1]) for r in cpr if r[1] < avg]
        hi_rev  = sum(r for _, r in high_c)
        lo_rev  = sum(r for _, r in low_c)
        tot_pie = hi_rev + lo_rev or 1
        hip, lop = hi_rev / tot_pie, lo_rev / tot_pie
        hi_w = max(int(hip * 100), 1)

        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("Profit Distribution by Customer")
        st.markdown(f"""
        <div style='font-size:11px;color:var(--muted);margin:6px 0 16px'>
            Avg spend&nbsp;<span style='color:var(--text);font-family:"Space Mono",monospace'>
            ₱{avg:,.2f}</span>&nbsp;·&nbsp;above avg = High Profit&nbsp;·&nbsp;{lbl}
        </div>
        <div class='bar-track' style='margin-bottom:8px'>
            <div class='bar-high' style='width:{hi_w}%'></div>
            <div class='bar-low'  style='width:{100-hi_w}%'></div>
        </div>
        <div style='display:flex;justify-content:space-between;margin-bottom:16px'>
            <span style='font-size:11px;color:var(--green);font-weight:700'>High {hip*100:.0f}%</span>
            <span style='font-size:11px;color:var(--orange);font-weight:700'>Low {lop*100:.0f}%</span>
        </div>
        """, unsafe_allow_html=True)
        ch, cl = st.columns(2)
        with ch:
            st.markdown(f"""
            <div style='background:var(--surf2);border:1px solid var(--border);border-radius:12px;
                        padding:14px 16px;margin-bottom:8px'>
                <div style='color:var(--green);font-weight:700;font-size:13px;margin-bottom:4px'>
                    🟢 High Profit — {hip*100:.1f}%
                </div>
                <div style='color:var(--muted);font-size:11px'>
                    {len(high_c)} customer{'s' if len(high_c)!=1 else ''}&nbsp;·&nbsp;
                    <span style='font-family:"Space Mono",monospace'>₱{hi_rev:,.2f}</span>
                </div>
            </div>""", unsafe_allow_html=True)
            st.progress(hip)
        with cl:
            st.markdown(f"""
            <div style='background:var(--surf2);border:1px solid var(--border);border-radius:12px;
                        padding:14px 16px;margin-bottom:8px'>
                <div style='color:var(--orange);font-weight:700;font-size:13px;margin-bottom:4px'>
                    🟡 Low Profit — {lop*100:.1f}%
                </div>
                <div style='color:var(--muted);font-size:11px'>
                    {len(low_c)} customer{'s' if len(low_c)!=1 else ''}&nbsp;·&nbsp;
                    <span style='font-family:"Space Mono",monospace'>₱{lo_rev:,.2f}</span>
                </div>
            </div>""", unsafe_allow_html=True)
            st.progress(lop)
        st.markdown("</div>", unsafe_allow_html=True)

    if daily:
        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("Daily Revenue (Recent)")
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        max_d = max(r[1] for r in daily) or 1
        for d_date, d_rev in daily:
            da, db = st.columns([2, 1])
            da.markdown(f"<span style='color:var(--muted);font-size:12px'>📅&nbsp;{d_date or '—'}</span>",
                        unsafe_allow_html=True)
            db.markdown(f"<div style='text-align:right;color:var(--green);font-weight:700;"
                        f"font-size:13px;font-family:\"Space Mono\",monospace'>₱{d_rev:,.2f}</div>",
                        unsafe_allow_html=True)
            st.progress(d_rev / max_d)
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_settings():
    user     = st.session_state.username
    role     = st.session_state.role
    is_admin = role == "Admin"

    page_header("Settings", "Account, pricing, and system preferences", "⚙️")

    badge_cls = "badge-admin" if is_admin else "badge-staff"
    st.markdown(f"""
    <div class='ls-section-box'>
        <div class='ls-section-title'>Account Info</div>
        <div style='height:14px'></div>
        <div style='display:flex;align-items:center;gap:18px'>
            <div style='width:58px;height:58px;border-radius:50%;flex-shrink:0;
                        background:linear-gradient(135deg,var(--accent2),var(--accent));
                        display:flex;align-items:center;justify-content:center;
                        font-weight:800;font-size:22px;color:#fff'>
                {user[0].upper() if user else "U"}
            </div>
            <div>
                <div style='font-size:18px;font-weight:700;color:var(--text)'>{user}</div>
                <div style='margin-top:5px'><span class='{badge_cls}'>{role}</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
    section_title("Change Password")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    old_pw  = st.text_input("Current Password",     type="password", key="s_old")
    p1, p2  = st.columns(2)
    new_pw  = p1.text_input("New Password",         type="password", key="s_new")
    conf_pw = p2.text_input("Confirm New Password", type="password", key="s_conf")
    if st.button("🔒 Update Password", type="primary", key="s_upd"):
        if not old_pw or not new_pw or not conf_pw:
            st.error("Please fill all password fields.")
        elif new_pw != conf_pw:
            st.error("New passwords do not match.")
        elif len(new_pw) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE username=?", (user,))
            row = cur.fetchone()
            if not row or row["password"] != hash_password(old_pw):
                st.error("Current password is incorrect.")
            else:
                cur.execute("UPDATE users SET password=? WHERE username=?",
                            (hash_password(new_pw), user))
                conn.commit()
                st.success("✅ Password changed successfully!")
            cur.close(); conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
    lock = "" if is_admin else "&nbsp;<span class='badge-pending'>🔒 Admin only</span>"
    section_title(f"Service Pricing{lock}")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    pc1, pc2, pc3 = st.columns(3)
    wash_r    = pc1.text_input("Wash (per kg ₱)",         value="50", disabled=not is_admin, key="pr_wash")
    washdry_r = pc2.text_input("Wash & Dry (per kg ₱)",   value="75", disabled=not is_admin, key="pr_wd")
    full_r    = pc3.text_input("Full Service (per kg ₱)", value="95", disabled=not is_admin, key="pr_fs")
    if is_admin:
        if st.button("💾 Save Pricing", type="primary", key="pr_save"):
            try:
                float(wash_r); float(washdry_r); float(full_r)
                st.success("✅ Pricing updated! Applies to new orders.")
            except ValueError:
                st.error("Please enter valid numbers for all prices.")
    else:
        st.markdown("<div style='font-size:12px;color:var(--muted);font-style:italic;margin-top:4px'>"
                    "Contact an Admin to update service pricing.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if is_admin:
        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("User Management")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, username, role FROM users ORDER BY id")
        users = cur.fetchall(); cur.close(); conn.close()

        for u_row in users:
            uid   = u_row["id"]; uname = u_row["username"]; urole = u_row["role"]
            is_self  = uname == user
            role_cls = "badge-admin" if urole == "Admin" else "badge-staff"
            grad = "var(--accent),var(--accent2)" if urole == "Admin" else "var(--accent2),var(--accent)"
            ca, cb = st.columns([5, 1])
            ca.markdown(f"""
            <div style='background:var(--surf2);border:1px solid var(--border);border-radius:12px;
                        padding:10px 16px;display:flex;align-items:center;gap:12px'>
                <div style='width:36px;height:36px;border-radius:50%;flex-shrink:0;
                            background:linear-gradient(135deg,{grad});
                            display:flex;align-items:center;justify-content:center;
                            font-weight:800;font-size:13px;color:#fff'>
                    {uname[0].upper()}
                </div>
                <div style='flex:1'>
                    <div style='font-size:13px;font-weight:700;color:var(--text)'>
                        {uname}{"&nbsp;<span class='badge-admin'>You</span>" if is_self else ""}
                    </div>
                    <span class='{role_cls}'>{urole}</span>
                </div>
            </div>""", unsafe_allow_html=True)
            if not is_self:
                if cb.button("🗑️", key=f"dul_{uid}"):
                    st.session_state[f"cdelu_{uid}"] = True

            if st.session_state.get(f"cdelu_{uid}"):
                st.warning(f"Delete user **{uname}**?")
                y2, n2, _ = st.columns([1, 1, 5])
                if y2.button("Delete", key=f"ydu_{uid}", type="primary"):
                    conn2 = get_connection(); cur2 = conn2.cursor()
                    cur2.execute("DELETE FROM users WHERE id=?", (uid,))
                    conn2.commit(); cur2.close(); conn2.close()
                    st.session_state.pop(f"cdelu_{uid}", None); st.rerun()
                if n2.button("Cancel", key=f"ndu_{uid}"):
                    st.session_state.pop(f"cdelu_{uid}", None); st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
init_session()
inject_css()
init_db()

if not st.session_state.logged_in:
    render_auth()
else:
    render_sidebar()
    v = st.session_state.view
    if   v == "dashboard": render_dashboard()
    elif v == "orders":    render_orders()
    elif v == "customers": render_customers()
    elif v == "reports":   render_reports()
    elif v == "settings":  render_settings()
