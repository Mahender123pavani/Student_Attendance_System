# db.py
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import date

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "sony@2003",  # <-- change if needed
    "database": "attendance_db"
}

def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print("DB connection error:", e)
        return None

def init_db():
    conn = get_connection()
    if not conn:
        print("Cannot init DB - no connection")
        return
    cur = conn.cursor()
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE,
            password_hash VARBINARY(255)
        )
    """)
    # Students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            roll_no VARCHAR(50) UNIQUE,
            name VARCHAR(255),
            department VARCHAR(100),
            year INT,
            phone VARCHAR(15),
            address VARCHAR(255)
        )
    """)
    # Attendance table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT,
            date DATE,
            status VARCHAR(20),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    # Default admin
    cur.execute("SELECT id FROM users WHERE username=%s", ("admin",))
    if not cur.fetchone():
        hashed = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt())
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", ("admin", hashed))
        conn.commit()
    cur.close()
    conn.close()

# ---------- User/Auth helpers ----------
def create_user(username: str, password: str):
    conn = get_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed))
    conn.commit()
    cur.close()
    conn.close()

def verify_user(username: str, password: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), row[0])

# ---------- Student helpers ----------
def add_student(roll_no, name, department, year, phone, address):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO students (roll_no, name, department, year, phone, address)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (roll_no, name, department, year, phone, address))
    conn.commit()
    cur.close()
    conn.close()

def get_all_students():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students ORDER BY roll_no")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows or []

def delete_student(student_id):
    conn = get_connection()
    cur = conn.cursor()
    # Delete attendance first to avoid foreign key error
    cur.execute("DELETE FROM attendance WHERE student_id=%s", (student_id,))
    cur.execute("DELETE FROM students WHERE id=%s", (student_id,))
    conn.commit()
    cur.close()
    conn.close()

def update_student(student_id, roll_no, name, department, year, phone, address):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE students 
        SET roll_no=%s, name=%s, department=%s, year=%s, phone=%s, address=%s
        WHERE id=%s
    """, (roll_no, name, department, year, phone, address, student_id))
    conn.commit()
    cur.close()
    conn.close()

# ---------- Attendance helpers ----------
def mark_attendance(student_id: int, status: str, attendance_date: date = None):
    attendance_date = attendance_date or date.today()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM attendance WHERE student_id=%s AND date=%s", (student_id, attendance_date))
    existing = cur.fetchone()
    if existing:
        cur.execute("UPDATE attendance SET status=%s, timestamp=NOW() WHERE id=%s", (status, existing[0]))
    else:
        cur.execute("INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)",
                    (student_id, attendance_date, status))
    conn.commit()
    cur.close()
    conn.close()

def mark_batch_attendance(attendance_dict):
    for student_id, status in attendance_dict.items():
        mark_attendance(student_id, status)

def get_attendance_by_date(att_date=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if att_date:
        cur.execute("""
            SELECT a.id, a.student_id, a.date, a.status, s.roll_no, s.name
            FROM attendance a
            JOIN students s ON s.id = a.student_id
            WHERE a.date=%s
            ORDER BY s.roll_no
        """, (att_date,))
    else:
        cur.execute("""
            SELECT a.id, a.student_id, a.date, a.status, s.roll_no, s.name
            FROM attendance a
            JOIN students s ON s.id = a.student_id
            ORDER BY a.date DESC, s.roll_no
        """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows or []