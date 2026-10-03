"""
database.py
Lapisan akses data (SQLite) untuk aplikasi SPP Omah Bocil.
Semua fungsi CRUD untuk tabel: students, packages, payments.
"""

import re
import sqlite3
from contextlib import contextmanager

DB_NAME = "spp_omahbocil.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_cursor(commit=False):
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def init_db():
    """Membuat tabel jika belum ada."""
    with get_cursor(commit=True) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                jabatan TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no_akun TEXT NOT NULL UNIQUE,
                nama TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Aktif',
                mulai TEXT,
                akhir TEXT,
                paket_id INTEGER,
                jatuh_tempo INTEGER NOT NULL DEFAULT 10,
                FOREIGN KEY (paket_id) REFERENCES packages(id) ON DELETE SET NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                bulan INTEGER NOT NULL,
                tahun INTEGER NOT NULL,
                jumlah INTEGER NOT NULL DEFAULT 0,
                tgl_bayar TEXT,
                ttd TEXT,
                stempel TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(student_id, bulan, tahun)
            )
        """)

        # --- Migrasi skema: tambah kolom baru tanpa menghapus data lama ---
        cur.execute("PRAGMA table_info(students)")
        existing_cols = {row["name"] for row in cur.fetchall()}
        if "foto" not in existing_cols:
            cur.execute("ALTER TABLE students ADD COLUMN foto TEXT")
        if "asal_sekolah" not in existing_cols:
            cur.execute("ALTER TABLE students ADD COLUMN asal_sekolah TEXT")
        if "kelas" not in existing_cols:
            cur.execute("ALTER TABLE students ADD COLUMN kelas TEXT")
        if "tahun_lahir" not in existing_cols:
            cur.execute("ALTER TABLE students ADD COLUMN tahun_lahir INTEGER")


# ---------------- PACKAGES ----------------

def get_all_packages():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM packages ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


def get_package(package_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM packages WHERE id = ?", (package_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def add_package(name, price):
    with get_cursor(commit=True) as cur:
        cur.execute("INSERT INTO packages (name, price) VALUES (?, ?)", (name, price))
        return cur.lastrowid


def update_package(package_id, name, price):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE packages SET name = ?, price = ? WHERE id = ?", (name, price, package_id))


def delete_package(package_id):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE students SET paket_id = NULL WHERE paket_id = ?", (package_id,))
        cur.execute("DELETE FROM packages WHERE id = ?", (package_id,))


# ---------------- STUDENTS ----------------

def get_all_students():
    with get_cursor() as cur:
        cur.execute("""
            SELECT s.*, p.name AS paket_name, p.price AS paket_price
            FROM students s LEFT JOIN packages p ON s.paket_id = p.id
            ORDER BY s.nama
        """)
        return [dict(r) for r in cur.fetchall()]


def get_active_students():
    return [s for s in get_all_students() if s["status"] == "Aktif"]


def get_student(student_id):
    with get_cursor() as cur:
        cur.execute("""
            SELECT s.*, p.name AS paket_name, p.price AS paket_price
            FROM students s LEFT JOIN packages p ON s.paket_id = p.id
            WHERE s.id = ?
        """, (student_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def find_student_by_no_akun(no_akun, exclude_id=None):
    with get_cursor() as cur:
        if exclude_id:
            cur.execute("SELECT * FROM students WHERE no_akun = ? AND id != ?", (no_akun, exclude_id))
        else:
            cur.execute("SELECT * FROM students WHERE no_akun = ?", (no_akun,))
        row = cur.fetchone()
        return dict(row) if row else None


def add_student(data):
    with get_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO students (no_akun, nama, status, mulai, akhir, paket_id, jatuh_tempo, foto,
                                   asal_sekolah, kelas, tahun_lahir)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data["no_akun"], data["nama"], data["status"], data.get("mulai"),
              data.get("akhir"), data.get("paket_id") or None, data["jatuh_tempo"],
              data.get("foto"), data.get("asal_sekolah"), data.get("kelas"),
              data.get("tahun_lahir")))
        return cur.lastrowid


def update_student(student_id, data):
    with get_cursor(commit=True) as cur:
        if data.get("foto") is not None:
            cur.execute("""
                UPDATE students SET no_akun=?, nama=?, status=?, mulai=?, akhir=?, paket_id=?, jatuh_tempo=?, foto=?,
                                     asal_sekolah=?, kelas=?, tahun_lahir=?
                WHERE id = ?
            """, (data["no_akun"], data["nama"], data["status"], data.get("mulai"),
                  data.get("akhir"), data.get("paket_id") or None, data["jatuh_tempo"],
                  data.get("foto"), data.get("asal_sekolah"), data.get("kelas"),
                  data.get("tahun_lahir"), student_id))
        else:
            # foto tidak diganti, pertahankan foto lama
            cur.execute("""
                UPDATE students SET no_akun=?, nama=?, status=?, mulai=?, akhir=?, paket_id=?, jatuh_tempo=?,
                                     asal_sekolah=?, kelas=?, tahun_lahir=?
                WHERE id = ?
            """, (data["no_akun"], data["nama"], data["status"], data.get("mulai"),
                  data.get("akhir"), data.get("paket_id") or None, data["jatuh_tempo"],
                  data.get("asal_sekolah"), data.get("kelas"), data.get("tahun_lahir"), student_id))


def get_next_no_akun(prefix="B", pad=3):
    """Hasilkan no akun berikutnya, format B001, B002, dst.
    Hanya melihat akun berformat prefix+angka; akun format lain diabaikan."""
    import re
    with get_cursor() as cur:
        cur.execute("SELECT no_akun FROM students")
        rows = cur.fetchall()
    max_num = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    for r in rows:
        m = pattern.match((r["no_akun"] or "").strip())
        if m:
            max_num = max(max_num, int(m.group(1)))
    next_num = max_num + 1
    return f"{prefix}{str(next_num).zfill(pad)}"


def delete_student(student_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM students WHERE id = ?", (student_id,))


# ---------------- PAYMENTS ----------------

def get_all_payments():
    with get_cursor() as cur:
        cur.execute("""
            SELECT pay.*, s.nama AS student_nama, s.no_akun
            FROM payments pay JOIN students s ON pay.student_id = s.id
        """)
        return [dict(r) for r in cur.fetchall()]


def get_payment(student_id, tahun, bulan):
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM payments WHERE student_id = ? AND tahun = ? AND bulan = ?
        """, (student_id, tahun, bulan))
        row = cur.fetchone()
        return dict(row) if row else None


