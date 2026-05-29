import streamlit as st
import sqlite3
import hashlib
import datetime
import os

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LaundroSoft POS",
    page_icon="🧺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── DATABASE ────────────────────────────────────────────────────────────────
DB_PATH = "laundrosoft.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service TEXT NOT NULL,
            weight REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL,
            date_created TEXT,
            pickup_date TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pricing (
            service TEXT PRIMARY KEY,
            rate REAL NOT NULL
        )
    """)
    conn.commit()

    # Default admin
    try:
        cur.execute(
            "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", hash_password("admin123"), "Admin")
        )
        conn.commit()
    except Exception:
        pass

    # Default pricing
    for svc, rate in [("Wash", 50.0), ("Wash & Dry", 75.0), ("Full Service", 95.0)]:
        cur.execute("INSERT OR IGNORE INTO pricing (service, rate) VALUES (?, ?)", (svc, rate))
    conn.commit()
    cur.close()
    conn.close()

def hash_password(password, salt="laundry_secure_123"):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def get_rates():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT service, rate FROM pricing")
    rates = {row["service"]: row["rate"] for row in cur.fetchall()}
    cur.close(); conn.close()
    return rates

# ─── STYLES ──────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    /* ── Global ── */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0F1117;
        color: #E8EAF6;
    }
    [data-testid="stSidebar"] {
        background-color: #1A1D27 !important;
        border-right: 1px solid #2E3352;
    }
    [data-testid="stSidebar"] * { color: #E8EAF6 !important; }

    /* ── Inputs ── */
    input, textarea, [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        background-color: #22263A !important;
        color: #E8EAF6 !important;
        border-color: #2E3352 !important;
        border-radius: 10px !important;
    }
    [data-baseweb="select"] > div {
        background-color: #22263A !important;
        border-color: #2E3352 !important;
        color: #E8EAF6 !important;
    }
    [data-baseweb="popover"] * {
        background-color: #22263A !important;
        color: #E8EAF6 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    .stButton > button:hover { opacity: 0.85; }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background-color: #1A1D27;
        border: 1px solid #2E3352;
        border-radius: 16px;
        padding: 20px;
    }
    [data-testid="metric-container"] label { color: #8892B0 !important; font-size: 12px; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #E8EAF6 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }

    /* ── Dividers ── */
    hr { border-color: #2E3352 !important; }

    /* ── Tabs ── */
    [data-baseweb="tab-list"] { background-color: #1A1D27 !important; border-radius: 10px; }
    [data-baseweb="tab"] { color: #8892B0 !important; }
    [aria-selected="true"] { color: #4F7EFF !important; border-bottom-color: #4F7EFF !important; }

    /* ── Cards ── */
    .order-card {
        background: #1A1D27;
        border: 1px solid #2E3352;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 10px;
    }
    .badge-done   { background:#22C55E22; color:#22C55E; border:1px solid #22C55E44;
                    border-radius:20px; padding:3px 10px; font-size:11px; font-weight:700; }
    .badge-pending{ background:#F59E0B22; color:#F59E0B; border:1px solid #F59E0B44;
                    border-radius:20px; padding:3px 10px; font-size:11px; font-weight:700; }
    .section-header { font-size:16px; font-weight:700; color:#E8EAF6; margin-bottom:4px; }

    /* ── Progress bar ── */
    .stProgress > div > div { background-color: #4F7EFF !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #1A1D27; }
    ::-webkit-scrollbar-thumb { background: #2E3352; border-radius: 3px; }

    /* ── Success / Error banners ── */
    [data-testid="stAlert"] { border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)


# ─── SESSION STATE INIT ───────────────────────────────────────────────────────
def init_session():
    for k, v in [
        ("logged_in", False),
        ("username", ""),
        ("role", ""),
        ("view", "dashboard"),
        ("auth_mode", "login"),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════
def render_auth():
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='display:flex;align-items:center;gap:12px;margin-bottom:32px'>
                <div style='width:44px;height:44px;background:#4F7EFF;border-radius:12px;
                            display:flex;align-items:center;justify-content:center;font-size:22px'>🧺</div>
                <div>
                    <div style='font-size:16px;font-weight:700;color:#E8EAF6'>LaundroSoft</div>
                    <div style='font-size:11px;color:#8892B0'>Point of Sale</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        mode = st.session_state.auth_mode
        st.markdown(
            f"<div style='font-size:28px;font-weight:700;color:#E8EAF6;margin-bottom:4px'>"
            f"{'Create account' if mode=='register' else 'Welcome back'}</div>"
            f"<div style='font-size:14px;color:#8892B0;margin-bottom:24px'>"
            f"{'Join LaundroSoft POS' if mode=='register' else 'Sign in to LaundroSoft POS'}</div>",
            unsafe_allow_html=True
        )

        username = st.text_input("Username", key="auth_user", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="auth_pass", placeholder="Enter your password")

        if mode == "login":
            if st.button("SIGN IN", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT password, role FROM users WHERE username=?", (username,))
                    row = cur.fetchone()
                    cur.close(); conn.close()
                    if row and row["password"] == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = row["role"]
                        st.session_state.view = "dashboard"
                        st.rerun()
                    elif row:
                        st.error("Incorrect password.")
                    else:
                        st.error("Username not found.")

            if st.button("Don't have an account? Register", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()

        else:  # register
            if st.button("REGISTER", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                            (username, hash_password(password), "Staff")
                        )
                        conn.commit()
                        cur.close(); conn.close()
                        st.success("Account created! You can now sign in.")
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username already exists.")

            if st.button("Already have an account? Sign in", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

    with col_r:
        st.markdown("""
            <div style='height:100%;display:flex;flex-direction:column;align-items:center;
                        justify-content:center;padding:60px 20px;opacity:0.2;margin-top:80px'>
                <div style='font-size:80px'>🧺</div>
                <div style='font-size:32px;font-weight:700;color:#E8EAF6;text-align:center'>LaundroSoft POS</div>
                <div style='font-size:20px;color:#E8EAF6;text-align:center;margin-top:12px'>
                    Manage your laundry<br>business with ease.
                </div>
            </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR NAV
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    user = st.session_state.username
    role = st.session_state.role

    st.sidebar.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:28px'>
            <div style='width:38px;height:38px;background:#4F7EFF;border-radius:10px;
                        display:flex;align-items:center;justify-content:center;font-size:18px'>🧺</div>
            <div>
                <div style='font-size:14px;font-weight:700'>LaundroSoft</div>
                <div style='font-size:10px;color:#8892B0'>POS System</div>
            </div>
        </div>
        <div style='font-size:10px;color:#8892B0;letter-spacing:2px;font-weight:700;margin-bottom:8px'>MENU</div>
    """, unsafe_allow_html=True)

    nav = [
        ("dashboard",  "📊 Dashboard"),
        ("orders",     "📋 Orders"),
        ("customers",  "👥 Customers"),
        ("reports",    "📈 Reports"),
        ("settings",   "⚙️ Settings"),
    ]
    for key, label in nav:
        active = st.session_state.view == key
        style = "background:#4F7EFF22;border:1px solid #4F7EFF44;border-radius:10px;" if active else ""
        color = "#4F7EFF" if active else "#8892B0"
        if st.sidebar.button(
            label,
            key=f"nav_{key}",
            use_container_width=True,
        ):
            st.session_state.view = key
            st.rerun()

    st.sidebar.markdown("<br><hr>", unsafe_allow_html=True)
    st.sidebar.markdown(f"""
        <div style='background:#22263A;border-radius:10px;padding:10px 12px;
                    display:flex;align-items:center;gap:8px'>
            <div style='width:32px;height:32px;background:#7C3AED;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:13px'>{user[0].upper()}</div>
            <div>
                <div style='font-size:12px;font-weight:700'>{user}</div>
                <div style='font-size:10px;color:#8892B0'>{role}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Log out", use_container_width=True):
        for k in ["logged_in", "username", "role", "view", "auth_mode"]:
            st.session_state[k] = False if k == "logged_in" else ("login" if k == "auth_mode" else "")
        st.session_state.view = "dashboard"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  NOTIFICATIONS HELPER
