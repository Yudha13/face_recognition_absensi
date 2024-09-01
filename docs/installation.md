
# Panduan Instalasi

Panduan ini akan membantu Anda mengatur sistem Face Recognition Absensi di mesin lokal Anda.

## Prasyarat
Sebelum menginstal, pastikan Anda memiliki hal-hal berikut:
- Python 3.7+
- MongoDB
- Raspberry Pi (untuk deployment)
- Flask dan dependensi Python lainnya (tercantum di `requirements.txt`)

## Langkah Instalasi
1. **Clone repository:**
   ```bash
   git clone <repository-url>
   ```

2. **Arahkan ke direktori proyek:**
   ```bash
   cd face_recognition_absensi
   ```

3. **Buat dan aktifkan virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Instal semua dependensi yang diperlukan:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Jalankan aplikasi:**
   Pastikan MongoDB sudah berjalan, kemudian mulai aplikasi dengan:
   ```bash
   ./run_app.sh
   ```
    