def get_payment_by_id(payment_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def delete_payment(payment_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM payments WHERE id = ?", (payment_id,))


def get_payments_for_student_year(student_id, tahun):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM payments WHERE student_id = ? AND tahun = ?", (student_id, tahun))
        return [dict(r) for r in cur.fetchall()]


def get_payments_for_year(tahun):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM payments WHERE tahun = ?", (tahun,))
        return [dict(r) for r in cur.fetchall()]


def get_payments_for_month(tahun, bulan):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM payments WHERE tahun = ? AND bulan = ?", (tahun, bulan))
        return [dict(r) for r in cur.fetchall()]


def get_all_years():
    with get_cursor() as cur:
        cur.execute("SELECT DISTINCT tahun FROM payments ORDER BY tahun")
        return [r["tahun"] for r in cur.fetchall()]


def get_payments_for_student_all(student_id):
    """Seluruh riwayat pembayaran seorang siswa, diurutkan tahun & bulan."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT * FROM payments WHERE student_id = ?
            ORDER BY tahun, bulan
        """, (student_id,))
        return [dict(r) for r in cur.fetchall()]


# ---------------- ADMINS (LOGIN) ----------------

def count_admins():
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM admins")
        return cur.fetchone()["c"]


def get_admin_by_username(username):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM admins WHERE username = ?", (username,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_admin(admin_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM admins WHERE id = ?", (admin_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_admin(username, password_hash):
    with get_cursor(commit=True) as cur:
        cur.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                    (username, password_hash))
        return cur.lastrowid


def update_admin_password(admin_id, password_hash):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE admins SET password_hash = ? WHERE id = ?", (password_hash, admin_id))


# ---------------- PENERIMA IURAN SPP ----------------

def get_all_recipients():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM recipients ORDER BY nama")
        return [dict(r) for r in cur.fetchall()]


def get_recipient(recipient_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM recipients WHERE id = ?", (recipient_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def add_recipient(nama, jabatan):
    with get_cursor(commit=True) as cur:
        cur.execute("INSERT INTO recipients (nama, jabatan) VALUES (?, ?)", (nama, jabatan))
        return cur.lastrowid


def update_recipient(recipient_id, nama, jabatan):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE recipients SET nama = ?, jabatan = ? WHERE id = ?",
                    (nama, jabatan, recipient_id))


def delete_recipient(recipient_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM recipients WHERE id = ?", (recipient_id,))


def upsert_payment(student_id, bulan, tahun, jumlah, tgl_bayar, ttd, stempel):
    with get_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO payments (student_id, bulan, tahun, jumlah, tgl_bayar, ttd, stempel)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id, bulan, tahun)
            DO UPDATE SET jumlah=excluded.jumlah, tgl_bayar=excluded.tgl_bayar,
                          ttd=excluded.ttd, stempel=excluded.stempel
        """, (student_id, bulan, tahun, jumlah, tgl_bayar, ttd, stempel))
