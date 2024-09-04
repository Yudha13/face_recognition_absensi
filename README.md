
# Absensi Face Recognition

## 📜 Deskripsi Proyek
Proyek ini adalah sistem absensi berbasis pengenalan wajah yang dibangun menggunakan Flask, MongoDB, dan Raspberry Pi. Sistem ini memungkinkan admin untuk mengelola data dosen, mahasiswa, kelas, serta laporan absensi dengan mudah.

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
