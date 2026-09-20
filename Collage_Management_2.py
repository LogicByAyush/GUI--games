from tkinter import *
import sqlite3
from datetime import datetime

# ═══════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════

LIGHT = {
    "bg": "#EFF6FB", "card": "#FFFFFF",
    "header": "#1565C0", "hfg": "#FFFFFF",
    "accent": "#1976D2", "afg": "#FFFFFF",
    "text": "#1A1A1A", "sub": "#666666",
    "ok": "#388E3C", "err": "#C62828",
    "nav": "#1565C0", "nav_fg": "#FFFFFF",
    "entry": "#FFFFFF", "border": "#BBDEFB",
    "soft": "#E3F2FD", "soft_fg": "#1565C0",
}

DARK = {
    "bg": "#111827", "card": "#1F2937",
    "header": "#0B1120", "hfg": "#FFFFFF",
    "accent": "#3B82F6", "afg": "#FFFFFF",
    "text": "#F3F4F6", "sub": "#9CA3AF",
    "ok": "#4ADE80", "err": "#F87171",
    "nav": "#0B1120", "nav_fg": "#F3F4F6",
    "entry": "#374151", "border": "#374151",
    "soft": "#1F2937", "soft_fg": "#93C5FD",
}

AVATAR_COLS = ["#1565C0","#00695C","#4527A0",
               "#AD1457","#E65100","#2E7D32","#0277BD"]

FIXED_BG = {LIGHT["header"], DARK["header"],
            "#1A237E", "#388E3C", "#E65100",
            "#6A1B9A", "#C63030", "#1976D2","#3B82F6"}


def avatar_color(key):
    return AVATAR_COLS[sum(ord(c) for c in str(key)) % len(AVATAR_COLS)]


def get_greeting():
    h = datetime.now().hour
    if   5 <= h < 12: return "Good Morning \U0001f305"
    elif 12 <= h < 17: return "Good Afternoon \u2600\ufe0f"
    elif 17 <= h < 21: return "Good Evening \U0001f306"
    else:              return "Good Night \U0001f319"


# ═══════════════════════════════════════════
#  ROOT & DATABASE
# ═══════════════════════════════════════════

root = Tk()
root.geometry("320x400")
root.title("College Management System")
root.configure(bg="#EFF6FB")
root.resizable(False, False)

conn = sqlite3.connect("college.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    admission_id TEXT PRIMARY KEY, college TEXT, password TEXT,
    name TEXT, contact_number TEXT, course TEXT, year TEXT,
    semester TEXT, class_section TEXT,
    total_fee REAL DEFAULT 0, fee_paid REAL DEFAULT 0,
    attendance_percentage REAL DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    result TEXT DEFAULT 'Pending')
""")

for col, typ in [
    ("name","TEXT"),("contact_number","TEXT"),("course","TEXT"),
    ("year","TEXT"),("semester","TEXT"),("class_section","TEXT"),
    ("total_fee","REAL DEFAULT 0"),("fee_paid","REAL DEFAULT 0"),
    ("attendance_percentage","REAL DEFAULT 0"),
    ("total_classes","INTEGER DEFAULT 0"),
    ("result","TEXT DEFAULT 'Pending'"),
]:
    try: cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
    except: pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins(
    admin_id TEXT PRIMARY KEY, password TEXT)
""")
cursor.execute("INSERT OR IGNORE INTO admins VALUES (?,?)", ("ADMIN001","admin123"))

cursor.execute("""
CREATE TABLE IF NOT EXISTS notices(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, message TEXT, posted_date TEXT)
""")
conn.commit()

SYLLABUS_INFO = {
    "bca":   "Sem 1: Programming, Maths\nSem 2: OOP, Digital Electronics\nSem 3: Data Structures, DBMS",
    "btech": "Sem 1: Engg Maths, Physics\nSem 2: Programming, Mechanics\nSem 3: Data Structures, Electronics",
    "bsc":   "Sem 1: Maths, Physics, Chemistry\nSem 2: Statistics, Computer Basics",
    "mca":   "Sem 1: Discrete Maths, C Programming\nSem 2: DBMS, OS, OOP\nSem 3: Networks, Web Tech",
}


# ═══════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════

def show_message(text):
    m = Toplevel()
    m.geometry("270x140")
    m.title("Message")
    m.resizable(False, False)
    Label(m, text=text, font=("Arial",12,"bold"), wraplength=230).pack(expand=True)


def get_user(aid):
    cursor.execute("SELECT * FROM users WHERE admission_id=?", (aid,))
    return cursor.fetchone()


def update_txt_file():
    try:
        cursor.execute("SELECT admission_id, college, password FROM users")
        rows = cursor.fetchall()
        with open("users_data.txt", "w") as f:
            for r in rows:
                f.write(
                    f"Admission ID : {r['admission_id']}\n"
                    f"College      : {r['college']}\n"
                    f"Password     : {r['password']}\n"
                    "---------------------\n"
                )
    except: pass


def save_text(aid, college, password):
    with open("users_data.txt", "a") as f:
        f.write(
            f"Admission ID : {aid}\n"
            f"College      : {college}\n"
            f"Password     : {password}\n"
            "---------------------\n"
        )


