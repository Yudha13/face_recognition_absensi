
# Panduan Penggunaan

Panduan ini menjelaskan cara menggunakan sistem Face Recognition Absensi setelah berhasil dijalankan.

## Dashboard Admin
Dashboard Admin memungkinkan Anda untuk:
- Mengelola data mahasiswa, dosen, dan kelas.
- Melihat dan mengekspor laporan absensi.

### Mengakses Dashboard Admin
1. Buka browser Anda.
2. Arahkan ke `http://<raspberry-pi-ip>:5000/admin`.
3. Masuk menggunakan kredensial berikut:
   - **Username:** admin
   - **Password:** admin123

### Mengelola Data
- **Mahasiswa:** Menambahkan, mengedit, atau menghapus data mahasiswa.
- **Dosen:** Mengelola informasi dosen dan kelas yang terkait.
- **Kelas:** Menyiapkan dan mengelola informasi kelas.

## Dashboard Dosen
Dashboard Dosen menyediakan antarmuka yang disesuaikan untuk dosen:
- Melihat kelas dan mahasiswa yang terkait.
- Mengunduh laporan absensi untuk setiap kelas.

### Mengakses Dashboard Dosen
1. Buka browser Anda.
2. Arahkan ke `http://<raspberry-pi-ip>:5000/dosen`.
3. Masuk menggunakan kredensial dosen Anda.

### Melihat Informasi Kelas
- Dosen dapat melihat informasi detail tentang kelas yang diajar.
- Data absensi untuk setiap kelas dapat diunduh dalam format Excel.
