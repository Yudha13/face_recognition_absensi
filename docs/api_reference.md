
# Referensi API

Bagian ini menyediakan informasi terperinci tentang endpoint API yang digunakan dalam sistem Face Recognition Absensi.

## Endpoints

### `/api/v1/admin`
- **Deskripsi:** Operasi khusus admin seperti mengelola pengguna, kelas, dan absensi.
- **Metode:** GET, POST, PUT, DELETE

### `/api/v1/dosen`
- **Deskripsi:** Operasi untuk dosen, termasuk melihat kelas dan absensi mahasiswa.
- **Metode:** GET

### `/api/v1/attendance`
- **Deskripsi:** Mengelola data absensi, termasuk permintaan pengenalan wajah dan pencatatan kehadiran.
- **Metode:** POST

## Contoh Permintaan
- **Mendapatkan semua mahasiswa:**
  ```bash
  curl -X GET http://<raspberry-pi-ip>:5000/api/v1/admin/students
  ```
- **Menambahkan kelas baru:**
  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"class_name": "Math 101"}' http://<raspberry-pi-ip>:5000/api/v1/admin/classes
  ```
    