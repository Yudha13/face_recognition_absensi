
# Absensi Face Recognition

![Logo](./docs/logo.png)

## 📜 Deskripsi Proyek
Proyek ini adalah sistem absensi berbasis pengenalan wajah yang dibangun menggunakan Flask, MongoDB, dan Raspberry Pi. Sistem ini memungkinkan admin untuk mengelola data dosen, mahasiswa, kelas, serta laporan absensi dengan mudah dan efisien.

**Catatan:** Sistem ini masih dalam tahap pengembangan dan belum sepenuhnya selesai.

## 🛠️ Log Pengembangan
Berikut adalah perkembangan penting dalam proyek ini:

- **1/09/2024**: Implementasi Dashboard Admin dan fitur CRUD (Create, Read, Update, Delete).
- **2/09/2024**: Implementasi Dashboard Dosen dan fitur CRUD yang relevan.
- **4/09/2024**: Perbaikan fitur Edit Kelas:
  - **Masalah Dropdown Dosen Tidak Muncul:** Dropdown untuk memilih dosen pengampu di halaman edit kelas tidak menampilkan daftar dosen. Masalah ini disebabkan oleh perbandingan `ObjectId` MongoDB dengan string di HTML template. Solusi yang diimplementasikan adalah penggunaan filter `|string` di Jinja2 untuk memastikan `ObjectId` dikonversi menjadi string sebelum dibandingkan.
  - **Error `BadRequestKeyError: 'nama_kelas'`:** Error ini muncul karena field `nama_kelas` tidak ada di form, sehingga server tidak bisa memproses key tersebut. Setelah menambahkan kembali input `nama_kelas` di template, error teratasi.
  - **Hasil Akhir:** Fitur edit kelas sekarang memungkinkan perubahan dosen pengampu, nama kelas, dan jadwal kelas dengan benar, dan perubahan tercermin di akun dosen terkait.

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
