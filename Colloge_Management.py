import tkinter as tk
from tkinter import ttk, messagebox, font
import sqlite3
import json
import os
import re
from datetime import datetime, date
import random
import hashlib
 
 
# ─────────────────────────────────────────────
#  DATABASE LAYER
# ─────────────────────────────────────────────
DB_FILE = "college_cms.db"
 
def get_conn():
    return sqlite3.connect(DB_FILE)
 
def init_db():
    conn = get_conn()
    c = conn.cursor()
 
    c.executescript("""
        PRAGMA foreign_keys = ON;
 
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'admin'
        );
 
        CREATE TABLE IF NOT EXISTS departments (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT UNIQUE NOT NULL,
            code    TEXT UNIQUE NOT NULL,
            hod     TEXT
        );
 
        CREATE TABLE IF NOT EXISTS courses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            dept_id     INTEGER,
            credits     INTEGER DEFAULT 3,
            semester    INTEGER DEFAULT 1,
            FOREIGN KEY(dept_id) REFERENCES departments(id)
        );
 
        CREATE TABLE IF NOT EXISTS faculty (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id      TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            email       TEXT,
            phone       TEXT,
            dept_id     INTEGER,
            designation TEXT,
            joining     TEXT,
            FOREIGN KEY(dept_id) REFERENCES departments(id)
        );
 
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no     TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            email       TEXT,
            phone       TEXT,
            dept_id     INTEGER,
            semester    INTEGER DEFAULT 1,
            gender      TEXT,
            dob         TEXT,
            address     TEXT,
            admission   TEXT,
            FOREIGN KEY(dept_id) REFERENCES departments(id)
        );
 
        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER,
            course_id   INTEGER,
            date        TEXT,
            status      TEXT DEFAULT 'Present',
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(course_id)  REFERENCES courses(id)
        );
 
        CREATE TABLE IF NOT EXISTS exams (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER,
            course_id   INTEGER,
            exam_type   TEXT,
            marks       REAL,
            max_marks   REAL DEFAULT 100,
            exam_date   TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(course_id)  REFERENCES courses(id)
        );
 
        CREATE TABLE IF NOT EXISTS fees (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER,
            amount      REAL,
            paid        REAL DEFAULT 0,
            due_date    TEXT,
            paid_date   TEXT,
            status      TEXT DEFAULT 'Pending',
            description TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        );
    """)
 
    # Default admin
    pw = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users(username,password,role) VALUES(?,?,?)",
              ("admin", pw, "admin"))
 
    # Seed demo data if empty
    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        _seed_demo(c)
 
    conn.commit()
    conn.close()
 
def _seed_demo(c):
    depts = [
        ("Computer Science", "CS", "Dr. Rajesh Kumar"),
        ("Electronics", "EC", "Dr. Priya Singh"),
        ("Mechanical", "ME", "Dr. Arun Gupta"),
        ("Civil", "CE", "Dr. Sunita Rao"),
        ("Mathematics", "MA", "Dr. Vikram Joshi"),
    ]
    c.executemany("INSERT INTO departments(name,code,hod) VALUES(?,?,?)", depts)
 
    courses_data = [
        ("CS101","Data Structures",1,4,1),
        ("CS102","Algorithms",1,4,1),
        ("CS201","Database Systems",1,3,2),
        ("CS202","Operating Systems",1,3,2),
        ("EC101","Digital Electronics",2,4,1),
        ("ME101","Engineering Mechanics",3,4,1),
    ]
    c.executemany("INSERT INTO courses(code,name,dept_id,credits,semester) VALUES(?,?,?,?,?)", courses_data)
 
    faculty_data = [
        ("EMP001","Dr. Amit Sharma","amit@college.edu","9876543210",1,"Professor","2015-06-01"),
        ("EMP002","Prof. Neha Verma","neha@college.edu","9876543211",1,"Associate Professor","2018-07-15"),
        ("EMP003","Dr. Sanjay Patel","sanjay@college.edu","9876543212",2,"Assistant Professor","2020-01-10"),
        ("EMP004","Mrs. Kavita Rao","kavita@college.edu","9876543213",3,"Lecturer","2019-08-20"),
    ]
    c.executemany("INSERT INTO faculty(emp_id,name,email,phone,dept_id,designation,joining) VALUES(?,?,?,?,?,?,?)", faculty_data)
 
    student_names = [
        "Rahul Sharma","Priya Singh","Amit Kumar","Neha Gupta","Rohit Verma",
        "Anjali Patel","Vikas Yadav","Sneha Mishra","Arjun Tiwari","Pooja Pandey",
        "Kunal Joshi","Divya Agarwal","Siddharth Rao","Meera Nair","Harsh Srivastava"
    ]
    genders = ["Male","Female","Male","Female","Male","Female","Male","Female","Male","Female",
               "Male","Female","Male","Female","Male"]
    for i, (name, gender) in enumerate(zip(student_names, genders)):
        roll = f"2024CS{str(i+1).zfill(3)}"
        email = name.lower().replace(" ", ".") + "@student.edu"
        c.execute("""INSERT INTO students(roll_no,name,email,phone,dept_id,semester,gender,dob,address,admission)
                     VALUES(?,?,?,?,?,?,?,?,?,?)""",
                  (roll, name, email, f"98765{i:05d}", 1, random.randint(1,4), gender,
                   f"200{random.randint(2,5)}-0{random.randint(1,9)}-{random.randint(10,28)}",
                   f"{random.randint(1,500)}, Varanasi, UP", "2024-07-01"))
 
    # Attendance & exam seed
    c.execute("SELECT id FROM students")
    sids = [r[0] for r in c.fetchall()]
    dates = ["2024-08-01","2024-08-02","2024-08-05","2024-08-06","2024-08-07"]
    for sid in sids:
        for d in dates:
            status = random.choice(["Present","Present","Present","Absent"])
            c.execute("INSERT INTO attendance(student_id,course_id,date,status) VALUES(?,?,?,?)",
                      (sid, 1, d, status))
        marks = round(random.uniform(45,98),1)
        c.execute("INSERT INTO exams(student_id,course_id,exam_type,marks,max_marks,exam_date) VALUES(?,?,?,?,?,?)",
                  (sid, 1, "Mid-Term", marks, 100, "2024-09-15"))
        marks2 = round(random.uniform(50,99),1)
        c.execute("INSERT INTO exams(student_id,course_id,exam_type,marks,max_marks,exam_date) VALUES(?,?,?,?,?,?)",
                  (sid, 1, "Final", marks2, 100, "2024-11-20"))
        paid = random.choice([True, False])
        c.execute("INSERT INTO fees(student_id,amount,paid,due_date,paid_date,status,description) VALUES(?,?,?,?,?,?,?)",
                  (sid, 45000, 45000 if paid else 0, "2024-08-31",
                   "2024-07-25" if paid else None,
                   "Paid" if paid else "Pending", "Annual Tuition Fee"))
 
 
# ─────────────────────────────────────────────
#  COLOUR / STYLE CONSTANTS
# ─────────────────────────────────────────────
C = {
    "bg":        "#0F1B2D",   # deep navy
    "sidebar":   "#162032",   # slightly lighter navy
    "card":      "#1E2E45",   # card bg
    "accent":    "#3B82F6",   # electric blue
    "accent2":   "#10B981",   # emerald
    "accent3":   "#F59E0B",   # amber
    "accent4":   "#EF4444",   # red
    "accent5":   "#8B5CF6",   # violet
    "text":      "#E2E8F0",   # near-white
    "text2":     "#94A3B8",   # muted slate
    "border":    "#2D4A6E",   # subtle border
    "hover":     "#243554",   # hover state
    "entry":     "#243554",   # entry bg
    "white":     "#FFFFFF",
    "green":     "#10B981",
    "red":       "#EF4444",
    "yellow":    "#F59E0B",
}
 
