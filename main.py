"""
main.py
Aplikasi web SPP Omah Bocil — Flask + SQLite.
Jalankan dengan: python main.py
Lalu buka http://127.0.0.1:5000 di browser.
"""

import csv
import io
import json
import os
from datetime import date, datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                    flash, Response, session)
from werkzeug.security import generate_password_hash, check_password_hash

import database as db

app = Flask(__name__)
# Di server produksi, atur SECRET_KEY lewat environment variable, jangan hardcode.
app.secret_key = os.environ.get("SECRET_KEY", "spp-omahbocil-secret-key-ganti-ini")

MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
          "Agustus", "September", "Oktober", "November", "Desember"]

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

db.init_db()

# Buat akun admin default jika belum ada admin sama sekali.
if db.count_admins() == 0:
    db.create_admin(DEFAULT_ADMIN_USERNAME, generate_password_hash(DEFAULT_ADMIN_PASSWORD))
    print("=" * 60)
    print("Akun admin default dibuat:")
    print(f"  Username : {DEFAULT_ADMIN_USERNAME}")
    print(f"  Password : {DEFAULT_ADMIN_PASSWORD}")
    print("SEGERA login lalu ganti password di menu 'Ganti Password'.")
    print("=" * 60)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_globals():
    return {
        "MONTHS": MONTHS,
        "active_tab": request.endpoint,
        "current_admin": session.get("admin_username"),
    }


def fmt_rupiah(n):
    try:
        return "Rp " + "{:,}".format(int(n or 0)).replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"


app.jinja_env.filters["rupiah"] = fmt_rupiah


# ---------------- AUTH (LOGIN ADMIN) ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = db.get_admin_by_username(username)
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            flash("Berhasil login.", "success")
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        flash("Username atau password salah.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah logout.", "success")
    return redirect(url_for("login"))


@app.route("/ganti-password", methods=["GET", "POST"])
@login_required
def ganti_password():
    if request.method == "POST":
        password_lama = request.form.get("password_lama", "")
        password_baru = request.form.get("password_baru", "")
        konfirmasi = request.form.get("konfirmasi", "")
        admin = db.get_admin(session["admin_id"])
        if not check_password_hash(admin["password_hash"], password_lama):
            flash("Password lama salah.", "error")
        elif len(password_baru) < 6:
            flash("Password baru minimal 6 karakter.", "error")
        elif password_baru != konfirmasi:
            flash("Konfirmasi password baru tidak cocok.", "error")
        else:
            db.update_admin_password(admin["id"], generate_password_hash(password_baru))
            flash("Password berhasil diganti.", "success")
            return redirect(url_for("dashboard"))
    return render_template("ganti_password.html")


# ---------------- DASHBOARD ----------------

@app.route("/")
@login_required
def dashboard():
    today = date.today()
    y, m, d = today.year, today.month, today.day

    students = db.get_active_students()
    payments_this_month = db.get_payments_for_month(y, m)
    paid_student_ids = {p["student_id"] for p in payments_this_month}

    belum_bayar = []
    for s in students:
        jt = s["jatuh_tempo"] or 10
        if d >= jt and s["id"] not in paid_student_ids:
            belum_bayar.append(s)

    total_bulan_ini = sum(p["jumlah"] for p in payments_this_month)

    return render_template(
        "dashboard.html",
        total_siswa_aktif=len(students),
        sudah_bayar=len(payments_this_month),
        belum_bayar=belum_bayar,
        total_bulan_ini=total_bulan_ini,
        bulan_sekarang=MONTHS[m - 1],
        tahun_sekarang=y,
    )


# ---------------- SISWA ----------------

@app.route("/siswa")
@login_required
def siswa_list():
    students = db.get_all_students()
    packages = db.get_all_packages()
    edit_id = request.args.get("edit", type=int)
    edit_student = db.get_student(edit_id) if edit_id else None
    return render_template("siswa.html", students=students, packages=packages,
                            edit_student=edit_student)


