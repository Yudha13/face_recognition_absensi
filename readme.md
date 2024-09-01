
# Face Recognition Absensi

![Logo](https://example.com/logo.png) <!-- Jika ada logo proyek, tambahkan link di sini -->

## 📜 Deskripsi Proyek
Proyek ini adalah sistem absensi berbasis pengenalan wajah yang dibangun menggunakan Flask, MongoDB, dan Raspberry Pi. Sistem ini memungkinkan admin untuk mengelola data dosen, mahasiswa, kelas, serta laporan absensi dengan mudah dan efisien.

**Catatan:** Sistem ini masih dalam tahap pengembangan dan belum sepenuhnya selesai. 

## 🛠️ Log Pengembangan
Berikut adalah perkembangan penting dalam proyek ini:

- **1/09/2024**: Implementasi Dashboard Admin dan fitur CRUD (Create, Read, Update, Delete).
- **2/09/2024**: Implementasi Dashboard Dosen dan fitur CRUD yang relevan.

## 🚀 Instalasi

Ikuti langkah-langkah di bawah ini untuk mengatur proyek di lingkungan lokal Anda:

1. **Clone repository ini:**
   ```bash
   git clone <repository-url>
   ```

2. **Navigasi ke direktori proyek:**
   ```bash
   cd face_recognition_absensi
   ```

3. **Buat dan aktifkan Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install dependensi yang diperlukan:**
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Cara Menjalankan Aplikasi
Pastikan MongoDB sudah berjalan dengan benar di sistem Anda.

Untuk memulai aplikasi, jalankan skrip berikut:
```bash
./run_app.sh
```

## 🎯 Fitur Utama
- **Pengenalan Wajah:** Penggunaan teknologi pengenalan wajah untuk memastikan kehadiran yang akurat.
- **Manajemen Admin:** Admin dapat mengelola data dosen, mahasiswa, kelas, dan laporan absensi.
- **Dashboard Interaktif:** Tersedia dashboard khusus untuk admin dan dosen untuk melihat data secara visual.

## 📚 Dokumentasi
Untuk informasi lebih lanjut mengenai penggunaan dan pengembangan sistem ini, silakan baca [dokumentasi lengkap](https://example.com/documentation).

## 💬 Kontribusi
Kami menyambut kontribusi dari siapa saja. Jika Anda ingin berkontribusi, silakan buat pull request atau buka issue baru di repository ini.

## 📝 Lisensi
Proyek ini dilisensikan di bawah [Lisensi MIT](LICENSE).