import flet as ft
import mysql.connector
import datetime
import hashlib

# ---------------- DATABASE CONFIG ----------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "2hrze4hr",
    "database": "myLaundry"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            service VARCHAR(100) NOT NULL,
            weight FLOAT NOT NULL,
            total FLOAT NOT NULL,
            status VARCHAR(50) NOT NULL,
            date_created VARCHAR(20),
            pickup_date VARCHAR(20)
        )
    """)
    conn.commit()

    default_admin_hash = hash_password("admin123")
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            ("admin", default_admin_hash, "Admin")
        )
        conn.commit()
    except mysql.connector.IntegrityError:
        pass

    cursor.close()
    conn.close()

def hash_password(password, salt="laundry_secure_123"):
    return hashlib.sha256((password + salt).encode()).hexdigest()

# ─── DESIGN TOKENS ───────────────────────────────────────────────────────────
C_BG       = "#0F1117"
C_SURFACE  = "#1A1D27"
C_SURFACE2 = "#22263A"
C_BORDER   = "#2E3352"
C_ACCENT   = "#4F7EFF"
C_ACCENT2  = "#7C3AED"
C_GREEN    = "#22C55E"
C_ORANGE   = "#F59E0B"
C_RED      = "#EF4444"
C_TEXT     = "#E8EAF6"
C_MUTED    = "#8892B0"
C_WHITE    = "#FFFFFF"


def main(page: ft.Page):
    page.title = "LaundroSoft POS"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = C_BG
    page.window_width = 1300
    page.window_height = 900
    page.padding = 0
    page.window.icon = "D:\\IM_systemProject\\myicon.ico"  # ← add this line

    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.INDIGO,
        color_scheme=ft.ColorScheme(
            primary=C_ACCENT,
            surface=C_SURFACE,
            on_primary=C_WHITE,
            on_surface=C_TEXT,
        )
    )

    session = {"role": None, "user": ""}

    # ── SNACKBAR ──────────────────────────────────────────────────────────────
    def show_msg(msg, is_error=False):
        page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.ERROR_OUTLINE if is_error else ft.Icons.CHECK_CIRCLE_OUTLINE,
                    color=C_WHITE, size=20
                ),
                ft.Text(msg, color=C_WHITE, size=13)
            ], spacing=10),
            bgcolor=C_RED if is_error else C_GREEN,
            duration=3000,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.Margin(left=20, right=20, top=0, bottom=20)
        )
        page.snack_bar.open = True
        page.update()

    # ── LOGOUT ────────────────────────────────────────────────────────────────
    def logout(e):
        def confirm(e):
            dlg.open = False
            page.update()
            session["role"] = None
            session["user"] = ""
            page.controls.clear()
            page.add(build_auth_view())
            page.update()

        def cancel(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=C_SURFACE,
            title=ft.Text("Log out?", color=C_TEXT, weight="bold"),
            content=ft.Text("You will be returned to the login screen.", color=C_MUTED),
            actions=[
                ft.TextButton("Cancel", on_click=cancel, style=ft.ButtonStyle(color=C_MUTED)),
                ft.FilledButton(
                    "Log out",
                    on_click=confirm,
                    style=ft.ButtonStyle(bgcolor=C_RED, color=C_WHITE)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ══════════════════════════════════════════════════════════════════════════
    #  AUTH VIEW
    # ══════════════════════════════════════════════════════════════════════════
    def build_auth_view():
        state = {"is_register": False}

        def field(label, icon, password=False, on_submit=None):
            return ft.TextField(
                label=label,
                label_style=ft.TextStyle(color=C_MUTED, size=13),
                prefix_icon=icon,
                password=password,
                can_reveal_password=password,
                width=360,
                bgcolor=C_SURFACE2,
                border_color=C_BORDER,
                focused_border_color=C_ACCENT,
                color=C_TEXT,
                cursor_color=C_ACCENT,
                on_submit=on_submit,
                border_radius=10,
            )

        headline = ft.Text("Welcome back", size=30, weight="bold", color=C_TEXT)
        subline  = ft.Text("Sign in to LaundroSoft POS", size=14, color=C_MUTED)
        user_in  = field("Username", ft.Icons.PERSON_OUTLINE_ROUNDED)
        pass_in  = field("Password", ft.Icons.LOCK_OUTLINE_ROUNDED, password=True,
                         on_submit=lambda e: handle_auth())

        submit_btn = ft.FilledButton(
            "SIGN IN",
            width=360, height=48,
            on_click=lambda e: handle_auth(),
            style=ft.ButtonStyle(
                bgcolor=C_ACCENT,
                color=C_WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=14, weight="bold", letter_spacing=1.5)
            )
        )
        toggle_btn = ft.TextButton(
            "Don't have an account? Register",
            on_click=lambda e: toggle(),
            style=ft.ButtonStyle(color=C_ACCENT)
        )

        def show_error(msg):
            def close(e):
                d.open = False
                page.update()
            d = ft.AlertDialog(
                bgcolor=C_SURFACE,
                title=ft.Text("Error", color=C_RED, weight="bold"),
                content=ft.Text(msg, color=C_MUTED),
                actions=[ft.TextButton("OK", on_click=close, style=ft.ButtonStyle(color=C_ACCENT))]
            )
            page.overlay.append(d)
            d.open = True
            page.update()

        def toggle():
            state["is_register"] = not state["is_register"]
            r = state["is_register"]
            headline.value = "Create account" if r else "Welcome back"
            subline.value  = "Join LaundroSoft POS" if r else "Sign in to LaundroSoft POS"
            submit_btn.text = "REGISTER" if r else "SIGN IN"
            toggle_btn.text = "Already have an account? Sign in" if r else "Don't have an account? Register"
            user_in.value = pass_in.value = ""
            page.update()

        def handle_auth():
            u = user_in.value.strip()
            p = pass_in.value
            if not u or not p:
                show_error("Please fill in all fields.")
                return
            hp = hash_password(p)
            try:
                conn = get_connection()
                cur  = conn.cursor()
                if state["is_register"]:
                    try:
                        cur.execute("INSERT INTO users (username,password,role) VALUES (%s,%s,%s)",
                                    (u, hp, "Staff"))
                        conn.commit()
                        show_msg("Account created! You can now sign in.")
                        toggle()
                    except mysql.connector.IntegrityError:
                        show_error("Username already exists.")
                else:
                    cur.execute("SELECT password,role FROM users WHERE username=%s", (u,))
                    res = cur.fetchone()
                    if res and res[0] == hp:
                        session["role"] = res[1]
                        session["user"] = u
                        cur.close(); conn.close()
                        load_dashboard()
                        return
                    elif res:
                        show_error("Incorrect password.")
                    else:
                        show_error("Username not found.")
                cur.close(); conn.close()
            except mysql.connector.Error as err:
                show_error(f"Database error: {err}")

        left_panel = ft.Container(
            width=420, expand=False,
            bgcolor=C_SURFACE,
            padding=ft.Padding(left=50, right=50, top=60, bottom=60),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                controls=[
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                width=44, height=44, border_radius=12, bgcolor=C_ACCENT,
                                content=ft.Icon(ft.Icons.LOCAL_LAUNDRY_SERVICE_ROUNDED, color=C_WHITE, size=24),
                                alignment=ft.Alignment(0, 0)
                            ),
                            ft.Column([
                                ft.Text("LaundroSoft", size=16, weight="bold", color=C_TEXT),
                                ft.Text("Point of Sale", size=11, color=C_MUTED),
                            ], spacing=0, tight=True)
                        ], spacing=12),
                        margin=ft.Margin(left=0, right=0, top=0, bottom=40)
                    ),
                    ft.Container(headline, margin=ft.Margin(left=0, right=0, top=0, bottom=4)),
                    ft.Container(subline,  margin=ft.Margin(left=0, right=0, top=0, bottom=32)),
                    ft.Container(user_in,  margin=ft.Margin(left=0, right=0, top=0, bottom=14)),
                    ft.Container(pass_in,  margin=ft.Margin(left=0, right=0, top=0, bottom=14)),
                    ft.Container(submit_btn, margin=ft.Margin(left=0, right=0, top=0, bottom=16)),
                    toggle_btn,
                ]
            )
        )

        right_panel = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=["#1a2340", "#0F1117", "#1a1040"]
            ),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    ft.Icon(ft.Icons.LOCAL_LAUNDRY_SERVICE_ROUNDED, size=80, color=C_ACCENT, opacity=0.3),
                    ft.Text("LaundroSoft POS", size=36, weight="bold", color=C_TEXT, opacity=0.15),
                    ft.Text("Manage your laundry\nbusiness with ease.",
                            size=22, color=C_TEXT, opacity=0.3,
                            text_align=ft.TextAlign.CENTER),
                ]
            )
        )

        return ft.Row([left_panel, right_panel], expand=True, spacing=0)

    # ══════════════════════════════════════════════════════════════════════════
    #  SHARED HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def badge(text, color):
        return ft.Container(
            content=ft.Text(text, size=11, weight="bold", color=color),
            padding=ft.Padding(left=10, right=10, top=4, bottom=4),
            border_radius=20,
            bgcolor=color + "22",
            border=ft.Border(left=ft.BorderSide(1, color + "44"), top=ft.BorderSide(1, color + "44"), right=ft.BorderSide(1, color + "44"), bottom=ft.BorderSide(1, color + "44")),
        )

    def icon_btn(ico, color, tooltip, on_click):
        return ft.IconButton(
            icon=ico, icon_color=color, tooltip=tooltip, icon_size=18,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.HOVERED: color + "22"},
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=on_click
        )

    def section_header(title, accent=C_ACCENT):
        return ft.Row([
            ft.Container(width=6, height=22, bgcolor=accent, border_radius=3),
            ft.Text(title, size=16, weight="bold", color=C_TEXT),
        ], spacing=10)

    def styled_field(label, icon, hint="", expand=1):
        return ft.TextField(
            label=label, hint_text=hint,
            label_style=ft.TextStyle(color=C_MUTED, size=12),
            prefix_icon=icon,
            bgcolor=C_SURFACE2,
            border_color=C_BORDER,
            focused_border_color=C_ACCENT,
            color=C_TEXT,
            cursor_color=C_ACCENT,
            border_radius=10,
            expand=expand,
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def load_dashboard():
        page.controls.clear()
        active_view = {"name": "dashboard"}

        stat_orders  = ft.Text("0",     size=34, weight="bold", color=C_TEXT)
        stat_pending = ft.Text("0",     size=34, weight="bold", color=C_ORANGE)
        stat_done    = ft.Text("0",     size=34, weight="bold", color=C_GREEN)
        stat_income  = ft.Text("₱0.00", size=34, weight="bold", color=C_ACCENT)

        content_area = ft.Column(expand=True, scroll=ft.ScrollMode.ADAPTIVE, spacing=0)

        nav_items = {}

        def nav_item(key, ico, label):
            is_active = active_view["name"] == key
            c = ft.Container(
                key=key,
                padding=ft.Padding(left=12, right=12, top=10, bottom=10),
                border_radius=10,
                bgcolor=C_ACCENT + "22" if is_active else "transparent",
                border=ft.Border(left=ft.BorderSide(1, C_ACCENT + "44"), top=ft.BorderSide(1, C_ACCENT + "44"), right=ft.BorderSide(1, C_ACCENT + "44"), bottom=ft.BorderSide(1, C_ACCENT + "44")) if is_active else ft.Border(left=ft.BorderSide(0, "transparent"), top=ft.BorderSide(0, "transparent"), right=ft.BorderSide(0, "transparent"), bottom=ft.BorderSide(0, "transparent")),
                content=ft.Row([
                    ft.Icon(ico, color=C_ACCENT if is_active else C_MUTED, size=18),
                    ft.Text(label, color=C_ACCENT if is_active else C_MUTED,
                            size=13, weight="bold" if is_active else "normal"),
                ], spacing=10),
                on_click=lambda e, k=key: switch_view(k),
                ink=True,
            )
            nav_items[key] = c
            return c

        def update_nav(active_key):
            configs = {
                "dashboard":  (ft.Icons.DASHBOARD_OUTLINED,      "Dashboard"),
                "orders":     (ft.Icons.RECEIPT_LONG_OUTLINED,    "Orders"),
                "customers":  (ft.Icons.PEOPLE_OUTLINE_ROUNDED,   "Customers"),
                "reports":    (ft.Icons.BAR_CHART_OUTLINED,       "Reports"),
                "settings":   (ft.Icons.SETTINGS_OUTLINED,        "Settings"),
            }
            for key, container in nav_items.items():
                is_active = key == active_key
                ico, lbl = configs[key]
                container.bgcolor = C_ACCENT + "22" if is_active else "transparent"
                container.border  = ft.Border(left=ft.BorderSide(1, C_ACCENT + "44"), top=ft.BorderSide(1, C_ACCENT + "44"), right=ft.BorderSide(1, C_ACCENT + "44"), bottom=ft.BorderSide(1, C_ACCENT + "44")) if is_active else ft.Border(left=ft.BorderSide(0, "transparent"), top=ft.BorderSide(0, "transparent"), right=ft.BorderSide(0, "transparent"), bottom=ft.BorderSide(0, "transparent"))
                container.content.controls[0].color = C_ACCENT if is_active else C_MUTED
                container.content.controls[1].color = C_ACCENT if is_active else C_MUTED
                container.content.controls[1].weight = "bold" if is_active else "normal"

        # ─────────────────────────────────────────────────────────────────────
        #  VIEW: DASHBOARD
        # ─────────────────────────────────────────────────────────────────────
        def stat_card(label, value_widget, icon, accent):
            return ft.Container(
                expand=1, padding=22,
                bgcolor=C_SURFACE, border_radius=16,
                border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                content=ft.Row([
                    ft.Container(
                        width=48, height=48, border_radius=12,
                        bgcolor=accent + "22",
                        content=ft.Icon(icon, color=accent, size=22),
                        alignment=ft.Alignment(0, 0)
                    ),
                    ft.Column([
                        ft.Text(label, size=12, color=C_MUTED),
                        value_widget,
                    ], spacing=2, tight=True)
                ], spacing=16)
            )

        name_in   = styled_field("Customer Name", ft.Icons.PERSON_OUTLINE_ROUNDED, "e.g. Juan dela Cruz")
        weight_in = styled_field("Weight (kg)",   ft.Icons.SCALE_OUTLINED,         "e.g. 3.5")

        service_in = ft.Dropdown(
            label="Service", label_style=ft.TextStyle(color=C_MUTED, size=12),
            bgcolor=C_SURFACE2, border_color=C_BORDER,
            focused_border_color=C_ACCENT, color=C_TEXT,
            border_radius=10, expand=1,
            options=[
                ft.dropdown.Option("Wash"),
                ft.dropdown.Option("Wash & Dry"),
                ft.dropdown.Option("Full Service"),
            ],
            value="Wash",
        )

        def on_date_change(e):
            if date_picker.value:
                pickup_display.value = date_picker.value.strftime("%Y-%m-%d")
                pickup_display.update()
            date_picker.open = False
            page.update()

        date_picker = ft.DatePicker(on_change=on_date_change, first_date=datetime.datetime.now())
        page.overlay.append(date_picker)

        pickup_display = ft.TextField(
            label="Pick-up Date (Optional)",
            label_style=ft.TextStyle(color=C_MUTED, size=12),
            prefix_icon=ft.Icons.CALENDAR_TODAY_OUTLINED,
            read_only=True, expand=1,
            bgcolor=C_SURFACE2, border_color=C_BORDER,
            focused_border_color=C_ACCENT, color=C_TEXT,
            border_radius=10,
            suffix=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH_OUTLINED, icon_color=C_ACCENT,
                on_click=lambda _: setattr(date_picker, "open", True) or page.update(),
            )
        )

        dash_table = ft.Column()

        # ── NOTIFICATION SYSTEM ───────────────────────────────────────────────
        PROFIT_LOW_THRESHOLD = 1000.0   # ₱ — adjust as needed
        notif_badge = ft.Text("0", size=9, color=C_WHITE, weight="bold")
        notif_badge_container = ft.Container(
            content=notif_badge,
            bgcolor=C_RED,
            border_radius=10,
            padding=ft.Padding(left=5, right=5, top=1, bottom=1),
            visible=False,
            offset=ft.Offset(-0.3, -0.7),
        )

        def get_notifications():
            """Return list of (icon, color, title, body) notification tuples."""
            notes = []
            try:
                conn = get_connection()
                cur  = conn.cursor()

                # 1) Low-profit check
                cur.execute("SELECT SUM(total) FROM orders WHERE status='Done'")
                earned = cur.fetchone()[0] or 0.0
                if earned < PROFIT_LOW_THRESHOLD:
                    notes.append((
                        ft.Icons.TRENDING_DOWN_ROUNDED,
                        C_RED,
                        "Low Revenue Alert",
                        f"Total completed revenue is ₱{earned:,.2f} — below the ₱{PROFIT_LOW_THRESHOLD:,.2f} threshold.",
                    ))

                # 2) Today's pick-up schedules
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                cur.execute(
                    "SELECT id, name, service FROM orders WHERE pickup_date=%s AND status='Pending'",
                    (today,)
                )
                pickups = cur.fetchall()
                for oid, cname, svc in pickups:
                    notes.append((
                        ft.Icons.LOCAL_SHIPPING_OUTLINED,
                        C_ORANGE,
                        "Pick-up Today",
                        f"Order #{oid} — {cname} ({svc}) is scheduled for pick-up today.",
                    ))

                cur.close(); conn.close()
            except mysql.connector.Error:
                pass
            return notes

        def show_notifications(e):
            notes = get_notifications()

            if not notes:
                items = [ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=C_GREEN, size=20),
                    ft.Text("No notifications right now. All good!", color=C_MUTED, size=13),
                ], spacing=10)]
            else:
                items = []
                for ico, col, title, body in notes:
                    items.append(
                        ft.Container(
                            padding=ft.Padding(left=14, right=14, top=12, bottom=12),
                            bgcolor=col + "11",
                            border_radius=10,
                            border=ft.Border(left=ft.BorderSide(1, col + "33"), top=ft.BorderSide(1, col + "33"), right=ft.BorderSide(1, col + "33"), bottom=ft.BorderSide(1, col + "33")),
                            content=ft.Row([
                                ft.Container(
                                    width=36, height=36, border_radius=8,
                                    bgcolor=col + "22",
                                    content=ft.Icon(ico, color=col, size=18),
                                    alignment=ft.Alignment(0, 0)
                                ),
                                ft.Column([
                                    ft.Text(title, size=13, color=C_TEXT, weight="bold"),
                                    ft.Text(body,  size=12, color=C_MUTED),
                                ], spacing=3, tight=True, expand=True)
                            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START)
                        )
                    )

            def close_dlg(e):
                dlg.open = False
                page.update()

            dlg = ft.AlertDialog(
                modal=False,
                bgcolor=C_SURFACE,
                title=ft.Row([
                    ft.Icon(ft.Icons.NOTIFICATIONS_OUTLINED, color=C_ACCENT, size=22),
                    ft.Text("Notifications", color=C_TEXT, weight="bold", size=17, expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE_ROUNDED, icon_color=C_MUTED, icon_size=18,
                        on_click=close_dlg,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                ], spacing=10),
                content=ft.Container(
                    width=420,
                    content=ft.Column(items, spacing=10, scroll=ft.ScrollMode.ADAPTIVE),
                ),
                actions=[
                    ft.TextButton(
                        "Close", on_click=close_dlg,
                        style=ft.ButtonStyle(color=C_MUTED)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        def update_notif_badge():
            notes = get_notifications()
            count = len(notes)
            notif_badge.value = str(count)
            notif_badge_container.visible = count > 0
            notif_badge_container.bgcolor = C_RED if any(
                "Low Revenue" in n[2] for n in notes
            ) else C_ORANGE

        notif_bell_btn = ft.Stack([
            ft.IconButton(
                icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                icon_color=C_MUTED,
                icon_size=22,
                tooltip="Notifications",
                on_click=show_notifications,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.HOVERED: C_ACCENT + "22"},
                    shape=ft.RoundedRectangleBorder(radius=10),
                )
            ),
            notif_badge_container,
        ])
        # ─────────────────────────────────────────────────────────────────────

        def refresh_dash():
            try:
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute("SELECT COUNT(*), SUM(total) FROM orders")
                cnt, inc = cur.fetchone()
                cur.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
                pend = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM orders WHERE status='Done'")
                done = cur.fetchone()[0]
                stat_orders.value  = str(cnt  or 0)
                stat_pending.value = str(pend or 0)
                stat_done.value    = str(done or 0)
                stat_income.value  = f"₱{inc or 0:,.2f}"

                cur.execute("SELECT id,name,service,weight,total,status,date_created,pickup_date FROM orders ORDER BY id DESC")
                cards = []
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                for row in cur.fetchall():
                    oid, name_v, svc_v, wt_v, tot_v, stat_v, date_v, pick_v = row
                    is_done      = stat_v == "Done"
                    pickup_str   = pick_v if pick_v else "—"
                    pickup_color = C_RED if pick_v == today and not is_done else C_MUTED
                    status_color = C_GREEN if is_done else C_ORANGE
                    status_label = "Done" if is_done else "Pending"

                    action_btns = ft.Row([
                        icon_btn(ft.Icons.TASK_ALT_ROUNDED, C_GREEN, "Mark as Done",
                                 lambda e, _id=oid: mark_done(_id)) if not is_done else ft.Container(width=36),
                        icon_btn(ft.Icons.DELETE_OUTLINE_ROUNDED, C_RED, "Delete",
                                 lambda e, _id=oid: delete_order(_id)),
                    ], spacing=2, tight=True)

                    top_row = ft.Row([
                        ft.Text(f"#{oid}", size=11, color=C_MUTED, weight="bold"),
                        ft.Text(name_v, size=14, color=C_TEXT, weight="bold", expand=True),
                        badge(status_label, status_color),
                        action_btns,
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

                    def chip(ico, val, col=C_MUTED):
                        return ft.Row([
                            ft.Icon(ico, size=13, color=col),
                            ft.Text(val, size=12, color=col),
                        ], spacing=4, tight=True)

                    bottom_row = ft.Row([
                        chip(ft.Icons.CALENDAR_TODAY_OUTLINED,  date_v or "—"),
                        ft.Container(width=1, height=14, bgcolor=C_BORDER),
                        chip(ft.Icons.LOCAL_SHIPPING_OUTLINED,  pickup_str, pickup_color),
                        ft.Container(width=1, height=14, bgcolor=C_BORDER),
                        chip(ft.Icons.SCALE_OUTLINED,           f"{wt_v} kg"),
                        ft.Container(width=1, height=14, bgcolor=C_BORDER),
                        chip(ft.Icons.DRY_CLEANING_OUTLINED,    svc_v, C_ACCENT),
                        ft.Container(expand=True),
                        ft.Text(f"₱{tot_v:,.2f}", size=14, color=C_GREEN, weight="bold"),
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

                    cards.append(
                        ft.Container(
                            padding=ft.Padding(left=16, right=12, top=14, bottom=14),
                            bgcolor=C_SURFACE2 if len(cards) % 2 == 0 else C_SURFACE,
                            border=ft.Border(bottom=ft.BorderSide(1, C_BORDER)),
                            content=ft.Column([top_row, bottom_row], spacing=8),
                        )
                    )

                dash_table.controls.clear()
                if not cards:
                    dash_table.controls.append(
                        ft.Container(
                            padding=40, alignment=ft.Alignment(0, 0),
                            content=ft.Column([
                                ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=C_MUTED, opacity=0.4),
                                ft.Text("No orders yet", color=C_MUTED, size=14),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                        )
                    )
                else:
                    hdr_style = ft.TextStyle(color=C_MUTED, size=10, weight="bold", letter_spacing=1.2)
                    header = ft.Container(
                        padding=ft.Padding(left=16, right=16, top=10, bottom=10),
                        bgcolor=C_SURFACE2,
                        content=ft.Row([
                            ft.Text("ID",       style=hdr_style, width=36),
                            ft.Text("CUSTOMER", style=hdr_style, expand=True),
                            ft.Text("STATUS",   style=hdr_style, width=72),
                            ft.Text("ACTIONS",  style=hdr_style, width=80),
                        ], spacing=10),
                    )
                    dash_table.controls.append(
                        ft.Container(
                            bgcolor=C_SURFACE, border_radius=16,
                            border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            content=ft.Column([header, *cards], spacing=0),
                        )
                    )
                cur.close(); conn.close()
                update_notif_badge()
                page.update()
            except mysql.connector.Error as err:
                show_msg(f"DB error: {err}", True)

        def add_order(e):
            if not name_in.value or not weight_in.value:
                show_msg("Please enter Customer Name and Weight.", True)
                return
            try:
                kg    = float(weight_in.value)
                rates = {"Wash": 50, "Wash & Dry": 75, "Full Service": 95}
                total = rates.get(service_in.value, 50) * kg
                pu    = pickup_display.value if pickup_display.value else ""
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute(
                    "INSERT INTO orders (name,service,weight,total,status,date_created,pickup_date) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (name_in.value, service_in.value, kg, total,
                     "Pending", datetime.datetime.now().strftime("%Y-%m-%d"), pu)
                )
                conn.commit()
                cur.close(); conn.close()
                name_in.value = weight_in.value = pickup_display.value = ""
                refresh_dash()
                show_msg("Order created successfully!")
            except ValueError:
                show_msg("Invalid weight. Please enter a number.", True)
            except mysql.connector.Error as err:
                show_msg(f"DB error: {err}", True)

        def mark_done(oid):
            try:
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute("UPDATE orders SET status='Done' WHERE id=%s", (oid,))
                conn.commit()
                cur.close(); conn.close()
                refresh_dash()
            except mysql.connector.Error as err:
                show_msg(f"DB error: {err}", True)

        def delete_order(oid):
            def confirm(e):
                dlg.open = False
                page.update()
                try:
                    conn = get_connection()
                    cur  = conn.cursor()
                    cur.execute("DELETE FROM orders WHERE id=%s", (oid,))
                    conn.commit()
                    cur.close(); conn.close()
                    refresh_dash()
                    show_msg("Order deleted.")
                except mysql.connector.Error as err:
                    show_msg(f"DB error: {err}", True)

            def cancel(e):
                dlg.open = False
                page.update()

            dlg = ft.AlertDialog(
                modal=True, bgcolor=C_SURFACE,
                title=ft.Text("Delete Order?", color=C_TEXT, weight="bold"),
                content=ft.Text(f"Order #{oid} will be permanently deleted.", color=C_MUTED),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel, style=ft.ButtonStyle(color=C_MUTED)),
                    ft.FilledButton("Delete", on_click=confirm, style=ft.ButtonStyle(bgcolor=C_RED, color=C_WHITE)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        def build_dashboard_view():
            return ft.Column(
                spacing=24,
                controls=[
                    ft.Row([
                        ft.Column([
                            ft.Text("Dashboard", size=26, weight="bold", color=C_TEXT),
                            ft.Text(datetime.datetime.now().strftime("%d %B %Y"), size=13, color=C_MUTED),
                        ], spacing=2),
                        notif_bell_btn,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    ft.Row([
                        stat_card("Total Orders",  stat_orders,  ft.Icons.RECEIPT_LONG_OUTLINED,    C_ACCENT),
                        stat_card("Pending",        stat_pending, ft.Icons.HOURGLASS_TOP_ROUNDED,    C_ORANGE),
                        stat_card("Completed",      stat_done,    ft.Icons.TASK_ALT_ROUNDED,         C_GREEN),
                        stat_card("Total Revenue",  stat_income,  ft.Icons.MONETIZATION_ON_OUTLINED, C_ACCENT),
                    ], spacing=16),

                    ft.Container(
                        padding=24, bgcolor=C_SURFACE, border_radius=16,
                        border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                        content=ft.Column([
                            section_header("New Transaction"),
                            ft.Container(height=4),
                            ft.Row([name_in, weight_in, service_in, pickup_display], spacing=14),
                            ft.Container(height=4),
                            ft.Row([
                                ft.FilledButton(
                                    "CREATE ORDER",
                                    icon=ft.Icons.ADD_SHOPPING_CART_OUTLINED,
                                    on_click=add_order, height=44,
                                    style=ft.ButtonStyle(
                                        bgcolor=C_ACCENT, color=C_WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        text_style=ft.TextStyle(size=13, weight="bold", letter_spacing=1)
                                    )
                                )
                            ])
                        ], spacing=14)
                    ),

                    ft.Row([
                        section_header("Orders", C_ACCENT2),
                        ft.FilledButton(
                            "Refresh", icon=ft.Icons.REFRESH_ROUNDED,
                            on_click=lambda e: refresh_dash(), height=36,
                            style=ft.ButtonStyle(
                                bgcolor=C_SURFACE2, color=C_MUTED,
                                shape=ft.RoundedRectangleBorder(radius=8),
                            )
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    dash_table,
                ]
            )

        # ─────────────────────────────────────────────────────────────────────
        #  VIEW: ORDERS
        # ─────────────────────────────────────────────────────────────────────
        def build_orders_view():
            filter_state = {"status": "All", "search": ""}
            orders_table = ft.Column()

            search_field = ft.TextField(
                hint_text="Search by customer name…",
                prefix_icon=ft.Icons.SEARCH_ROUNDED,
                bgcolor=C_SURFACE2, border_color=C_BORDER,
                focused_border_color=C_ACCENT, color=C_TEXT,
                cursor_color=C_ACCENT, border_radius=10,
                width=280,
                on_change=lambda e: (filter_state.update({"search": e.control.value}), load_orders_table()),
            )

            filter_btns_row = ft.Row(spacing=8)

            def set_filter(f):
                filter_state["status"] = f
                for btn in filter_btns_row.controls:
                    is_sel = btn.data == f
                    btn.style = ft.ButtonStyle(
                        bgcolor=C_ACCENT if is_sel else C_SURFACE2,
                        color=C_WHITE if is_sel else C_MUTED,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    )
                load_orders_table()
                filter_btns_row.update()

            for label in ["All", "Pending", "Done"]:
                btn = ft.FilledButton(
                    label, height=36, data=label,
                    on_click=lambda e, l=label: set_filter(l),
                    style=ft.ButtonStyle(
                        bgcolor=C_ACCENT if label == "All" else C_SURFACE2,
                        color=C_WHITE if label == "All" else C_MUTED,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    )
                )
                filter_btns_row.controls.append(btn)

            def load_orders_table():
                try:
                    conn = get_connection()
                    cur  = conn.cursor()
                    query = "SELECT id,name,service,weight,total,status,date_created,pickup_date FROM orders"
                    conditions = []
                    params = []
                    if filter_state["status"] != "All":
                        conditions.append("status=%s")
                        params.append(filter_state["status"])
                    if filter_state["search"]:
                        conditions.append("name LIKE %s")
                        params.append(f"%{filter_state['search']}%")
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                    query += " ORDER BY id DESC"
                    cur.execute(query, params)

                    cards = []
                    today = datetime.datetime.now().strftime("%Y-%m-%d")
                    for row in cur.fetchall():
                        oid, name_v, svc_v, wt_v, tot_v, stat_v, date_v, pick_v = row
                        is_done      = stat_v == "Done"
                        pickup_str   = pick_v if pick_v else "—"
                        pickup_color = C_RED if pick_v == today and not is_done else C_MUTED
                        status_color = C_GREEN if is_done else C_ORANGE
                        status_label = "Done" if is_done else "Pending"

                        action_btns = ft.Row([
                            icon_btn(ft.Icons.TASK_ALT_ROUNDED, C_GREEN, "Mark as Done",
                                     lambda e, _id=oid: _mark_done_orders(_id)) if not is_done else ft.Container(width=36),
                            icon_btn(ft.Icons.EDIT_OUTLINED, C_ACCENT, "Edit",
                                     lambda e, _id=oid, _n=name_v, _s=svc_v, _w=wt_v, _p=pick_v:
                                         edit_order_dialog(_id, _n, _s, _w, _p)),
                            icon_btn(ft.Icons.DELETE_OUTLINE_ROUNDED, C_RED, "Delete",
                                     lambda e, _id=oid: _delete_order_orders(_id)),
                        ], spacing=2, tight=True)

                        # ── top row: ID · customer · status badge · actions ──
                        top_row = ft.Row([
                            ft.Text(f"#{oid}", size=11, color=C_MUTED, weight="bold"),
                            ft.Text(name_v, size=14, color=C_TEXT, weight="bold", expand=True),
                            badge(status_label, status_color),
                            action_btns,
                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

                        # ── bottom row: meta chips ──────────────────────────
                        def chip(ico, val, col=C_MUTED):
                            return ft.Row([
                                ft.Icon(ico, size=13, color=col),
                                ft.Text(val, size=12, color=col),
                            ], spacing=4, tight=True)

                        bottom_row = ft.Row([
                            chip(ft.Icons.CALENDAR_TODAY_OUTLINED,    date_v or "—"),
                            ft.Container(width=1, height=14, bgcolor=C_BORDER),
                            chip(ft.Icons.LOCAL_SHIPPING_OUTLINED,    pickup_str, pickup_color),
                            ft.Container(width=1, height=14, bgcolor=C_BORDER),
                            chip(ft.Icons.SCALE_OUTLINED,             f"{wt_v} kg"),
                            ft.Container(width=1, height=14, bgcolor=C_BORDER),
                            chip(ft.Icons.DRY_CLEANING_OUTLINED,      svc_v, C_ACCENT),
                            ft.Container(expand=True),
                            ft.Text(f"₱{tot_v:,.2f}", size=14, color=C_GREEN, weight="bold"),
                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

                        cards.append(
                            ft.Container(
                                padding=ft.Padding(left=16, right=12, top=14, bottom=14),
                                bgcolor=C_SURFACE2 if len(cards) % 2 == 0 else C_SURFACE,
                                border=ft.Border(
                                    bottom=ft.BorderSide(1, C_BORDER)
                                ),
                                content=ft.Column([top_row, bottom_row], spacing=8),
                            )
                        )

                    orders_table.controls.clear()
                    if not cards:
                        orders_table.controls.append(
                            ft.Container(
                                padding=40, alignment=ft.Alignment(0, 0),
                                content=ft.Column([
                                    ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=C_MUTED, opacity=0.4),
                                    ft.Text("No orders found", color=C_MUTED, size=14),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                            )
                        )
                    else:
                        # Header bar
                        hdr_style = ft.TextStyle(color=C_MUTED, size=10, weight="bold",
                                                  letter_spacing=1.2)
                        header = ft.Container(
                            padding=ft.Padding(left=16, right=16, top=10, bottom=10),
                            bgcolor=C_SURFACE2,
                            content=ft.Row([
                                ft.Text("ORDER",    style=hdr_style, expand=False, width=36),
                                ft.Text("CUSTOMER", style=hdr_style, expand=True),
                                ft.Text("STATUS",   style=hdr_style, width=72),
                                ft.Text("ACTIONS",  style=hdr_style, width=108),
                            ], spacing=10),
                        )
                        orders_table.controls.append(
                            ft.Container(
                                bgcolor=C_SURFACE, border_radius=16,
                                border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                content=ft.Column([header, *cards], spacing=0),
                            )
                        )
                    cur.close(); conn.close()
                    page.update()
                except mysql.connector.Error as err:
                    show_msg(f"DB error: {err}", True)

            def _mark_done_orders(oid):
                try:
                    conn = get_connection()
                    cur  = conn.cursor()
                    cur.execute("UPDATE orders SET status='Done' WHERE id=%s", (oid,))
                    conn.commit()
                    cur.close(); conn.close()
                    load_orders_table()
                    show_msg("Order marked as Done.")
                except mysql.connector.Error as err:
                    show_msg(f"DB error: {err}", True)

            def _delete_order_orders(oid):
                def confirm(e):
                    dlg.open = False
                    page.update()
                    try:
                        conn = get_connection()
                        cur  = conn.cursor()
                        cur.execute("DELETE FROM orders WHERE id=%s", (oid,))
                        conn.commit()
                        cur.close(); conn.close()
                        load_orders_table()
                        show_msg("Order deleted.")
                    except mysql.connector.Error as err:
                        show_msg(f"DB error: {err}", True)
                def cancel(e):
                    dlg.open = False; page.update()
                dlg = ft.AlertDialog(
                    modal=True, bgcolor=C_SURFACE,
                    title=ft.Text("Delete Order?", color=C_TEXT, weight="bold"),
                    content=ft.Text(f"Order #{oid} will be permanently deleted.", color=C_MUTED),
                    actions=[
                        ft.TextButton("Cancel", on_click=cancel, style=ft.ButtonStyle(color=C_MUTED)),
                        ft.FilledButton("Delete", on_click=confirm, style=ft.ButtonStyle(bgcolor=C_RED, color=C_WHITE)),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()

            def edit_order_dialog(oid, cur_name, cur_svc, cur_wt, cur_pickup):
                e_name   = ft.TextField(label="Customer Name", value=cur_name,
                                        bgcolor=C_SURFACE2, border_color=C_BORDER,
                                        focused_border_color=C_ACCENT, color=C_TEXT,
                                        border_radius=10, width=300)
                e_weight = ft.TextField(label="Weight (kg)", value=str(cur_wt),
                                        bgcolor=C_SURFACE2, border_color=C_BORDER,
                                        focused_border_color=C_ACCENT, color=C_TEXT,
                                        border_radius=10, width=140)
                e_svc = ft.Dropdown(
                    label="Service", value=cur_svc,
                    bgcolor=C_SURFACE2, border_color=C_BORDER,
                    focused_border_color=C_ACCENT, color=C_TEXT,
                    border_radius=10, width=180,
                    options=[ft.dropdown.Option("Wash"), ft.dropdown.Option("Wash & Dry"), ft.dropdown.Option("Full Service")],
                )
                e_pickup = ft.TextField(label="Pick-up Date", value=cur_pickup or "",
                                        bgcolor=C_SURFACE2, border_color=C_BORDER,
                                        focused_border_color=C_ACCENT, color=C_TEXT,
                                        border_radius=10, width=160,
                                        hint_text="YYYY-MM-DD")

                def save(ev):
                    try:
                        kg    = float(e_weight.value)
                        rates = {"Wash": 50, "Wash & Dry": 75, "Full Service": 95}
                        total = rates.get(e_svc.value, 50) * kg
                        conn  = get_connection()
                        cur   = conn.cursor()
                        cur.execute(
                            "UPDATE orders SET name=%s, service=%s, weight=%s, total=%s, pickup_date=%s WHERE id=%s",
                            (e_name.value, e_svc.value, kg, total, e_pickup.value, oid)
                        )
                        conn.commit()
                        cur.close(); conn.close()
                        dlg.open = False
                        page.update()
                        load_orders_table()
                        show_msg("Order updated.")
                    except ValueError:
                        show_msg("Invalid weight.", True)
                    except mysql.connector.Error as err:
                        show_msg(f"DB error: {err}", True)

                def cancel(ev):
                    dlg.open = False; page.update()

                dlg = ft.AlertDialog(
                    modal=True, bgcolor=C_SURFACE,
                    title=ft.Text(f"Edit Order #{oid}", color=C_TEXT, weight="bold"),
                    content=ft.Column([
                        e_name,
                        ft.Row([e_weight, e_svc, e_pickup], spacing=10),
                    ], spacing=14, tight=True),
                    actions=[
                        ft.TextButton("Cancel", on_click=cancel, style=ft.ButtonStyle(color=C_MUTED)),
                        ft.FilledButton("Save", on_click=save, style=ft.ButtonStyle(bgcolor=C_ACCENT, color=C_WHITE)),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()

            load_orders_table()

            return ft.Column(spacing=24, controls=[
                ft.Row([
                    ft.Column([
                        ft.Text("Orders", size=26, weight="bold", color=C_TEXT),
                        ft.Text("View and manage all laundry orders", size=13, color=C_MUTED),
                    ], spacing=2),
                    ft.Row([search_field], spacing=10),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([filter_btns_row], spacing=10),
                orders_table,
            ])

        # ─────────────────────────────────────────────────────────────────────
        #  VIEW: CUSTOMERS
        # ─────────────────────────────────────────────────────────────────────
        def build_customers_view():
            cust_list = ft.Column(spacing=12)
            search_val = {"v": ""}

            search_field = ft.TextField(
                hint_text="Search customer name…",
                prefix_icon=ft.Icons.SEARCH_ROUNDED,
                bgcolor=C_SURFACE2, border_color=C_BORDER,
                focused_border_color=C_ACCENT, color=C_TEXT,
                cursor_color=C_ACCENT, border_radius=10, width=280,
                on_change=lambda e: (search_val.update({"v": e.control.value}), load_customers()),
            )

            def load_customers():
                try:
                    conn = get_connection()
                    cur  = conn.cursor()
                    query = """
                        SELECT name, COUNT(*) as orders, SUM(total) as spent, MAX(date_created) as last
                        FROM orders
                    """
                    params = []
                    if search_val["v"]:
                        query += " WHERE name LIKE %s"
                        params.append(f"%{search_val['v']}%")
                    query += " GROUP BY name ORDER BY spent DESC"
                    cur.execute(query, params)
                    data = cur.fetchall()
                    cur.close(); conn.close()

                    cust_list.controls.clear()
                    if not data:
                        cust_list.controls.append(
                            ft.Container(
                                padding=40, alignment=ft.Alignment(0, 0),
                                content=ft.Column([
                                    ft.Icon(ft.Icons.PEOPLE_OUTLINE_ROUNDED, size=48, color=C_MUTED, opacity=0.4),
                                    ft.Text("No customers found", color=C_MUTED, size=14),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                            )
                        )
                    else:
                        for cname, order_cnt, total_spent, last_date in data:
                            initials = "".join([w[0].upper() for w in cname.split()[:2]])
                            cust_list.controls.append(
                                ft.Container(
                                    bgcolor=C_SURFACE, border_radius=14,
                                    border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                                    padding=ft.Padding(left=20, right=20, top=16, bottom=16),
                                    content=ft.Row([
                                        ft.CircleAvatar(
                                            content=ft.Text(initials, color=C_WHITE, size=14, weight="bold"),
                                            bgcolor=C_ACCENT2, radius=22
                                        ),
                                        ft.Column([
                                            ft.Text(cname, size=14, weight="bold", color=C_TEXT),
                                            ft.Text(f"Last order: {last_date or '—'}", size=11, color=C_MUTED),
                                        ], spacing=2, tight=True, expand=True),
                                        ft.Column([
                                            ft.Text(f"{order_cnt} order{'s' if order_cnt != 1 else ''}",
                                                    size=12, color=C_ACCENT, weight="bold"),
                                            ft.Text("total orders", size=10, color=C_MUTED),
                                        ], spacing=2, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                        ft.Container(width=1, height=40, bgcolor=C_BORDER),
                                        ft.Column([
                                            ft.Text(f"₱{total_spent:,.2f}",
                                                    size=16, color=C_GREEN, weight="bold"),
                                            ft.Text("total spent", size=10, color=C_MUTED),
                                        ], spacing=2, tight=True, horizontal_alignment=ft.CrossAxisAlignment.END),
                                    ], spacing=16)
                                )
                            )
                    page.update()
                except mysql.connector.Error as err:
                    show_msg(f"DB error: {err}", True)

            load_customers()

            return ft.Column(spacing=24, controls=[
                ft.Row([
                    ft.Column([
                        ft.Text("Customers", size=26, weight="bold", color=C_TEXT),
                        ft.Text("All unique customers derived from orders", size=13, color=C_MUTED),
                    ], spacing=2),
                    search_field,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                cust_list,
            ])

        # ─────────────────────────────────────────────────────────────────────
        #  VIEW: REPORTS
        # ─────────────────────────────────────────────────────────────────────
        def build_reports_view():
            report_content = ft.Column(spacing=16)
            period_state = {"v": "today"}

            def load_report():
                try:
                    conn = get_connection()
                    cur  = conn.cursor()
                    today = datetime.datetime.now().strftime("%Y-%m-%d")
                    period = period_state["v"]

                    if period == "today":
                        date_filter = "date_created = %s"
                        date_param  = today
                        label = "Today"
                    elif period == "week":
                        week_start = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                        date_filter = "date_created >= %s"
                        date_param  = week_start
                        label = "Last 7 Days"
                    elif period == "month":
                        month_start = datetime.datetime.now().strftime("%Y-%m-01")
                        date_filter = "date_created >= %s"
                        date_param  = month_start
                        label = "This Month"
                    else:
                        date_filter = "1=1"
                        date_param  = None
                        label = "All Time"

                    base = f"FROM orders WHERE {date_filter}" if date_param else "FROM orders"
                    p    = (date_param,) if date_param else ()

                    cur.execute(f"SELECT COUNT(*), COALESCE(SUM(total),0) {base}", p)
                    total_orders, total_rev = cur.fetchone()

                    cur.execute(f"SELECT COUNT(*) {base} AND status='Done'", p)
                    done_cnt = cur.fetchone()[0]

                    cur.execute(f"SELECT COUNT(*) {base} AND status='Pending'", p)
                    pend_cnt = cur.fetchone()[0]

                    cur.execute(f"SELECT service, COUNT(*), COALESCE(SUM(total),0) {base} GROUP BY service ORDER BY SUM(total) DESC", p)
                    by_service = cur.fetchall()

                    cur.execute(f"SELECT name, COUNT(*), COALESCE(SUM(total),0) {base} GROUP BY name ORDER BY SUM(total) DESC LIMIT 5", p)
                    top_customers = cur.fetchall()

                    cur.execute(f"SELECT date_created, COALESCE(SUM(total),0) {base} GROUP BY date_created ORDER BY date_created DESC LIMIT 7", p)
                    daily = cur.fetchall()

                    cur.close(); conn.close()

                    report_content.controls.clear()

                    def mini_stat(label, value, color, icon):
                        return ft.Container(
                            expand=1, padding=20, bgcolor=C_SURFACE, border_radius=14,
                            border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(
                                        width=36, height=36, border_radius=10,
                                        bgcolor=color + "22",
                                        content=ft.Icon(icon, color=color, size=18),
                                        alignment=ft.Alignment(0, 0)
                                    ),
                                    ft.Text(label, size=11, color=C_MUTED),
                                ], spacing=10),
                                ft.Text(value, size=26, weight="bold", color=color),
                            ], spacing=6)
                        )

                    report_content.controls.append(
                        ft.Row([
                            mini_stat("Total Orders",  str(total_orders),       C_TEXT,   ft.Icons.RECEIPT_LONG_OUTLINED),
                            mini_stat("Revenue",       f"₱{total_rev:,.2f}",    C_GREEN,  ft.Icons.MONETIZATION_ON_OUTLINED),
                            mini_stat("Completed",     str(done_cnt),           C_ACCENT, ft.Icons.TASK_ALT_ROUNDED),
                            mini_stat("Pending",       str(pend_cnt),           C_ORANGE, ft.Icons.HOURGLASS_TOP_ROUNDED),
                        ], spacing=14)
                    )

                    if by_service:
                        max_rev = max(r for _, _, r in by_service) or 1
                        svc_items = []
                        for svc, cnt, rev in by_service:
                            pct = rev / max_rev if max_rev else 0
                            svc_items.append(ft.Column([
                                ft.Row([
                                    ft.Text(svc, size=13, color=C_TEXT, expand=True),
                                    ft.Text(f"{cnt} orders", size=11, color=C_MUTED, width=70),
                                    ft.Text(f"₱{rev:,.2f}", size=13, color=C_GREEN, weight="bold", width=100),
                                ], spacing=8),
                                ft.ProgressBar(value=pct, bgcolor=C_SURFACE2, color=C_ACCENT, height=8,
                                               border_radius=4),
                            ], spacing=6))

                        report_content.controls.append(
                            ft.Container(
                                padding=22, bgcolor=C_SURFACE, border_radius=14,
                                border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                                content=ft.Column([
                                    section_header("Revenue by Service"),
                                    ft.Container(height=4),
                                    *svc_items,
                                ], spacing=12)
                            )
                        )

                    if top_customers:
                        cust_rows = []
                        for i, (cname, cnt, rev) in enumerate(top_customers):
                            medal = ["🥇", "🥈", "🥉"]
                            rank_text = medal[i] if i < 3 else f"#{i+1}"
                            cust_rows.append(
                                ft.Container(
                                    padding=ft.Padding(left=16, right=16, top=12, bottom=12),
                                    bgcolor=C_SURFACE2, border_radius=10,
                                    content=ft.Row([
                                        ft.Text(rank_text, size=16, width=36),
                                        ft.Text(cname, size=13, color=C_TEXT, weight="bold", expand=True),
                                        ft.Text(f"{cnt} orders", size=11, color=C_MUTED, width=80),
                                        ft.Text(f"₱{rev:,.2f}", size=13, color=C_GREEN, weight="bold"),
                                    ], spacing=10)
                                )
                            )
                        report_content.controls.append(
                            ft.Container(
                                padding=22, bgcolor=C_SURFACE, border_radius=14,
                                border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                                content=ft.Column([
                                    section_header("Top 5 Customers", C_ACCENT2),
                                    ft.Container(height=4),
                                    *cust_rows,
                                ], spacing=8)
                            )
                        )

                    # ── PROFIT DISTRIBUTION CHART ────────────────────────────────────────
                    # Fetch per-customer revenue for the selected period
                    conn2 = get_connection()
                    cur2  = conn2.cursor()
                    if date_param:
                        cur2.execute(
                            f"SELECT name, COALESCE(SUM(total),0) FROM orders "
                            f"WHERE {date_filter} GROUP BY name",
                            (date_param,)
                        )
                    else:
                        cur2.execute(
                            "SELECT name, COALESCE(SUM(total),0) FROM orders GROUP BY name"
                        )
                    cust_profit_rows = cur2.fetchall()
                    cur2.close(); conn2.close()

                    if cust_profit_rows:
                        all_revenues   = [r for _, r in cust_profit_rows]
                        avg_rev        = sum(all_revenues) / len(all_revenues) if all_revenues else 0

                        high_customers = [(n, r) for n, r in cust_profit_rows if r >= avg_rev]
                        low_customers  = [(n, r) for n, r in cust_profit_rows if r <  avg_rev]
                        high_rev       = sum(r for _, r in high_customers)
                        low_rev        = sum(r for _, r in low_customers)
                        total_pie_rev  = high_rev + low_rev or 1

                        high_pct = high_rev / total_pie_rev
                        low_pct  = low_rev  / total_pie_rev

                        BAR_W = 420   # total width of the stacked bar

                        def _legend_dot(color):
                            return ft.Container(
                                width=12, height=12, border_radius=6, bgcolor=color
                            )

                        def _legend_row(lbl, count, revenue, pct, color):
                            return ft.Row([
                                _legend_dot(color),
                                ft.Column([
                                    ft.Text(lbl, size=13, color=C_TEXT, weight="bold"),
                                    ft.Text(
                                        f"{count} customer{'s' if count != 1 else ''} · ₱{revenue:,.2f}",
                                        size=11, color=C_MUTED,
                                    ),
                                ], spacing=1, tight=True, expand=True),
                                ft.Text(f"{pct*100:.1f}%", size=15, weight="bold", color=color),
                            ], spacing=10)

                        # ── stacked horizontal bar ──────────────────────────────────────
                        high_w = max(int(BAR_W * high_pct), 4 if high_pct > 0 else 0)
                        low_w  = max(int(BAR_W * low_pct),  4 if low_pct  > 0 else 0)

                        stacked_bar = ft.Row(
                            spacing=0,
                            controls=[
                                ft.Container(
                                    width=high_w, height=28,
                                    bgcolor=C_GREEN,
                                    border_radius=ft.BorderRadius(
                                        top_left=8, bottom_left=8,
                                        top_right=0, bottom_right=0
                                    ) if low_w > 0 else ft.BorderRadius(top_left=8, top_right=8, bottom_left=8, bottom_right=8),
                                    tooltip=f"High Profit {high_pct*100:.1f}%",
                                ),
                                ft.Container(
                                    width=low_w, height=28,
                                    bgcolor=C_ORANGE,
                                    border_radius=ft.BorderRadius(
                                        top_left=0, bottom_left=0,
                                        top_right=8, bottom_right=8
                                    ) if high_w > 0 else ft.BorderRadius(top_left=8, top_right=8, bottom_left=8, bottom_right=8),
                                    tooltip=f"Low Profit {low_pct*100:.1f}%",
                                ),
                            ]
                        )

                        # ── per-customer mini bars ──────────────────────────────────────
                        def _cust_bar(name, rev, color, max_r):
                            bar_pct = rev / max_r if max_r else 0
                            return ft.Column([
                                ft.Row([
                                    ft.Container(
                                        width=8, height=8, border_radius=4, bgcolor=color
                                    ),
                                    ft.Text(name, size=11, color=C_TEXT, expand=True),
                                    ft.Text(f"₱{rev:,.0f}", size=11, color=color, weight="bold"),
                                ], spacing=6),
                                ft.Container(
                                    height=6, border_radius=3,
                                    bgcolor=C_SURFACE2,
                                    content=ft.Row(
                                        spacing=0,
                                        controls=[
                                            ft.Container(
                                                width=max(int(220 * bar_pct), 4),
                                                height=6, bgcolor=color,
                                                border_radius=3,
                                            )
                                        ]
                                    )
                                ),
                            ], spacing=3)

                        max_all = max(all_revenues) or 1

                        high_bars = ft.Column(
                            spacing=8,
                            controls=[_cust_bar(n, r, C_GREEN, max_all)
                                      for n, r in sorted(high_customers, key=lambda x: -x[1])[:5]]
                        )
                        low_bars = ft.Column(
                            spacing=8,
                            controls=[_cust_bar(n, r, C_ORANGE, max_all)
                                      for n, r in sorted(low_customers, key=lambda x: -x[1])[:5]]
                        )

                        report_content.controls.append(
                            ft.Container(
                                padding=22, bgcolor=C_SURFACE, border_radius=14,
                                border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                                content=ft.Column([
                                    section_header("Profit Distribution by Customer", C_GREEN),
                                    ft.Text(
                                        f"Avg spend ₱{avg_rev:,.2f} · customers above = High Profit · {label}",
                                        size=11, color=C_MUTED, italic=True,
                                    ),
                                    ft.Container(height=10),

                                    # ── stacked bar visual ──
                                    stacked_bar,
                                    ft.Row([
                                        ft.Text(f"High {high_pct*100:.0f}%", size=10,
                                                color=C_GREEN, weight="bold"),
                                        ft.Container(expand=True),
                                        ft.Text(f"Low {low_pct*100:.0f}%", size=10,
                                                color=C_ORANGE, weight="bold"),
                                    ]),

                                    ft.Container(height=10),

                                    # ── legend summary row ──
                                    _legend_row("High Profit", len(high_customers),
                                                high_rev, high_pct, C_GREEN),
                                    ft.Container(height=4),
                                    _legend_row("Low Profit",  len(low_customers),
                                                low_rev,  low_pct,  C_ORANGE),

                                    ft.Container(height=14),

                                    # ── detailed breakdown side by side ──
                                    ft.Row([
                                        ft.Container(
                                            expand=True,
                                            padding=ft.Padding(left=14, right=14, top=12, bottom=12),
                                            bgcolor=C_SURFACE2, border_radius=10,
                                            content=ft.Column([
                                                ft.Row([
                                                    ft.Container(
                                                        width=8, height=8,
                                                        border_radius=4, bgcolor=C_GREEN
                                                    ),
                                                    ft.Text("High Profit Customers",
                                                            size=11, color=C_GREEN, weight="bold"),
                                                ], spacing=6),
                                                ft.Container(height=6),
                                                high_bars if high_customers else
                                                    ft.Text("None", size=11, color=C_MUTED),
                                            ], spacing=0)
                                        ),
                                        ft.Container(width=12),
                                        ft.Container(
                                            expand=True,
                                            padding=ft.Padding(left=14, right=14, top=12, bottom=12),
                                            bgcolor=C_SURFACE2, border_radius=10,
                                            content=ft.Column([
                                                ft.Row([
                                                    ft.Container(
                                                        width=8, height=8,
                                                        border_radius=4, bgcolor=C_ORANGE
                                                    ),
                                                    ft.Text("Low Profit Customers",
                                                            size=11, color=C_ORANGE, weight="bold"),
                                                ], spacing=6),
                                                ft.Container(height=6),
                                                low_bars if low_customers else
                                                    ft.Text("None", size=11, color=C_MUTED),
                                            ], spacing=0)
                                        ),
                                    ], spacing=0),

                                ], spacing=6)
                            )
                        )

                    if daily:
                        day_items = []
                        max_day = max(r for _, r in daily) or 1
                        for d_date, d_rev in daily:
                            pct = d_rev / max_day if max_day else 0
                            day_items.append(ft.Column([
                                ft.Row([
                                    ft.Text(d_date or "—", size=12, color=C_TEXT, expand=True),
                                    ft.Text(f"₱{d_rev:,.2f}", size=13, color=C_GREEN, weight="bold"),
                                ], spacing=8),
                                ft.ProgressBar(value=pct, bgcolor=C_SURFACE2, color=C_ACCENT2, height=6,
                                               border_radius=3),
                            ], spacing=4))

                        report_content.controls.append(
                            ft.Container(
                                padding=22, bgcolor=C_SURFACE, border_radius=14,
                                border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                                content=ft.Column([
                                    section_header("Daily Revenue (Recent)", C_GREEN),
                                    ft.Container(height=4),
                                    *day_items,
                                ], spacing=10)
                            )
                        )

                    if not total_orders:
                        report_content.controls.append(
                            ft.Container(
                                padding=40,
                                content=ft.Column([
                                    ft.Icon(ft.Icons.BAR_CHART_OUTLINED, size=48, color=C_MUTED, opacity=0.4),
                                    ft.Text("No data for this period", color=C_MUTED, size=14),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                            )
                        )

                    page.update()
                except mysql.connector.Error as err:
                    show_msg(f"DB error: {err}", True)

            period_btns = ft.Row(spacing=8)

            def set_period(p):
                period_state["v"] = p
                for btn in period_btns.controls:
                    is_sel = btn.data == p
                    btn.style = ft.ButtonStyle(
                        bgcolor=C_ACCENT if is_sel else C_SURFACE2,
                        color=C_WHITE if is_sel else C_MUTED,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    )
                load_report()
                period_btns.update()

            for label, key in [("Today", "today"), ("Last 7 Days", "week"), ("This Month", "month"), ("All Time", "all")]:
                btn = ft.FilledButton(
                    label, height=36, data=key,
                    on_click=lambda e, k=key: set_period(k),
                    style=ft.ButtonStyle(
                        bgcolor=C_ACCENT if key == "today" else C_SURFACE2,
                        color=C_WHITE if key == "today" else C_MUTED,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    )
                )
                period_btns.controls.append(btn)

            load_report()

            return ft.Column(spacing=24, controls=[
                ft.Row([
                    ft.Column([
                        ft.Text("Reports", size=26, weight="bold", color=C_TEXT),
                        ft.Text("Business analytics and performance overview", size=13, color=C_MUTED),
                    ], spacing=2),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                period_btns,
                report_content,
            ])

        # ─────────────────────────────────────────────────────────────────────
        #  VIEW: SETTINGS
        # ─────────────────────────────────────────────────────────────────────
        def build_settings_view():
            is_admin = session["role"] == "Admin"

            old_pw  = ft.TextField(label="Current Password", password=True, can_reveal_password=True,
                                   bgcolor=C_SURFACE2, border_color=C_BORDER,
                                   focused_border_color=C_ACCENT, color=C_TEXT,
                                   border_radius=10, width=320)
            new_pw  = ft.TextField(label="New Password", password=True, can_reveal_password=True,
                                   bgcolor=C_SURFACE2, border_color=C_BORDER,
                                   focused_border_color=C_ACCENT, color=C_TEXT,
                                   border_radius=10, width=320)
            conf_pw = ft.TextField(label="Confirm New Password", password=True, can_reveal_password=True,
                                   bgcolor=C_SURFACE2, border_color=C_BORDER,
                                   focused_border_color=C_ACCENT, color=C_TEXT,
                                   border_radius=10, width=320)

            def change_password(e):
                if not old_pw.value or not new_pw.value or not conf_pw.value:
                    show_msg("Please fill all password fields.", True); return
                if new_pw.value != conf_pw.value:
                    show_msg("New passwords do not match.", True); return
                if len(new_pw.value) < 6:
                    show_msg("New password must be at least 6 characters.", True); return
                try:
                    conn = get_connection()
                    cur  = conn.cursor()
                    cur.execute("SELECT password FROM users WHERE username=%s", (session["user"],))
                    res = cur.fetchone()
                    if not res or res[0] != hash_password(old_pw.value):
                        show_msg("Current password is incorrect.", True)
                        cur.close(); conn.close(); return
                    cur.execute("UPDATE users SET password=%s WHERE username=%s",
                                (hash_password(new_pw.value), session["user"]))
                    conn.commit()
                    cur.close(); conn.close()
                    old_pw.value = new_pw.value = conf_pw.value = ""
                    page.update()
                    show_msg("Password changed successfully!")
                except mysql.connector.Error as err:
                    show_msg(f"DB error: {err}", True)

            users_list = ft.Column(spacing=10)

            def load_users():
                if not is_admin:
                    return
                try:
                    conn = get_connection()
                    cur  = conn.cursor()
                    cur.execute("SELECT id, username, role FROM users ORDER BY id")
                    data = cur.fetchall()
                    cur.close(); conn.close()
                    users_list.controls.clear()
                    for uid, uname, urole in data:
                        is_self = uname == session["user"]
                        users_list.controls.append(
                            ft.Container(
                                bgcolor=C_SURFACE2, border_radius=10,
                                padding=ft.Padding(left=16, right=16, top=12, bottom=12),
                                content=ft.Row([
                                    ft.CircleAvatar(
                                        content=ft.Text(uname[0].upper(), color=C_WHITE, size=12, weight="bold"),
                                        bgcolor=C_ACCENT if urole == "Admin" else C_ACCENT2, radius=18
                                    ),
                                    ft.Column([
                                        ft.Text(uname, size=13, color=C_TEXT, weight="bold"),
                                        ft.Text(urole, size=11, color=C_MUTED),
                                    ], spacing=1, tight=True, expand=True),
                                    badge("You", C_ACCENT) if is_self else ft.Container(),
                                    ft.Container() if is_self else icon_btn(
                                        ft.Icons.DELETE_OUTLINE_ROUNDED, C_RED, "Delete user",
                                        lambda e, _id=uid, _n=uname: delete_user(_id, _n)
                                    ),
                                ], spacing=12)
                            )
                        )
                    page.update()
                except mysql.connector.Error as err:
                    show_msg(f"DB error: {err}", True)

            def delete_user(uid, uname):
                def confirm(e):
                    dlg.open = False; page.update()
                    try:
                        conn = get_connection()
                        cur  = conn.cursor()
                        cur.execute("DELETE FROM users WHERE id=%s", (uid,))
                        conn.commit()
                        cur.close(); conn.close()
                        load_users()
                        show_msg(f"User '{uname}' deleted.")
                    except mysql.connector.Error as err:
                        show_msg(f"DB error: {err}", True)
                def cancel(e):
                    dlg.open = False; page.update()
                dlg = ft.AlertDialog(
                    modal=True, bgcolor=C_SURFACE,
                    title=ft.Text("Delete User?", color=C_TEXT, weight="bold"),
                    content=ft.Text(f"User '{uname}' will be permanently removed.", color=C_MUTED),
                    actions=[
                        ft.TextButton("Cancel", on_click=cancel, style=ft.ButtonStyle(color=C_MUTED)),
                        ft.FilledButton("Delete", on_click=confirm, style=ft.ButtonStyle(bgcolor=C_RED, color=C_WHITE)),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.overlay.append(dlg)
                dlg.open = True; page.update()

            price_wash    = ft.TextField(
                label="Wash (per kg ₱)", value="50",
                bgcolor=C_SURFACE2, border_color=C_BORDER,
                focused_border_color=C_ACCENT if is_admin else C_BORDER,
                color=C_TEXT if is_admin else C_MUTED,
                border_radius=10, width=160,
                read_only=not is_admin,
            )
            price_washdry = ft.TextField(
                label="Wash & Dry (per kg ₱)", value="75",
                bgcolor=C_SURFACE2, border_color=C_BORDER,
                focused_border_color=C_ACCENT if is_admin else C_BORDER,
                color=C_TEXT if is_admin else C_MUTED,
                border_radius=10, width=200,
                read_only=not is_admin,
            )
            price_full    = ft.TextField(
                label="Full Service (per kg ₱)", value="95",
                bgcolor=C_SURFACE2, border_color=C_BORDER,
                focused_border_color=C_ACCENT if is_admin else C_BORDER,
                color=C_TEXT if is_admin else C_MUTED,
                border_radius=10, width=200,
                read_only=not is_admin,
            )
            pricing_note  = ft.Text("", size=12, color=C_GREEN)

            def save_pricing(e):
                if not is_admin:
                    show_msg("Only Admins can update pricing.", True)
                    return
                try:
                    float(price_wash.value)
                    float(price_washdry.value)
                    float(price_full.value)
                    pricing_note.value = "✓ Pricing saved (applies to new orders)"
                    pricing_note.update()
                    show_msg("Pricing updated!")
                except ValueError:
                    show_msg("Please enter valid numbers for all prices.", True)

            load_users()

            if is_admin:
                pricing_controls = [
                    section_header("Service Pricing", C_GREEN),
                    ft.Container(height=4),
                    ft.Row([price_wash, price_washdry, price_full], spacing=14),
                    ft.Row([
                        ft.FilledButton(
                            "Save Pricing", icon=ft.Icons.SAVE_OUTLINED,
                            on_click=save_pricing, height=44,
                            style=ft.ButtonStyle(
                                bgcolor=C_GREEN, color=C_WHITE,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            )
                        ),
                        pricing_note,
                    ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ]
            else:
                pricing_controls = [
                    ft.Row([
                        section_header("Service Pricing", C_GREEN),
                        ft.Container(
                            padding=ft.Padding(left=10, right=10, top=4, bottom=4),
                            border_radius=20,
                            bgcolor=C_ORANGE + "22",
                            border=ft.Border(left=ft.BorderSide(1, C_ORANGE + "44"), top=ft.BorderSide(1, C_ORANGE + "44"), right=ft.BorderSide(1, C_ORANGE + "44"), bottom=ft.BorderSide(1, C_ORANGE + "44")),
                            content=ft.Row([
                                ft.Icon(ft.Icons.LOCK_OUTLINE_ROUNDED, color=C_ORANGE, size=13),
                                ft.Text("Admin only", size=11, color=C_ORANGE, weight="bold"),
                            ], spacing=5),
                        ),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=4),
                    ft.Row([price_wash, price_washdry, price_full], spacing=14),
                    ft.Text(
                        "Contact an Admin to update service pricing.",
                        size=12, color=C_MUTED, italic=True,
                    ),
                ]

            sections = [
                ft.Container(
                    padding=24, bgcolor=C_SURFACE, border_radius=14,
                    border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                    content=ft.Column([
                        section_header("Account Info"),
                        ft.Container(height=4),
                        ft.Row([
                            ft.CircleAvatar(
                                content=ft.Text(
                                    session["user"][0].upper() if session["user"] else "U",
                                    color=C_WHITE, size=20, weight="bold"
                                ),
                                bgcolor=C_ACCENT2, radius=28
                            ),
                            ft.Column([
                                ft.Text(session["user"], size=16, color=C_TEXT, weight="bold"),
                                ft.Text(f"Role: {session['role']}", size=12, color=C_MUTED),
                            ], spacing=3, tight=True)
                        ], spacing=16)
                    ], spacing=14)
                ),

                ft.Container(
                    padding=24, bgcolor=C_SURFACE, border_radius=14,
                    border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                    content=ft.Column([
                        section_header("Change Password"),
                        ft.Container(height=4),
                        ft.Row([old_pw], spacing=14),
                        ft.Row([new_pw, conf_pw], spacing=14),
                        ft.FilledButton(
                            "Update Password", icon=ft.Icons.LOCK_RESET_OUTLINED,
                            on_click=change_password, height=44,
                            style=ft.ButtonStyle(
                                bgcolor=C_ACCENT, color=C_WHITE,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            )
                        )
                    ], spacing=14)
                ),

                ft.Container(
                    padding=24, bgcolor=C_SURFACE, border_radius=14,
                    border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                    content=ft.Column(pricing_controls, spacing=14)
                ),
            ]

            if is_admin:
                sections.append(
                    ft.Container(
                        padding=24, bgcolor=C_SURFACE, border_radius=14,
                        border=ft.Border(left=ft.BorderSide(1, C_BORDER), top=ft.BorderSide(1, C_BORDER), right=ft.BorderSide(1, C_BORDER), bottom=ft.BorderSide(1, C_BORDER)),
                        content=ft.Column([
                            ft.Row([
                                section_header("User Management", C_RED),
                                ft.FilledButton(
                                    "Refresh", icon=ft.Icons.REFRESH_ROUNDED,
                                    on_click=lambda e: load_users(), height=36,
                                    style=ft.ButtonStyle(
                                        bgcolor=C_SURFACE2, color=C_MUTED,
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    )
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(height=4),
                            users_list,
                        ], spacing=14)
                    )
                )

            return ft.Column(spacing=24, controls=[
                ft.Row([
                    ft.Column([
                        ft.Text("Settings", size=26, weight="bold", color=C_TEXT),
                        ft.Text("Account, pricing, and system preferences", size=13, color=C_MUTED),
                    ], spacing=2),
                ]),
                *sections,
            ])

        # ─────────────────────────────────────────────────────────────────────
        #  VIEW SWITCHER
        # ─────────────────────────────────────────────────────────────────────
        def switch_view(view_name):
            active_view["name"] = view_name
            update_nav(view_name)
            content_area.controls.clear()

            builders = {
                "dashboard": build_dashboard_view,
                "orders":    build_orders_view,
                "customers": build_customers_view,
                "reports":   build_reports_view,
                "settings":  build_settings_view,
            }
            view = builders.get(view_name, build_dashboard_view)()
            content_area.controls.append(
                ft.Container(
                    expand=True,
                    padding=ft.Padding(left=28, right=28, top=28, bottom=28),
                    content=view,
                )
            )
            if view_name == "dashboard":
                refresh_dash()
            page.update()

        # ── SIDEBAR ──────────────────────────────────────────────────────────
        sidebar = ft.Container(
            width=220,
            bgcolor=C_SURFACE,
            border=ft.Border(right=ft.BorderSide(1, C_BORDER)),
            padding=ft.Padding(left=18, right=18, top=30, bottom=30),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Row([
                        ft.Container(
                            width=38, height=38, border_radius=10, bgcolor=C_ACCENT,
                            content=ft.Icon(ft.Icons.LOCAL_LAUNDRY_SERVICE_ROUNDED, color=C_WHITE, size=20),
                            alignment=ft.Alignment(0, 0)
                        ),
                        ft.Column([
                            ft.Text("LaundroSoft", size=14, weight="bold", color=C_TEXT),
                            ft.Text("POS System",  size=10, color=C_MUTED),
                        ], spacing=0, tight=True)
                    ], spacing=10),
                    ft.Container(height=32),
                    ft.Divider(color=C_BORDER, height=1),
                    ft.Container(height=20),
                    ft.Text("MENU", size=10, color=C_MUTED, weight="bold",
                            style=ft.TextStyle(letter_spacing=2)),
                    ft.Container(height=8),
                    nav_item("dashboard", ft.Icons.DASHBOARD_OUTLINED,      "Dashboard"),
                    ft.Container(height=4),
                    nav_item("orders",    ft.Icons.RECEIPT_LONG_OUTLINED,    "Orders"),
                    ft.Container(height=4),
                    nav_item("customers", ft.Icons.PEOPLE_OUTLINE_ROUNDED,   "Customers"),
                    ft.Container(height=4),
                    nav_item("reports",   ft.Icons.BAR_CHART_OUTLINED,       "Reports"),
                    ft.Container(height=4),
                    nav_item("settings",  ft.Icons.SETTINGS_OUTLINED,        "Settings"),
                    ft.Container(expand=True),
                    ft.Divider(color=C_BORDER, height=1),
                    ft.Container(height=16),
                    ft.Container(
                        padding=ft.Padding(left=12, right=12, top=10, bottom=10),
                        border_radius=10, bgcolor=C_SURFACE2,
                        content=ft.Row([
                            ft.CircleAvatar(
                                content=ft.Text(
                                    session["user"][0].upper() if session["user"] else "U",
                                    color=C_WHITE, size=13, weight="bold"
                                ),
                                bgcolor=C_ACCENT2, radius=16
                            ),
                            ft.Column([
                                ft.Text(session["user"], size=12, color=C_TEXT, weight="bold"),
                                ft.Text(session["role"],  size=10, color=C_MUTED),
                            ], spacing=0, tight=True, expand=True),
                            ft.IconButton(
                                ft.Icons.LOGOUT_ROUNDED, icon_color=C_MUTED,
                                icon_size=16, tooltip="Log out", on_click=logout
                            )
                        ], spacing=8)
                    )
                ]
            )
        )

        main_content = ft.Container(
            expand=True, bgcolor=C_BG,
            content=ft.Column(
                expand=True, spacing=0,
                controls=[content_area]
            )
        )

        page.add(ft.Row([sidebar, main_content], expand=True, spacing=0))
        switch_view("dashboard")

    init_db()
    page.add(build_auth_view())


if __name__ == "__main__":
    ft.app(main, assets_dir="assets")