@app.route("/siswa/save", methods=["POST"])
@login_required
def siswa_save():
    student_id = request.form.get("sid", type=int)
    no_akun = request.form.get("no_akun", "").strip()
    nama = request.form.get("nama", "").strip()

    dup = db.find_student_by_no_akun(no_akun, exclude_id=student_id)
    if dup:
        flash("No Akun sudah dipakai siswa lain.", "error")
        return redirect(url_for("siswa_list"))

    data = {
        "no_akun": no_akun,
        "nama": nama,
        "status": request.form.get("status", "Aktif"),
        "mulai": request.form.get("mulai") or None,
        "akhir": request.form.get("akhir") or None,
        "paket_id": request.form.get("paket_id", type=int),
        "jatuh_tempo": request.form.get("jatuh_tempo", type=int) or 10,
    }
    if student_id:
        db.update_student(student_id, data)
        flash("Data siswa berhasil diperbarui.", "success")
    else:
        db.add_student(data)
        flash("Siswa baru berhasil ditambahkan.", "success")
    return redirect(url_for("siswa_list"))


@app.route("/siswa/hapus/<int:student_id>", methods=["POST"])
@login_required
def siswa_hapus(student_id):
    db.delete_student(student_id)
    flash("Siswa dihapus. Riwayat pembayarannya juga ikut terhapus.", "success")
    return redirect(url_for("siswa_list"))


# ---------------- PAKET ----------------

@app.route("/paket")
@login_required
def paket_list():
    packages = db.get_all_packages()
    edit_id = request.args.get("edit", type=int)
    edit_package = db.get_package(edit_id) if edit_id else None
    return render_template("paket.html", packages=packages, edit_package=edit_package)


@app.route("/paket/save", methods=["POST"])
@login_required
def paket_save():
    package_id = request.form.get("pid", type=int)
    name = request.form.get("name", "").strip()
    price = request.form.get("price", type=int) or 0
    if package_id:
        db.update_package(package_id, name, price)
        flash("Paket berhasil diperbarui.", "success")
    else:
        db.add_package(name, price)
        flash("Paket baru berhasil ditambahkan.", "success")
    return redirect(url_for("paket_list"))


@app.route("/paket/hapus/<int:package_id>", methods=["POST"])
@login_required
def paket_hapus(package_id):
    db.delete_package(package_id)
    flash("Paket dihapus.", "success")
    return redirect(url_for("paket_list"))


# ---------------- PENERIMA IURAN SPP ----------------

@app.route("/penerima")
@login_required
def penerima_list():
    recipients = db.get_all_recipients()
    edit_id = request.args.get("edit", type=int)
    edit_recipient = db.get_recipient(edit_id) if edit_id else None
    return render_template("penerima.html", recipients=recipients, edit_recipient=edit_recipient)


@app.route("/penerima/save", methods=["POST"])
@login_required
def penerima_save():
    recipient_id = request.form.get("rid", type=int)
    nama = request.form.get("nama", "").strip()
    jabatan = request.form.get("jabatan", "").strip()
    if not nama:
        flash("Nama penerima wajib diisi.", "error")
        return redirect(url_for("penerima_list"))
    if recipient_id:
        db.update_recipient(recipient_id, nama, jabatan)
        flash("Data penerima berhasil diperbarui.", "success")
    else:
        db.add_recipient(nama, jabatan)
        flash("Penerima baru berhasil ditambahkan.", "success")
    return redirect(url_for("penerima_list"))


@app.route("/penerima/hapus/<int:recipient_id>", methods=["POST"])
@login_required
def penerima_hapus(recipient_id):
    db.delete_recipient(recipient_id)
    flash("Penerima dihapus.", "success")
    return redirect(url_for("penerima_list"))


# ---------------- INPUT SPP ----------------

@app.route("/input-spp")
@login_required
def input_spp():
    students = db.get_active_students()
    today = date.today()

    student_id = request.args.get("student_id", type=int)
    tahun = request.args.get("tahun", type=int) or today.year
    if not student_id and students:
        student_id = students[0]["id"]

    kartu = []
    selected_student = None
    if student_id:
        selected_student = db.get_student(student_id)
        payments = {p["bulan"]: p for p in db.get_payments_for_student_year(student_id, tahun)}
        for i, m in enumerate(MONTHS, start=1):
            kartu.append({"no": i, "bulan": m, "payment": payments.get(i)})

    jumlah_default = ""
    if selected_student and selected_student.get("paket_price") is not None:
        jumlah_default = selected_student["paket_price"]

    return render_template(
        "input_spp.html",
        students=students,
        selected_student=selected_student,
        student_id=student_id,
        tahun=tahun,
        kartu=kartu,
        today=today.isoformat(),
        jumlah_default=jumlah_default,
        recipients=db.get_all_recipients(),
    )


