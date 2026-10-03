# HANDOFF — SPP Omah Bocil

Dokumen ini untuk developer lain yang melanjutkan/memelihara aplikasi ini. Bukan untuk end-user.

## Ringkasan Teknis

- **Stack**: Python 3.10+, Flask 3.x, SQLite (file tunggal, tanpa server DB terpisah), Jinja2 untuk templating, tanpa JS framework (vanilla JS minimal, hanya `onchange="this.form.submit()"` untuk filter).
- **Auth**: session-based (cookie Flask), bukan Flask-Login. Password di-hash dengan `werkzeug.security`. Tidak ada role/permission bertingkat — satu level "admin" saja.
- **Tidak ada migrasi framework** (tidak pakai Alembic/Flask-Migrate). Perubahan skema dilakukan manual di `database.py` fungsi `init_db()` dengan pola "cek kolom via `PRAGMA table_info`, `ALTER TABLE ADD COLUMN` kalau belum ada". Lihat migrasi kolom `foto` di `students` sebagai contoh.

## Struktur File

```
app.py               # semua route Flask, logika request/response
database.py           # satu-satunya file yang menyentuh SQL langsung
templates/            # Jinja2, semua extend dari base.html
static/
  style.css            # satu file CSS untuk semua halaman
  logo_omahbocil.png
  uploads/siswa/       # foto siswa hasil upload (di-gitignore, dibuat otomatis saat runtime)
spp_omahbocil.db       # dibuat otomatis saat pertama run (di-gitignore)
```

## Konvensi yang Dipakai

- **Semua akses DB lewat `database.py`** — jangan tulis SQL langsung di `app.py`. Tiap fungsi buka/tutup koneksi sendiri lewat context manager `get_cursor()`.
- **Nama fungsi DB**: `get_all_x`, `get_x`, `add_x`, `update_x`, `delete_x` per entitas (students, packages, recipients, payments, admins).
- **Flash messages** dengan kategori `"success"` atau `"error"` saja (lihat CSS `.flash.success` / `.flash.error`).
- **Proteksi route**: tambahkan decorator `@login_required` di bawah `@app.route(...)` untuk semua halaman yang butuh login (semua kecuali `/login`).
- **Upload file**: pola di `save_foto_siswa()` — validasi ekstensi, generate nama file pakai `uuid4` (hindari tabrakan nama & path traversal), simpan ke `UPLOAD_FOLDER`. Kalau menambah jenis upload baru, ikuti pola yang sama.
- **Harga/uang**: selalu disimpan sebagai integer rupiah (bukan float), ditampilkan lewat Jinja filter `rupiah` (didaftarkan di `app.py`).
- **Bulan**: disimpan sebagai integer 1–12, nama bulan diambil dari list `MONTHS` di `app.py` (index `bulan - 1`).

## Hal yang Perlu Diperhatikan Kalau Menambah Fitur

- **`payments` punya constraint `UNIQUE(student_id, bulan, tahun)`** — satu siswa hanya bisa punya satu baris pembayaran per bulan per tahun. Fungsi `upsert_payment()` memanfaatkan ini (`ON CONFLICT ... DO UPDATE`). Kalau mau multi-pembayaran per bulan (misal cicilan), constraint ini harus dilonggarkan dan semua kode yang assume "1 payment = 1 bulan" harus direvisi (terutama kartu SPP bulanan di `input_spp.html` dan laporan).
- **Hapus siswa = CASCADE hapus payments-nya** (`FOREIGN KEY ... ON DELETE CASCADE`). Ini disengaja, tapi tidak ada konfirmasi dobel di UI selain `confirm()` JS biasa — kalau butuh audit trail/undo, perlu ditambah soft-delete.
- **Tidak ada rate limiting / brute-force protection di `/login`.** Kalau aplikasi mulai diakses publik luas, pertimbangkan tambah Flask-Limiter.
- **`SECRET_KEY` fallback ke string hardcoded** kalau env var `SECRET_KEY` tidak diset — ingatkan user untuk selalu set env var ini di hosting produksi (sudah dicatat di README).
- **Upload foto dibatasi 3MB** (`MAX_CONTENT_LENGTH`) dan ekstensi `png/jpg/jpeg/gif/webp` saja — sesuaikan di `app.py` kalau kebutuhan berubah.

## Changelog / Riwayat Fitur

Riwayat perubahan untuk END-USER ada di dalam aplikasi sendiri, menu **Riwayat** (`/riwayat`), datanya di list `CHANGELOG` dalam `app.py`. **Setiap kali menambah fitur, tambahkan entri baru di urutan paling atas list tersebut** supaya tetap sinkron dengan histori yang dilihat user di web.

## Deploy

Lihat `README.md` untuk instalasi lokal, dan `PANDUAN-UPLOAD-DEPLOY.md` (kalau ada di repo) untuk langkah upload ke GitHub via drag & drop + deploy ke PythonAnywhere tanpa command line git di komputer lokal. Update kode di server dilakukan dengan `git pull` di Bash console PythonAnywhere, lalu reload web app dari tab Web.

## Ide Pengembangan Selanjutnya (belum dikerjakan)

- Role multi-admin dengan hak akses berbeda (misal admin vs bendahara read-only).
- Notifikasi WA/email otomatis untuk reminder tunggakan (saat ini reminder hanya tampil di dashboard).
- Backup otomatis `spp_omahbocil.db` terjadwal (hosting gratis seperti PythonAnywhere free tier tidak auto-backup).