def draw_avatar(parent, key, size=50, bg_col="white"):
    color = avatar_color(str(key))
    cv = Canvas(parent, width=size, height=size,
                bg=bg_col, highlightthickness=0)
    r = size // 2
    cv.create_oval(3, 3, size-3, size-3, fill=color, outline="")
    cv.create_text(r, r, text=str(key or "?")[0].upper(),
                   fill="white", font=("Arial", r//2+5, "bold"))
    return cv


# ═══════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════

def admin_panel(admin_id):

    win = Toplevel(root)
    win.geometry("340x500")
    win.title("Admin Panel")
    win.configure(bg="#EFF6FB")
    win.resizable(False, False)

    content = Frame(win, bg="#EFF6FB")
    content.pack(fill=BOTH, expand=True)

    def clr():
        for w in content.winfo_children():
            w.destroy()

    def hdr(title, back=None):
        h = Frame(content, bg="#1A237E")
        h.pack(fill=X)
        if back:
            Button(h, text="\u2190", bg="#1A237E", fg="white",
                   relief=FLAT, font=("Arial",14,"bold"),
                   cursor="hand2", command=back).pack(side=LEFT, padx=8, pady=8)
        Label(h, text=title, bg="#1A237E", fg="white",
              font=("Arial",13,"bold")).pack(side=LEFT, padx=12, pady=12)

    def show_main():
        clr()
        hdr("  Admin Panel")
        Frame(content, bg="#EFF6FB", height=20).pack()

        for txt, col, cmd in [
            ("  Post Notice",        "#1976D2", show_post_notice),
            ("  Manage Notices",     "#0277BD", show_manage_notices),
            ("  Update Student",     "#2E7D32", show_update_student),
            ("  Change Password",    "#6A1B9A", show_change_pass),
        ]:
            Button(content, text=txt, bg=col, fg="white",
                   font=("Arial",11,"bold"), relief=FLAT, width=24,
                   pady=11, cursor="hand2", anchor="w", padx=20,
                   command=cmd).pack(pady=5)

    def show_post_notice():
        clr()
        hdr("  Post Notice", show_main)
        Frame(content, bg="#EFF6FB", height=10).pack()

        Label(content, text="Title", bg="#EFF6FB",
              font=("Arial",10,"bold")).pack(anchor="w", padx=20)
        te = Entry(content, font=("Arial",11), width=30,
                   relief=GROOVE, bd=2)
        te.pack(padx=20, pady=4)

        Label(content, text="Message", bg="#EFF6FB",
              font=("Arial",10,"bold")).pack(anchor="w", padx=20)
        me = Text(content, font=("Arial",10), width=30, height=5,
                  relief=GROOVE, bd=2)
        me.pack(padx=20, pady=4)

        def post():
            t = te.get().strip()
            m = me.get("1.0", END).strip()
            if not t or not m:
                show_message("Fill both\ntitle and message")
                return
            cursor.execute(
                "INSERT INTO notices(title,message,posted_date) VALUES(?,?,?)",
                (t, m, datetime.now().strftime("%d %b %Y, %H:%M"))
            )
            conn.commit()
            show_message("Notice posted!")
            show_main()

        Button(content, text="Post Notice", bg="#388E3C", fg="white",
               relief=FLAT, font=("Arial",11,"bold"), width=16,
               pady=9, cursor="hand2", command=post).pack(pady=12)

    def show_manage_notices():
        clr()
        hdr("  Manage Notices", show_main)
        cursor.execute("SELECT id,title,posted_date FROM notices ORDER BY id DESC")
        rows = cursor.fetchall()

        if not rows:
            Frame(content, bg="#EFF6FB", height=30).pack()
            Label(content, text="No notices yet", fg="#999999",
                  bg="#EFF6FB", font=("Arial",11)).pack()
            return

        for row in rows:
            card = Frame(content, bg="white", relief=GROOVE, bd=1)
            card.pack(fill=X, padx=12, pady=4)
            Label(card, text=row["title"], bg="white",
                  font=("Arial",10,"bold"), anchor="w").pack(side=LEFT, padx=10, pady=8)
            Label(card, text=row["posted_date"] or "",
                  bg="white", fg="#999999",
                  font=("Arial",8)).pack(side=LEFT)
            nid = row["id"]
            Button(card, text="Delete", bg="#C62828", fg="white",
                   relief=FLAT, font=("Arial",9), cursor="hand2",
                   command=lambda i=nid: (
                       cursor.execute("DELETE FROM notices WHERE id=?", (i,)),
                       conn.commit(),
                       show_manage_notices()
                   )).pack(side=RIGHT, padx=8, pady=5)

    def show_update_student():
        clr()
        hdr("  Update Student", show_main)
        Frame(content, bg="#EFF6FB", height=15).pack()

        Label(content, text="Admission ID", bg="#EFF6FB",
              font=("Arial",10,"bold")).pack()
        ide = Entry(content, font=("Arial",12), width=22,
                    relief=GROOVE, bd=2)
        ide.pack(pady=6)
        ide.focus()

        def search():
            aid = ide.get().strip()
            u = get_user(aid)
            if not u:
                show_message("Student not found")
                return
            show_edit_form(aid, u)

        Button(content, text="Search Student", bg="#1976D2", fg="white",
               relief=FLAT, font=("Arial",11,"bold"), width=16,
               pady=8, cursor="hand2", command=search).pack(pady=8)
        ide.bind("<Return>", lambda e: search())

    def show_edit_form(aid, user):
        clr()
        hdr(f"  Editing: {aid}", show_update_student)
        Frame(content, bg="#EFF6FB", height=8).pack()

        Label(content, text=f"Name: {user['name'] or '-'}",
              bg="#EFF6FB", fg="#444444",
              font=("Arial",10)).pack(anchor="w", padx=20)

        fields = [
            ("Attendance %",  "attendance_percentage", user["attendance_percentage"] or 0),
            ("Total Classes", "total_classes",         user["total_classes"] or 0),
            ("Total Fee",     "total_fee",             user["total_fee"] or 0),
            ("Fee Paid",      "fee_paid",              user["fee_paid"] or 0),
        ]

        entries = {}
        for lbl, key, val in fields:
            Label(content, text=lbl, bg="#EFF6FB",
                  font=("Arial",10,"bold")).pack(anchor="w", padx=20, pady=(4,0))
            e = Entry(content, font=("Arial",11), width=24,
                      relief=GROOVE, bd=2)
            e.insert(0, str(val))
            e.pack(padx=20, pady=2)
            entries[key] = e

        Label(content, text="Result", bg="#EFF6FB",
              font=("Arial",10,"bold")).pack(anchor="w", padx=20, pady=(6,2))
        rv = StringVar(value=user["result"] or "Pending")
        rf = Frame(content, bg="#EFF6FB")
        rf.pack(anchor="w", padx=30)
        for opt in ["Pending","Pass","Fail","Distinction"]:
            Radiobutton(rf, text=opt, variable=rv, value=opt,
                        bg="#EFF6FB", font=("Arial",9)).pack(side=LEFT, padx=4)

        def save():
            try:
                att  = float(entries["attendance_percentage"].get())
                cls  = int(entries["total_classes"].get())
                tf   = float(entries["total_fee"].get())
                fp   = float(entries["fee_paid"].get())
            except ValueError:
                show_message("Enter valid\nnumeric values")
                return
            cursor.execute(
                """UPDATE users SET attendance_percentage=?,total_classes=?,
                   total_fee=?,fee_paid=?,result=? WHERE admission_id=?""",
                (att, cls, tf, fp, rv.get(), aid)
            )
            conn.commit()
            show_message("Student updated!")
            show_main()

        Button(content, text="Save Changes", bg="#388E3C", fg="white",
               relief=FLAT, font=("Arial",11,"bold"), width=16,
               pady=8, cursor="hand2", command=save).pack(pady=10)

    def show_change_pass():
        clr()
        hdr("  Change Password", show_main)
        Frame(content, bg="#EFF6FB", height=20).pack()

        Label(content, text="Current Password", bg="#EFF6FB",
              font=("Arial",10,"bold")).pack()
        old_e = Entry(content, show="*", font=("Arial",12), width=22,
                      relief=GROOVE, bd=2)
        old_e.pack(pady=4)

        Label(content, text="New Password", bg="#EFF6FB",
              font=("Arial",10,"bold")).pack(pady=(10,0))
        new_e = Entry(content, show="*", font=("Arial",12), width=22,
                      relief=GROOVE, bd=2)
        new_e.pack(pady=4)

        def upd():
            cursor.execute("SELECT password FROM admins WHERE admin_id=?",
                           (admin_id,))
            row = cursor.fetchone()
            if not row or old_e.get() != row[0]:
                show_message("Current password\nis wrong")
                return
            if not new_e.get():
                show_message("New password\ncan't be empty")
                return
            cursor.execute("UPDATE admins SET password=? WHERE admin_id=?",
                           (new_e.get(), admin_id))
            conn.commit()
            show_message("Password updated!")
            show_main()

        Button(content, text="Update", bg="#1976D2", fg="white",
               relief=FLAT, font=("Arial",11,"bold"), width=14,
               pady=8, cursor="hand2", command=upd).pack(pady=14)

    show_main()


# ═══════════════════════════════════════════
#  HOME PAGE
# ═══════════════════════════════════════════

def home_page(admission_id):

    dm = {"on": False}

    def TH():
        return DARK if dm["on"] else LIGHT

    win = Toplevel(root)
    win.geometry("340x540")
    win.title("Home")
    win.resizable(False, False)

    content = Frame(win)
    content.pack(fill=BOTH, expand=True)

    def clr():
        for w in content.winfo_children():
            w.destroy()

    # ---- Theme applicator ----

    def apply():
        T = TH()
        win.configure(bg=T["bg"])

        def restyle(w):
            cls = w.winfo_class()
            try: bg = w.cget("bg")
            except: bg = ""

            if bg in FIXED_BG or bg == "#1A237E":
                return

            try:
                if cls == "Frame":
                    w.configure(bg=T["bg"])
                elif cls == "Label":
                    par_bg = w.master.cget("bg") if w.master else T["bg"]
                    if par_bg in FIXED_BG or par_bg == "#1A237E":
                        return
                    w.configure(bg=par_bg, fg=T["text"])
                elif cls == "Button":
                    cbg = w.cget("bg")
                    if cbg in FIXED_BG or cbg == "#1A237E":
                        return
                    w.configure(bg=T["soft"], fg=T["soft_fg"],
                                activebackground=T["accent"],
                                activeforeground="white")
                elif cls == "Entry":
                    w.configure(bg=T["entry"], fg=T["text"],
                                insertbackground=T["text"])
                elif cls == "Canvas":
                    par_bg = w.master.cget("bg") if w.master else T["bg"]
                    if par_bg not in FIXED_BG:
                        w.configure(bg=par_bg)
                elif cls == "Text":
                    w.configure(bg=T["entry"], fg=T["text"],
                                insertbackground=T["text"])
                elif cls == "Radiobutton":
                    par_bg = w.master.cget("bg") if w.master else T["bg"]
                    w.configure(bg=par_bg, fg=T["text"],
                                activebackground=par_bg,
                                selectcolor=par_bg)
            except: pass

            for c in w.winfo_children():
                restyle(c)

        restyle(content)
        nav.configure(bg=TH()["nav"])
        for c in nav.winfo_children():
            try: c.configure(bg=TH()["nav"], fg=TH()["nav_fg"])
            except: pass

    # ---- Shared screen header ----

    def screen_hdr(title, back=None):
        T = TH()
        h = Frame(content, bg=T["header"])
        h.pack(fill=X)
        if back:
            Button(h, text="\u2190", bg=T["header"], fg="white",
                   relief=FLAT, font=("Arial",15,"bold"),
                   cursor="hand2", command=back).pack(side=LEFT, padx=8, pady=6)
        Label(h, text=title, bg=T["header"], fg="white",
              font=("Arial",12,"bold")).pack(side=LEFT, padx=12, pady=12)

    # ---- Home banner (avatar + greeting) ----

    def home_banner():
        T = TH()
        user = get_user(admission_id)
        name = user["name"] or admission_id
        h = Frame(content, bg=T["header"])
        h.pack(fill=X)
        av = draw_avatar(h, name, size=46, bg_col=T["header"])
        av.pack(side=LEFT, padx=12, pady=10)
        info = Frame(h, bg=T["header"])
        info.pack(side=LEFT)
        Label(info, text=get_greeting(), bg=T["header"],
              fg="#90CAF9", font=("Arial",9)).pack(anchor="w")
        Label(info, text=name, bg=T["header"], fg="white",
              font=("Arial",12,"bold")).pack(anchor="w")
        Label(info, text=f"{user['course'] or ''} | {user['semester'] or ''} Sem",
              bg=T["header"], fg="#BBDEFB",
              font=("Arial",8)).pack(anchor="w")

    # ─── Tab: Home ────────────────────────────────────

    def show_home():
        clr()
        T = TH()
        home_banner()
        Frame(content, bg=T["bg"], height=12).pack()

        grid = Frame(content, bg=T["bg"])
        grid.pack(fill=BOTH, expand=True, padx=12)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=1)
        grid.rowconfigure(1, weight=1)

        tiles = [
            ("\U0001f4ca\nAttendance", "#1565C0", show_attendance),
            ("\U0001f4cb\nResult",     "#2E7D32", show_result),
            ("\U0001f4b0\nFees",       "#E65100", show_fees),
            ("\U0001f4da\nSyllabus",   "#6A1B9A", show_syllabus),
        ]
        for i, (txt, col, cmd) in enumerate(tiles):
            r, c = divmod(i, 2)
            Button(grid, text=txt, bg=col, fg="white",
                   font=("Arial",14,"bold"), relief=FLAT,
                   cursor="hand2", command=cmd).grid(
                       row=r, column=c, padx=6, pady=6, sticky="nsew")

        apply()

    # ─── Attendance ───────────────────────────────────

    def show_attendance():
        clr()
        T = TH()
        screen_hdr("\U0001f4ca Attendance", show_home)
        user = get_user(admission_id)
        total = user["total_classes"] or 0
        att   = user["attendance_percentage"] or 0

        Frame(content, bg=T["bg"], height=30).pack()

        if total == 0:
            Label(content, text="Attendance details\nnot available yet",
                  fg=T["sub"], bg=T["bg"], font=("Arial",11)).pack(pady=20)
        else:
            color = T["ok"] if att >= 75 else T["err"]
            Label(content, text=f"{att:.1f}%", fg=color, bg=T["bg"],
                  font=("Arial",36,"bold")).pack()
            Label(content, text=f"Total Classes Running : {total}",
                  bg=T["bg"], fg=T["sub"], font=("Arial",10)).pack(pady=6)
            status = "\u2705 Good Attendance" if att >= 75 else "\u26a0\ufe0f  Attendance Low - Attend more classes"
            Label(content, text=status, bg=T["bg"], fg=color,
                  font=("Arial",10,"bold")).pack(pady=4)

        Button(content, text="\u2190 Back", bg=T["accent"], fg="white",
               relief=FLAT, font=("Arial",10,"bold"),
               cursor="hand2", command=show_home).pack(pady=25)
        apply()

    # ─── Result ───────────────────────────────────────

    def show_result():
        clr()
        T = TH()
        screen_hdr("\U0001f4cb Result", show_home)
        user = get_user(admission_id)
        result = user["result"] or "Pending"

        Frame(content, bg=T["bg"], height=40).pack()

        color = T["ok"] if result in ("Pass","Distinction") else \
                T["err"] if result == "Fail" else T["sub"]

        Label(content, text=result, fg=color, bg=T["bg"],
              font=("Arial",30,"bold")).pack()
        Frame(content, bg=T["bg"], height=10).pack()

        msg = {"Pass":"  Congratulations!",
               "Distinction":"\U0001f3c6 Outstanding Result!",
               "Fail":"\U0001f4d6 Keep studying, you can do it!",
               "Pending":"\U0001f550 Result not declared yet"}.get(result,"")
        if msg:
            Label(content, text=msg, bg=T["bg"], fg=T["sub"],
                  font=("Arial",11)).pack()

        Button(content, text="\u2190 Back", bg=T["accent"], fg="white",
               relief=FLAT, font=("Arial",10,"bold"),
               cursor="hand2", command=show_home).pack(pady=35)
        apply()

    # ─── Fees ─────────────────────────────────────────

    def show_fees():
        clr()
        T = TH()
        screen_hdr("\U0001f4b0 Fees", show_home)
        user = get_user(admission_id)
        total   = user["total_fee"] or 0
        paid    = user["fee_paid"] or 0
        remain  = total - paid

        Frame(content, bg=T["bg"], height=18).pack()

        if total == 0:
            Label(content, text="Fee details not added yet",
                  fg=T["sub"], bg=T["bg"], font=("Arial",11)).pack(pady=20)
        else:
            card = Frame(content, bg=T["card"], relief=GROOVE, bd=1)
            card.pack(fill=X, padx=18, pady=8)
            for lbl, val, color in [
                ("Total Fee",  f"\u20b9{total:.0f}", T["text"]),
                ("Fee Paid",   f"\u20b9{paid:.0f}",  T["ok"]),
                ("Remaining",  f"\u20b9{remain:.0f}", T["err"] if remain > 0 else T["ok"]),
            ]:
                row = Frame(card, bg=T["card"])
                row.pack(fill=X, padx=14, pady=7)
                Label(row, text=lbl, bg=T["card"], fg=T["sub"],
                      font=("Arial",10)).pack(side=LEFT)
                Label(row, text=val, bg=T["card"], fg=color,
                      font=("Arial",11,"bold")).pack(side=RIGHT)

            if remain > 0:
                Button(content, text=f"Pay \u20b9{remain:.0f} Now",
                       bg="#E65100", fg="white",
                       relief=FLAT, font=("Arial",11,"bold"),
                       width=20, pady=10, cursor="hand2",
                       command=lambda: pay_fee(remain)).pack(pady=10)
            else:
                Label(content, text="\u2705 Fully Paid",
                      fg=T["ok"], bg=T["bg"],
                      font=("Arial",12,"bold")).pack(pady=10)

        Button(content, text="\u2190 Back", bg=T["accent"], fg="white",
               relief=FLAT, font=("Arial",10,"bold"),
               cursor="hand2", command=show_home).pack(pady=8)
        apply()

    def pay_fee(amount):
        cursor.execute(
            "UPDATE users SET fee_paid = fee_paid + ? WHERE admission_id=?",
            (amount, admission_id))
        conn.commit()
        show_message("Fee paid\nsuccessfully \u2705")
        show_fees()

    # ─── Syllabus ─────────────────────────────────────

    def show_syllabus():
        clr()
        T = TH()
        screen_hdr("\U0001f4da Syllabus", show_home)
        user = get_user(admission_id)
        key  = (user["course"] or "").strip().lower()
        text = SYLLABUS_INFO.get(key,
               "Syllabus not added yet\nfor this course.\nContact admin.")

        Frame(content, bg=T["bg"], height=12).pack()
        Label(content, text=f"Course : {user['course'] or '-'}",
              bg=T["bg"], fg=T["sub"], font=("Arial",10)).pack()
        Frame(content, bg=T["bg"], height=8).pack()

        card = Frame(content, bg=T["card"], relief=GROOVE, bd=1)
        card.pack(fill=X, padx=18, pady=4)
        Label(card, text=text, bg=T["card"], fg=T["text"],
              font=("Arial",10), justify=LEFT,
              wraplength=270).pack(padx=14, pady=14)

        Button(content, text="\u2190 Back", bg=T["accent"], fg="white",
               relief=FLAT, font=("Arial",10,"bold"),
               cursor="hand2", command=show_home).pack(pady=18)
        apply()

    # ─── Tab: Notice ──────────────────────────────────

    def show_notice():
        clr()
        T = TH()
        screen_hdr("\U0001f4e2 Notices")
        cursor.execute("SELECT * FROM notices ORDER BY id DESC")
        rows = cursor.fetchall()

        if not rows:
            Frame(content, bg=T["bg"], height=30).pack()
            Label(content, text="\U0001f4ed No notices yet",
                  fg=T["sub"], bg=T["bg"], font=("Arial",11)).pack(pady=15)
        else:
            for n in rows:
                card = Frame(content, bg=T["card"], relief=GROOVE, bd=1)
                card.pack(fill=X, padx=12, pady=5)
                Label(card, text=n["title"], bg=T["card"], fg=T["text"],
                      font=("Arial",10,"bold")).pack(anchor="w", padx=10, pady=(8,2))
                Label(card, text=n["message"], bg=T["card"], fg=T["sub"],
                      font=("Arial",9), wraplength=270,
                      justify=LEFT).pack(anchor="w", padx=10)
                Label(card, text=n["posted_date"] or "",
                      bg=T["card"], fg=T["sub"],
                      font=("Arial",8)).pack(anchor="e", padx=10, pady=(0,6))
        apply()

    # ─── Tab: ID Card ─────────────────────────────────

    def show_id_card():
        clr()
        T = TH()
        screen_hdr("\U0001f194 ID Card")
        user = get_user(admission_id)
        name = user["name"] or admission_id

        Frame(content, bg=T["bg"], height=12).pack()

        av_f = Frame(content, bg=T["bg"])
        av_f.pack()
        av = draw_avatar(av_f, name, size=66, bg_col=T["bg"])
        av.pack()

        Label(content, text=name, bg=T["bg"], fg=T["text"],
              font=("Arial",13,"bold")).pack(pady=(4,0))
        Label(content, text=user["college"] or "",
              bg=T["bg"], fg=T["sub"], font=("Arial",9)).pack()

        Frame(content, bg=T["bg"], height=8).pack()

        card = Frame(content, bg=T["card"], relief=GROOVE, bd=1)
        card.pack(fill=X, padx=16, pady=4)

        for lbl, val in [
            ("Admission ID", admission_id),
            ("Course",       user["course"]),
            ("Year",         user["year"]),
            ("Semester",     user["semester"]),
            ("Class",        user["class_section"]),
            ("Contact",      user["contact_number"]),
        ]:
            row = Frame(card, bg=T["card"])
            row.pack(fill=X, padx=12, pady=4)
            Label(row, text=lbl, bg=T["card"], fg=T["sub"],
                  font=("Arial",9), width=13, anchor="w").pack(side=LEFT)
            Label(row, text=val or "-", bg=T["card"], fg=T["text"],
                  font=("Arial",9,"bold")).pack(side=LEFT)
        apply()

    # ─── Tab: Profile ─────────────────────────────────

    def show_profile():
        clr()
        T = TH()
        screen_hdr("\U0001f464 Profile")
        Frame(content, bg=T["bg"], height=12).pack()

        dark_lbl = "\U0001f319 Dark Mode : ON" if dm["on"] else "\u2600\ufe0f  Dark Mode : OFF"

        for txt, cmd in [
            ("\u2139\ufe0f   Information",    show_information),
            ("\u270f\ufe0f   Edit Information", show_edit_information),
            ("\U0001f510  Change Password",  show_change_password),
            (dark_lbl,                        toggle_dark),
            ("\U0001f6aa  Logout",            logout),
        ]:
            Button(content, text=txt, bg=T["soft"], fg=T["soft_fg"],
                   relief=FLAT, font=("Arial",11), width=26,
                   pady=11, cursor="hand2", anchor="w", padx=20,
                   command=cmd).pack(pady=3, padx=18, fill=X)
        apply()

    def toggle_dark():
        dm["on"] = not dm["on"]
        show_profile()

    # ─── Profile → Information ────────────────────────

    def show_information():
        clr()
        T = TH()
        screen_hdr("\u2139\ufe0f  Information", show_profile)
        user = get_user(admission_id)

        Frame(content, bg=T["bg"], height=10).pack()

        card = Frame(content, bg=T["card"], relief=GROOVE, bd=1)
        card.pack(fill=X, padx=16, pady=6)

        for lbl, val in [
            ("Name",         user["name"]),
            ("Admission ID", admission_id),
            ("College",      user["college"]),
            ("Course",       user["course"]),
            ("Year",         user["year"]),
            ("Semester",     user["semester"]),
            ("Class",        user["class_section"]),
            ("Contact",      user["contact_number"]),
        ]:
            row = Frame(card, bg=T["card"])
            row.pack(fill=X, padx=12, pady=5)
            Label(row, text=lbl, bg=T["card"], fg=T["sub"],
                  font=("Arial",9), width=13, anchor="w").pack(side=LEFT)
            Label(row, text=val or "-", bg=T["card"], fg=T["text"],
                  font=("Arial",9,"bold")).pack(side=LEFT)
        apply()

    # ─── Profile → Edit Information ──────────────────

    def show_edit_information():
        clr()
        T = TH()
        screen_hdr("\u270f\ufe0f  Edit Information", show_profile)
        user = get_user(admission_id)

        Frame(content, bg=T["bg"], height=8).pack()

        name_set = bool(user["name"] and user["name"].strip())
        name_entry = None

        if name_set:
            Label(content, text=f"Name : {user['name']}  (fixed)",
                  fg=T["sub"], bg=T["bg"], font=("Arial",9)).pack(anchor="w", padx=20)
        else:
            Label(content, text="Name (can be set only once)",
                  bg=T["bg"], fg=T["text"],
                  font=("Arial",10,"bold")).pack(anchor="w", padx=20)
            name_entry = Entry(content, bg=T["entry"], fg=T["text"],
                               font=("Arial",11), width=26, relief=GROOVE, bd=2)
            name_entry.pack(padx=20, pady=3)

        Label(content, text=f"Admission ID : {admission_id}  (fixed)",
              fg=T["sub"], bg=T["bg"],
              font=("Arial",9)).pack(anchor="w", padx=20, pady=(3,8))

        editable = [
            ("College",        "college"),
            ("Contact Number", "contact_number"),
            ("Course",         "course"),
            ("Year",           "year"),
            ("Semester",       "semester"),
            ("Class / Section","class_section"),
        ]

        entries = {}
        for lbl, key in editable:
            Label(content, text=lbl, bg=T["bg"], fg=T["text"],
                  font=("Arial",10,"bold")).pack(anchor="w", padx=20)
            e = Entry(content, bg=T["entry"], fg=T["text"],
                      font=("Arial",11), width=26, relief=GROOVE, bd=2)
            e.insert(0, user[key] or "")
            e.pack(padx=20, pady=2)
            entries[key] = e

        def save():
            new_name = user["name"]
            if not name_set and name_entry:
                t = name_entry.get().strip()
                if t: new_name = t

            cursor.execute(
                """UPDATE users SET name=?,college=?,contact_number=?,
                   course=?,year=?,semester=?,class_section=?
                   WHERE admission_id=?""",
                (new_name,
                 entries["college"].get().strip(),
                 entries["contact_number"].get().strip(),
                 entries["course"].get().strip(),
                 entries["year"].get().strip(),
                 entries["semester"].get().strip(),
                 entries["class_section"].get().strip(),
                 admission_id)
            )
            conn.commit()
            show_message("Information updated \u2705")
            show_profile()

        Button(content, text="Save", bg=T["accent"], fg="white",
               relief=FLAT, font=("Arial",11,"bold"), width=14,
               pady=8, cursor="hand2", command=save).pack(pady=10)
        apply()

    # ─── Profile → Change Password ────────────────────

    def show_change_password():
        clr()
        T = TH()
        screen_hdr("\U0001f510 Change Password", show_profile)
        Frame(content, bg=T["bg"], height=20).pack()

        Label(content, text="Current Password", bg=T["bg"], fg=T["text"],
              font=("Arial",10,"bold")).pack(anchor="w", padx=25)
        old_e = Entry(content, show="*", bg=T["entry"], fg=T["text"],
                      font=("Arial",12), width=24, relief=GROOVE, bd=2)
        old_e.pack(padx=25, pady=5)
        old_e.focus()

        Label(content, text="New Password", bg=T["bg"], fg=T["text"],
              font=("Arial",10,"bold")).pack(anchor="w", padx=25, pady=(10,0))
        new_e = Entry(content, show="*", bg=T["entry"], fg=T["text"],
                      font=("Arial",12), width=24, relief=GROOVE, bd=2)
        new_e.pack(padx=25, pady=5)

        def update():
            user = get_user(admission_id)
            if old_e.get() != user["password"]:
                show_message("Current password\nis wrong")
                return
            if not new_e.get():
                show_message("New password\ncan't be empty")
                return
            cursor.execute("UPDATE users SET password=? WHERE admission_id=?",
                           (new_e.get(), admission_id))
            conn.commit()
            update_txt_file()
            show_message("Password updated \u2705")
            show_profile()

        Button(content, text="Update", bg=T["accent"], fg="white",
               relief=FLAT, font=("Arial",11,"bold"), width=14,
               pady=9, cursor="hand2", command=update).pack(pady=18)
        new_e.bind("<Return>", lambda e: update())
        apply()

    def logout():
        win.destroy()

    # ─── Bottom nav ───────────────────────────────────

    T = TH()
    nav = Frame(win, bg=T["nav"])
    nav.pack(side=BOTTOM, fill=X)

    for txt, cmd in [
        ("\U0001f3e0\nHome",    show_home),
        ("\U0001f4e2\nNotice",  show_notice),
        ("\U0001f194\nID Card", show_id_card),
        ("\U0001f464\nProfile", show_profile),
    ]:
        Button(nav, text=txt, bg=T["nav"], fg="white",
               relief=FLAT, font=("Arial",8), cursor="hand2",
               activebackground=T["accent"], command=cmd
               ).pack(side=LEFT, expand=True, fill=X, pady=5)

    show_home()


# ═══════════════════════════════════════════
#  REGISTRATION
# ═══════════════════════════════════════════

def register_page():

    win = Toplevel(root)
    win.geometry("340x500")
    win.title("Create Account")
    win.configure(bg="#EFF6FB")
    win.resizable(False, False)

    data = {}

    def clr():
        for w in win.winfo_children():
            w.destroy()

    def hdr(title):
        h = Frame(win, bg="#1565C0")
        h.pack(fill=X)
        Label(h, text=title, bg="#1565C0", fg="white",
              font=("Arial",13,"bold")).pack(padx=15, pady=12)

    def progress(step, total=3):
        pf = Frame(win, bg="#EFF6FB")
        pf.pack(fill=X, padx=15, pady=3)
        Label(pf, text=f"Step {step} of {total}", bg="#EFF6FB",
              fg="#999999", font=("Arial",9)).pack(side=RIGHT)

    def nav_btns(back_fn, next_fn, skip_fn=None):
        f = Frame(win, bg="#EFF6FB")
        f.pack(pady=14)
        if back_fn:
            Button(f, text="\u2190 Back", bg="#E3F2FD", fg="#1565C0",
                   relief=FLAT, font=("Arial",10), width=10,
                   cursor="hand2", command=back_fn).pack(side=LEFT, padx=4)
        if skip_fn:
            Button(f, text="Skip", bg="#EFF6FB", fg="#888888",
                   relief=FLAT, font=("Arial",10), width=8,
                   cursor="hand2", command=skip_fn).pack(side=LEFT, padx=4)
        Button(f, text="Next \u2192", bg="#1976D2", fg="white",
               relief=FLAT, font=("Arial",10,"bold"), width=10,
               cursor="hand2", command=next_fn).pack(side=LEFT, padx=4)

    def field(label, val="", secret=False):
        Label(win, text=label, bg="#EFF6FB",
              font=("Arial",10,"bold")).pack(anchor="w", padx=25)
        e = Entry(win, font=("Arial",12), width=26,
                  relief=GROOVE, bd=2,
                  show="*" if secret else "")
        e.insert(0, val)
        e.pack(padx=25, pady=4)
        return e

    # Step 1: Admission ID

    def step1():
        clr()
        hdr("Create Account")
        progress(1)
        Frame(win, bg="#EFF6FB", height=12).pack()
        e = field("Admission ID", data.get("admission_id",""))
        e.focus()

        def nxt():
            aid = e.get().strip()
            if not aid:
                show_message("Admission ID\ncan't be empty")
                return
            if get_user(aid):
                show_message("Account already\nexists for this ID")
                return
            data["admission_id"] = aid
            step2()

        nav_btns(None, nxt)
        e.bind("<Return>", lambda ev: nxt())

    # Step 2: College + Password

    def step2():
        clr()
        hdr("Create Account")
        progress(2)
        Frame(win, bg="#EFF6FB", height=8).pack()
        ec = field("College Name", data.get("college",""))
        ep = field("Password", data.get("password",""), secret=True)
        ec.focus()

        def nxt():
            if not ec.get().strip():
                show_message("College name\ncan't be empty")
                return
            if not ep.get():
                show_message("Password\ncan't be empty")
                return
            data["college"] = ec.get().strip()
            data["password"] = ep.get()
            step3()

        nav_btns(step1, nxt)
        ep.bind("<Return>", lambda ev: nxt())

    # Step 3: ID Card Details

    def step3():
        clr()
        hdr("Create Account")
        progress(3)
        Label(win, text="ID Card Details", bg="#EFF6FB",
              font=("Arial",12,"bold")).pack(pady=(6,0))
        Label(win, text="(optional, skip to fill later)",
              bg="#EFF6FB", fg="#888888", font=("Arial",9)).pack(pady=(0,6))

        FIELDS = [
            ("Full Name",       "name"),
            ("Contact Number",  "contact_number"),
            ("Course",          "course"),
            ("Year",            "year"),
            ("Semester",        "semester"),
            ("Class/Section",   "class_section"),
        ]

        entries = {}
        for lbl, key in FIELDS:
            Label(win, text=lbl, bg="#EFF6FB",
                  font=("Arial",9,"bold")).pack(anchor="w", padx=25)
            e = Entry(win, font=("Arial",10), width=26,
                      relief=GROOVE, bd=2)
            e.insert(0, data.get(key,""))
            e.pack(padx=25, pady=1)
            entries[key] = e

        def nxt():
            for k, e in entries.items():
                data[k] = e.get().strip()
            create_account()

        def skip():
            for _, k in FIELDS:
                data.setdefault(k,"")
            create_account()

        nav_btns(step2, nxt, skip_fn=skip)

    def create_account():
        cursor.execute(
            """INSERT INTO users
               (admission_id,college,password,name,contact_number,
                course,year,semester,class_section) VALUES(?,?,?,?,?,?,?,?,?)""",
            (data["admission_id"], data["college"], data["password"],
             data.get("name",""), data.get("contact_number",""),
             data.get("course",""), data.get("year",""),
             data.get("semester",""), data.get("class_section",""))
        )
        conn.commit()
        save_text(data["admission_id"], data["college"], data["password"])
        show_message("Account Created\nSuccessfully \U0001f389")
        home_page(data["admission_id"])
        win.destroy()

    step1()


# ═══════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════

def login_page():
    win = Toplevel(root)
    win.geometry("320x320")
    win.title("Login")
    win.configure(bg="#EFF6FB")
    win.resizable(False, False)

    hdr = Frame(win, bg="#1565C0")
    hdr.pack(fill=X)
    Label(hdr, text="Login", bg="#1565C0", fg="white",
          font=("Arial",13,"bold")).pack(padx=15, pady=14)

    Frame(win, bg="#EFF6FB", height=20).pack()

    Label(win, text="Admission ID", bg="#EFF6FB",
          font=("Arial",10,"bold")).pack()
    id_e = Entry(win, font=("Arial",12), width=24,
                 relief=GROOVE, bd=2)
    id_e.pack(pady=5)
    id_e.focus()

    Label(win, text="Password", bg="#EFF6FB",
          font=("Arial",10,"bold")).pack(pady=(10,0))
    pw_e = Entry(win, show="*", font=("Arial",12), width=24,
                 relief=GROOVE, bd=2)
    pw_e.pack(pady=5)

    def check():
        uid  = id_e.get().strip()
        pw   = pw_e.get()
        user = get_user(uid)
        if not user:
            show_message("User ID not found")
            return
        if user["password"] != pw:
            show_message("Password incorrect")
            return
        win.destroy()
        home_page(uid)

    Button(win, text="Login", bg="#1976D2", fg="white",
           relief=FLAT, font=("Arial",12,"bold"), width=18,
           pady=9, cursor="hand2", command=check).pack(pady=20)

    pw_e.bind("<Return>", lambda e: check())


# ═══════════════════════════════════════════
#  ADMIN LOGIN
# ═══════════════════════════════════════════

def admin_login_page():
    win = Toplevel(root)
    win.geometry("320x300")
    win.title("Admin Login")
    win.configure(bg="#1A237E")
    win.resizable(False, False)

    Label(win, text="\u2699\ufe0f Admin Login", bg="#1A237E", fg="white",
          font=("Arial",14,"bold")).pack(pady=20)

    body = Frame(win, bg="#EFF6FB")
    body.pack(fill=BOTH, expand=True)
    Frame(body, bg="#EFF6FB", height=15).pack()

    Label(body, text="Admin ID", bg="#EFF6FB",
          font=("Arial",10,"bold")).pack()
    id_e = Entry(body, font=("Arial",12), width=24,
                 relief=GROOVE, bd=2)
    id_e.pack(pady=5)
    id_e.focus()

    Label(body, text="Password", bg="#EFF6FB",
          font=("Arial",10,"bold")).pack(pady=(8,0))
    pw_e = Entry(body, show="*", font=("Arial",12), width=24,
                 relief=GROOVE, bd=2)
    pw_e.pack(pady=5)

    def check():
        aid = id_e.get().strip()
        pw  = pw_e.get()
        cursor.execute("SELECT * FROM admins WHERE admin_id=?", (aid,))
        row = cursor.fetchone()
        if not row:
            show_message("Admin ID not found")
            return
        if row["password"] != pw:
            show_message("Password incorrect")
            return
        win.destroy()
        admin_panel(aid)

    Button(body, text="Login as Admin", bg="#1A237E", fg="white",
           relief=FLAT, font=("Arial",11,"bold"), width=18,
           pady=9, cursor="hand2", command=check).pack(pady=16)
    pw_e.bind("<Return>", lambda e: check())


# ═══════════════════════════════════════════
#  MAIN SCREEN
# ═══════════════════════════════════════════

# Header
hdr_frame = Frame(root, bg="#1565C0")
hdr_frame.pack(fill=X)
Label(hdr_frame, text="\U0001f3eb", bg="#1565C0",
      font=("Arial",30)).pack(pady=(18,4))
Label(hdr_frame, text="College Management",
      bg="#1565C0", fg="white",
      font=("Arial",15,"bold")).pack()
Label(hdr_frame, text="System",
      bg="#1565C0", fg="#90CAF9",
      font=("Arial",11)).pack(pady=(0,20))

# Body
body = Frame(root, bg="#EFF6FB")
body.pack(fill=BOTH, expand=True)

Frame(body, bg="#EFF6FB", height=22).pack()

Button(body, text="Login",
       bg="#1976D2", fg="white", relief=FLAT,
       font=("Arial",12,"bold"), width=22, pady=11,
       cursor="hand2", command=login_page).pack(pady=6)

Button(body, text="Create New Account",
       bg="#388E3C", fg="white", relief=FLAT,
       font=("Arial",12,"bold"), width=22, pady=11,
       cursor="hand2", command=register_page).pack(pady=6)

Button(body, text="Admin Login",
       bg="#EFF6FB", fg="#888888", relief=FLAT,
       font=("Arial",9), width=22, cursor="hand2",
       command=admin_login_page).pack(pady=4)

root.mainloop()