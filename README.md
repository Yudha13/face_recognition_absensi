# Absensi Face Recognition

## 📜 Deskripsi Project
Project ini adalah sistem absensi berbasis pengenalan wajah yang dibangun menggunakan Flask, MongoDB, dan Raspberry Pi. Sistem ini memungkinkan admin untuk mengelola data dosen, mahasiswa, kelas, serta laporan absensi dengan mudah.

**Catatan:** Sistem ini masih dalam tahap pengembangan dan belum sepenuhnya selesai.

## 🛠️ Log Pengembangan

- **1/09/2024**: Implementasi Dashboard Admin dan fitur CRUD (Create, Read, Update, Delete).
- **2/09/2024**: Implementasi Dashboard Dosen dan fitur CRUD yang relevan.
- **4/09/2024**: 
  - **Perbaikan Fitur Edit Kelas:**
    - Dropdown dosen pengampu tidak menampilkan daftar dosen di halaman edit kelas. Masalah ini diselesaikan dengan penggunaan filter `|string` di Jinja2 untuk memastikan `ObjectId` dikonversi menjadi string.
    - `BadRequestKeyError: 'nama_kelas'`: Error terjadi karena field `nama_kelas` tidak ada di form. Setelah ditambahkan kembali di template, masalah teratasi.
    - Fitur edit kelas sekarang memungkinkan perubahan dosen pengampu, nama kelas, dan jadwal kelas, serta perubahan ini tercermin di akun dosen yang terkait.
  - **Implementasi Fitur Kelola Mahasiswa:**
    - **Fitur Kelola Mahasiswa di Kelas:** Mahasiswa dapat ditambahkan atau dihapus dari kelas melalui halaman **kelola_kelas_mahasiswa.html** yang sudah diperbarui dengan tampilan menggunakan tabel Bootstrap.
    - Setiap kali mahasiswa dihapus dari sistem, jumlah mahasiswa di setiap kelas diperbarui secara otomatis menggunakan `update_many` di MongoDB.
    - **Solusi Penghapusan Mahasiswa di Sistem:** Jumlah mahasiswa di kelas yang terkait dengan mahasiswa tersebut sekarang diperbarui dengan benar di tabel kelola kelas setelah mahasiswa dihapus dari list mahasiswa.

- **6/09/2024**:
  - **Perbaikan pada Kelola Kelas, Dosen, dan Mahasiswa**:
    - Pengelolaan kelas, dosen, dan mahasiswa oleh admin telah disempurnakan. Tombol "Kelola Mahasiswa" ditambahkan pada setiap kelas untuk mengelola mahasiswa di kelas terkait.
    - Penggunaan **SweetAlert2** untuk konfirmasi penghapusan data telah diterapkan pada semua fitur pengelolaan.
    - Semua tabel di halaman admin telah dibuat responsif dengan **DataTables** yang mendukung fitur pencarian dan pagination.
    -Penyimpanan Jadwal dalam Bentuk Date: Jadwal kelas sekarang disimpan dalam bentuk date di database.
    -Pencegahan Bentrokan Jadwal: Fitur validasi jadwal telah ditambahkan untuk mencegah kelas memiliki jadwal yang bertabrakan dengan kelas lain.

- **7/09/2024**:
  - **Training Foto Mahasiswa dan Absensi:**
    - Implementasi fitur training foto mahasiswa berhasil dilakukan. Model hasil training disimpan di direktori `models/NIM_mahasiswa/`.
    - Integrasi **Local Binary Pattern (LBP)** untuk deteksi wajah dan pengenalan wajah berjalan dengan baik.
    - Proses training mahasiswa ditampilkan di dashboard admin secara real-time menggunakan AJAX polling.
  - **Pengenalan Wajah untuk Absensi:**
    - Absensi dapat dimulai secara manual oleh admin melalui tombol "Mulai Kelas" pada halaman kelola kelas.
    - **Proses Absensi Real-Time:** Status absensi ditampilkan di dashboard dengan informasi mengenai kelas yang sedang berlangsung.
    - Fitur **Stop Kelas** untuk menghentikan proses absensi juga telah ditambahkan ke dashboard admin.
  - **Masalah yang Masih Ada:**
    - Pengenalan wajah untuk beberapa mahasiswa kurang akurat, terutama dalam pencatatan NIM dan confidence level.
    - Perbaikan visualisasi informasi pada window kamera masih diperlukan untuk menampilkan data absensi dan wajah dengan lebih jelas.

## 🎯 Fitur Utama
- **Pengenalan Wajah:** Penggunaan teknologi pengenalan wajah untuk memastikan kehadiran yang akurat.
- **Manajemen Admin:** Admin dapat mengelola data dosen, mahasiswa, kelas, dan laporan absensi.
- **Dashboard Interaktif:** Tersedia dashboard khusus untuk admin dan dosen untuk melihat data secara visual.

## 📚 Dokumentasi
Untuk informasi lebih lanjut mengenai penggunaan dan pengembangan sistem ini, silakan baca [dokumentasi lengkap](./docs/index.md).

## 💬 Kontribusi
Kami menyambut kontribusi dari siapa saja. Jika Anda ingin berkontribusi, silakan buat pull request atau buka issue baru di repository ini.

## 📝 Lisensi
Proyek ini dilisensikan di bawah [Lisensi MIT](LICENSE).
