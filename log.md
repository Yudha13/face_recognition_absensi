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

- **20/09/2024**:
  - **Modifikasi Fungsi Start dan Stop Kelas:**
    - Ditambahkan fitur untuk mencatat waktu mulai dan selesai absensi di database.
    - Dihitung selisih waktu kehadiran mahasiswa berdasarkan waktu mulai absensi.
    - Pada frontend, proses stop kelas diperbaiki dengan penambahan argumen `kelas_id`.
    - Tombol "Stop Kelas" di dashboard admin diaktifkan dan telah diuji agar berfungsi dengan baik.
    
  - **Laporan Absensi:**
    - Perbaikan tampilan laporan absensi agar lebih responsif dan rapi.
    - Ditambahkan kolom waktu pada laporan absensi dan rincian jumlah mahasiswa yang hadir dari total mahasiswa dalam kelas.
    - Fitur unduh laporan absensi per tanggal telah diperbaiki.

-**27/09/2024**:

- **Fitur Unduh Rekap Absensi:**
  - Implementasi fitur unduh rekap absensi kelas dalam format Excel yang disesuaikan untuk mencakup semua sesi absensi.
  - Tabel absensi ditampilkan secara dinamis dengan persentase kehadiran mahasiswa dan disusun dalam format yang rapi untuk dicetak di kertas A4.
  - Tampilan header laporan absensi diatur agar judul, dosen, dan jadwal kelas terformat dengan baik tanpa border.

- **Perbaikan Laporan Per Sesi Absensi:**
  - Fitur unduh laporan per sesi absensi diperbaiki untuk mencatat kehadiran, keterlambatan, dan ketidakhadiran mahasiswa secara akurat berdasarkan ID sesi absensi.
  - Implementasi frontend dan backend untuk unduh laporan absensi per sesi selesai.

- **Perbaikan Halaman Detail Absensi:**
  - Masalah penampilan tanggal di header halaman **Detail Absensi** telah diperbaiki.
  - Sekarang data absensi ditampilkan berdasarkan ID sesi absensi yang benar, bukan hanya berdasarkan tanggal.
  - Nama mahasiswa yang hadir, waktu kehadiran, dan status kehadiran diperbaiki agar tampil sesuai sesi.

- **Perbaikan Fitur Edit Dosen:**
  - Masalah password yang hilang saat melakukan edit dosen tanpa mengubah password telah diperbaiki. Sekarang, jika password tidak diisi saat mengedit, password lama tetap dipertahankan.

### **27/09/2024**:

- **Fitur Unduh Rekap Absensi:**
  - Implementasi fitur unduh rekap absensi kelas dalam format Excel yang disesuaikan untuk mencakup semua sesi absensi.
  - Tabel absensi ditampilkan secara dinamis dengan persentase kehadiran mahasiswa dan disusun dalam format yang rapi untuk dicetak di kertas A4.
  - Tampilan header laporan absensi diatur agar judul, dosen, dan jadwal kelas terformat dengan baik tanpa border.

- **Perbaikan Laporan Per Sesi Absensi:**
  - Fitur unduh laporan per sesi absensi diperbaiki untuk mencatat kehadiran, keterlambatan, dan ketidakhadiran mahasiswa secara akurat berdasarkan ID sesi absensi.
  - Implementasi frontend dan backend untuk unduh laporan absensi per sesi selesai.

- **Perbaikan Halaman Detail Absensi:**
  - Masalah penampilan tanggal di header halaman **Detail Absensi** telah diperbaiki.
  - Sekarang data absensi ditampilkan berdasarkan ID sesi absensi yang benar, bukan hanya berdasarkan tanggal.
  - Nama mahasiswa yang hadir, waktu kehadiran, dan status kehadiran diperbaiki agar tampil sesuai sesi.

- **Perbaikan Fitur Edit Dosen:**
  - Masalah password yang hilang saat melakukan edit dosen tanpa mengubah password telah diperbaiki. Sekarang, jika password tidak diisi saat mengedit, password lama tetap dipertahankan.

- **Fitur Sesi Absensi di Dashboard:**
  - Menambahkan fitur di halaman **Dashboard Admin** dan **Dashboard Dosen** untuk menampilkan sesi absensi yang sedang berlangsung.
  - Admin dapat memantau sesi yang aktif secara langsung dari dashboard dan menghentikan sesi jika diperlukan.

### **29/09/2024**

- **Perbaikan Dashboard Dosen dan Admin**:
  - Menampilkan nama dosen yang sedang login di dashboard dosen dan memperbaiki tampilan kelas yang sedang berlangsung agar sesuai dengan dosen yang berkaitan.
  - Fitur "Stop Kelas" diperbaiki sehingga hanya muncul untuk dosen yang memiliki kelas yang sedang berlangsung.
  
- **Implementasi Alert Login Gagal**:
  - Dosen dan admin sekarang mendapatkan alert ketika login gagal. SweetAlert digunakan untuk menampilkan pesan interaktif.

- **Modifikasi Tampilan Sidebar**:
  - Menambahkan sidebar admin dan dosen yang lebih modern. Menghilangkan informasi user di sidebar dan menampilkan logo modern pada sidebar.
  
- **Pembuatan Login Dosen yang Serupa dengan Admin**:
  - Membuat halaman login dosen dengan desain serupa seperti login admin, menggunakan elemen UI yang seragam dan responsif.

- **Penyesuaian Tampilan Kelola Mahasiswa**:
  - Menambahkan indikator status training pada halaman kelola mahasiswa dengan label hijau untuk yang sudah di-train, kuning untuk sedang training, dan merah untuk yang belum di-train.

- **Sistem Siap untuk Di Uji**:
  - Sistem sudah siap untuk diuji dengan berbagai macam skenario.