NAV_ITEMS = [
    ("🏠", "Dashboard",   "dashboard"),
    ("🎓", "Students",    "students"),
    ("👨‍🏫", "Faculty",   "faculty"),
    ("📚", "Courses",     "courses"),
    ("🏛️", "Departments", "departments"),
    ("📋", "Attendance",  "attendance"),
    ("📝", "Exams",       "exams"),
    ("💰", "Fees",        "fees"),
]
 
 
# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class CollegeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("College Management System")
        self.geometry("1280x760")
        self.minsize(1100, 680)
        self.configure(bg=C["bg"])
 
        # Try to set icon color via window bg
        try:
            self.iconphoto(True, tk.PhotoImage(width=1, height=1))
        except Exception:
            pass
 
        self.current_section = tk.StringVar(value="dashboard")
        self._frames = {}
        self._nav_btns = {}
 
        self._build_layout()
        self._show_section("dashboard")
 
    # ── Layout ────────────────────────────────
    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=C["sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
 
        # Brand header
        brand = tk.Frame(self.sidebar, bg=C["accent"], pady=18)
        brand.pack(fill="x")
        tk.Label(brand, text="🎓", font=("Segoe UI Emoji", 22), bg=C["accent"],
                 fg=C["white"]).pack()
        tk.Label(brand, text="CMS", font=("Segoe UI", 14, "bold"),
                 bg=C["accent"], fg=C["white"]).pack()
        tk.Label(brand, text="College Portal", font=("Segoe UI", 8),
                 bg=C["accent"], fg="#DBEAFE").pack()
 
        tk.Frame(self.sidebar, height=12, bg=C["sidebar"]).pack()
 
        # Nav buttons
        for icon, label, key in NAV_ITEMS:
            btn = tk.Button(
                self.sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                font=("Segoe UI", 10),
                bg=C["sidebar"], fg=C["text2"],
                activebackground=C["hover"], activeforeground=C["text"],
                relief="flat", cursor="hand2", padx=14, pady=10,
                command=lambda k=key: self._show_section(k)
            )
            btn.pack(fill="x", padx=6, pady=2)
            self._nav_btns[key] = btn
 
        # Bottom info
        tk.Frame(self.sidebar, bg=C["sidebar"]).pack(expand=True, fill="y")
        tk.Label(self.sidebar, text="© 2024 College CMS", font=("Segoe UI", 7),
                 bg=C["sidebar"], fg=C["text2"]).pack(pady=8)
 
        # Main content area
        self.content = tk.Frame(self, bg=C["bg"])
        self.content.pack(side="left", fill="both", expand=True)
 
        # Build all sections
        builders = {
            "dashboard":   DashboardFrame,
            "students":    StudentsFrame,
            "faculty":     FacultyFrame,
            "courses":     CoursesFrame,
            "departments": DepartmentsFrame,
            "attendance":  AttendanceFrame,
            "exams":       ExamsFrame,
            "fees":        FeesFrame,
        }
        for key, cls in builders.items():
            f = cls(self.content, self)
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._frames[key] = f
 
    def _show_section(self, key):
        # Update nav highlight
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.config(bg=C["accent"], fg=C["white"])
            else:
                btn.config(bg=C["sidebar"], fg=C["text2"])
 
        self._frames[key].tkraise()
        self._frames[key].refresh()
 
 
# ─────────────────────────────────────────────
#  BASE FRAME
# ─────────────────────────────────────────────
class BaseFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
 
    def refresh(self):
        pass
 
    # ── Reusable widgets ─────────────────────
    def _page_title(self, parent, icon, title, subtitle=""):
        hdr = tk.Frame(parent, bg=C["bg"], pady=18)
        hdr.pack(fill="x", padx=28)
        tk.Label(hdr, text=f"{icon}  {title}",
                 font=("Segoe UI", 20, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(side="left")
        if subtitle:
            tk.Label(hdr, text=subtitle,
                     font=("Segoe UI", 9),
                     bg=C["bg"], fg=C["text2"]).pack(side="left", padx=14, pady=6)
 
    def _card(self, parent, **kwargs):
        f = tk.Frame(parent, bg=C["card"],
                     highlightbackground=C["border"],
                     highlightthickness=1, **kwargs)
        return f
 
    def _btn(self, parent, text, cmd, color=None, **kwargs):
        color = color or C["accent"]
        b = tk.Button(parent, text=text, command=cmd,
                      bg=color, fg=C["white"],
                      font=("Segoe UI", 9, "bold"),
                      relief="flat", cursor="hand2",
                      padx=14, pady=6, **kwargs)
        b.bind("<Enter>", lambda e: b.config(bg=self._darken(color)))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b
 
    def _darken(self, hex_color):
        r,g,b = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
        r,g,b = max(0,r-25), max(0,g-25), max(0,b-25)
        return f"#{r:02x}{g:02x}{b:02x}"
 
    def _label_entry(self, parent, label, row, col=0, width=22, default=""):
        tk.Label(parent, text=label, font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text2"]).grid(row=row, column=col*2,
                 sticky="e", padx=(10,6), pady=5)
        var = tk.StringVar(value=default)
        e = tk.Entry(parent, textvariable=var, width=width,
                     bg=C["entry"], fg=C["text"],
                     insertbackground=C["text"],
                     relief="flat", font=("Segoe UI", 9))
        e.grid(row=row, column=col*2+1, sticky="w", padx=(0,14), pady=5)
        return var
 
    def _combo(self, parent, label, options, row, col=0, width=20):
        tk.Label(parent, text=label, font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text2"]).grid(row=row, column=col*2,
                 sticky="e", padx=(10,6), pady=5)
        var = tk.StringVar()
        cb = ttk.Combobox(parent, textvariable=var, values=options,
                          width=width, state="readonly",
                          font=("Segoe UI", 9))
        cb.grid(row=row, column=col*2+1, sticky="w", padx=(0,14), pady=5)
        if options:
            cb.current(0)
        return var, cb
 
    def _treeview(self, parent, columns, headings, height=14):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("CMS.Treeview",
            background=C["card"], foreground=C["text"],
            fieldbackground=C["card"], rowheight=30,
            font=("Segoe UI", 9))
        style.configure("CMS.Treeview.Heading",
            background=C["accent"], foreground=C["white"],
            font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("CMS.Treeview",
            background=[("selected", C["accent"])],
            foreground=[("selected", C["white"])])
 
        frame = tk.Frame(parent, bg=C["card"])
        tv = ttk.Treeview(frame, columns=columns, show="headings",
                          height=height, style="CMS.Treeview")
        for col, hdg in zip(columns, headings):
            tv.heading(col, text=hdg)
            tv.column(col, width=110, anchor="center")
 
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=vsb.set)
        tv.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return frame, tv
 
    def _stat_card(self, parent, icon, value, label, color):
        f = tk.Frame(parent, bg=color, padx=20, pady=16)
        tk.Label(f, text=icon, font=("Segoe UI Emoji", 22), bg=color,
                 fg=C["white"]).pack()
        tk.Label(f, text=str(value), font=("Segoe UI", 22, "bold"),
                 bg=color, fg=C["white"]).pack()
        tk.Label(f, text=label, font=("Segoe UI", 9),
                 bg=color, fg="#DBEAFE").pack()
        return f
 
    def _get_depts(self):
        conn = get_conn()
        rows = conn.execute("SELECT id, name FROM departments ORDER BY name").fetchall()
        conn.close()
        return rows   # [(id, name), ...]
 
    def _get_courses(self):
        conn = get_conn()
        rows = conn.execute("SELECT id, code || ' - ' || name FROM courses ORDER BY code").fetchall()
        conn.close()
        return rows
 
 
# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────
class DashboardFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()
 
    def _build(self):
        self._page_title(self, "🏠", "Dashboard", "Welcome to College Management System")
        self._stats_row = tk.Frame(self, bg=C["bg"])
        self._stats_row.pack(fill="x", padx=28, pady=(0,18))
        self._charts_row = tk.Frame(self, bg=C["bg"])
        self._charts_row.pack(fill="both", expand=True, padx=28, pady=(0,18))
 
    def refresh(self):
        for w in self._stats_row.winfo_children():
            w.destroy()
        for w in self._charts_row.winfo_children():
            w.destroy()
        self._load_stats()
        self._load_recent()
 
    def _load_stats(self):
        conn = get_conn()
        ns = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        nf = conn.execute("SELECT COUNT(*) FROM faculty").fetchone()[0]
        nc = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        nd = conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
        fees_due = conn.execute("SELECT COUNT(*) FROM fees WHERE status='Pending'").fetchone()[0]
        conn.close()
 
        stats = [
            ("🎓", ns, "Students",    C["accent"]),
            ("👨‍🏫", nf, "Faculty",   C["accent2"]),
            ("📚", nc, "Courses",     C["accent5"]),
            ("🏛️", nd, "Departments", C["accent3"]),
            ("💰", fees_due, "Fees Due",  C["accent4"]),
        ]
        for icon, val, lbl, col in stats:
            card = self._stat_card(self._stats_row, icon, val, lbl, col)
            card.pack(side="left", expand=True, fill="both", padx=6, pady=4)
 
    def _load_recent(self):
        # Recent students
        left = self._card(self._charts_row)
        left.pack(side="left", fill="both", expand=True, padx=(0,8))
 
        tk.Label(left, text="📋  Recent Students", font=("Segoe UI", 11, "bold"),
                 bg=C["card"], fg=C["text"], pady=10).pack(fill="x", padx=14)
 
        cols = ("roll","name","dept","sem")
        hdgs = ("Roll No", "Name", "Dept", "Sem")
        tf, tv = self._treeview(left, cols, hdgs, height=8)
        tf.pack(fill="both", expand=True, padx=10, pady=(0,10))
 
        conn = get_conn()
        rows = conn.execute("""
            SELECT s.roll_no, s.name, d.code, s.semester
            FROM students s LEFT JOIN departments d ON s.dept_id=d.id
            ORDER BY s.id DESC LIMIT 10
        """).fetchall()
        conn.close()
        for r in rows:
            tv.insert("", "end", values=r)
 
        # Quick actions
        right = self._card(self._charts_row)
        right.pack(side="left", fill="both", expand=True, padx=(8,0))
        tk.Label(right, text="⚡  Quick Actions", font=("Segoe UI", 11, "bold"),
                 bg=C["card"], fg=C["text"], pady=10).pack(fill="x", padx=14)
 
        actions = [
            ("➕  Add New Student",  "students",    C["accent"]),
            ("➕  Add Faculty",      "faculty",     C["accent2"]),
            ("📋  Mark Attendance",  "attendance",  C["accent3"]),
            ("📝  Enter Marks",      "exams",       C["accent5"]),
            ("💰  Record Fee",       "fees",        C["accent4"]),
            ("📚  Manage Courses",   "courses",     "#64748B"),
        ]
        for txt, section, col in actions:
            self._btn(right, txt,
                      lambda s=section: self.app._show_section(s),
                      color=col).pack(fill="x", padx=14, pady=5)
 
        # Today's date info
        tk.Frame(right, height=1, bg=C["border"]).pack(fill="x", padx=14, pady=8)
        today = datetime.now().strftime("%A, %d %B %Y")
        tk.Label(right, text=f"📅  {today}", font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text2"]).pack(pady=(0,12))
 
 
# ─────────────────────────────────────────────
#  STUDENTS
# ─────────────────────────────────────────────
class StudentsFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._sel_id = None
        self._build()
 
    def _build(self):
        self._page_title(self, "🎓", "Students", "Manage student records")
 
        top = tk.Frame(self, bg=C["bg"])
        top.pack(fill="x", padx=28, pady=(0,10))
 
        # Search
        self._search_var = tk.StringVar()
        se = tk.Entry(top, textvariable=self._search_var, width=30,
                      bg=C["entry"], fg=C["text"], insertbackground=C["text"],
                      relief="flat", font=("Segoe UI", 10))
        se.pack(side="left", ipady=6, padx=(0,8))
        se.insert(0, "🔍  Search students...")
        se.bind("<FocusIn>", lambda e: se.delete(0,"end") if se.get().startswith("🔍") else None)
        self._search_var.trace_add("write", lambda *_: self._load_table())
 
        self._btn(top, "➕ Add Student", self._open_add).pack(side="left", padx=4)
        self._btn(top, "✏️ Edit",        self._open_edit, color=C["accent3"]).pack(side="left", padx=4)
        self._btn(top, "🗑️ Delete",     self._delete,    color=C["accent4"]).pack(side="left", padx=4)
        self._btn(top, "🔄 Refresh",    self.refresh,    color="#64748B").pack(side="left", padx=4)
 
        cols = ("roll","name","gender","dept","sem","phone","email","admission")
        hdgs = ("Roll No","Name","Gender","Dept","Semester","Phone","Email","Admission")
        tf, self._tv = self._treeview(self, cols, hdgs, height=18)
        tf.pack(fill="both", expand=True, padx=28, pady=(0,18))
        self._tv.bind("<<TreeviewSelect>>", lambda e: self._on_select())
 
    def _on_select(self):
        sel = self._tv.selection()
        self._sel_id = sel[0] if sel else None
 
    def _load_table(self):
        self._tv.delete(*self._tv.get_children())
        q = self._search_var.get().strip()
        if q.startswith("🔍"):
            q = ""
        conn = get_conn()
        sql = """
            SELECT s.id, s.roll_no, s.name, s.gender, d.code, s.semester,
                   s.phone, s.email, s.admission
            FROM students s LEFT JOIN departments d ON s.dept_id=d.id
            WHERE s.name LIKE ? OR s.roll_no LIKE ?
            ORDER BY s.roll_no
        """
        rows = conn.execute(sql, (f"%{q}%", f"%{q}%")).fetchall()
        conn.close()
        for r in rows:
            iid = self._tv.insert("", "end",
                values=(r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8]))
            self._tv.item(iid, tags=(str(r[0]),))
 
    def refresh(self):
        self._load_table()
 
    def _get_selected_db_id(self):
        sel = self._tv.selection()
        if not sel:
            return None
        return int(self._tv.item(sel[0], "tags")[0])
 
    def _open_add(self):
        StudentDialog(self, None)
 
    def _open_edit(self):
        db_id = self._get_selected_db_id()
        if not db_id:
            messagebox.showwarning("Select", "Please select a student first.")
            return
        StudentDialog(self, db_id)
 
    def _delete(self):
        db_id = self._get_selected_db_id()
        if not db_id:
            messagebox.showwarning("Select", "Please select a student.")
            return
        if messagebox.askyesno("Confirm", "Delete this student?"):
            conn = get_conn()
            conn.execute("DELETE FROM students WHERE id=?", (db_id,))
            conn.commit()
            conn.close()
            self._load_table()
 
 
class StudentDialog(tk.Toplevel):
    def __init__(self, parent_frame, student_id):
        super().__init__()
        self.pf = parent_frame
        self.sid = student_id
        self.title("Add Student" if student_id is None else "Edit Student")
        self.geometry("600x520")
        self.configure(bg=C["card"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if student_id:
            self._load(student_id)
 
    def _build(self):
        tk.Label(self, text="Student Information",
                 font=("Segoe UI", 13, "bold"),
                 bg=C["card"], fg=C["text"]).pack(pady=14)
 
        f = tk.Frame(self, bg=C["card"])
        f.pack(padx=20, pady=4)
 
        depts = self.pf._get_depts()
        dept_names = [d[1] for d in depts]
        self._dept_map = {d[1]: d[0] for d in depts}
 
        self._roll    = self.pf._label_entry(f, "Roll No *",    0, 0)
        self._name    = self.pf._label_entry(f, "Full Name *",  0, 1)
        self._email   = self.pf._label_entry(f, "Email",        1, 0)
        self._phone   = self.pf._label_entry(f, "Phone",        1, 1)
        self._dob     = self.pf._label_entry(f, "Date of Birth", 2, 0, default="YYYY-MM-DD")
        self._addr    = self.pf._label_entry(f, "Address",      2, 1, width=22)
        self._adm     = self.pf._label_entry(f, "Admission Date", 3, 0, default=str(date.today()))
 
        self._dept_var, _ = self.pf._combo(f, "Department",  dept_names, 3, 1)
        self._sem_var,  _ = self.pf._combo(f, "Semester",    [str(i) for i in range(1,9)], 4, 0)
        self._gen_var,  _ = self.pf._combo(f, "Gender",      ["Male","Female","Other"], 4, 1)
 
        bf = tk.Frame(self, bg=C["card"])
        bf.pack(pady=18)
        self.pf._btn(bf, "💾 Save", self._save).pack(side="left", padx=8)
        self.pf._btn(bf, "✖ Cancel", self.destroy, color="#64748B").pack(side="left", padx=8)
 
    def _load(self, sid):
        conn = get_conn()
        r = conn.execute("""
            SELECT s.roll_no,s.name,s.email,s.phone,s.dob,s.address,s.admission,
                   d.name,s.semester,s.gender
            FROM students s LEFT JOIN departments d ON s.dept_id=d.id
            WHERE s.id=?""", (sid,)).fetchone()
        conn.close()
        if r:
            self._roll.set(r[0]); self._name.set(r[1])
            self._email.set(r[2] or ""); self._phone.set(r[3] or "")
            self._dob.set(r[4] or ""); self._addr.set(r[5] or "")
            self._adm.set(r[6] or "")
            if r[7]: self._dept_var.set(r[7])
            self._sem_var.set(str(r[8]))
            if r[9]: self._gen_var.set(r[9])
 
    def _save(self):
        roll = self._roll.get().strip()
        name = self._name.get().strip()
        if not roll or not name:
            messagebox.showerror("Error", "Roll No and Name are required.", parent=self)
            return
        dept_id = self._dept_map.get(self._dept_var.get())
        try:
            conn = get_conn()
            if self.sid is None:
                conn.execute("""
                    INSERT INTO students(roll_no,name,email,phone,dob,address,admission,dept_id,semester,gender)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (roll,name,self._email.get(),self._phone.get(),
                     self._dob.get(),self._addr.get(),self._adm.get(),
                     dept_id,int(self._sem_var.get()),self._gen_var.get()))
            else:
                conn.execute("""
                    UPDATE students SET roll_no=?,name=?,email=?,phone=?,dob=?,address=?,
                    admission=?,dept_id=?,semester=?,gender=? WHERE id=?""",
                    (roll,name,self._email.get(),self._phone.get(),
                     self._dob.get(),self._addr.get(),self._adm.get(),
                     dept_id,int(self._sem_var.get()),self._gen_var.get(),self.sid))
            conn.commit()
            conn.close()
            self.pf.refresh()
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Roll No already exists.", parent=self)
 
 
# ─────────────────────────────────────────────
#  FACULTY
# ─────────────────────────────────────────────
class FacultyFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()
 
    def _build(self):
        self._page_title(self, "👨‍🏫", "Faculty", "Manage faculty members")
 
        top = tk.Frame(self, bg=C["bg"])
        top.pack(fill="x", padx=28, pady=(0,10))
        self._search_var = tk.StringVar()
        se = tk.Entry(top, textvariable=self._search_var, width=30,
                      bg=C["entry"], fg=C["text"], insertbackground=C["text"],
                      relief="flat", font=("Segoe UI", 10))
        se.pack(side="left", ipady=6, padx=(0,8))
        self._search_var.trace_add("write", lambda *_: self._load_table())
        self._btn(top, "➕ Add Faculty",  self._open_add).pack(side="left", padx=4)
        self._btn(top, "✏️ Edit",        self._open_edit, color=C["accent3"]).pack(side="left", padx=4)
        self._btn(top, "🗑️ Delete",      self._delete,    color=C["accent4"]).pack(side="left", padx=4)
 
        cols = ("emp_id","name","designation","dept","email","phone","joining")
        hdgs = ("Emp ID","Name","Designation","Department","Email","Phone","Joining")
        tf, self._tv = self._treeview(self, cols, hdgs, height=18)
        tf.pack(fill="both", expand=True, padx=28, pady=(0,18))
 
    def _load_table(self):
        self._tv.delete(*self._tv.get_children())
        q = self._search_var.get().strip()
        conn = get_conn()
        rows = conn.execute("""
            SELECT f.id, f.emp_id, f.name, f.designation, d.name, f.email, f.phone, f.joining
            FROM faculty f LEFT JOIN departments d ON f.dept_id=d.id
            WHERE f.name LIKE ? OR f.emp_id LIKE ?
            ORDER BY f.emp_id
        """, (f"%{q}%", f"%{q}%")).fetchall()
        conn.close()
        for r in rows:
            iid = self._tv.insert("", "end", values=r[1:])
            self._tv.item(iid, tags=(str(r[0]),))
 
    def refresh(self):
        self._load_table()
 
    def _get_selected_db_id(self):
        sel = self._tv.selection()
        if not sel: return None
        return int(self._tv.item(sel[0], "tags")[0])
 
    def _open_add(self):   FacultyDialog(self, None)
    def _open_edit(self):
        db_id = self._get_selected_db_id()
        if not db_id:
            messagebox.showwarning("Select", "Please select a faculty member.")
            return
        FacultyDialog(self, db_id)
 
    def _delete(self):
        db_id = self._get_selected_db_id()
        if not db_id:
            messagebox.showwarning("Select", "Please select a faculty member.")
            return
        if messagebox.askyesno("Confirm", "Delete this faculty member?"):
            conn = get_conn()
            conn.execute("DELETE FROM faculty WHERE id=?", (db_id,))
            conn.commit(); conn.close()
            self._load_table()
 
 
class FacultyDialog(tk.Toplevel):
    def __init__(self, pf, fid):
        super().__init__()
        self.pf = pf; self.fid = fid
        self.title("Add Faculty" if fid is None else "Edit Faculty")
        self.geometry("580x440")
        self.configure(bg=C["card"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if fid: self._load(fid)
 
    def _build(self):
        tk.Label(self, text="Faculty Information",
                 font=("Segoe UI", 13, "bold"),
                 bg=C["card"], fg=C["text"]).pack(pady=14)
        f = tk.Frame(self, bg=C["card"])
        f.pack(padx=20)
        depts = self.pf._get_depts()
        self._dept_map = {d[1]: d[0] for d in depts}
        designations = ["Professor","Associate Professor","Assistant Professor","Lecturer","HOD"]
 
        self._emp   = self.pf._label_entry(f, "Emp ID *",       0, 0)
        self._name  = self.pf._label_entry(f, "Full Name *",    0, 1)
        self._email = self.pf._label_entry(f, "Email",          1, 0)
        self._phone = self.pf._label_entry(f, "Phone",          1, 1)
        self._join  = self.pf._label_entry(f, "Joining Date",   2, 0, default=str(date.today()))
        self._dept_var,_ = self.pf._combo(f, "Department", [d[1] for d in depts], 2, 1)
        self._des_var,_  = self.pf._combo(f, "Designation", designations, 3, 0)
 
        bf = tk.Frame(self, bg=C["card"]); bf.pack(pady=18)
        self.pf._btn(bf, "💾 Save", self._save).pack(side="left", padx=8)
        self.pf._btn(bf, "✖ Cancel", self.destroy, color="#64748B").pack(side="left", padx=8)
 
    def _load(self, fid):
        conn = get_conn()
        r = conn.execute("""
            SELECT f.emp_id,f.name,f.email,f.phone,f.joining,d.name,f.designation
            FROM faculty f LEFT JOIN departments d ON f.dept_id=d.id WHERE f.id=?
        """, (fid,)).fetchone()
        conn.close()
        if r:
            self._emp.set(r[0]); self._name.set(r[1])
            self._email.set(r[2] or ""); self._phone.set(r[3] or "")
            self._join.set(r[4] or "")
            if r[5]: self._dept_var.set(r[5])
            if r[6]: self._des_var.set(r[6])
 
    def _save(self):
        emp = self._emp.get().strip(); name = self._name.get().strip()
        if not emp or not name:
            messagebox.showerror("Error", "Emp ID and Name required.", parent=self); return
        dept_id = self._dept_map.get(self._dept_var.get())
        try:
            conn = get_conn()
            if self.fid is None:
                conn.execute("INSERT INTO faculty(emp_id,name,email,phone,joining,dept_id,designation) VALUES(?,?,?,?,?,?,?)",
                             (emp,name,self._email.get(),self._phone.get(),self._join.get(),dept_id,self._des_var.get()))
            else:
                conn.execute("UPDATE faculty SET emp_id=?,name=?,email=?,phone=?,joining=?,dept_id=?,designation=? WHERE id=?",
                             (emp,name,self._email.get(),self._phone.get(),self._join.get(),dept_id,self._des_var.get(),self.fid))
            conn.commit(); conn.close()
            self.pf.refresh(); self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Emp ID already exists.", parent=self)
 
 
# ─────────────────────────────────────────────
#  COURSES
# ─────────────────────────────────────────────
class CoursesFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()
 
    def _build(self):
        self._page_title(self, "📚", "Courses", "Manage academic courses")
        top = tk.Frame(self, bg=C["bg"])
        top.pack(fill="x", padx=28, pady=(0,10))
        self._btn(top, "➕ Add Course", self._add).pack(side="left", padx=4)
        self._btn(top, "✏️ Edit",      self._edit, color=C["accent3"]).pack(side="left", padx=4)
        self._btn(top, "🗑️ Delete",   self._delete, color=C["accent4"]).pack(side="left", padx=4)
 
        cols = ("code","name","dept","credits","semester")
        hdgs = ("Code","Course Name","Department","Credits","Semester")
        tf, self._tv = self._treeview(self, cols, hdgs, height=18)
        tf.pack(fill="both", expand=True, padx=28, pady=(0,18))
 
    def _load_table(self):
        self._tv.delete(*self._tv.get_children())
        conn = get_conn()
        rows = conn.execute("""
            SELECT c.id, c.code, c.name, d.name, c.credits, c.semester
            FROM courses c LEFT JOIN departments d ON c.dept_id=d.id ORDER BY c.code
        """).fetchall()
        conn.close()
        for r in rows:
            iid = self._tv.insert("", "end", values=r[1:])
            self._tv.item(iid, tags=(str(r[0]),))
 
    def refresh(self): self._load_table()
 
    def _get_sel(self):
        sel = self._tv.selection()
        if not sel: return None
        return int(self._tv.item(sel[0], "tags")[0])
 
    def _add(self): CourseDialog(self, None)
    def _edit(self):
        i = self._get_sel()
        if not i: messagebox.showwarning("Select","Select a course."); return
        CourseDialog(self, i)
    def _delete(self):
        i = self._get_sel()
        if not i: messagebox.showwarning("Select","Select a course."); return
        if messagebox.askyesno("Confirm","Delete this course?"):
            conn = get_conn()
            conn.execute("DELETE FROM courses WHERE id=?", (i,))
            conn.commit(); conn.close(); self._load_table()
 
 
class CourseDialog(tk.Toplevel):
    def __init__(self, pf, cid):
        super().__init__()
        self.pf = pf; self.cid = cid
        self.title("Add Course" if cid is None else "Edit Course")
        self.geometry("500x340")
        self.configure(bg=C["card"])
        self.resizable(False, False); self.grab_set()
        self._build()
        if cid: self._load(cid)
 
    def _build(self):
        tk.Label(self, text="Course Information", font=("Segoe UI",13,"bold"),
                 bg=C["card"], fg=C["text"]).pack(pady=14)
        f = tk.Frame(self, bg=C["card"]); f.pack(padx=20)
        depts = self.pf._get_depts()
        self._dept_map = {d[1]: d[0] for d in depts}
        self._code = self.pf._label_entry(f, "Course Code *", 0, 0)
        self._name = self.pf._label_entry(f, "Course Name *", 0, 1)
        self._cred_var,_ = self.pf._combo(f, "Credits", ["1","2","3","4","5","6"], 1, 0, width=18)
        self._sem_var,_  = self.pf._combo(f, "Semester", [str(i) for i in range(1,9)], 1, 1, width=18)
        self._dept_var,_ = self.pf._combo(f, "Department", [d[1] for d in depts], 2, 0)
        bf = tk.Frame(self, bg=C["card"]); bf.pack(pady=18)
        self.pf._btn(bf, "💾 Save", self._save).pack(side="left", padx=8)
        self.pf._btn(bf, "✖ Cancel", self.destroy, color="#64748B").pack(side="left", padx=8)
 
    def _load(self, cid):
        conn = get_conn()
        r = conn.execute("SELECT c.code,c.name,c.credits,c.semester,d.name FROM courses c LEFT JOIN departments d ON c.dept_id=d.id WHERE c.id=?", (cid,)).fetchone()
        conn.close()
        if r:
            self._code.set(r[0]); self._name.set(r[1])
            self._cred_var.set(str(r[2])); self._sem_var.set(str(r[3]))
            if r[4]: self._dept_var.set(r[4])
 
    def _save(self):
        code = self._code.get().strip(); name = self._name.get().strip()
        if not code or not name:
            messagebox.showerror("Error","Code and Name required.",parent=self); return
        dept_id = self._dept_map.get(self._dept_var.get())
        try:
            conn = get_conn()
            if self.cid is None:
                conn.execute("INSERT INTO courses(code,name,dept_id,credits,semester) VALUES(?,?,?,?,?)",
                             (code,name,dept_id,int(self._cred_var.get()),int(self._sem_var.get())))
            else:
                conn.execute("UPDATE courses SET code=?,name=?,dept_id=?,credits=?,semester=? WHERE id=?",
                             (code,name,dept_id,int(self._cred_var.get()),int(self._sem_var.get()),self.cid))
            conn.commit(); conn.close()
            self.pf.refresh(); self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error","Course code already exists.",parent=self)
 
 
# ─────────────────────────────────────────────
#  DEPARTMENTS
# ─────────────────────────────────────────────
class DepartmentsFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()
 
    def _build(self):
        self._page_title(self, "🏛️", "Departments", "Manage college departments")
        top = tk.Frame(self, bg=C["bg"]); top.pack(fill="x", padx=28, pady=(0,10))
        self._btn(top, "➕ Add Dept", self._add).pack(side="left", padx=4)
        self._btn(top, "✏️ Edit",    self._edit, color=C["accent3"]).pack(side="left", padx=4)
        self._btn(top, "🗑️ Delete", self._delete, color=C["accent4"]).pack(side="left", padx=4)
 
        main = tk.Frame(self, bg=C["bg"]); main.pack(fill="both", expand=True, padx=28, pady=(0,18))
 
        cols = ("code","name","hod")
        hdgs = ("Code","Department Name","Head of Department")
        tf, self._tv = self._treeview(main, cols, hdgs, height=12)
        tf.pack(side="left", fill="both", expand=True, padx=(0,14))
 
        # Stats panel
        self._stat_frame = self._card(main, width=240)
        self._stat_frame.pack(side="left", fill="y")
        self._stat_frame.pack_propagate(False)
 
    def _load_table(self):
        self._tv.delete(*self._tv.get_children())
        conn = get_conn()
        rows = conn.execute("SELECT id,code,name,hod FROM departments ORDER BY name").fetchall()
        conn.close()
        for r in rows:
            iid = self._tv.insert("", "end", values=(r[1],r[2],r[3]))
            self._tv.item(iid, tags=(str(r[0]),))
        self._load_stats()
 
    def _load_stats(self):
        for w in self._stat_frame.winfo_children(): w.destroy()
        tk.Label(self._stat_frame, text="Department Stats",
                 font=("Segoe UI",10,"bold"), bg=C["card"], fg=C["text"]).pack(pady=12)
        conn = get_conn()
        rows = conn.execute("""
            SELECT d.name,
                   (SELECT COUNT(*) FROM students s WHERE s.dept_id=d.id) AS sc,
                   (SELECT COUNT(*) FROM faculty f WHERE f.dept_id=d.id) AS fc,
                   (SELECT COUNT(*) FROM courses c WHERE c.dept_id=d.id) AS cc
            FROM departments d ORDER BY d.name
        """).fetchall()
        conn.close()
        colors = [C["accent"],C["accent2"],C["accent3"],C["accent4"],C["accent5"]]
        for i, r in enumerate(rows):
            col = colors[i % len(colors)]
            sf = tk.Frame(self._stat_frame, bg=C["card"], pady=6)
            sf.pack(fill="x", padx=10, pady=4)
            tk.Label(sf, text=r[0][:18], font=("Segoe UI",9,"bold"),
                     bg=C["card"], fg=col).pack(anchor="w")
            tk.Label(sf, text=f"Students: {r[1]}  Faculty: {r[2]}  Courses: {r[3]}",
                     font=("Segoe UI",8), bg=C["card"], fg=C["text2"]).pack(anchor="w")
            tk.Frame(sf, height=1, bg=C["border"]).pack(fill="x", pady=4)
 
    def refresh(self): self._load_table()
 
    def _get_sel(self):
        sel = self._tv.selection()
        if not sel: return None
        return int(self._tv.item(sel[0], "tags")[0])
 
    def _add(self): DeptDialog(self, None)
    def _edit(self):
        i = self._get_sel()
        if not i: messagebox.showwarning("Select","Select a department."); return
        DeptDialog(self, i)
    def _delete(self):
        i = self._get_sel()
        if not i: messagebox.showwarning("Select","Select a department."); return
        if messagebox.askyesno("Confirm","Delete this department?"):
            conn = get_conn()
            conn.execute("DELETE FROM departments WHERE id=?", (i,))
            conn.commit(); conn.close(); self._load_table()
 
 
class DeptDialog(tk.Toplevel):
    def __init__(self, pf, did):
        super().__init__()
        self.pf = pf; self.did = did
        self.title("Add Department" if did is None else "Edit Department")
        self.geometry("440x260")
        self.configure(bg=C["card"]); self.resizable(False, False); self.grab_set()
        self._build()
        if did: self._load(did)
 
    def _build(self):
        tk.Label(self, text="Department Information", font=("Segoe UI",13,"bold"),
                 bg=C["card"], fg=C["text"]).pack(pady=14)
        f = tk.Frame(self, bg=C["card"]); f.pack(padx=20)
        self._name = self.pf._label_entry(f, "Dept Name *", 0, 0)
        self._code = self.pf._label_entry(f, "Dept Code *", 0, 1, width=10)
        self._hod  = self.pf._label_entry(f, "Head of Dept", 1, 0)
        bf = tk.Frame(self, bg=C["card"]); bf.pack(pady=18)
        self.pf._btn(bf, "💾 Save", self._save).pack(side="left", padx=8)
        self.pf._btn(bf, "✖ Cancel", self.destroy, color="#64748B").pack(side="left", padx=8)
 
    def _load(self, did):
        conn = get_conn()
        r = conn.execute("SELECT name,code,hod FROM departments WHERE id=?", (did,)).fetchone()
        conn.close()
        if r:
            self._name.set(r[0]); self._code.set(r[1]); self._hod.set(r[2] or "")
 
    def _save(self):
        name = self._name.get().strip(); code = self._code.get().strip().upper()
        if not name or not code:
            messagebox.showerror("Error","Name and Code required.",parent=self); return
        try:
            conn = get_conn()
            if self.did is None:
                conn.execute("INSERT INTO departments(name,code,hod) VALUES(?,?,?)",
                             (name, code, self._hod.get().strip()))
            else:
                conn.execute("UPDATE departments SET name=?,code=?,hod=? WHERE id=?",
                             (name, code, self._hod.get().strip(), self.did))
            conn.commit(); conn.close()
            self.pf.refresh(); self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error","Name or Code already exists.",parent=self)
 
 
# ─────────────────────────────────────────────
#  ATTENDANCE
# ─────────────────────────────────────────────
class AttendanceFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()
 
    def _build(self):
        self._page_title(self, "📋", "Attendance", "Track student attendance")
 
        ctrl = self._card(self)
        ctrl.pack(fill="x", padx=28, pady=(0,12))
 
        inner = tk.Frame(ctrl, bg=C["card"]); inner.pack(padx=14, pady=12)
 
        courses = self._get_courses()
        self._course_map = {c[1]: c[0] for c in courses}
        self._course_var, _ = self._combo(inner, "Course", [c[1] for c in courses], 0, 0)
        self._date_var = self._label_entry(inner, "Date (YYYY-MM-DD)", 0, 1,
                                           default=str(date.today()))
        self._btn(inner, "📋 Load Students", self._load_attendance,
                  color=C["accent2"]).grid(row=0, column=4, padx=14)
        self._btn(inner, "💾 Save Attendance", self._save_attendance).grid(row=0, column=5, padx=4)
 
        # Attendance list
        self._att_frame = self._card(self)
        self._att_frame.pack(fill="both", expand=True, padx=28, pady=(0,18))
        self._student_vars = {}
 
    def _load_attendance(self):
        for w in self._att_frame.winfo_children(): w.destroy()
        self._student_vars = {}
 
        course_id = self._course_map.get(self._course_var.get())
        att_date  = self._date_var.get().strip()
 
        conn = get_conn()
        students = conn.execute("""
            SELECT s.id, s.roll_no, s.name
            FROM students s ORDER BY s.roll_no
        """).fetchall()
 
        existing = {r[0]: r[1] for r in conn.execute(
            "SELECT student_id, status FROM attendance WHERE course_id=? AND date=?",
            (course_id, att_date)).fetchall()}
        conn.close()
 
        tk.Label(self._att_frame, text=f"Attendance — {self._course_var.get()} — {att_date}",
                 font=("Segoe UI",10,"bold"), bg=C["card"], fg=C["text"]).pack(pady=8)
 
        # Header
        hdr = tk.Frame(self._att_frame, bg=C["border"])
        hdr.pack(fill="x", padx=14)
        for t, w in [("Roll No",12),("Name",25),("Status",14)]:
            tk.Label(hdr, text=t, font=("Segoe UI",9,"bold"), width=w,
                     bg=C["border"], fg=C["white"]).pack(side="left", padx=4, pady=6)
 
        canvas = tk.Canvas(self._att_frame, bg=C["card"], highlightthickness=0)
        sb = ttk.Scrollbar(self._att_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=14, pady=(0,12))
 
        inner = tk.Frame(canvas, bg=C["card"])
        canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
 
        for idx, (sid, roll, name) in enumerate(students):
            row_bg = C["card"] if idx % 2 == 0 else C["hover"]
            rf = tk.Frame(inner, bg=row_bg); rf.pack(fill="x")
            tk.Label(rf, text=roll, width=12, bg=row_bg, fg=C["text"],
                     font=("Segoe UI",9)).pack(side="left", padx=4, pady=5)
            tk.Label(rf, text=name, width=25, bg=row_bg, fg=C["text"],
                     font=("Segoe UI",9), anchor="w").pack(side="left", padx=4, pady=5)
            var = tk.StringVar(value=existing.get(sid, "Present"))
            self._student_vars[sid] = var
            for status, color in [("Present", C["green"]), ("Absent", C["red"]), ("Late", C["yellow"])]:
                tk.Radiobutton(rf, text=status, variable=var, value=status,
                               bg=row_bg, fg=color, selectcolor=row_bg,
                               activebackground=row_bg,
                               font=("Segoe UI",9)).pack(side="left", padx=6)
 
    def _save_attendance(self):
        if not self._student_vars:
            messagebox.showwarning("Warning","Load students first."); return
        course_id = self._course_map.get(self._course_var.get())
        att_date  = self._date_var.get().strip()
        conn = get_conn()
        conn.execute("DELETE FROM attendance WHERE course_id=? AND date=?", (course_id, att_date))
        for sid, var in self._student_vars.items():
            conn.execute("INSERT INTO attendance(student_id,course_id,date,status) VALUES(?,?,?,?)",
                         (sid, course_id, att_date, var.get()))
        conn.commit(); conn.close()
        messagebox.showinfo("Saved", f"Attendance saved for {att_date}.")
 
    def refresh(self): pass
 
 
# ─────────────────────────────────────────────
#  EXAMS
# ─────────────────────────────────────────────
class ExamsFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()
 
    def _build(self):
        self._page_title(self, "📝", "Exams & Marks", "Record and view exam results")
 
        left = tk.Frame(self, bg=C["bg"])
        left.pack(side="left", fill="y", padx=(28,8), pady=(0,18))
 
        # Entry form
        form = self._card(left); form.pack(fill="x", pady=(0,12))
        tk.Label(form, text="Enter Marks", font=("Segoe UI",10,"bold"),
                 bg=C["card"], fg=C["text"]).pack(pady=10, padx=14, anchor="w")
 
        fg = tk.Frame(form, bg=C["card"]); fg.pack(padx=14, pady=(0,12))
 
        students = self._get_students()
        courses  = self._get_courses()
        self._stu_map = {s[1]: s[0] for s in students}
        self._crs_map = {c[1]: c[0] for c in courses}
 
        self._stu_var,_ = self._combo(fg, "Student", [s[1] for s in students], 0, 0, width=26)
        self._crs_var,_ = self._combo(fg, "Course",  [c[1] for c in courses],  1, 0, width=26)
        self._typ_var,_ = self._combo(fg, "Exam Type",
                                      ["Mid-Term","Final","Internal","Assignment","Quiz"], 2, 0, width=26)
        self._marks_var = self._label_entry(fg, "Marks Obtained", 3, 0, width=26)
        self._max_var   = self._label_entry(fg, "Max Marks",      4, 0, width=26, default="100")
        self._date_var  = self._label_entry(fg, "Exam Date",      5, 0, width=26, default=str(date.today()))
 
        self._btn(fg, "💾 Save Marks", self._save_marks).grid(row=6, column=1, pady=12, sticky="w")
 
        # Summary card
        sum_card = self._card(left); sum_card.pack(fill="both", expand=True)
        tk.Label(sum_card, text="Student Summary", font=("Segoe UI",10,"bold"),
                 bg=C["card"], fg=C["text"]).pack(pady=10, padx=14, anchor="w")
        self._stu_var.trace_add("write", lambda *_: self._load_summary())
        self._sum_label = tk.Label(sum_card, text="Select a student to view summary.",
                                   font=("Segoe UI",9), bg=C["card"], fg=C["text2"],
                                   justify="left", padx=14)
        self._sum_label.pack(anchor="w", pady=4)
 
        # Results table
        right = tk.Frame(self, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True, pady=(0,18), padx=(0,28))
 
        tk.Label(right, text="All Exam Records", font=("Segoe UI",11,"bold"),
                 bg=C["bg"], fg=C["text"]).pack(pady=8, anchor="w")
        self._btn(right, "🔄 Refresh", self.refresh, color="#64748B").pack(anchor="w", pady=(0,8))
 
        cols = ("student","course","type","marks","max","pct","date")
        hdgs = ("Student","Course","Type","Marks","Max","Percentage","Date")
        tf, self._tv = self._treeview(right, cols, hdgs, height=18)
        tf.pack(fill="both", expand=True)
 
    def _get_students(self):
        conn = get_conn()
        rows = conn.execute("SELECT id, roll_no || ' - ' || name FROM students ORDER BY roll_no").fetchall()
        conn.close(); return rows
 
    def _load_summary(self):
        stu_label = self._stu_var.get()
        sid = self._stu_map.get(stu_label)
        if not sid: return
        conn = get_conn()
        rows = conn.execute("""
            SELECT e.exam_type, AVG(e.marks), AVG(e.max_marks), COUNT(*)
            FROM exams e WHERE e.student_id=? GROUP BY e.exam_type
        """, (sid,)).fetchall()
        conn.close()
        if not rows:
            self._sum_label.config(text="No records found."); return
        txt = ""
        for r in rows:
            pct = (r[1]/r[2]*100) if r[2] else 0
            grade = "A+" if pct>=90 else "A" if pct>=80 else "B" if pct>=70 else "C" if pct>=60 else "D" if pct>=50 else "F"
            txt += f"{r[0]:15s}  Avg: {r[1]:.1f}/{r[2]:.0f}  ({pct:.1f}%)  Grade: {grade}\n"
        self._sum_label.config(text=txt)
 
    def _load_table(self):
        self._tv.delete(*self._tv.get_children())
        conn = get_conn()
        rows = conn.execute("""
            SELECT s.name, c.code, e.exam_type, e.marks, e.max_marks, e.exam_date
            FROM exams e
            JOIN students s ON e.student_id=s.id
            JOIN courses  c ON e.course_id=c.id
            ORDER BY e.exam_date DESC
        """).fetchall()
        conn.close()
        for r in rows:
            pct = f"{(r[3]/r[4]*100):.1f}%" if r[4] else "-"
            self._tv.insert("", "end", values=(r[0],r[1],r[2],r[3],r[4],pct,r[5]))
 
    def _save_marks(self):
        sid = self._stu_map.get(self._stu_var.get())
        cid = self._crs_map.get(self._crs_var.get())
        try:
            marks = float(self._marks_var.get())
            max_m = float(self._max_var.get())
        except ValueError:
            messagebox.showerror("Error","Marks must be numeric."); return
        conn = get_conn()
        conn.execute("INSERT INTO exams(student_id,course_id,exam_type,marks,max_marks,exam_date) VALUES(?,?,?,?,?,?)",
                     (sid,cid,self._typ_var.get(),marks,max_m,self._date_var.get()))
        conn.commit(); conn.close()
        messagebox.showinfo("Saved","Marks saved.")
        self._load_table(); self._load_summary()
 
    def refresh(self): self._load_table()
 
 
# ─────────────────────────────────────────────
#  FEES
# ─────────────────────────────────────────────
class FeesFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()
 
    def _build(self):
        self._page_title(self, "💰", "Fee Management", "Track student fees and payments")
 
        top = tk.Frame(self, bg=C["bg"]); top.pack(fill="x", padx=28, pady=(0,10))
        self._btn(top, "➕ Add Fee Record", self._add).pack(side="left", padx=4)
        self._btn(top, "✅ Mark Paid",      self._mark_paid, color=C["accent2"]).pack(side="left", padx=4)
        self._btn(top, "🔄 Refresh",       self.refresh, color="#64748B").pack(side="left", padx=4)
 
        # Summary bar
        self._sum_frame = tk.Frame(self, bg=C["bg"])
        self._sum_frame.pack(fill="x", padx=28, pady=(0,8))
 
        cols = ("student","desc","amount","paid","balance","due","status")
        hdgs = ("Student","Description","Amount","Paid","Balance","Due Date","Status")
        tf, self._tv = self._treeview(self, cols, hdgs, height=16)
        tf.pack(fill="both", expand=True, padx=28, pady=(0,18))
 
    def _load_table(self):
        self._tv.delete(*self._tv.get_children())
        for w in self._sum_frame.winfo_children(): w.destroy()
 
        conn = get_conn()
        rows = conn.execute("""
            SELECT f.id, s.name, f.description, f.amount, f.paid, f.due_date, f.status
            FROM fees f JOIN students s ON f.student_id=s.id ORDER BY f.status, s.name
        """).fetchall()
        totals = conn.execute("SELECT SUM(amount), SUM(paid) FROM fees").fetchone()
        conn.close()
 
        total  = totals[0] or 0
        paid   = totals[1] or 0
        unpaid = total - paid
 
        # Summary cards
        for lbl, val, col in [
            ("Total Fees", f"₹{total:,.0f}", C["accent"]),
            ("Collected",  f"₹{paid:,.0f}",  C["green"]),
            ("Pending",    f"₹{unpaid:,.0f}", C["red"]),
        ]:
            f = tk.Frame(self._sum_frame, bg=col, padx=20, pady=8)
            f.pack(side="left", padx=6)
            tk.Label(f, text=val, font=("Segoe UI",14,"bold"), bg=col, fg=C["white"]).pack()
            tk.Label(f, text=lbl, font=("Segoe UI",8), bg=col, fg="#DBEAFE").pack()
 
        for r in rows:
            bal = (r[3] or 0) - (r[4] or 0)
            tag = "paid" if r[6] == "Paid" else "pending"
            iid = self._tv.insert("", "end",
                values=(r[1], r[2], f"₹{r[3]:,.0f}", f"₹{r[4]:,.0f}",
                        f"₹{bal:,.0f}", r[5], r[6]), tags=(str(r[0]), tag))
        self._tv.tag_configure("paid",    foreground=C["green"])
        self._tv.tag_configure("pending", foreground=C["yellow"])
 
    def refresh(self): self._load_table()
 
    def _get_sel_fee_id(self):
        sel = self._tv.selection()
        if not sel: return None
        return int(self._tv.item(sel[0], "tags")[0])
 
    def _add(self): FeeDialog(self)
    def _mark_paid(self):
        fid = self._get_sel_fee_id()
        if not fid: messagebox.showwarning("Select","Select a fee record."); return
        conn = get_conn()
        r = conn.execute("SELECT amount FROM fees WHERE id=?", (fid,)).fetchone()
        conn.execute("UPDATE fees SET paid=?,status='Paid',paid_date=? WHERE id=?",
                     (r[0], str(date.today()), fid))
        conn.commit(); conn.close()
        self._load_table()
 
 
class FeeDialog(tk.Toplevel):
    def __init__(self, pf):
        super().__init__()
        self.pf = pf
        self.title("Add Fee Record")
        self.geometry("480x320")
        self.configure(bg=C["card"]); self.resizable(False, False); self.grab_set()
        self._build()
 
    def _build(self):
        tk.Label(self, text="Fee Record", font=("Segoe UI",13,"bold"),
                 bg=C["card"], fg=C["text"]).pack(pady=14)
        f = tk.Frame(self, bg=C["card"]); f.pack(padx=20)
 
        conn = get_conn()
        students = conn.execute("SELECT id, roll_no || ' - ' || name FROM students ORDER BY roll_no").fetchall()
        conn.close()
        self._stu_map = {s[1]: s[0] for s in students}
        self._stu_var,_ = self.pf._combo(f, "Student", [s[1] for s in students], 0, 0, width=28)
        self._desc  = self.pf._label_entry(f, "Description", 1, 0, width=28, default="Annual Tuition Fee")
        self._amt   = self.pf._label_entry(f, "Amount (₹)",  2, 0, width=28, default="45000")
        self._due   = self.pf._label_entry(f, "Due Date",    3, 0, width=28, default=str(date.today()))
 
        bf = tk.Frame(self, bg=C["card"]); bf.pack(pady=18)
        self.pf._btn(bf, "💾 Save", self._save).pack(side="left", padx=8)
        self.pf._btn(bf, "✖ Cancel", self.destroy, color="#64748B").pack(side="left", padx=8)
 
    def _save(self):
        sid = self._stu_map.get(self._stu_var.get())
        try:
            amt = float(self._amt.get())
        except ValueError:
            messagebox.showerror("Error","Amount must be numeric.",parent=self); return
        conn = get_conn()
        conn.execute("INSERT INTO fees(student_id,amount,paid,due_date,status,description) VALUES(?,?,?,?,?,?)",
                     (sid, amt, 0, self._due.get(), "Pending", self._desc.get()))
        conn.commit(); conn.close()
        self.pf.refresh(); self.destroy()
 
 
# ─────────────────────────────────────────────
#  LOGIN SCREEN
# ─────────────────────────────────────────────
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("College Management System — Login")
        self.geometry("420x500")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self._build()
 
    def _build(self):
        tk.Frame(self, height=50, bg=C["bg"]).pack()
 
        # Brand
        brand = tk.Frame(self, bg=C["accent"], padx=40, pady=24)
        brand.pack(padx=60)
        tk.Label(brand, text="🎓", font=("Segoe UI Emoji", 36), bg=C["accent"],
                 fg=C["white"]).pack()
        tk.Label(brand, text="College Management System",
                 font=("Segoe UI", 12, "bold"), bg=C["accent"], fg=C["white"]).pack()
        tk.Label(brand, text="Administrator Portal",
                 font=("Segoe UI", 9), bg=C["accent"], fg="#DBEAFE").pack()
 
        form = tk.Frame(self, bg=C["card"], padx=30, pady=24)
        form.pack(padx=60, pady=20, fill="x")
 
        tk.Label(form, text="Username", font=("Segoe UI",9),
                 bg=C["card"], fg=C["text2"]).pack(anchor="w")
        self._user = tk.Entry(form, font=("Segoe UI",11),
                              bg=C["entry"], fg=C["text"],
                              insertbackground=C["text"], relief="flat")
        self._user.pack(fill="x", ipady=8, pady=(2,14))
        self._user.insert(0, "admin")
 
        tk.Label(form, text="Password", font=("Segoe UI",9),
                 bg=C["card"], fg=C["text2"]).pack(anchor="w")
        self._pw = tk.Entry(form, show="●", font=("Segoe UI",11),
                            bg=C["entry"], fg=C["text"],
                            insertbackground=C["text"], relief="flat")
        self._pw.pack(fill="x", ipady=8, pady=(2,18))
        self._pw.insert(0, "admin123")
        self._pw.bind("<Return>", lambda e: self._login())
 
        self._err = tk.Label(form, text="", font=("Segoe UI",9),
                             bg=C["card"], fg=C["red"])
        self._err.pack()
 
        login_btn = tk.Button(form, text="LOGIN →",
                              command=self._login,
                              bg=C["accent"], fg=C["white"],
                              font=("Segoe UI", 11, "bold"),
                              relief="flat", cursor="hand2", pady=10)
        login_btn.pack(fill="x", pady=(6,0))
 
        tk.Label(self, text="Default: admin / admin123",
                 font=("Segoe UI",8), bg=C["bg"], fg=C["text2"]).pack()
 
    def _login(self):
        username = self._user.get().strip()
        password = hashlib.sha256(self._pw.get().encode()).hexdigest()
        conn = get_conn()
        row = conn.execute("SELECT id FROM users WHERE username=? AND password=?",
                           (username, password)).fetchone()
        conn.close()
        if row:
            self.destroy()
            app = CollegeApp()
            app.mainloop()
        else:
            self._err.config(text="❌  Invalid username or password")
 
 
# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    win = LoginWindow()
    win.mainloop()