# ══════════════════════════════════════════════════════════════════════════════
def get_notifications():
    notes = []
    PROFIT_LOW_THRESHOLD = 1000.0
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status='Done'")
    earned = cur.fetchone()[0] or 0.0
    if earned < PROFIT_LOW_THRESHOLD:
        notes.append(("🔴", "Low Revenue Alert",
                       f"Total completed revenue is ₱{earned:,.2f} — below the ₱{PROFIT_LOW_THRESHOLD:,.2f} threshold."))

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT id, name, service FROM orders WHERE pickup_date=? AND status='Pending'", (today,))
    for row in cur.fetchall():
        notes.append(("🟡", "Pick-up Today",
                       f"Order #{row['id']} — {row['name']} ({row['service']}) is scheduled for pick-up today."))

    cur.close(); conn.close()
    return notes


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def render_dashboard():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders")
    total_cnt, total_rev = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
    pend = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Done'")
    done = cur.fetchone()[0]
    cur.close(); conn.close()

    # Header row
    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown(f"""
            <div style='font-size:26px;font-weight:700;color:#E8EAF6'>Dashboard</div>
            <div style='font-size:13px;color:#8892B0'>{datetime.datetime.now().strftime('%d %B %Y')}</div>
        """, unsafe_allow_html=True)
    with h2:
        notes = get_notifications()
        bell_label = f"🔔 Notifications ({len(notes)})" if notes else "🔔 Notifications"
        if st.button(bell_label, use_container_width=True):
            st.session_state["show_notifs"] = not st.session_state.get("show_notifs", False)

    if st.session_state.get("show_notifs"):
        if not notes:
            st.success("✅ No notifications right now. All good!")
        else:
            for icon, title, body in notes:
                st.warning(f"**{icon} {title}** — {body}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Stat cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Total Orders", total_cnt)
    c2.metric("⏳ Pending", pend)
    c3.metric("✅ Completed", done)
    c4.metric("💰 Total Revenue", f"₱{total_rev:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🛒 New Transaction</div>", unsafe_allow_html=True)

    with st.container():
        rates = get_rates()
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        with f1:
            cust_name = st.text_input("Customer Name", placeholder="e.g. Juan dela Cruz", key="dash_name")
        with f2:
            weight = st.text_input("Weight (kg)", placeholder="e.g. 3.5", key="dash_weight")
        with f3:
            service = st.selectbox("Service", list(rates.keys()), key="dash_service")
        with f4:
            pickup = st.date_input("Pick-up Date (Optional)", value=None, key="dash_pickup",
                                   min_value=datetime.date.today())

        if st.button("➕ CREATE ORDER", type="primary"):
            if not cust_name or not weight:
                st.error("Please enter Customer Name and Weight.")
            else:
                try:
                    kg = float(weight)
                    total = rates.get(service, 50) * kg
                    pickup_str = pickup.strftime("%Y-%m-%d") if pickup else ""
                    conn2 = get_connection()
                    cur2 = conn2.cursor()
                    cur2.execute(
                        "INSERT INTO orders (name,service,weight,total,status,date_created,pickup_date) VALUES (?,?,?,?,?,?,?)",
                        (cust_name, service, kg, total, "Pending",
                         datetime.datetime.now().strftime("%Y-%m-%d"), pickup_str)
                    )
                    conn2.commit()
                    cur2.close(); conn2.close()
                    st.success(f"Order created! Total: ₱{total:,.2f}")
                    st.rerun()
                except ValueError:
                    st.error("Invalid weight. Please enter a number.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📋 Recent Orders</div>", unsafe_allow_html=True)
    _render_orders_table(limit=20, show_edit=False)


