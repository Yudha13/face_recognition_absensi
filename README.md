# Absensi Face Recognition

## 📜 Deskripsi Project
Project ini adalah sistem absensi berbasis pengenalan wajah yang dibangun menggunakan **Flask**, **MongoDB**, dan **Raspberry Pi**. Sistem ini memudahkan admin dalam mengelola data dosen, mahasiswa, kelas, serta laporan absensi.

**Catatan:** Sistem ini masih dalam tahap pengembangan dan belum sepenuhnya selesai.

## 🛠️ Log Pengembangan

- **1/09/2024**: Mulai implementasi Dashboard Admin dan fitur CRUD (Create, Read, Update, Delete).
- **2/09/2024**: Dashboard Dosen beserta fitur CRUD yang relevan selesai diimplementasi.
- **4/09/2024**: 
  - **Perbaikan Fitur Edit Kelas:**
    - Dropdown dosen pengampu tidak menampilkan daftar dosen di halaman edit kelas. Masalah ini diperbaiki dengan menggunakan filter `|string` di Jinja2 untuk memastikan `ObjectId` dikonversi menjadi string.
    - `BadRequestKeyError: 'nama_kelas'`: Error ini terjadi karena field `nama_kelas` tidak ada di form. Setelah ditambahkan, masalah terselesaikan.
    - Fitur edit kelas sekarang memungkinkan perubahan dosen pengampu, nama kelas, dan jadwal kelas, serta perubahan ini juga tercermin di akun dosen terkait.
  - **Fitur Kelola Mahasiswa di Kelas:**
    - Mahasiswa bisa ditambahkan atau dihapus dari kelas melalui halaman **kelola_kelas_mahasiswa.html**, yang sudah diperbarui menggunakan tabel Bootstrap.
    - Jumlah mahasiswa di setiap kelas otomatis diperbarui saat mahasiswa dihapus dari sistem menggunakan `update_many` di MongoDB.
    - Penghapusan mahasiswa dari sistem juga memperbarui jumlah mahasiswa di kelas terkait.

- **6/09/2024**:
  - **Perbaikan pada Kelola Kelas, Dosen, dan Mahasiswa**:
    - Admin sekarang bisa lebih mudah mengelola kelas, dosen, dan mahasiswa. Tombol "Kelola Mahasiswa" ditambahkan untuk mengelola mahasiswa di setiap kelas.
    - Konfirmasi penghapusan data sekarang menggunakan **SweetAlert2**.
    - Semua tabel di halaman admin telah di-update agar lebih responsif menggunakan **DataTables** yang mendukung pencarian dan pagination.
    - Jadwal kelas sekarang disimpan dalam format date di database.
    - **Pencegahan Bentrokan Jadwal:** Fitur validasi jadwal ditambahkan agar kelas tidak memiliki jadwal yang bertabrakan dengan kelas lain.

- **7/09/2024**:
  - **Training Foto Mahasiswa dan Absensi:**
    - Fitur training foto mahasiswa telah diimplementasikan. Model training disimpan di direktori `models/NIM_mahasiswa/`.
    - Integrasi **Local Binary Pattern (LBP)** untuk deteksi dan pengenalan wajah berjalan dengan baik.
    - Proses training mahasiswa ditampilkan di dashboard admin secara real-time menggunakan AJAX polling.
  - **Absensi Berbasis Pengenalan Wajah:**
    - Absensi bisa dimulai secara manual oleh admin dari halaman kelola kelas. Status absensi akan muncul secara real-time di dashboard.
    - **Fitur Stop Kelas**: Admin dapat menghentikan absensi kapan saja melalui dashboard.

- **13/09/2024**:
  - **Perbaikan BuildError di Laporan Absensi:**
    - Error `BuildError` muncul saat mencoba melihat detail absensi ketika tidak ada data absensi di database. Sekarang, jika tidak ada data absensi, akan muncul pesan "Tidak ada data absensi yang tersedia."
  - **Bug pada Proses Absensi:**
    - Pengenalan wajah masih belum optimal, terutama dalam pencatatan NIM dan confidence level.
    - Jendela kamera kadang tidak tertutup dengan benar saat kelas dihentikan.

## 🎯 Fitur Utama
- **Pengenalan Wajah:** Penggunaan teknologi Face Recognition untuk memastikan kehadiran mahasiswa secara akurat.
- **Manajemen Admin:** Admin dapat mengelola data dosen, mahasiswa, kelas, dan laporan absensi dengan mudah.
- **Dashboard Interaktif:** Tersedia dashboard khusus untuk admin dan dosen yang menampilkan data secara visual.

## 📚 Dokumentasi
Untuk info lebih lanjut soal penggunaan dan pengembangan sistem, silakan cek [dokumentasi lengkap](./docs/index.md).

## 💬 Kontribusi
Kami menyambut kontribusi dari siapa saja. Jika tertarik untuk berkontribusi, silakan buat pull request atau buka issue di repository ini.

## 📝 Lisensi
Proyek ini dilisensikan di bawah [Lisensi MIT](LICENSE).

Bagian dari proyek ini menggunakan OpenCV dan Haar Cascade yang dilisensikan di bawah [BSD 3-Clause License](LICENSE_OPEN_CV.md).
