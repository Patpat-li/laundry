import streamlit as st
import sqlite3
import hashlib
import datetime

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LaundroSoft POS",
    page_icon="🧺",
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
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, service TEXT NOT NULL,
        weight REAL NOT NULL, total REAL NOT NULL,
        status TEXT NOT NULL, date_created TEXT, pickup_date TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS pricing (
        service TEXT PRIMARY KEY, rate REAL NOT NULL)""")
    conn.commit()
    cur.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)",
                ("admin", hash_password("admin123"), "Admin"))
    for svc, rate in [("Wash",50.0),("Wash & Dry",75.0),("Full Service",95.0)]:
        cur.execute("INSERT OR IGNORE INTO pricing (service,rate) VALUES (?,?)",(svc,rate))
    conn.commit()
    cur.close()
    conn.close()

def hash_password(pw, salt="laundry_secure_123"):
    return hashlib.sha256((pw+salt).encode()).hexdigest()

def get_rates():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT service,rate FROM pricing")
    r = {row["service"]: row["rate"] for row in cur.fetchall()}
    cur.close()
    conn.close()
    return r

# ─── SVG LOGO ─────────────────────────────────────────────────────────────────
LOGO_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48' width='{w}' height='{h}'>"
    "<defs><linearGradient id='lg' x1='0%' y1='0%' x2='100%' y2='100%'>"
    "<stop offset='0%' style='stop-color:#4F7EFF'/>"
    "<stop offset='100%' style='stop-color:#7C3AED'/>"
    "</linearGradient></defs>"
    "<rect width='48' height='48' rx='12' fill='url(#lg)'/>"
    "<rect x='9' y='11' width='30' height='28' rx='4' fill='none' stroke='white' stroke-width='2.2'/>"
    "<circle cx='24' cy='27' r='8' fill='none' stroke='white' stroke-width='2'/>"
    "<circle cx='24' cy='27' r='4.5' fill='none' stroke='white' stroke-width='1.2' stroke-dasharray='2.5 2'/>"
    "<line x1='9' y1='18' x2='39' y2='18' stroke='white' stroke-width='1.8'/>"
    "<circle cx='14' cy='14.5' r='1.8' fill='white'/>"
    "<circle cx='19.5' cy='14.5' r='1.8' fill='white' opacity='0.6'/>"
    "<path d='M18 27.5 Q21 25.5 24 27.5 Q27 29.5 30 27.5' fill='none' stroke='white' stroke-width='1.3' stroke-linecap='round'/>"
    "</svg>"
)

def logo(w=38, h=38):
    return LOGO_SVG.format(w=w, h=h)

# ─── CSS ──────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #0B0E1A !important;
        color: #E8EAF6;
        font-family: 'Inter', sans-serif !important;
    }
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stDecoration"] { display:none; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111527 0%, #0D1020 100%) !important;
        border-right: 1px solid #1E2340 !important;
    }
    [data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }
    [data-testid="stSidebarContent"] { padding: 0 !important; }

    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: #8892B0 !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 10px 14px !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(79,126,255,0.12) !important;
        color: #4F7EFF !important;
    }

    [data-testid="stMain"] .block-container {
        padding: 2rem 2.5rem 3rem !important;
        max-width: 1300px !important;
    }

    input, textarea {
        background-color: #161929 !important;
        color: #E8EAF6 !important;
        border: 1px solid #1E2340 !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
    }
    input:focus, textarea:focus {
        border-color: #4F7EFF !important;
        box-shadow: 0 0 0 3px rgba(79,126,255,0.15) !important;
    }
    [data-baseweb="select"] > div {
        background-color: #161929 !important;
        border: 1px solid #1E2340 !important;
        border-radius: 10px !important;
        color: #E8EAF6 !important;
    }
    [data-baseweb="popover"] * {
        background-color: #1A1D2E !important;
        color: #E8EAF6 !important;
    }
    label { color: #8892B0 !important; font-size: 12px !important; font-weight: 500 !important; }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4F7EFF, #7C3AED) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        letter-spacing: 0.3px !important;
        transition: opacity 0.15s !important;
    }
    .stButton > button[kind="primary"]:hover { opacity: 0.88 !important; }
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.15s ease !important;
    }

    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #131628, #161929) !important;
        border: 1px solid #1E2340 !important;
        border-radius: 18px !important;
        padding: 22px !important;
        position: relative;
        overflow: hidden;
    }
    [data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #4F7EFF, #7C3AED);
        border-radius: 18px 18px 0 0;
    }
    [data-testid="metric-container"] label {
        color: #8892B0 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: 0.8px !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricValue"] {
        color: #E8EAF6 !important;
        font-size: 30px !important;
        font-weight: 800 !important;
    }

    .ls-card {
        background: linear-gradient(135deg, #131628, #161929);
        border: 1px solid #1E2340;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 12px;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .ls-card:hover {
        border-color: #2E3660;
        box-shadow: 0 4px 24px rgba(0,0,0,0.35);
    }
    .ls-section-box {
        background: linear-gradient(135deg, #131628, #161929);
        border: 1px solid #1E2340;
        border-radius: 18px;
        padding: 24px 28px;
        margin-bottom: 20px;
    }

    .badge-done {
        background: rgba(34,197,94,0.12);
        color: #22C55E;
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .badge-pending {
        background: rgba(245,158,11,0.12);
        color: #F59E0B;
        border: 1px solid rgba(245,158,11,0.3);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .badge-admin {
        background: rgba(79,126,255,0.12);
        color: #4F7EFF;
        border: 1px solid rgba(79,126,255,0.3);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 700;
    }

    .ls-section-title {
        font-size: 15px;
        font-weight: 700;
        color: #E8EAF6;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .ls-section-title::before {
        content: '';
        display: inline-block;
        width: 4px; height: 18px;
        background: linear-gradient(180deg, #4F7EFF, #7C3AED);
        border-radius: 2px;
    }
    .ls-page-title {
        font-size: 28px;
        font-weight: 800;
        color: #E8EAF6;
        letter-spacing: -0.5px;
    }
    .ls-page-sub {
        font-size: 13px;
        color: #8892B0;
        margin-bottom: 24px;
        margin-top: 2px;
    }

    /* FIX 1: auth-panel now only styles a container div; inputs are placed inside
       via st.container() so they are visually grouped. We style the mid column
       background here instead of wrapping Streamlit widgets in raw HTML. */
    .auth-wrapper {
        background: linear-gradient(160deg, #131628, #0F1220);
        border: 1px solid #1E2340;
        border-radius: 24px;
        padding: 44px 48px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, #4F7EFF, #7C3AED) !important;
        border-radius: 4px !important;
    }
    .stProgress > div > div {
        background: #1E2340 !important;
        border-radius: 4px !important;
    }

    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border: none !important;
    }

    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #0B0E1A; }
    ::-webkit-scrollbar-thumb { background: #1E2340; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #2E3660; }

    hr { border-color: #1E2340 !important; margin: 16px 0 !important; }

    .notif-item {
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        display: flex;
        gap: 14px;
        align-items: flex-start;
    }
    .notif-warn { background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); }
    .notif-error { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2); }

    .cust-avatar {
        width: 46px; height: 46px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7C3AED, #4F7EFF);
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 15px; color: white;
        flex-shrink: 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ─── SESSION ──────────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "logged_in": False,
        "username": "",
        "role": "",
        "view": "dashboard",
        "auth_mode": "login",
        # FIX 2: pre-initialise filter/notification states to avoid missing-key
        # edge cases on first render
        "show_notifs": False,
        "ord_filter": "All",
        "rpt_period": "today",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════
def render_auth():
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("<br>", unsafe_allow_html=True)
        mode = st.session_state.auth_mode

        # Logo + brand (outside the card — decorative header)
        st.markdown(f"""
        <div style='text-align:center;margin-bottom:32px'>
            <div style='display:inline-flex;align-items:center;gap:14px;
                        background:linear-gradient(135deg,#131628,#161929);
                        border:1px solid #1E2340;border-radius:20px;
                        padding:18px 28px;'>
                {logo(52, 52)}
                <div style='text-align:left'>
                    <div style='font-size:24px;font-weight:800;
                                background:linear-gradient(135deg,#4F7EFF,#A78BFA);
                                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                                letter-spacing:-0.5px'>LaundroSoft</div>
                    <div style='font-size:12px;color:#8892B0;font-weight:500;letter-spacing:1px'>
                        POINT OF SALE
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # FIX 1: Render the card background as a wrapper div, then place a
        # st.container() inside so Streamlit widgets actually sit inside it.
        # We open the wrapper div here, render widgets, then close it.
        st.markdown("<div class='auth-wrapper'>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='font-size:26px;font-weight:800;color:#E8EAF6;margin-bottom:4px'>
            {'Create account' if mode == 'register' else 'Welcome back 👋'}
        </div>
        <div style='font-size:13px;color:#8892B0;margin-bottom:28px'>
            {'Register a new LaundroSoft account' if mode == 'register' else 'Sign in to your LaundroSoft POS'}
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", key="auth_user", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="auth_pass",
                                 placeholder="Enter your password")
        st.markdown("<br>", unsafe_allow_html=True)

        if mode == "login":
            if st.button("Sign In →", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT password,role FROM users WHERE username=?", (username,))
                    row = cur.fetchone()
                    cur.close()
                    conn.close()
                    if row and row["password"] == hash_password(password):
                        st.session_state.update({"logged_in": True, "username": username,
                                                  "role": row["role"], "view": "dashboard"})
                        st.rerun()
                    elif row:
                        st.error("Incorrect password.")
                    else:
                        st.error("Username not found.")

            st.markdown("<div style='text-align:center;margin-top:16px'>", unsafe_allow_html=True)
            if st.button("Don't have an account? Register", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            if st.button("Create Account →", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                                    (username, hash_password(password), "Staff"))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("Account created! You can now sign in.")
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username already exists.")

            if st.button("Already have an account? Sign in", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

        st.markdown("""
        <div style='text-align:center;margin-top:28px;color:#3A4060;font-size:11px'>
            Default admin: <b style='color:#4F7EFF'>admin</b> / <b style='color:#4F7EFF'>admin123</b>
        </div>
        """, unsafe_allow_html=True)

        # Close the auth-wrapper div
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    user = st.session_state.username
    role = st.session_state.role

    with st.sidebar:
        st.markdown(f"""
        <div style='padding:24px 20px 16px'>
            <div style='display:flex;align-items:center;gap:12px;margin-bottom:24px'>
                {logo(42, 42)}
                <div>
                    <div style='font-size:15px;font-weight:800;
                                background:linear-gradient(135deg,#4F7EFF,#A78BFA);
                                -webkit-background-clip:text;-webkit-text-fill-color:transparent'>
                        LaundroSoft
                    </div>
                    <div style='font-size:10px;color:#4A527A;font-weight:600;letter-spacing:1.2px'>
                        POS SYSTEM
                    </div>
                </div>
            </div>
            <div style='height:1px;background:linear-gradient(90deg,#1E2340,transparent);margin-bottom:20px'></div>
            <div style='font-size:10px;color:#3A4060;letter-spacing:2px;font-weight:700;
                        margin-bottom:10px;padding-left:4px'>NAVIGATION</div>
        </div>
        """, unsafe_allow_html=True)

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
                <div style='background:rgba(79,126,255,0.12);border:1px solid rgba(79,126,255,0.25);
                            border-radius:10px;padding:2px 0;margin:2px 16px 2px'>
                </div>
                """, unsafe_allow_html=True)
            _, col_btn = st.columns([0.08, 0.92])
            with col_btn:
                if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                    st.session_state.view = key
                    st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='padding:0 16px 12px'>
            <div style='height:1px;background:linear-gradient(90deg,#1E2340,transparent);margin-bottom:16px'></div>
            <div style='background:linear-gradient(135deg,#131628,#161929);
                        border:1px solid #1E2340;border-radius:14px;
                        padding:12px 14px;display:flex;align-items:center;gap:10px'>
                <div style='width:36px;height:36px;border-radius:50%;flex-shrink:0;
                            background:linear-gradient(135deg,#7C3AED,#4F7EFF);
                            display:flex;align-items:center;justify-content:center;
                            font-weight:800;font-size:14px;color:white'>
                    {user[0].upper()}
                </div>
                <div style='flex:1;min-width:0'>
                    <div style='font-size:13px;font-weight:700;color:#E8EAF6;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{user}</div>
                    <div style='font-size:10px;color:#8892B0;font-weight:500'>{role}</div>
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
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def page_header(title, subtitle, icon=""):
    st.markdown(f"""
    <div style='margin-bottom:28px'>
        <div class='ls-page-title'>{icon} {title}</div>
        <div class='ls-page-sub'>{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def section_title(text):
    st.markdown(f"<div class='ls-section-title'>{text}</div>", unsafe_allow_html=True)

def get_notifications():
    notes = []
    THRESHOLD = 1000.0
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status='Done'")
    earned = cur.fetchone()[0] or 0.0
    if earned < THRESHOLD:
        notes.append(("error", "⚠️ Low Revenue Alert",
                       f"Completed revenue ₱{earned:,.2f} is below the ₱{THRESHOLD:,.2f} threshold."))
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT id,name,service FROM orders WHERE pickup_date=? AND status='Pending'", (today,))
    for row in cur.fetchall():
        notes.append(("warn", "📦 Pick-up Today",
                       f"Order #{row['id']} — {row['name']} ({row['service']}) is due today."))
    cur.close()
    conn.close()
    return notes

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def render_dashboard():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*),COALESCE(SUM(total),0) FROM orders")
    total_cnt, total_rev = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
    pend = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Done'")
    done = cur.fetchone()[0]
    cur.close()
    conn.close()

    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown(f"""
        <div class='ls-page-title'>Dashboard</div>
        <div class='ls-page-sub'>
            {datetime.datetime.now().strftime('%A, %d %B %Y')}
        </div>
        """, unsafe_allow_html=True)
    with h2:
        notes = get_notifications()
        lbl = f"🔔 Alerts ({len(notes)})" if notes else "🔔 Alerts"
        if st.button(lbl, use_container_width=True):
            st.session_state["show_notifs"] = not st.session_state.get("show_notifs", False)

    if st.session_state.get("show_notifs"):
        for kind, title, body in notes:
            cls = "notif-error" if kind == "error" else "notif-warn"
            st.markdown(f"""
            <div class='notif-item {cls}' style='margin-top:6px'>
                <div>
                    <div style='font-size:13px;font-weight:700;color:#E8EAF6'>{title}</div>
                    <div style='font-size:12px;color:#8892B0;margin-top:3px'>{body}</div>
                </div>
            </div>""", unsafe_allow_html=True)
        if not notes:
            st.success("✅ All clear — no notifications right now.")

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋  Total Orders",  total_cnt)
    c2.metric("⏳  Pending",        pend)
    c3.metric("✅  Completed",      done)
    c4.metric("💰  Total Revenue",  f"₱{total_rev:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
    section_title("New Transaction")
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    rates = get_rates()
    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    cust_name = f1.text_input("Customer Name", placeholder="e.g. Juan dela Cruz", key="dash_name")
    weight    = f2.text_input("Weight (kg)",   placeholder="e.g. 3.5",            key="dash_weight")
    service   = f3.selectbox("Service", list(rates.keys()),                        key="dash_service")
    # FIX 3: date_input with value=None crashes on some Streamlit versions.
    # Use a checkbox to make the pickup date optional instead.
    use_pickup = f4.checkbox("Set pick-up date", key="dash_use_pickup")
    if use_pickup:
        pickup = f4.date_input("Pick-up Date", value=datetime.date.today(),
                               min_value=datetime.date.today(), key="dash_pickup")
    else:
        pickup = None

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("➕  Create Order", type="primary", key="dash_create"):
        if not cust_name or not weight:
            st.error("Please enter Customer Name and Weight.")
        else:
            try:
                kg    = float(weight)
                if kg <= 0:
                    st.error("Weight must be greater than zero.")
                else:
                    total = rates.get(service, 50) * kg
                    pu    = pickup.strftime("%Y-%m-%d") if pickup else ""
                    conn2 = get_connection()
                    cur2  = conn2.cursor()
                    cur2.execute(
                        "INSERT INTO orders (name,service,weight,total,status,date_created,pickup_date)"
                        " VALUES (?,?,?,?,?,?,?)",
                        (cust_name, service, kg, total, "Pending",
                         datetime.datetime.now().strftime("%Y-%m-%d"), pu))
                    conn2.commit()
                    cur2.close()
                    conn2.close()
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
    conn = get_connection()
    cur  = conn.cursor()
    q = "SELECT id,name,service,weight,total,status,date_created,pickup_date FROM orders"
    conds, params = [], []
    if status_filter != "All":
        conds.append("status=?")
        params.append(status_filter)
    if search:
        conds.append("name LIKE ?")
        params.append(f"%{search}%")
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY id DESC"
    if limit:
        q += f" LIMIT {limit}"
    cur.execute(q, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    if not rows:
        st.markdown("""
        <div style='text-align:center;padding:48px;color:#3A4060;
                    background:linear-gradient(135deg,#0F1220,#131628);
                    border:1px dashed #1E2340;border-radius:16px'>
            <div style='font-size:32px;margin-bottom:12px'>📭</div>
            <div style='font-size:14px;font-weight:600'>No orders found</div>
        </div>""", unsafe_allow_html=True)
        return

    for row in rows:
        oid    = row["id"]
        name_v = row["name"]
        svc_v  = row["service"]
        wt_v   = row["weight"]
        tot_v  = row["total"]
        stat_v = row["status"]
        date_v = row["date_created"]
        pick_v = row["pickup_date"]
        is_done = stat_v == "Done"
        badge   = "<span class='badge-done'>✓ Done</span>" if is_done else "<span class='badge-pending'>⏳ Pending</span>"
        pick_color = "#EF4444" if pick_v == today and not is_done else "#4A527A"
        pickup_str = pick_v or "—"

        st.markdown(f"""
        <div class='ls-card'>
          <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px'>
            <div style='display:flex;align-items:center;gap:10px'>
              <span style='color:#3A4060;font-size:11px;font-weight:700;
                           background:#0F1220;border:1px solid #1E2340;
                           border-radius:6px;padding:2px 7px'>#{oid}</span>
              <span style='color:#E8EAF6;font-size:15px;font-weight:700'>{name_v}</span>
              {badge}
            </div>
            <div style='font-size:16px;font-weight:800;
                        background:linear-gradient(135deg,#22C55E,#16A34A);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent'>
              ₱{tot_v:,.2f}
            </div>
          </div>
          <div style='display:flex;gap:18px;flex-wrap:wrap'>
            <span style='color:#4A527A;font-size:12px'>📅 <span style='color:#8892B0'>{date_v or "—"}</span></span>
            <span style='color:#4A527A;font-size:12px'>🚚 <span style='color:{pick_color}'>{pickup_str}</span></span>
            <span style='color:#4A527A;font-size:12px'>⚖️ <span style='color:#8892B0'>{wt_v} kg</span></span>
            <span style='color:#4A527A;font-size:12px'>👕 <span style='color:#4F7EFF;font-weight:600'>{svc_v}</span></span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # FIX 4: Rewrote button layout logic to be explicit per branch — eliminates
        # the confusing conditional column-unpacking and the intermediate None
        # assignments that made the intent hard to follow and error-prone.
        if not is_done:
            if show_edit:
                b1, b2, b3, _ = st.columns([1, 1, 1, 5])
                if b1.button("✅ Done",  key=f"done_{oid}_{status_filter}_{show_edit}"):
                    conn2 = get_connection(); cur2 = conn2.cursor()
                    cur2.execute("UPDATE orders SET status='Done' WHERE id=?", (oid,))
                    conn2.commit(); cur2.close(); conn2.close(); st.rerun()
                if b2.button("✏️ Edit", key=f"edit_{oid}_{status_filter}_{show_edit}"):
                    st.session_state[f"editing_{oid}"] = not st.session_state.get(f"editing_{oid}", False)
                if b3.button("🗑️",     key=f"del_{oid}_{status_filter}_{show_edit}"):
                    st.session_state[f"confirm_del_{oid}"] = True
            else:
                b1, b2, _ = st.columns([1, 1, 6])
                if b1.button("✅ Done", key=f"done_{oid}_{status_filter}_{show_edit}"):
                    conn2 = get_connection(); cur2 = conn2.cursor()
                    cur2.execute("UPDATE orders SET status='Done' WHERE id=?", (oid,))
                    conn2.commit(); cur2.close(); conn2.close(); st.rerun()
                if b2.button("🗑️",    key=f"del_{oid}_{status_filter}_{show_edit}"):
                    st.session_state[f"confirm_del_{oid}"] = True
        else:
            if show_edit:
                b1, b2, _ = st.columns([1, 1, 6])
                if b1.button("✏️ Edit", key=f"edit_{oid}_{status_filter}_{show_edit}"):
                    st.session_state[f"editing_{oid}"] = not st.session_state.get(f"editing_{oid}", False)
                if b2.button("🗑️",    key=f"del_{oid}_{status_filter}_{show_edit}"):
                    st.session_state[f"confirm_del_{oid}"] = True
            else:
                b1, _ = st.columns([1, 7])
                if b1.button("🗑️",   key=f"del_{oid}_{status_filter}_{show_edit}"):
                    st.session_state[f"confirm_del_{oid}"] = True

        # Delete confirmation (always rendered outside the branch so it survives reruns)
        if st.session_state.get(f"confirm_del_{oid}"):
            st.warning(f"⚠️ Delete Order #{oid} for **{name_v}**?")
            yc, nc, _ = st.columns([1, 1, 5])
            if yc.button("Delete", key=f"yes_del_{oid}", type="primary"):
                conn3 = get_connection(); cur3 = conn3.cursor()
                cur3.execute("DELETE FROM orders WHERE id=?", (oid,))
                conn3.commit(); cur3.close(); conn3.close()
                st.session_state.pop(f"confirm_del_{oid}", None)
                st.rerun()
            if nc.button("Cancel", key=f"no_del_{oid}"):
                st.session_state.pop(f"confirm_del_{oid}", None)
                st.rerun()

        # Inline edit form
        if show_edit and st.session_state.get(f"editing_{oid}"):
            rates = get_rates()
            st.markdown(
                f"<div style='padding:16px;background:#0F1220;border:1px solid #2E3660;"
                f"border-radius:12px;margin-bottom:10px;'>",
                unsafe_allow_html=True)
            st.markdown(f"**✏️ Editing Order #{oid}**")
            e1, e2, e3, e4 = st.columns([2, 1, 1, 1])
            e_name   = e1.text_input("Customer Name", value=name_v,      key=f"ename_{oid}")
            e_weight = e2.text_input("Weight (kg)",   value=str(wt_v),   key=f"ewt_{oid}")
            svc_opts = list(rates.keys())
            e_svc    = e3.selectbox("Service", svc_opts,
                                    index=svc_opts.index(svc_v) if svc_v in svc_opts else 0,
                                    key=f"esvc_{oid}")
            e_pickup = e4.text_input("Pick-up Date", value=pick_v or "",
                                     placeholder="YYYY-MM-DD", key=f"epick_{oid}")
            if st.button("💾 Save Changes", key=f"save_{oid}", type="primary"):
                try:
                    kg    = float(e_weight)
                    if kg <= 0:
                        st.error("Weight must be greater than zero.")
                    else:
                        total = rates.get(e_svc, 50) * kg
                        conn4 = get_connection(); cur4 = conn4.cursor()
                        cur4.execute(
                            "UPDATE orders SET name=?,service=?,weight=?,total=?,pickup_date=? WHERE id=?",
                            (e_name, e_svc, kg, total, e_pickup, oid))
                        conn4.commit(); cur4.close(); conn4.close()
                        st.session_state.pop(f"editing_{oid}", None)
                        st.rerun()
                except ValueError:
                    st.error("Invalid weight. Please enter a number.")
            st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  ORDERS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_orders():
    page_header("Orders", "View and manage all laundry orders", "📋")

    sc, sf = st.columns([2, 3])
    search = sc.text_input("🔍  Search customer", placeholder="Type a name…", key="ord_search")
    with sf:
        st.markdown("<br>", unsafe_allow_html=True)
        fa, fb, fc = st.columns(3)
        if fa.button("All",     use_container_width=True, key="flt_all"):     st.session_state["ord_filter"] = "All"
        if fb.button("Pending", use_container_width=True, key="flt_pending"): st.session_state["ord_filter"] = "Pending"
        if fc.button("Done",    use_container_width=True, key="flt_done"):    st.session_state["ord_filter"] = "Done"

    flt = st.session_state.get("ord_filter", "All")
    flt_colors = {"All": "#4F7EFF", "Pending": "#F59E0B", "Done": "#22C55E"}
    st.markdown(f"""
    <div style='margin:8px 0 16px;font-size:12px;color:#8892B0'>
        Filter: <span style='color:{flt_colors.get(flt, "#4F7EFF")};font-weight:700'>{flt}</span>
    </div>""", unsafe_allow_html=True)
    _render_orders_table(status_filter=flt, search=search, show_edit=True)

# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMERS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_customers():
    page_header("Customers", "All unique customers derived from orders", "👥")

    search = st.text_input("🔍  Search customer", placeholder="Type a name…", key="cust_search")

    conn = get_connection()
    cur  = conn.cursor()
    q = "SELECT name,COUNT(*) orders,COALESCE(SUM(total),0) spent,MAX(date_created) last FROM orders"
    p = []
    if search:
        q += " WHERE name LIKE ?"
        p.append(f"%{search}%")
    q += " GROUP BY name ORDER BY spent DESC"
    cur.execute(q, p)
    data = cur.fetchall()
    cur.close()
    conn.close()

    if not data:
        st.markdown("""<div style='text-align:center;padding:48px;color:#3A4060;
                        background:linear-gradient(135deg,#0F1220,#131628);
                        border:1px dashed #1E2340;border-radius:16px'>
            <div style='font-size:32px;margin-bottom:12px'>👥</div>
            <div style='font-size:14px;font-weight:600'>No customers found</div>
        </div>""", unsafe_allow_html=True)
        return

    for row in data:
        cname = row["name"]
        oc    = row["orders"]
        spent = row["spent"]
        last  = row["last"]
        initials = "".join([w[0].upper() for w in cname.split()[:2]])
        st.markdown(f"""
        <div class='ls-card' style='display:flex;align-items:center;gap:18px'>
            <div class='cust-avatar'>{initials}</div>
            <div style='flex:1'>
                <div style='font-size:15px;font-weight:700;color:#E8EAF6'>{cname}</div>
                <div style='font-size:11px;color:#4A527A;margin-top:2px'>
                    Last order: <span style='color:#8892B0'>{last or "—"}</span>
                </div>
            </div>
            <div style='text-align:center;min-width:90px'>
                <div style='font-size:14px;font-weight:800;color:#4F7EFF'>{oc}</div>
                <div style='font-size:10px;color:#4A527A;font-weight:600;letter-spacing:0.5px'>ORDER{'S' if oc != 1 else ''}</div>
            </div>
            <div style='width:1px;height:36px;background:#1E2340'></div>
            <div style='text-align:right;min-width:110px'>
                <div style='font-size:17px;font-weight:800;
                            background:linear-gradient(135deg,#22C55E,#16A34A);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent'>
                    ₱{spent:,.2f}
                </div>
                <div style='font-size:10px;color:#4A527A;font-weight:600;letter-spacing:0.5px'>TOTAL SPENT</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  REPORTS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_reports():
    page_header("Reports", "Business analytics and performance overview", "📈")

    pa, pb, pc, pd = st.columns(4)
    if pa.button("Today",       use_container_width=True): st.session_state["rpt_period"] = "today"
    if pb.button("Last 7 Days", use_container_width=True): st.session_state["rpt_period"] = "week"
    if pc.button("This Month",  use_container_width=True): st.session_state["rpt_period"] = "month"
    if pd.button("All Time",    use_container_width=True): st.session_state["rpt_period"] = "all"

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
    <div style='margin:-8px 0 20px;'>
        <span style='background:rgba(79,126,255,0.1);color:#4F7EFF;
                     border:1px solid rgba(79,126,255,0.2);border-radius:20px;
                     padding:4px 14px;font-size:12px;font-weight:700'>
            📅 {lbl}
        </span>
    </div>""", unsafe_allow_html=True)

    conn = get_connection()
    cur  = conn.cursor()
    p = (date_param,) if date_param else ()

    # FIX 5: Extracted the WHERE clause construction to avoid duplicating the
    # entire query block. One code path now handles both filtered and unfiltered.
    where = f"WHERE {date_filter}" if date_filter else ""

    def qry(sql):
        cur.execute(sql, p)
        return cur.fetchone()

    def qrys(sql):
        cur.execute(sql, p)
        return cur.fetchall()

    r_tot  = qry(f"SELECT COUNT(*),COALESCE(SUM(total),0) FROM orders {where}")
    r_done = qry(f"SELECT COUNT(*) FROM orders {where} {'AND' if where else 'WHERE'} status='Done'")
    r_pend = qry(f"SELECT COUNT(*) FROM orders {where} {'AND' if where else 'WHERE'} status='Pending'")
    by_svc = qrys(f"SELECT service,COUNT(*),COALESCE(SUM(total),0) FROM orders {where} GROUP BY service ORDER BY SUM(total) DESC")
    top_c  = qrys(f"SELECT name,COUNT(*),COALESCE(SUM(total),0) FROM orders {where} GROUP BY name ORDER BY SUM(total) DESC LIMIT 5")
    daily  = qrys(f"SELECT date_created,COALESCE(SUM(total),0) FROM orders {where} GROUP BY date_created ORDER BY date_created DESC LIMIT 7")
    cpr    = qrys(f"SELECT name,COALESCE(SUM(total),0) FROM orders {where} GROUP BY name")

    cur.close()
    conn.close()

    # FIX 6: Use explicit column indexing instead of tuple unpacking on sqlite3.Row
    # for single-column results, to be safe across all Streamlit/SQLite versions.
    tot_ord  = r_tot[0]
    tot_rev  = r_tot[1]
    done_cnt = r_done[0]
    pend_cnt = r_pend[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋  Total Orders",  tot_ord)
    c2.metric("💰  Revenue",        f"₱{tot_rev:,.2f}")
    c3.metric("✅  Completed",      done_cnt)
    c4.metric("⏳  Pending",        pend_cnt)
    st.markdown("<br>", unsafe_allow_html=True)

    if by_svc:
        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("Revenue by Service")
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        max_r = max(row[2] for row in by_svc) or 1
        for row in by_svc:
            svc, cnt, rev = row[0], row[1], row[2]
            la, lb = st.columns([3, 1])
            la.markdown(f"<span style='color:#E8EAF6;font-size:13px;font-weight:600'>{svc}</span>"
                        f" <span style='color:#4A527A;font-size:11px'>({cnt} orders)</span>",
                        unsafe_allow_html=True)
            lb.markdown(f"<div style='text-align:right;color:#22C55E;font-weight:700;font-size:13px'>₱{rev:,.2f}</div>",
                        unsafe_allow_html=True)
            st.progress(rev / max_r)
        st.markdown("</div>", unsafe_allow_html=True)

    if top_c:
        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("Top 5 Customers")
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        medals = ["🥇", "🥈", "🥉", "4th", "5th"]
        for i, row in enumerate(top_c):
            cn, cc, cr = row[0], row[1], row[2]
            st.markdown(f"""
            <div style='background:#0F1220;border:1px solid #1E2340;border-radius:12px;
                        padding:12px 18px;display:flex;align-items:center;margin-bottom:8px'>
                <span style='font-size:18px;width:38px'>{medals[i]}</span>
                <span style='flex:1;font-size:13px;font-weight:700;color:#E8EAF6'>{cn}</span>
                <span style='font-size:11px;color:#4A527A;width:80px'>{cc} order{'s' if cc != 1 else ''}</span>
                <span style='font-size:14px;font-weight:800;
                             background:linear-gradient(135deg,#22C55E,#16A34A);
                             -webkit-background-clip:text;-webkit-text-fill-color:transparent'>
                    ₱{cr:,.2f}
                </span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if cpr:
        all_rev = [row[1] for row in cpr]
        avg     = sum(all_rev) / len(all_rev) if all_rev else 0
        # FIX 7: Use explicit indexing (row[0], row[1]) instead of `for n, r in cpr`
        # to avoid ambiguity with sqlite3.Row iteration semantics.
        high_c = [(row[0], row[1]) for row in cpr if row[1] >= avg]
        low_c  = [(row[0], row[1]) for row in cpr if row[1] <  avg]
        hi_rev = sum(r for _, r in high_c)
        lo_rev = sum(r for _, r in low_c)
        tot_pie = hi_rev + lo_rev or 1
        hip, lop = hi_rev / tot_pie, lo_rev / tot_pie

        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("Profit Distribution by Customer")
        st.markdown(f"<div style='font-size:11px;color:#4A527A;margin:6px 0 16px'>"
                    f"Avg spend ₱{avg:,.2f} · above avg = High Profit · {lbl}</div>",
                    unsafe_allow_html=True)
        ch, cl = st.columns(2)
        with ch:
            st.markdown(f"<div style='color:#22C55E;font-weight:700;font-size:13px'>"
                        f"🟢 High Profit — {hip*100:.1f}%</div>"
                        f"<div style='color:#4A527A;font-size:11px;margin-bottom:8px'>"
                        f"{len(high_c)} customers · ₱{hi_rev:,.2f}</div>",
                        unsafe_allow_html=True)
            st.progress(hip)
        with cl:
            st.markdown(f"<div style='color:#F59E0B;font-weight:700;font-size:13px'>"
                        f"🟡 Low Profit — {lop*100:.1f}%</div>"
                        f"<div style='color:#4A527A;font-size:11px;margin-bottom:8px'>"
                        f"{len(low_c)} customers · ₱{lo_rev:,.2f}</div>",
                        unsafe_allow_html=True)
            st.progress(lop)
        st.markdown("</div>", unsafe_allow_html=True)

    if daily:
        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("Daily Revenue (Recent)")
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        max_d = max(row[1] for row in daily) or 1
        for row in daily:
            d_date, d_rev = row[0], row[1]
            da, db = st.columns([2, 1])
            da.markdown(f"<span style='color:#8892B0;font-size:12px'>📅 {d_date or '—'}</span>",
                        unsafe_allow_html=True)
            db.markdown(f"<div style='text-align:right;color:#22C55E;font-weight:700;font-size:13px'>"
                        f"₱{d_rev:,.2f}</div>", unsafe_allow_html=True)
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

    st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
    section_title("Account Info")
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:18px;margin-top:16px'>
        <div style='width:60px;height:60px;border-radius:50%;flex-shrink:0;
                    background:linear-gradient(135deg,#7C3AED,#4F7EFF);
                    display:flex;align-items:center;justify-content:center;
                    font-weight:800;font-size:22px;color:white'>
            {user[0].upper()}
        </div>
        <div>
            <div style='font-size:18px;font-weight:800;color:#E8EAF6'>{user}</div>
            <div style='display:flex;align-items:center;gap:8px;margin-top:4px'>
                <span class='badge-{"admin" if is_admin else "pending"}'>{role}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
    section_title("Change Password")
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
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
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("SELECT password FROM users WHERE username=?", (user,))
            row = cur.fetchone()
            if not row or row["password"] != hash_password(old_pw):
                st.error("Current password is incorrect.")
            else:
                cur.execute("UPDATE users SET password=? WHERE username=?",
                            (hash_password(new_pw), user))
                conn.commit()
                st.success("✅ Password changed successfully!")
            cur.close()
            conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
    lock = ("" if is_admin else
            " &nbsp;<span style='background:rgba(245,158,11,0.1);color:#F59E0B;"
            "border:1px solid rgba(245,158,11,0.25);border-radius:20px;padding:2px 10px;"
            "font-size:11px'>🔒 Admin only</span>")
    section_title(f"Service Pricing{lock}")
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    rates = get_rates()
    pc1, pc2, pc3 = st.columns(3)
    wash_r    = pc1.text_input("Wash (per kg ₱)",         value=str(rates.get("Wash", 50)),         disabled=not is_admin, key="pr_wash")
    washdry_r = pc2.text_input("Wash & Dry (per kg ₱)",   value=str(rates.get("Wash & Dry", 75)),   disabled=not is_admin, key="pr_wd")
    full_r    = pc3.text_input("Full Service (per kg ₱)", value=str(rates.get("Full Service", 95)), disabled=not is_admin, key="pr_fs")
    if is_admin:
        if st.button("💾 Save Pricing", type="primary", key="pr_save"):
            try:
                nr = {
                    "Wash":         float(wash_r),
                    "Wash & Dry":   float(washdry_r),
                    "Full Service": float(full_r),
                }
                if any(v <= 0 for v in nr.values()):
                    st.error("All prices must be greater than zero.")
                else:
                    conn = get_connection()
                    cur  = conn.cursor()
                    for s, r in nr.items():
                        cur.execute("INSERT OR REPLACE INTO pricing (service,rate) VALUES (?,?)", (s, r))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("✅ Pricing updated! Applies to new orders.")
            except ValueError:
                st.error("Please enter valid numbers for all prices.")
    else:
        st.markdown("<div style='font-size:12px;color:#4A527A;font-style:italic;margin-top:4px'>"
                    "Contact an Admin to update service pricing.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if is_admin:
        st.markdown("<div class='ls-section-box'>", unsafe_allow_html=True)
        section_title("User Management")
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id,username,role FROM users ORDER BY id")
        users = cur.fetchall()
        cur.close()
        conn.close()

        for u in users:
            uid, uname, urole = u["id"], u["username"], u["role"]
            is_self = uname == user
            ca, cb = st.columns([4, 1])
            ca.markdown(f"""
            <div style='background:#0F1220;border:1px solid #1E2340;border-radius:12px;
                        padding:10px 16px;display:flex;align-items:center;gap:12px'>
                <div style='width:38px;height:38px;border-radius:50%;flex-shrink:0;
                            background:linear-gradient(135deg,{"#4F7EFF,#7C3AED" if urole=="Admin" else "#7C3AED,#4F7EFF"});
                            display:flex;align-items:center;justify-content:center;
                            font-weight:800;font-size:13px;color:white'>
                    {uname[0].upper()}
                </div>
                <div>
                    <div style='font-size:13px;font-weight:700;color:#E8EAF6'>
                        {uname}
                        {'&nbsp;<span class="badge-admin">You</span>' if is_self else ''}
                    </div>
                    <div style='font-size:10px;color:#4A527A;margin-top:2px;font-weight:600'>{urole.upper()}</div>
                </div>
            </div>""", unsafe_allow_html=True)
            if not is_self:
                if cb.button("🗑️", key=f"dul_{uid}"):
                    st.session_state[f"cdelu_{uid}"] = True
            if st.session_state.get(f"cdelu_{uid}"):
                st.warning(f"Delete user **{uname}**?")
                y2, n2, _ = st.columns([1, 1, 5])
                if y2.button("Delete", key=f"ydu_{uid}", type="primary"):
                    conn2 = get_connection()
                    cur2  = conn2.cursor()
                    cur2.execute("DELETE FROM users WHERE id=?", (uid,))
                    conn2.commit()
                    cur2.close()
                    conn2.close()
                    st.session_state.pop(f"cdelu_{uid}", None)
                    st.rerun()
                if n2.button("Cancel", key=f"ndu_{uid}"):
                    st.session_state.pop(f"cdelu_{uid}", None)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
init_db()
init_session()
inject_css()

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