# ══════════════════════════════════════════════════════════════════════════════
#  ORDERS HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _render_orders_table(limit=None, show_edit=True, status_filter="All", search=""):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT id,name,service,weight,total,status,date_created,pickup_date FROM orders"
    conditions = []
    params = []
    if status_filter != "All":
        conditions.append("status=?")
        params.append(status_filter)
    if search:
        conditions.append("name LIKE ?")
        params.append(f"%{search}%")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    if limit:
        query += f" LIMIT {limit}"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close(); conn.close()

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    if not rows:
        st.markdown("<div style='text-align:center;color:#8892B0;padding:40px'>📭 No orders found</div>",
                    unsafe_allow_html=True)
        return

    for row in rows:
        oid, name_v, svc_v, wt_v, tot_v, stat_v, date_v, pick_v = (
            row["id"], row["name"], row["service"], row["weight"],
            row["total"], row["status"], row["date_created"], row["pickup_date"]
        )
        is_done = stat_v == "Done"
        badge = f"<span class='badge-done'>Done</span>" if is_done else f"<span class='badge-pending'>Pending</span>"
        pickup_color = "#EF4444" if pick_v == today and not is_done else "#8892B0"
        pickup_str = pick_v if pick_v else "—"

        st.markdown(f"""
        <div class='order-card'>
            <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px'>
                <div>
                    <span style='color:#8892B0;font-size:11px;font-weight:700'>#{oid}</span>
                    &nbsp;&nbsp;
                    <span style='color:#E8EAF6;font-size:14px;font-weight:700'>{name_v}</span>
                    &nbsp;&nbsp;{badge}
                </div>
                <div style='color:#22C55E;font-size:14px;font-weight:700'>₱{tot_v:,.2f}</div>
            </div>
            <div style='display:flex;gap:16px;font-size:12px;color:#8892B0;flex-wrap:wrap'>
                <span>📅 {date_v or '—'}</span>
                <span style='color:{pickup_color}'>🚚 {pickup_str}</span>
                <span>⚖️ {wt_v} kg</span>
                <span style='color:#4F7EFF'>👕 {svc_v}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action buttons
        btn_cols = st.columns([1, 1, 1, 6] if not is_done else [1, 1, 7])
        if not is_done:
            if btn_cols[0].button("✅ Done", key=f"done_{oid}_{status_filter}"):
                conn2 = get_connection()
                cur2 = conn2.cursor()
                cur2.execute("UPDATE orders SET status='Done' WHERE id=?", (oid,))
                conn2.commit()
                cur2.close(); conn2.close()
                st.rerun()
            if show_edit and btn_cols[1].button("✏️ Edit", key=f"edit_{oid}_{status_filter}"):
                st.session_state[f"editing_{oid}"] = not st.session_state.get(f"editing_{oid}", False)
            if btn_cols[2].button("🗑️ Delete", key=f"del_{oid}_{status_filter}"):
                st.session_state[f"confirm_del_{oid}"] = True
        else:
            if show_edit and btn_cols[0].button("✏️ Edit", key=f"edit_{oid}_{status_filter}"):
                st.session_state[f"editing_{oid}"] = not st.session_state.get(f"editing_{oid}", False)
            if btn_cols[1].button("🗑️ Delete", key=f"del_{oid}_{status_filter}"):
                st.session_state[f"confirm_del_{oid}"] = True

        # Delete confirmation
        if st.session_state.get(f"confirm_del_{oid}"):
            st.warning(f"Delete Order #{oid}?")
            yc, nc = st.columns(2)
            if yc.button("Yes, Delete", key=f"yes_del_{oid}", type="primary"):
                conn3 = get_connection()
                cur3 = conn3.cursor()
                cur3.execute("DELETE FROM orders WHERE id=?", (oid,))
                conn3.commit()
                cur3.close(); conn3.close()
                st.session_state.pop(f"confirm_del_{oid}", None)
                st.rerun()
            if nc.button("Cancel", key=f"no_del_{oid}"):
                st.session_state.pop(f"confirm_del_{oid}", None)
                st.rerun()

        # Edit form
        if show_edit and st.session_state.get(f"editing_{oid}"):
            rates = get_rates()
            with st.container():
                st.markdown(f"**Edit Order #{oid}**")
                e1, e2, e3, e4 = st.columns([2, 1, 1, 1])
                with e1:
                    e_name = st.text_input("Customer Name", value=name_v, key=f"ename_{oid}")
                with e2:
                    e_weight = st.text_input("Weight (kg)", value=str(wt_v), key=f"ewt_{oid}")
                with e3:
                    svc_opts = list(rates.keys())
                    e_svc = st.selectbox("Service", svc_opts,
                                         index=svc_opts.index(svc_v) if svc_v in svc_opts else 0,
                                         key=f"esvc_{oid}")
                with e4:
                    e_pickup = st.text_input("Pick-up Date", value=pick_v or "",
                                             placeholder="YYYY-MM-DD", key=f"epick_{oid}")
                if st.button("💾 Save Changes", key=f"save_{oid}"):
                    try:
                        kg = float(e_weight)
                        total = rates.get(e_svc, 50) * kg
                        conn4 = get_connection()
                        cur4 = conn4.cursor()
                        cur4.execute(
                            "UPDATE orders SET name=?,service=?,weight=?,total=?,pickup_date=? WHERE id=?",
                            (e_name, e_svc, kg, total, e_pickup, oid)
                        )
                        conn4.commit()
                        cur4.close(); conn4.close()
                        st.session_state.pop(f"editing_{oid}", None)
                        st.rerun()
                    except ValueError:
                        st.error("Invalid weight.")


# ══════════════════════════════════════════════════════════════════════════════
#  ORDERS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_orders():
    st.markdown("<div style='font-size:26px;font-weight:700;color:#E8EAF6'>Orders</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:13px;color:#8892B0;margin-bottom:20px'>View and manage all laundry orders</div>",
                unsafe_allow_html=True)

    col_search, col_filter = st.columns([2, 3])
    with col_search:
        search = st.text_input("🔍 Search by customer name", placeholder="Search…", key="orders_search")
    with col_filter:
        st.markdown("<br>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        if f1.button("All", use_container_width=True, key="flt_all"):
            st.session_state["orders_filter"] = "All"
        if f2.button("Pending", use_container_width=True, key="flt_pending"):
            st.session_state["orders_filter"] = "Pending"
        if f3.button("Done", use_container_width=True, key="flt_done"):
            st.session_state["orders_filter"] = "Done"

    current_filter = st.session_state.get("orders_filter", "All")
    st.markdown(f"<div style='color:#8892B0;font-size:12px;margin-bottom:12px'>Showing: <b>{current_filter}</b></div>",
                unsafe_allow_html=True)
    _render_orders_table(status_filter=current_filter, search=search, show_edit=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMERS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_customers():
    st.markdown("<div style='font-size:26px;font-weight:700;color:#E8EAF6'>Customers</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:13px;color:#8892B0;margin-bottom:20px'>All unique customers derived from orders</div>",
                unsafe_allow_html=True)

    search = st.text_input("🔍 Search customer", placeholder="Search by name…", key="cust_search")

    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT name, COUNT(*) as orders, COALESCE(SUM(total),0) as spent, MAX(date_created) as last
        FROM orders
    """
    params = []
    if search:
        query += " WHERE name LIKE ?"
        params.append(f"%{search}%")
    query += " GROUP BY name ORDER BY spent DESC"
    cur.execute(query, params)
    data = cur.fetchall()
    cur.close(); conn.close()

    if not data:
        st.markdown("<div style='text-align:center;color:#8892B0;padding:40px'>👥 No customers found</div>",
                    unsafe_allow_html=True)
        return

    for row in data:
        cname, order_cnt, total_spent, last_date = row["name"], row["orders"], row["spent"], row["last"]
        initials = "".join([w[0].upper() for w in cname.split()[:2]])
        st.markdown(f"""
        <div class='order-card' style='display:flex;align-items:center;gap:16px'>
            <div style='width:44px;height:44px;background:#7C3AED;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:14px;flex-shrink:0'>{initials}</div>
            <div style='flex:1'>
                <div style='font-size:14px;font-weight:700;color:#E8EAF6'>{cname}</div>
                <div style='font-size:11px;color:#8892B0'>Last order: {last_date or '—'}</div>
            </div>
            <div style='text-align:center;min-width:80px'>
                <div style='font-size:13px;font-weight:700;color:#4F7EFF'>{order_cnt} order{'s' if order_cnt != 1 else ''}</div>
                <div style='font-size:10px;color:#8892B0'>total orders</div>
            </div>
            <div style='width:1px;height:40px;background:#2E3352'></div>
            <div style='text-align:right;min-width:100px'>
                <div style='font-size:16px;font-weight:700;color:#22C55E'>₱{total_spent:,.2f}</div>
                <div style='font-size:10px;color:#8892B0'>total spent</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  REPORTS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_reports():
    st.markdown("<div style='font-size:26px;font-weight:700;color:#E8EAF6'>Reports</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:13px;color:#8892B0;margin-bottom:20px'>Business analytics and performance overview</div>",
                unsafe_allow_html=True)

    p1, p2, p3, p4 = st.columns(4)
    if p1.button("Today", use_container_width=True):    st.session_state["report_period"] = "today"
    if p2.button("Last 7 Days", use_container_width=True): st.session_state["report_period"] = "week"
    if p3.button("This Month", use_container_width=True): st.session_state["report_period"] = "month"
    if p4.button("All Time", use_container_width=True): st.session_state["report_period"] = "all"

    period = st.session_state.get("report_period", "today")
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    if period == "today":
        date_filter, date_param, label = "date_created = ?", today, "Today"
    elif period == "week":
        week_start = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        date_filter, date_param, label = "date_created >= ?", week_start, "Last 7 Days"
    elif period == "month":
        month_start = datetime.datetime.now().strftime("%Y-%m-01")
        date_filter, date_param, label = "date_created >= ?", month_start, "This Month"
    else:
        date_filter, date_param, label = None, None, "All Time"

    st.markdown(f"<div style='color:#8892B0;font-size:12px;margin:8px 0 20px'>Period: <b>{label}</b></div>",
                unsafe_allow_html=True)

    conn = get_connection()
    cur = conn.cursor()

    if date_param:
        base, p = f"FROM orders WHERE {date_filter}", (date_param,)
    else:
        base, p = "FROM orders", ()

    cur.execute(f"SELECT COUNT(*), COALESCE(SUM(total),0) {base}", p)
    total_orders, total_rev = cur.fetchone()

    # Handle the AND conditions for filtered queries
    if date_param:
        cur.execute(f"SELECT COUNT(*) FROM orders WHERE {date_filter} AND status='Done'", p)
        done_cnt = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM orders WHERE {date_filter} AND status='Pending'", p)
        pend_cnt = cur.fetchone()[0]
        cur.execute(f"SELECT service, COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE {date_filter} GROUP BY service ORDER BY SUM(total) DESC", p)
        by_service = cur.fetchall()
        cur.execute(f"SELECT name, COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE {date_filter} GROUP BY name ORDER BY SUM(total) DESC LIMIT 5", p)
        top_customers = cur.fetchall()
        cur.execute(f"SELECT date_created, COALESCE(SUM(total),0) FROM orders WHERE {date_filter} GROUP BY date_created ORDER BY date_created DESC LIMIT 7", p)
        daily = cur.fetchall()
        cur.execute(f"SELECT name, COALESCE(SUM(total),0) FROM orders WHERE {date_filter} GROUP BY name", p)
        cust_profit_rows = cur.fetchall()
    else:
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='Done'")
        done_cnt = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
        pend_cnt = cur.fetchone()[0]
        cur.execute("SELECT service, COUNT(*), COALESCE(SUM(total),0) FROM orders GROUP BY service ORDER BY SUM(total) DESC")
        by_service = cur.fetchall()
        cur.execute("SELECT name, COUNT(*), COALESCE(SUM(total),0) FROM orders GROUP BY name ORDER BY SUM(total) DESC LIMIT 5")
        top_customers = cur.fetchall()
        cur.execute("SELECT date_created, COALESCE(SUM(total),0) FROM orders GROUP BY date_created ORDER BY date_created DESC LIMIT 7")
        daily = cur.fetchall()
        cur.execute("SELECT name, COALESCE(SUM(total),0) FROM orders GROUP BY name")
        cust_profit_rows = cur.fetchall()

    cur.close(); conn.close()

    # Summary stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Total Orders", total_orders)
    c2.metric("💰 Revenue", f"₱{total_rev:,.2f}")
    c3.metric("✅ Completed", done_cnt)
    c4.metric("⏳ Pending", pend_cnt)

    st.markdown("<br>", unsafe_allow_html=True)

    # Revenue by service
    if by_service:
        st.markdown("<div class='section-header'>Revenue by Service</div>", unsafe_allow_html=True)
        max_rev = max(r[2] for r in by_service) or 1
        for svc, cnt, rev in by_service:
            pct = rev / max_rev if max_rev else 0
            col_a, col_b = st.columns([3, 1])
            col_a.markdown(f"<span style='color:#E8EAF6;font-size:13px'>{svc}</span> "
                           f"<span style='color:#8892B0;font-size:11px'>({cnt} orders)</span>",
                           unsafe_allow_html=True)
            col_b.markdown(f"<div style='text-align:right;color:#22C55E;font-weight:700'>₱{rev:,.2f}</div>",
                           unsafe_allow_html=True)
            st.progress(pct)
        st.markdown("<br>", unsafe_allow_html=True)

    # Top customers
    if top_customers:
        st.markdown("<div class='section-header'>🏆 Top 5 Customers</div>", unsafe_allow_html=True)
        medals = ["🥇", "🥈", "🥉", "#4", "#5"]
        for i, row in enumerate(top_customers):
            cname, cnt, rev = row[0], row[1], row[2]
            st.markdown(f"""
            <div style='background:#22263A;border-radius:10px;padding:12px 16px;
                        display:flex;align-items:center;margin-bottom:8px'>
                <span style='font-size:16px;width:36px'>{medals[i]}</span>
                <span style='flex:1;font-size:13px;font-weight:700;color:#E8EAF6'>{cname}</span>
                <span style='font-size:11px;color:#8892B0;width:80px'>{cnt} orders</span>
                <span style='font-size:13px;font-weight:700;color:#22C55E'>₱{rev:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Profit distribution
    if cust_profit_rows:
        all_revenues = [r[1] for r in cust_profit_rows]
        avg_rev = sum(all_revenues) / len(all_revenues) if all_revenues else 0
        high_customers = [(n, r) for n, r in cust_profit_rows if r >= avg_rev]
        low_customers  = [(n, r) for n, r in cust_profit_rows if r <  avg_rev]
        high_rev = sum(r for _, r in high_customers)
        low_rev  = sum(r for _, r in low_customers)
        total_pie = high_rev + low_rev or 1
        high_pct = high_rev / total_pie
        low_pct  = low_rev  / total_pie

        st.markdown("<div class='section-header'>📊 Profit Distribution by Customer</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#8892B0;font-size:11px;margin-bottom:12px'>Avg spend ₱{avg_rev:,.2f} · customers above = High Profit · {label}</div>",
                    unsafe_allow_html=True)

        col_h, col_l = st.columns(2)
        with col_h:
            st.markdown(f"<div style='color:#22C55E;font-weight:700'>🟢 High Profit ({high_pct*100:.1f}%)</div>"
                        f"<div style='color:#8892B0;font-size:11px'>{len(high_customers)} customers · ₱{high_rev:,.2f}</div>",
                        unsafe_allow_html=True)
            st.progress(high_pct)
        with col_l:
            st.markdown(f"<div style='color:#F59E0B;font-weight:700'>🟡 Low Profit ({low_pct*100:.1f}%)</div>"
                        f"<div style='color:#8892B0;font-size:11px'>{len(low_customers)} customers · ₱{low_rev:,.2f}</div>",
                        unsafe_allow_html=True)
            st.progress(low_pct)
        st.markdown("<br>", unsafe_allow_html=True)

    # Daily revenue
    if daily:
        st.markdown("<div class='section-header'>📅 Daily Revenue (Recent)</div>", unsafe_allow_html=True)
        max_day = max(r[1] for r in daily) or 1
        for d_date, d_rev in daily:
            pct = d_rev / max_day if max_day else 0
            da, db = st.columns([2, 1])
            da.markdown(f"<span style='color:#E8EAF6;font-size:12px'>{d_date or '—'}</span>",
                        unsafe_allow_html=True)
            db.markdown(f"<div style='text-align:right;color:#22C55E;font-weight:700'>₱{d_rev:,.2f}</div>",
                        unsafe_allow_html=True)
            st.progress(pct)


# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS VIEW
# ══════════════════════════════════════════════════════════════════════════════
def render_settings():
    user = st.session_state.username
    role = st.session_state.role
    is_admin = role == "Admin"

    st.markdown("<div style='font-size:26px;font-weight:700;color:#E8EAF6'>Settings</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:13px;color:#8892B0;margin-bottom:20px'>Account, pricing, and system preferences</div>",
                unsafe_allow_html=True)

    # Account info
    with st.container():
        st.markdown("<div class='section-header'>👤 Account Info</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:16px;background:#1A1D27;
                    border:1px solid #2E3352;border-radius:14px;padding:20px;margin-bottom:16px'>
            <div style='width:56px;height:56px;background:#7C3AED;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:20px'>{user[0].upper()}</div>
            <div>
                <div style='font-size:16px;font-weight:700;color:#E8EAF6'>{user}</div>
                <div style='font-size:12px;color:#8892B0'>Role: {role}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Change Password
    with st.container():
        st.markdown("<div class='section-header'>🔒 Change Password</div>", unsafe_allow_html=True)
        old_pw  = st.text_input("Current Password",      type="password", key="set_old_pw")
        new_pw  = st.text_input("New Password",          type="password", key="set_new_pw")
        conf_pw = st.text_input("Confirm New Password",  type="password", key="set_conf_pw")

        if st.button("Update Password", type="primary"):
            if not old_pw or not new_pw or not conf_pw:
                st.error("Please fill all password fields.")
            elif new_pw != conf_pw:
                st.error("New passwords do not match.")
            elif len(new_pw) < 6:
                st.error("New password must be at least 6 characters.")
            else:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT password FROM users WHERE username=?", (user,))
                row = cur.fetchone()
                if not row or row["password"] != hash_password(old_pw):
                    st.error("Current password is incorrect.")
                else:
                    cur.execute("UPDATE users SET password=? WHERE username=?",
                                (hash_password(new_pw), user))
                    conn.commit()
                    st.success("Password changed successfully!")
                cur.close(); conn.close()

    st.markdown("<br>", unsafe_allow_html=True)

    # Service Pricing
    with st.container():
        if is_admin:
            st.markdown("<div class='section-header'>💵 Service Pricing</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='section-header'>💵 Service Pricing &nbsp;<span style='background:#F59E0B22;color:#F59E0B;border:1px solid #F59E0B44;border-radius:20px;padding:2px 10px;font-size:11px'>🔒 Admin only</span></div>",
                        unsafe_allow_html=True)

        rates = get_rates()
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            wash_rate = st.text_input("Wash (per kg ₱)", value=str(rates.get("Wash", 50)),
                                      disabled=not is_admin, key="price_wash")
        with pc2:
            washdry_rate = st.text_input("Wash & Dry (per kg ₱)", value=str(rates.get("Wash & Dry", 75)),
                                         disabled=not is_admin, key="price_washdry")
        with pc3:
            full_rate = st.text_input("Full Service (per kg ₱)", value=str(rates.get("Full Service", 95)),
                                      disabled=not is_admin, key="price_full")

        if is_admin:
            if st.button("💾 Save Pricing", type="primary"):
                try:
                    new_rates = {
                        "Wash": float(wash_rate),
                        "Wash & Dry": float(washdry_rate),
                        "Full Service": float(full_rate),
                    }
                    conn = get_connection()
                    cur = conn.cursor()
                    for svc, rate in new_rates.items():
                        cur.execute("INSERT OR REPLACE INTO pricing (service, rate) VALUES (?, ?)", (svc, rate))
                    conn.commit()
                    cur.close(); conn.close()
                    st.success("Pricing updated! (Applies to new orders)")
                except ValueError:
                    st.error("Please enter valid numbers for all prices.")
        else:
            st.markdown("<div style='font-size:12px;color:#8892B0;font-style:italic'>Contact an Admin to update service pricing.</div>",
                        unsafe_allow_html=True)

    # User Management (Admin only)
    if is_admin:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-header' style='color:#EF4444'>🛡️ User Management</div>",
                    unsafe_allow_html=True)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, role FROM users ORDER BY id")
        users = cur.fetchall()
        cur.close(); conn.close()

        for u in users:
            uid, uname, urole = u["id"], u["username"], u["role"]
            is_self = uname == user
            col_a, col_b = st.columns([4, 1])
            col_a.markdown(f"""
            <div style='background:#22263A;border-radius:10px;padding:10px 14px;
                        display:flex;align-items:center;gap:10px'>
                <div style='width:36px;height:36px;background:{"#4F7EFF" if urole=="Admin" else "#7C3AED"};
                            border-radius:50%;display:flex;align-items:center;justify-content:center;
                            font-weight:700;font-size:12px'>{uname[0].upper()}</div>
                <div>
                    <div style='font-size:13px;font-weight:700;color:#E8EAF6'>{uname}
                        {'&nbsp;<span style="background:#4F7EFF22;color:#4F7EFF;border:1px solid #4F7EFF44;border-radius:20px;padding:2px 8px;font-size:11px">You</span>' if is_self else ''}
                    </div>
                    <div style='font-size:11px;color:#8892B0'>{urole}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not is_self:
                if col_b.button("🗑️ Delete", key=f"del_user_{uid}"):
                    st.session_state[f"confirm_del_user_{uid}"] = True

            if st.session_state.get(f"confirm_del_user_{uid}"):
                st.warning(f"Delete user '{uname}'?")
                y2, n2 = st.columns(2)
                if y2.button("Yes, Delete", key=f"yes_del_user_{uid}", type="primary"):
                    conn2 = get_connection()
                    cur2 = conn2.cursor()
                    cur2.execute("DELETE FROM users WHERE id=?", (uid,))
                    conn2.commit()
                    cur2.close(); conn2.close()
                    st.session_state.pop(f"confirm_del_user_{uid}", None)
                    st.rerun()
                if n2.button("Cancel", key=f"no_del_user_{uid}"):
                    st.session_state.pop(f"confirm_del_user_{uid}", None)
                    st.rerun()


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
    view = st.session_state.view
    if view == "dashboard":
        render_dashboard()
    elif view == "orders":
        render_orders()
    elif view == "customers":
        render_customers()
    elif view == "reports":
        render_reports()
    elif view == "settings":
        render_settings()
