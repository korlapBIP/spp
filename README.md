# SPP Omah Bocil — Manajer SPP

Aplikasi web sederhana untuk mengelola SPP Bimbingan Belajar Omah Bocil.
Dibangun dengan **Flask** (Python) dan **SQLite**, dilengkapi login admin.

## Fitur

- 🔐 Login admin (username & password, session-based)
- 👦 CRUD data siswa
- 📦 CRUD paket SPP
- 🧾 CRUD **penerima iuran SPP** (nama petugas yang menerima pembayaran, muncul sebagai saran di kolom TTD)
- 💰 Input pembayaran SPP bulanan + kartu SPP per siswa
- 📊 Dashboard ringkasan & reminder tunggakan
- 📈 Laporan keuangan: per tahun, atas nama siswa, dan atas nama bulan
- ⬇️ Export data ke CSV & JSON

## Instalasi

```bash
git clone <url-repo-anda>
cd spp-omahbocil
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Buka `http://127.0.0.1:5000` di browser. Database `spp_omahbocil.db` akan otomatis dibuat saat pertama kali dijalankan.

## Login Pertama Kali

Saat pertama kali dijalankan, aplikasi otomatis membuat akun admin default:

```
Username: admin
Password: admin123
```

**⚠️ Penting:** langsung login lalu ganti password ini di menu **Ganti Password**, terutama sebelum aplikasi dipakai secara nyata / online.

## Struktur Proyek

```
spp-omahbocil/
├── main.py              # Routing Flask & logika aplikasi
├── database.py          # Akses SQLite (semua query & CRUD)
├── requirements.txt
├── .gitignore
├── templates/           # Halaman HTML (Jinja2)
└── static/style.css     # Gaya tampilan
```

## Catatan Keamanan Sebelum Deploy

- Jangan commit file `.db` ke repo (sudah ada di `.gitignore`).
- Set environment variable `SECRET_KEY` dengan nilai acak yang kuat saat deploy:
  ```bash
  export SECRET_KEY="ganti-dengan-string-acak-yang-panjang"
  ```
- Jangan gunakan `app.run(debug=True)` di produksi.
- Ganti password admin default sebelum aplikasi diakses publik.