@app.route("/input-spp/save", methods=["POST"])
@login_required
def input_spp_save():
    student_id = request.form.get("student_id", type=int)
    bulan = request.form.get("bulan", type=int)
    tahun = request.form.get("tahun", type=int)
    jumlah = request.form.get("jumlah", type=int) or 0
    tgl_bayar = request.form.get("tgl_bayar") or None
    ttd = request.form.get("ttd", "").strip()
    stempel = request.form.get("stempel", "Belum")

    db.upsert_payment(student_id, bulan, tahun, jumlah, tgl_bayar, ttd, stempel)
    flash("Pembayaran SPP berhasil disimpan.", "success")
    return redirect(url_for("input_spp", student_id=student_id, tahun=tahun))


# ---------------- LAPORAN ----------------

@app.route("/laporan")
@login_required
def laporan():
    today = date.today()
    years = set(db.get_all_years())
    years.add(today.year)
    years = sorted(years)
    tahun = request.args.get("tahun", type=int) or today.year

    # --- Laporan per bulan (ringkasan semua bulan dalam 1 tahun) ---
    payments = db.get_payments_for_year(tahun)
    rows = []
    grand_total = 0
    for i, m in enumerate(MONTHS, start=1):
        bulan_payments = [p for p in payments if p["bulan"] == i]
        total = sum(p["jumlah"] for p in bulan_payments)
        grand_total += total
        rows.append({"bulan": m, "jumlah_bayar": len(bulan_payments), "total": total})

    # --- Laporan atas nama siswa (riwayat pembayaran 1 siswa) ---
    all_students = db.get_all_students()
    siswa_id = request.args.get("siswa_id", type=int)
    if not siswa_id and all_students:
        siswa_id = all_students[0]["id"]
    riwayat_siswa = []
    siswa_terpilih = None
    total_siswa = 0
    if siswa_id:
        siswa_terpilih = db.get_student(siswa_id)
        for p in db.get_payments_for_student_all(siswa_id):
            riwayat_siswa.append({
                "bulan": MONTHS[p["bulan"] - 1],
                "tahun": p["tahun"],
                "jumlah": p["jumlah"],
                "tgl_bayar": p["tgl_bayar"],
                "ttd": p["ttd"],
                "stempel": p["stempel"],
            })
            total_siswa += p["jumlah"]

    # --- Laporan atas nama bulan (status semua siswa aktif pada 1 bulan+tahun) ---
    lbulan = request.args.get("lbulan", type=int) or today.month
    ltahun = request.args.get("ltahun", type=int) or today.year
    status_bulan = []
    total_bulan_terpilih = 0
    lunas_count = 0
    for s in db.get_active_students():
        p = db.get_payment(s["id"], ltahun, lbulan)
        status_bulan.append({
            "no_akun": s["no_akun"],
            "nama": s["nama"],
            "jumlah": p["jumlah"] if p else None,
            "tgl_bayar": p["tgl_bayar"] if p else None,
            "status": "Lunas" if p else "Belum",
        })
        if p:
            lunas_count += 1
            total_bulan_terpilih += p["jumlah"]

    return render_template(
        "laporan.html",
        years=years,
        tahun=tahun,
        rows=rows,
        grand_total=grand_total,
        all_students=all_students,
        siswa_id=siswa_id,
        siswa_terpilih=siswa_terpilih,
        riwayat_siswa=riwayat_siswa,
        total_siswa=total_siswa,
        lbulan=lbulan,
        ltahun=ltahun,
        status_bulan=status_bulan,
        total_bulan_terpilih=total_bulan_terpilih,
        lunas_count=lunas_count,
    )


@app.route("/export/csv")
@login_required
def export_csv():
    payments = db.get_all_payments()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["No Akun", "Nama Siswa", "Bulan", "Tahun", "Jumlah Iuran",
                      "Tanggal Bayar", "TTD", "Stempel"])
    for p in payments:
        writer.writerow([
            p.get("no_akun", ""), p.get("student_nama", ""),
            MONTHS[p["bulan"] - 1] if p["bulan"] else "", p["tahun"],
            p["jumlah"], p.get("tgl_bayar", ""), p.get("ttd", ""), p.get("stempel", ""),
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=laporan-spp-omahbocil.csv"},
    )


@app.route("/export/json")
@login_required
def export_json():
    data = {
        "students": db.get_all_students(),
        "packages": db.get_all_packages(),
        "payments": db.get_all_payments(),
        "exportedAt": datetime.now().isoformat(),
    }
    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=database-spp-omahbocil.json"},
    )


if __name__ == "__main__":
    app.run(debug=True)
