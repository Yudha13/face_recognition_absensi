#jalankan script ini jika user admin belum ada atau saat pertama kali
from pymongo import MongoClient

# Koneksi ke MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Sesuaikan dengan URI MongoDB Anda
db = client['absensi_db']  # Ganti dengan nama database yang sesuai

# Buat data user admin
admin_user = {
    "username": "admin",
    "password": "admin123", 
    "role": "admin" 
}

# Masukkan user admin ke dalam koleksi admin
db.admin.insert_one(admin_user)

print("User admin berhasil dibuat dengan username 'admin' dan password 'admin123'")