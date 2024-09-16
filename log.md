## 🛠️ Log Pengembangan

- **1/09/2024**: 
  - Mulai implementasi Dashboard Admin dan fitur CRUD (Create, Read, Update, Delete) untuk mengelola mahasiswa, dosen, dan kelas.
  
- **2/09/2024**: 
  - Penyelesaian implementasi Dashboard Dosen dan fitur CRUD yang relevan, seperti melihat data kelas yang diajar.
  
- **4/09/2024**: 
  - **Perbaikan Fitur Edit Kelas:**
    - Dropdown dosen pengampu tidak menampilkan daftar dosen di halaman edit kelas. Masalah ini diperbaiki dengan menggunakan filter `|string` di Jinja2.
    - Error `BadRequestKeyError: 'nama_kelas'` diperbaiki dengan menambahkan field `nama_kelas` di form.
    - Sekarang memungkinkan perubahan dosen pengampu, nama kelas, dan jadwal kelas, serta perubahan ini tercermin di akun dosen terkait.
  
  - **Fitur Kelola Mahasiswa di Kelas:**
    - Mahasiswa dapat ditambah atau dihapus dari kelas melalui halaman **kelola_kelas_mahasiswa.html**.
    - Jumlah mahasiswa otomatis diperbarui saat mahasiswa dihapus dari sistem.
    - Penghapusan mahasiswa dari sistem memperbarui jumlah mahasiswa di kelas.

- **6/09/2024**:
  - **Perbaikan Kelola Kelas, Dosen, dan Mahasiswa:**
    - Fitur pengelolaan kelas, dosen, dan mahasiswa lebih terstruktur dengan penambahan tombol "Kelola Mahasiswa".
    - Semua tabel di halaman admin diperbarui agar lebih responsif dengan **DataTables**.
    - Validasi jadwal ditambahkan untuk mencegah bentrokan jadwal kelas.

- **7/09/2024**:
  - **Training Foto Mahasiswa dan Absensi:**
    - Training foto mahasiswa diintegrasikan menggunakan **Local Binary Pattern (LBP)** untuk pengenalan wajah.
    - Absensi berbasis face recognition dapat dimulai oleh admin, dan status absensi ditampilkan secara real-time di dashboard.
  
- **13/09/2024**:
  - **Perbaikan BuildError di Laporan Absensi:**
    - Error `BuildError` saat melihat detail absensi diatasi. Jika tidak ada data absensi, pesan "Tidak ada data absensi yang tersedia" muncul.
  
- **16/09/2024**:
  - **Penyempurnaan Face Recognition:**
    - Perbaikan pelabelan mahasiswa yang sebelumnya menggunakan NIM, kini menggunakan `ObjectId` dari MongoDB.
    - Confidence level diatur untuk hasil pengenalan wajah yang lebih akurat.
    - **Perbaikan Tampilan Kamera:**
      - Kotak hijau untuk wajah yang sudah terdeteksi dan ditandai sebagai hadir.
      - Kotak biru untuk wajah yang terdeteksi tetapi bukan bagian dari sesi absensi.
      - Kotak merah untuk wajah yang tidak dikenali.
    
  - **Pengelolaan Absensi:**
    - Tampilan laporan absensi diperbaiki agar tanggal absensi dapat ditampilkan dengan benar.
    - Rute untuk melihat detail absensi diatur ulang untuk menampilkan nama dan NIM mahasiswa yang hadir dengan benar.
    
  - **Perbaikan Bug:**
    - Bug pada pengelolaan NIM mahasiswa saat menambah atau mengedit data sudah diperbaiki. Sekarang, validasi NIM bentrok muncul saat masih di halaman tambah/edit mahasiswa.
    - Absensi berhasil mencatat kehadiran dan memperbarui laporan absensi di halaman kelola admin.

## Update Selanjutnya:
- Penambahan pengujian dengan lebih banyak data mahasiswa.
- Perbaikan fitur pengunduhan laporan absensi.
- Penyesuaian tampilan dashboard dosen agar lebih informatif.
