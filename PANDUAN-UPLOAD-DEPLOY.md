# Panduan Upload ke GitHub & Deploy Aplikasi SPP Omah Bocil

Panduan ini untuk yang **tidak mau pakai Git di komputer sendiri** — semua lewat browser (drag & drop + dashboard).

---

## Bagian 1 — Upload Kode ke GitHub (Drag & Drop)

### 1. Ekstrak zip di komputer
Klik kanan file `spp-omahbocil.zip` yang sudah didownload, pilih **Extract All / Ekstrak Semua**.
Buka folder hasil ekstrak sampai terlihat isinya: `app.py`, `database.py`, `requirements.txt`, `README.md`, `.gitignore`, folder `templates`, dan folder `static`.

### 2. Select semua file dan folder
Masuk ke dalam folder hasil ekstrak (bukan di luar foldernya), lalu tekan **Ctrl+A** untuk memilih semua file & folder sekaligus.

### 3. Drag ke halaman GitHub
Buka `github.com/<username>/<nama-repo>/upload/main` di browser.
Drag semua file/folder yang terpilih tadi ke kotak **"Drag files here to add them to your repository"**.
Folder `templates` dan `static` akan otomatis ikut terupload lengkap dengan isinya.

### 4. Tunggu proses upload selesai
Tunggu progress bar tiap file sampai penuh sebelum lanjut.

### 5. Isi pesan commit
Di kotak **Commit changes**, isi misalnya: `Upload aplikasi SPP Omah Bocil`.
Pastikan opsi **"Commit directly to the main branch"** tetap terpilih.

### 6. Klik Commit changes
Klik tombol hijau **Commit changes**. Setelah refresh, semua file akan muncul di repo.

**Catatan:**
- File `.gitignore` mungkin tersembunyi di File Explorer — aktifkan *"Show hidden files"* kalau perlu, atau lewati saja (tidak wajib).
- Jangan upload file `spp_omahbocil.db` kalau ada — data siswa/pembayaran sebaiknya tidak masuk repo publik.
- Untuk update file di lain waktu: buka repo → **Add file** → **Upload files** → drag file yang berubah.

---

## Bagian 2 — Deploy ke PythonAnywhere (Agar Bisa Diakses Lewat Link)

> GitHub hanya menyimpan kode, tidak menjalankannya. Supaya aplikasi bisa diakses lewat link publik, perlu di-*deploy* ke hosting yang bisa menjalankan Python — di sini pakai **PythonAnywhere** (gratis, data SQLite lebih awet dibanding hosting gratis lain).

### 1. Daftar akun gratis
Buka [pythonanywhere.com](https://www.pythonanywhere.com) → **Pricing & signup** → pilih paket **Beginner** (gratis) → daftar dengan email.

### 2. Buka Bash console
Di dashboard, buka tab **Consoles** → klik **Bash**. Ini terminal milik server PythonAnywhere, bukan di komputer kamu.

### 3. Clone repo dari GitHub
```bash
git clone https://github.com/<username>/<nama-repo>.git
```
Ganti `<username>/<nama-repo>` dengan alamat repo kamu. Kamu tidak perlu install git di laptop sendiri — ini dijalankan di server PythonAnywhere.

### 4. Buat virtual environment & install Flask
```bash
mkvirtualenv --python=python3.10 spp-venv
cd <nama-repo>
pip install -r requirements.txt
```

### 5. Buat web app baru
Buka tab **Web** → **Add a new web app** → pilih domain gratis (`namamu.pythonanywhere.com`) → pilih **Manual configuration** → pilih **Python 3.10**.

### 6. Atur source code & WSGI file
Di halaman konfigurasi web app, isi:
- **Source code**: `/home/namamu/<nama-repo>`
- **Virtualenv**: `/home/namamu/.virtualenvs/spp-venv`

Klik link **WSGI configuration file**, hapus semua isinya, ganti dengan:
```python
import sys
path = '/home/namamu/<nama-repo>'
if path not in sys.path:
    sys.path.append(path)
from app import app as application
```
Ganti `namamu` dan `<nama-repo>` sesuai username & nama repo kamu.

### 7. Atur static files
Masih di tab **Web**, scroll ke bagian **Static files**:
- **URL**: `/static/`
- **Path**: `/home/namamu/<nama-repo>/static/`

Ini supaya logo dan CSS tampil dengan benar.

### 8. Reload & buka linknya
Scroll ke atas, klik tombol hijau **Reload namamu.pythonanywhere.com**.
Buka link tersebut — aplikasi SPP Omah Bocil sudah live dan bisa diakses siapa saja.

---

## Setelah Live — Langkah Keamanan Wajib

1. Buka link aplikasi kamu, login dengan akun default:
   ```
   Username: admin
   Password: admin123
   ```
2. **Segera** buka menu **Ganti Password** dan ganti ke password yang kuat — karena link ini bisa diakses siapa saja yang tahu alamatnya.
3. (Opsional, disarankan) Di tab **Web** PythonAnywhere, bagian **Environment variables**, tambahkan `SECRET_KEY` dengan nilai acak yang panjang, lalu reload web app.

---

## Update Aplikasi di Kemudian Hari

Kalau nanti kamu mengubah kode dan sudah di-upload ulang ke GitHub (via drag & drop, Bagian 1), tinggal jalankan ini di Bash console PythonAnywhere untuk menarik perubahan terbaru:
```bash
cd ~/<nama-repo>
git pull
```
Lalu reload web app dari tab **Web**.
