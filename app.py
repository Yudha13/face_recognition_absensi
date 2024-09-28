import subprocess
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, SECRET_KEY
from bson.objectid import ObjectId
import pandas as pd
from flask import send_file
from datetime import datetime
import os
import shutil
from werkzeug.utils import secure_filename
from training.train_model import train_model  # panggil fungsi train
from flask import session
import threading
import logging
from bson import ObjectId
import threading
import locale
import io

app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')  # Set locale Indonesia

#########################################
#Pada Bagian ini adalah rute untuk admin#
#########################################

# Login Admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = db.admin.find_one({"username": username})
        
        if admin and admin['password'] == password:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Login Gagal: Username atau Password salah.'
            return render_template('admin/login.html', error=error)
    return render_template('admin/login.html')

# Logout Admin
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# Dashboard Admin
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' in session:
        jumlah_mahasiswa = db.mahasiswa.count_documents({})
        jumlah_dosen = db.dosen.count_documents({})
        jumlah_kelas = db.kelas.count_documents({})

        # Menghitung total absensi dari semua kelas
        total_absensi = db.absensi.count_documents({})

        # Status proses training
        training_status = session.get('training_status', None)  # Ambil status training dari session

        return render_template('admin/dashboard.html',
                               jumlah_mahasiswa=jumlah_mahasiswa,
                               jumlah_dosen=jumlah_dosen,
                               jumlah_kelas=jumlah_kelas,
                               jumlah_laporan_absensi=total_absensi,
                               training_status=training_status)
    else:
        return redirect(url_for('admin_login'))

#rute check status absensi
@app.route('/check_absensi_status', methods=['GET'])
def check_absensi_status():
    # Cari kelas yang statusnya sedang berlangsung
    kelas_berlangsung = db.kelas.find_one({"status": "Berlangsung"})

    if kelas_berlangsung:
        return {
            "status": "kelas_berlangsung",
            "nama_kelas": kelas_berlangsung["nama_kelas"],
            "kelas_id": str(kelas_berlangsung["_id"])
        }
    else:
        return {"status": "no_class"}

#######################################################################################################
## RUTE PENGELOLAAN MAHASISWA

# Kelola Mahasiswa
@app.route('/admin/kelola_mahasiswa', methods=['GET'])
def kelola_mahasiswa():
    if 'admin_logged_in' in session:
        mahasiswa = list(db.mahasiswa.find())  # Ubah menjadi list
        return render_template('admin/mahasiswa/kelola_mahasiswa.html', mahasiswa=mahasiswa)
    else:
        return redirect(url_for('admin_login'))

# Tambah Mahasiswa
@app.route('/admin/tambah_mahasiswa', methods=['POST', 'GET'])
def tambah_mahasiswa():
    if 'admin_logged_in' in session:
        if request.method == 'POST':
            nim = request.form['nim']
            nama = request.form['nama']
            email = request.form['email']
            nomor_hp = request.form['nomor_hp']
            foto_mahasiswa = request.files.getlist('foto_mahasiswa[]')

            # Cek apakah NIM sudah ada di database
            existing_mahasiswa = db.mahasiswa.find_one({'nim': nim})
            if existing_mahasiswa:
                flash(f'Mahasiswa dengan NIM {nim} sudah ada di database. Silakan gunakan NIM yang berbeda.', 'danger')
                return render_template('admin/mahasiswa/tambah_mahasiswa.html') 

            # Simpan data mahasiswa ke database
            mahasiswa = {
                'nim': nim,
                'nama': nama,
                'email': email,
                'nomor_hp': nomor_hp,
                'trained': False
            }
            inserted_mahasiswa = db.mahasiswa.insert_one(mahasiswa)
            mahasiswa_id = str(inserted_mahasiswa.inserted_id)

            # Proses unggah foto jika ada
            if foto_mahasiswa and foto_mahasiswa[0].filename != '':
                path = os.path.join('training/images', mahasiswa_id)
                if not os.path.exists(path):
                    os.makedirs(path)

                for foto in foto_mahasiswa:
                    if foto and foto.filename != '':
                        filename = secure_filename(foto.filename)
                        foto.save(os.path.join(path, filename))

                flash('Mahasiswa berhasil ditambahkan. Foto telah diunggah dan siap untuk training.', 'success')
            else:
                flash('Mahasiswa berhasil ditambahkan. Tidak ada foto yang diunggah.', 'info')

            return redirect(url_for('kelola_mahasiswa'))
        return render_template('admin/mahasiswa/tambah_mahasiswa.html')
    else:
        return redirect(url_for('admin_login'))

# Edit Mahasiswa
@app.route('/admin/edit_mahasiswa/<id>', methods=['GET', 'POST'])
def edit_mahasiswa(id):
    if 'admin_logged_in' in session:
        mahasiswa = db.mahasiswa.find_one({"_id": ObjectId(id)})
        if mahasiswa:
            if request.method == 'POST':
                nim = request.form['nim']
                nama = request.form['nama']
                email = request.form['email']
                nomor_hp = request.form['nomor_hp']
                foto_mahasiswa = request.files.getlist('foto_mahasiswa[]')

                # Cek apakah NIM sudah ada di database dan bukan milik mahasiswa lain
                existing_mahasiswa = db.mahasiswa.find_one({'nim': nim, '_id': {'$ne': ObjectId(id)}})
                if existing_mahasiswa:
                    flash(f'Mahasiswa dengan NIM {nim} sudah ada di database. Silakan gunakan NIM yang berbeda.', 'danger')
                    return render_template('admin/mahasiswa/edit_mahasiswa.html', mahasiswa=mahasiswa)

                # Update data mahasiswa di database
                db.mahasiswa.update_one({'_id': ObjectId(id)}, {
                    "$set": {
                        'nim': nim,
                        'nama': nama,
                        'email': email,
                        'nomor_hp': nomor_hp
                    }
                })

                # Proses unggah foto jika ada
                if foto_mahasiswa and foto_mahasiswa[0].filename != '':
                    folder_path = os.path.join('training/images', str(mahasiswa['_id']))

                    # Buat direktori jika belum ada
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)

                    # Simpan foto yang diunggah
                    for foto in foto_mahasiswa:
                        if foto and foto.filename != '':
                            filename = secure_filename(foto.filename)
                            foto.save(os.path.join(folder_path, filename))

                    flash('Data mahasiswa berhasil diperbarui. Foto telah diunggah dan siap untuk training.', 'success')
                else:
                    flash('Data mahasiswa berhasil diperbarui.', 'success')

                return redirect(url_for('kelola_mahasiswa'))
            return render_template('admin/mahasiswa/edit_mahasiswa.html', mahasiswa=mahasiswa)
        else:
            flash('Mahasiswa tidak ditemukan.', 'danger')
            return redirect(url_for('kelola_mahasiswa'))
    else:
        return redirect(url_for('admin_login'))

# Training Foto Mahasiswa
@app.route('/admin/train_mahasiswa/<id>', methods=['GET'])
def train_mahasiswa(id):
    if 'admin_logged_in' in session:
        mahasiswa = db.mahasiswa.find_one({"_id": ObjectId(id)})
        if mahasiswa:
            folder_path = os.path.join('training/images', str(mahasiswa['_id']))

            # Cek apakah folder ada dan tidak kosong
            if not os.path.exists(folder_path) or len(os.listdir(folder_path)) < 10:
                flash('Training gagal. Pastikan ada minimal 10 foto untuk mahasiswa ini.', 'danger')
                return redirect(url_for('kelola_mahasiswa'))

            try:
                # Update status di database
                db.mahasiswa.update_one({'_id': ObjectId(id)}, {"$set": {"training_in_progress": True}})

                nim = mahasiswa['nim']  # Ambil NIM dari data mahasiswa
                index = 0  # Atur index sesuai logika aplikasi Anda, misalnya urutan mahasiswa di database
                
                # Jalankan training di thread terpisah dengan nim dan index
                training_thread = threading.Thread(target=background_training, args=(str(mahasiswa['_id']), folder_path, nim, index))
                training_thread.start()

                flash(f'Training sedang berlangsung untuk Mahasiswa NIM {nim}', 'info')
            except Exception as e:
                flash(f'Training gagal: {str(e)}', 'danger')

        else:
            flash('Mahasiswa tidak ditemukan.', 'danger')

        return redirect(url_for('kelola_mahasiswa'))
    else:
        return redirect(url_for('admin_login'))

# Fungsi untuk menjalankan training di latar belakang
def background_training(mahasiswa_id, folder_path, nim, index):
    try:
        logging.info(f'Training dimulai untuk Mahasiswa ID {mahasiswa_id} dengan NIM {nim}')
        train_model(mahasiswa_id, nim, index)  # Panggil fungsi training dengan nim dan index
        db.mahasiswa.update_one({'_id': ObjectId(mahasiswa_id)}, {"$set": {"trained": True, "training_in_progress": False}})
        logging.info(f'Training selesai untuk Mahasiswa ID {mahasiswa_id}, NIM {nim}')

        # Hapus folder yang berisi foto setelah training selesai
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            logging.info(f'Folder foto di {folder_path} berhasil dihapus.')

    except Exception as e:
        logging.error(f'Training gagal untuk Mahasiswa ID {mahasiswa_id}: {str(e)}')
        db.mahasiswa.update_one({'_id': ObjectId(mahasiswa_id)}, {"$set": {"training_in_progress": False}})

# Endpoint untuk memeriksa status training secara real-time dengan progress
@app.route('/check_all_training_status')
def check_all_training_status():
    # Ambil semua mahasiswa yang sedang dalam proses training dan progressnya
    mahasiswa_in_training = list(db.mahasiswa.find({"training_in_progress": True}, {"_id": 1, "nama": 1, "progress": 1}))
    
    if mahasiswa_in_training:
        return {"status": "training_in_progress", "mahasiswa": mahasiswa_in_training}, 200
    
    return {"status": "no_training"}, 204

# Hapus Mahasiswa
@app.route('/admin/hapus_mahasiswa/<id>', methods=['POST', 'GET'])
def hapus_mahasiswa(id):
    if 'admin_logged_in' in session:
        mahasiswa = db.mahasiswa.find_one({"_id": ObjectId(id)})
        if mahasiswa:
            nim = mahasiswa['nim']  # Pastikan NIM diambil dari data mahasiswa

            # Hapus data mahasiswa dari database
            db.mahasiswa.delete_one({"_id": ObjectId(id)})
            flash('Mahasiswa berhasil dihapus.', 'success')

            # Hapus foto dari folder training/images
            image_path = os.path.join('training/images', str(mahasiswa['_id']))  # Gunakan ObjectId untuk path foto
            if os.path.exists(image_path):
                shutil.rmtree(image_path)  # Hapus seluruh folder beserta foto
                print(f"[INFO] Folder foto untuk mahasiswa ID {mahasiswa['_id']} berhasil dihapus.")

            # Hapus model mahasiswa dari folder models menggunakan NIM
            model_path = os.path.join('models', nim)  # Gunakan NIM untuk path model
            if os.path.exists(model_path):
                shutil.rmtree(model_path)  # Hapus seluruh folder beserta model
                print(f"[INFO] Folder model untuk mahasiswa dengan NIM {nim} berhasil dihapus.")

            # Perbarui data kelas yang berhubungan dengan mahasiswa ini
            db.kelas.update_many({}, {"$pull": {"mahasiswa": ObjectId(id)}})
            print(f"[INFO] Data kelas diperbarui, mahasiswa ID {mahasiswa['_id']} dihapus dari semua kelas.")

        else:
            flash('Mahasiswa tidak ditemukan.', 'danger')
            print(f"[ERROR] Mahasiswa dengan ID {id} tidak ditemukan di database.")

        return redirect(url_for('kelola_mahasiswa'))
    else:
        return redirect(url_for('admin_login'))

## RUTE PENGELOLAAN DOSEN

# Kelola Dosen
@app.route('/admin/kelola_dosen', methods=['GET', 'POST'])
def kelola_dosen():
    if 'admin_logged_in' in session:
        dosen = list(db.dosen.find())  # Ubah menjadi list
        return render_template('admin/dosen/kelola_dosen.html', dosen=dosen)
    else:
        return redirect(url_for('admin_login'))

# Tambah Dosen
@app.route('/admin/tambah_dosen', methods=['GET', 'POST'])
def tambah_dosen():
    if 'admin_logged_in' in session:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            nidn = request.form['nidn']
            nama = request.form['nama']
            email = request.form['email']
            nomor_hp = request.form['nomor_hp']

            # Cek apakah NIDN sudah ada
            existing_dosen = db.dosen.find_one({"nidn": nidn})
            if existing_dosen:
                flash('NIDN sudah digunakan, masukkan NIDN yang berbeda.', 'danger')
                return redirect(url_for('tambah_dosen'))

            # Simpan dosen baru ke database
            db.dosen.insert_one({
                "username": username,
                "password": password,
                "nidn": nidn,
                "nama": nama,
                "email": email,
                "nomor_hp": nomor_hp
            })
            flash('Dosen berhasil ditambahkan.', 'success')  # Flash message sukses
            return redirect(url_for('kelola_dosen'))  # Kembali ke halaman kelola dosen
        return render_template('admin/dosen/tambah_dosen.html')
    else:
        return redirect(url_for('admin_login'))

# Edit Dosen
@app.route('/admin/edit_dosen/<id>', methods=['GET', 'POST'])
def edit_dosen(id):
    if 'admin_logged_in' in session:
        dosen = db.dosen.find_one({"_id": ObjectId(id)})
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']  # Bisa kosong
            nidn = request.form['nidn']
            nama = request.form['nama']
            email = request.form['email']
            nomor_hp = request.form['nomor_hp']

            # Cek apakah NIDN sudah ada di dosen lain
            existing_dosen = db.dosen.find_one({"nidn": nidn, "_id": {"$ne": ObjectId(id)}})
            if existing_dosen:
                flash('NIDN sudah digunakan, masukkan NIDN yang berbeda.', 'danger')
                return redirect(url_for('edit_dosen', id=id))

            # Update data dosen tanpa mengubah password jika password kosong
            update_data = {
                "username": username,
                "nidn": nidn,
                "nama": nama,
                "email": email,
                "nomor_hp": nomor_hp
            }

            # Hanya update password jika diisi
            if password:
                update_data["password"] = password  # Tambahkan peng-hash-an jika perlu

            # Update data dosen
            db.dosen.update_one({"_id": ObjectId(id)}, {"$set": update_data})

            flash('Dosen berhasil diperbarui.', 'success')
            return redirect(url_for('kelola_dosen'))

        return render_template('admin/dosen/edit_dosen.html', dosen=dosen)
    else:
        return redirect(url_for('admin_login'))

# Hapus Dosen
@app.route('/admin/hapus_dosen/<id>', methods=['GET', 'POST'])
def hapus_dosen(id):
    if 'admin_logged_in' in session:
        db.dosen.delete_one({"_id": ObjectId(id)})
        flash('Dosen berhasil dihapus.', 'success')  # Pesan flash
        return redirect(url_for('kelola_dosen'))
    else:
        return redirect(url_for('admin_login'))

## RUTE PENGELOLAAN KELAS

# Kelola Kelas
@app.route('/admin/kelola_kelas', methods=['GET', 'POST'])
def kelola_kelas():
    if 'admin_logged_in' in session:
        # Gunakan lookup untuk mengambil data dosen dengan left join
        kelas_list = db.kelas.aggregate([
            {
                '$lookup': {
                    'from': 'dosen',
                    'localField': 'dosen_pengampu',
                    'foreignField': '_id',
                    'as': 'dosen'
                }
            },
            {
                '$unwind': {
                    'path': '$dosen',
                    'preserveNullAndEmptyArrays': True  # Ini memastikan bahwa kelas tetap muncul meskipun dosen tidak ditemukan
                }
            }
        ])

        # Membuat jadwal kelas sebagai gabungan hari, jam mulai, dan jam selesai
        kelas_data = []
        for kelas in kelas_list:
            jadwal_kelas = f"{kelas['hari']} {kelas['jam_mulai']} - {kelas['jam_selesai']}"
            kelas['jadwal_kelas'] = jadwal_kelas
            kelas_data.append(kelas)

        return render_template('admin/kelas/kelola_kelas.html', kelas_list=kelas_data)
    else:
        return redirect(url_for('admin_login'))

# Tambah Kelas
@app.route('/admin/tambah_kelas', methods=['GET', 'POST'])
def tambah_kelas():
    if 'admin_logged_in' in session:
        if request.method == 'POST':
            nama_kelas = request.form['nama_kelas']
            dosen_pengampu = ObjectId(request.form['dosen_pengampu'])
            hari = request.form['hari']
            jam_mulai_jam = request.form['jam_mulai_jam']
            jam_mulai_menit = request.form['jam_mulai_menit']
            jam_selesai_jam = request.form['jam_selesai_jam']
            jam_selesai_menit = request.form['jam_selesai_menit']

            # Gabungkan jam dan menit
            jam_mulai = f"{jam_mulai_jam}:{jam_mulai_menit}"
            jam_selesai = f"{jam_selesai_jam}:{jam_selesai_menit}"

            # Cek apakah ada kelas lain yang jadwalnya bertabrakan
            if cek_jadwal_bentrok(hari, jam_mulai, jam_selesai):
                # Jika ada jadwal bertabrakan, kembalikan pesan error
                flash('Jadwal kelas bertabrakan dengan kelas lain. Silakan pilih jadwal lain.', 'danger')
                return redirect(url_for('tambah_kelas'))

            # Simpan kelas jika tidak ada bentrok
            db.kelas.insert_one({
                "nama_kelas": nama_kelas,
                "dosen_pengampu": dosen_pengampu,
                "hari": hari,
                "jam_mulai": jam_mulai,
                "jam_selesai": jam_selesai,
                "mahasiswa": []
            })
            return redirect(url_for('kelola_kelas'))

        daftar_dosen = db.dosen.find()
        return render_template('admin/kelas/tambah_kelas.html', daftar_dosen=daftar_dosen)
    else:
        return redirect(url_for('admin_login'))

# Edit Kelas
@app.route('/admin/edit_kelas/<id>', methods=['GET', 'POST'])
def edit_kelas(id):
    if 'admin_logged_in' in session:
        # Ambil data kelas berdasarkan ID
        kelas = db.kelas.find_one({"_id": ObjectId(id)})

        # Lookup untuk mendapatkan data dosen berdasarkan dosen_pengampu
        if kelas:
            dosen_pengampu = db.dosen.find_one({"_id": kelas['dosen_pengampu']})
            kelas['dosen'] = dosen_pengampu  # Tambahkan data dosen ke dalam object kelas

        if request.method == 'POST':
            # Proses pengeditan data kelas
            # ...
            pass

        if request.method == 'POST':
            # Ambil data dari form yang diinputkan user
            nama_kelas = request.form['nama_kelas']
            dosen_pengampu = ObjectId(request.form['dosen_pengampu'])
            hari = request.form['hari']
            jam_mulai_jam = request.form['jam_mulai_jam']
            jam_mulai_menit = request.form['jam_mulai_menit']
            jam_selesai_jam = request.form['jam_selesai_jam']
            jam_selesai_menit = request.form['jam_selesai_menit']

            # Gabungkan jam dan menit
            jam_mulai = f"{jam_mulai_jam}:{jam_mulai_menit}"
            jam_selesai = f"{jam_selesai_jam}:{jam_selesai_menit}"

            # Cek apakah jadwal bentrok dengan kelas lain, kecuali kelas yang sedang diedit
            if cek_jadwal_bentrok(hari, jam_mulai, jam_selesai, kelas_id=ObjectId(id)):
                flash('Jadwal kelas bertabrakan dengan kelas lain. Silakan pilih jadwal lain.', 'danger')
                return redirect(url_for('edit_kelas', id=id))

            # Update data kelas di MongoDB
            db.kelas.update_one({"_id": ObjectId(id)}, {
                "$set": {
                    "nama_kelas": nama_kelas,
                    "dosen_pengampu": dosen_pengampu,
                    "hari": hari,
                    "jam_mulai": jam_mulai,
                    "jam_selesai": jam_selesai
                }
            })
            return redirect(url_for('kelola_kelas'))

        # Ambil daftar dosen untuk dropdown list di menu
        daftar_dosen = list(db.dosen.find())
        return render_template('admin/kelas/edit_kelas.html', kelas=kelas, daftar_dosen=daftar_dosen)
    else:
        return redirect(url_for('admin_login'))

# Fungsi untuk memeriksa bentrokan jadwal
def cek_jadwal_bentrok(hari, jam_mulai_baru, jam_selesai_baru, kelas_id=None):
    # Cari semua kelas yang ada di hari yang sama
    kelas_di_hari = db.kelas.find({"hari": hari})

    # Konversi waktu dari string ke format datetime
    jam_mulai_baru = datetime.strptime(jam_mulai_baru, '%H:%M')
    jam_selesai_baru = datetime.strptime(jam_selesai_baru, '%H:%M')

    for kelas in kelas_di_hari:
        if kelas_id and kelas['_id'] == kelas_id:
            continue  # Abaikan jika itu adalah kelas yang sedang diedit

        jam_mulai_ada = datetime.strptime(kelas['jam_mulai'], '%H:%M')
        jam_selesai_ada = datetime.strptime(kelas['jam_selesai'], '%H:%M')

        # Cek apakah ada tumpang tindih:
        if (jam_mulai_baru < jam_selesai_ada and jam_selesai_baru > jam_mulai_ada):
            return True  # Bentrok jadwal ditemukan
    return False  # Tidak ada bentrok

# Hapus Kelas
@app.route('/admin/hapus_kelas/<id>', methods=['POST', 'GET'])
def hapus_kelas(id):
    if 'admin_logged_in' in session:
        # Hapus kelas berdasarkan ID
        db.kelas.delete_one({"_id": ObjectId(id)})
        db.absensi.delete_many({"kelas_id": ObjectId(id)})

        # Kirim pesan flash untuk konfirmasi penghapusan
        flash('Kelas dan data absensinya berhasil dihapus.', 'success')

        # Redirect kembali ke halaman kelola kelas
        return redirect(url_for('kelola_kelas'))
    else:
        return redirect(url_for('admin_login'))

# Kelola Mahasiswa dalam Kelas
@app.route('/admin/kelola_kelas_mahasiswa/<id>', methods=['GET', 'POST'])
def kelola_kelas_mahasiswa(id):
    if 'admin_logged_in' in session:
        kelas = db.kelas.find_one({"_id": ObjectId(id)})
        daftar_mahasiswa = list(db.mahasiswa.find())
        
        return render_template('admin/kelas/kelola_kelas_mahasiswa.html', kelas=kelas, daftar_mahasiswa=daftar_mahasiswa)
    else:
        return redirect(url_for('admin_login'))

@app.route('/admin/simpan_mahasiswa_ke_kelas/<id>', methods=['POST'])
def simpan_mahasiswa_ke_kelas(id):
    if 'admin_logged_in' in session:
        mahasiswa_ids = [ObjectId(mhs_id) for mhs_id in request.form.getlist('mahasiswa[]')]
        
        # Update kelas dengan mahasiswa yang dipilih
        db.kelas.update_one({"_id": ObjectId(id)}, {"$set": {"mahasiswa": mahasiswa_ids}})
        
        return redirect(url_for('kelola_kelas'))
    else:
        return redirect(url_for('admin_login'))

## RUTE LAPORAN ABSENSI

#laporan absensi  
@app.route('/admin/laporan_absensi')
def laporan_absensi():
    if 'admin_logged_in' in session:
        # Ambil daftar kelas beserta detail
        kelas_list = list(db.kelas.aggregate([
            {
                '$lookup': {
                    'from': 'dosen',
                    'localField': 'dosen_pengampu',
                    'foreignField': '_id',
                    'as': 'dosen'
                }
            },
            {
                '$unwind': {
                    'path': '$dosen',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$project': {
                    'nama_kelas': 1,
                    'dosen.nama': 1,
                    'jumlah_mahasiswa': {'$size': '$mahasiswa'},
                    'hari': 1,
                    'jam_mulai': 1,
                    'jam_selesai': 1,
                    '_id': 1  # Pastikan kelas_id termasuk di sini
                }
            }
        ]))

        return render_template('admin/absensi/laporan_absensi.html', kelas_list=kelas_list)
    else:
        return redirect(url_for('admin_login'))

# Rute lihat absensi
@app.route('/admin/lihat_absensi/<kelas_id>')
def lihat_absensi(kelas_id):
    if 'admin_logged_in' in session:
        # Ambil data absensi berdasarkan kelas yang dipilih
        absensi_list = list(db.absensi.find(
            {'kelas_id': ObjectId(kelas_id)},  # Filter absensi berdasarkan kelas_id
            {
                'waktu_mulai': 1,
                'waktu_selesai': 1,
                'mahasiswa_hadir': 1
            }
        ))

        # Ambil data kelas untuk menghitung total mahasiswa
        kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})
        total_mahasiswa = len(kelas['mahasiswa'])  # Hitung total mahasiswa yang terdaftar di kelas

        # Kirim data absensi dan total_mahasiswa ke template
        return render_template('admin/absensi/lihat_absensi.html', absensi_list=absensi_list, kelas=kelas, total_mahasiswa=total_mahasiswa)
    else:
        return redirect(url_for('admin_login'))

#rute detail absensi
@app.route('/admin/lihat_detail_absensi/<kelas_id>/<absensi_id>')
def lihat_detail_absensi(kelas_id, absensi_id):
    if 'admin_logged_in' in session:
        # Ambil data absensi berdasarkan ID absensi yang dipilih
        absensi = db.absensi.find_one({
            '_id': ObjectId(absensi_id),
            'kelas_id': ObjectId(kelas_id)
        })

        if not absensi:
            flash("Data absensi tidak ditemukan untuk sesi ini", "danger")
            return redirect(url_for('lihat_absensi', kelas_id=kelas_id))

        # Ambil seluruh mahasiswa di kelas tersebut
        kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})
        mahasiswa_list = list(db.mahasiswa.find({"_id": {"$in": kelas['mahasiswa']}}, {'nama': 1, 'nim': 1}))

        # Siapkan data absensi dengan status kehadiran
        detail_absensi = []
        hadir_ids = {str(hadir['mahasiswa_id']) for hadir in absensi['mahasiswa_hadir']}

        for mahasiswa in mahasiswa_list:
            mahasiswa_id_str = str(mahasiswa['_id'])
            if mahasiswa_id_str in hadir_ids:
                hadir_mahasiswa = next(
                    (hadir for hadir in absensi['mahasiswa_hadir'] if str(hadir['mahasiswa_id']) == mahasiswa_id_str),
                    {}
                )
                detail_absensi.append({
                    'nama': mahasiswa['nama'],
                    'nim': mahasiswa['nim'],
                    'status': 'Terlambat' if hadir_mahasiswa.get('terlambat', False) else 'Hadir',
                    'waktu': hadir_mahasiswa['waktu_hadir'].strftime('%H:%M:%S')  # Hanya menampilkan waktu hadir
                })
            else:
                detail_absensi.append({
                    'nama': mahasiswa['nama'],
                    'nim': mahasiswa['nim'],
                    'status': 'Tidak Hadir',
                    'waktu': '-'  # Tidak hadir tidak memiliki waktu hadir
                })

        # Format tanggal absensi
        tanggal = absensi['waktu_mulai'].strftime('%d-%m-%Y')

        # Kirim data absensi, kelas, dan tanggal ke template HTML
        return render_template('admin/absensi/lihat_detail_absensi.html', detail_absensi=detail_absensi, kelas=kelas, absensi=absensi, tanggal=tanggal)
    else:
        return redirect(url_for('admin_login'))

#laporan per sesi
@app.route('/admin/unduh_laporan_absensi/<absensi_id>')
def unduh_laporan_absensi(absensi_id):
    if 'admin_logged_in' in session:
        # Ambil data absensi berdasarkan ID
        absensi = db.absensi.find_one({"_id": ObjectId(absensi_id)})

        if not absensi:
            flash("Absensi tidak ditemukan", "danger")
            return redirect(url_for('laporan_absensi'))

        # Ambil informasi kelas
        kelas = db.kelas.find_one({"_id": absensi['kelas_id']})
        dosen = db.dosen.find_one({"_id": kelas['dosen_pengampu']})

        # Ambil semua mahasiswa yang terdaftar di kelas tersebut
        mahasiswa_list = list(db.mahasiswa.find({"_id": {"$in": kelas['mahasiswa']}}))
        mahasiswa_dict = {str(mhs['_id']): mhs for mhs in mahasiswa_list}

        # Siapkan data absensi per mahasiswa
        absensi_data = {}
        waktu_mulai = absensi['waktu_mulai'].strftime('%H:%M:%S')
        waktu_selesai = absensi.get('waktu_selesai', 'N/A').strftime('%H:%M:%S') if absensi.get('waktu_selesai') else 'N/A'

        # Loop melalui absensi mahasiswa yang hadir di sesi ini
        for hadir in absensi['mahasiswa_hadir']:
            mahasiswa_id = hadir['mahasiswa_id']
            absensi_data[mahasiswa_id] = {
                'terlambat': hadir['terlambat'],
                'waktu_hadir': hadir['waktu_hadir'].strftime('%H:%M:%S')
            }

        # Siapkan data untuk laporan
        data = []
        for mhs_id, mhs_data in mahasiswa_dict.items():
            if mhs_id in absensi_data:
                status_kehadiran = "Terlambat" if absensi_data[mhs_id]['terlambat'] else "Hadir"
                waktu_hadir = absensi_data[mhs_id]['waktu_hadir']
            else:
                status_kehadiran = "Tidak Hadir"
                waktu_hadir = "N/A"

            data.append({
                "NIM": mhs_data['nim'],
                "Nama Mahasiswa": mhs_data['nama'],
                "Status Kehadiran": status_kehadiran,
                "Waktu Kehadiran": waktu_hadir
            })

        # Buat DataFrame dari data
        df = pd.DataFrame(data)

        # Simpan ke file Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Absensi Sesi')

            # Format header
            header_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#d9ead3'})
            merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
            time_format = workbook.add_format({'align': 'center'})
            border_format = workbook.add_format({'border': 1})

            # Tulis header laporan (Merge cells)
            tanggal_absensi = absensi['waktu_mulai'].strftime('%d-%m-%Y')
            worksheet.merge_range('A1:D1', f"Absensi Kelas {kelas['nama_kelas']} Tanggal {tanggal_absensi}", merge_format)
            worksheet.merge_range('A2:D2', f"Dosen: {dosen['nama']}     Jadwal: {kelas['jam_mulai']} - {kelas['jam_selesai']}", merge_format)
            worksheet.merge_range('A3:D3', f"Proses Absensi: {waktu_mulai} - {waktu_selesai}", merge_format)

            # Tulis header tabel
            worksheet.write(4, 0, "No", header_format)
            worksheet.write(4, 1, "NIM", header_format)
            worksheet.write(4, 2, "Nama Mahasiswa", header_format)
            worksheet.write(4, 3, "Status Kehadiran", header_format)
            worksheet.write(4, 4, "Waktu Kehadiran", header_format)

            # Tulis data absensi
            for idx, row in enumerate(df.itertuples(), start=1):
                worksheet.write(idx + 4, 0, idx, border_format)
                worksheet.write(idx + 4, 1, row.NIM, border_format)
                worksheet.write(idx + 4, 2, row._2, border_format)  # Nama Mahasiswa
                worksheet.write(idx + 4, 3, row._3, border_format)  # Status Kehadiran
                worksheet.write(idx + 4, 4, row._4, border_format)  # Waktu Kehadiran

        output.seek(0)

        return send_file(output, download_name=f'Absensi_{kelas["nama_kelas"]}_{tanggal_absensi}.xlsx', as_attachment=True)
    else:
        return redirect(url_for('admin_login'))

# Fungsi untuk menghitung persentase kehadiran
def hitung_persentase_kehadiran(hadir_list, total_sesi):
    hadir_count = len([h for h in hadir_list if h in ["Hadir", "Terlambat"]])
    return (hadir_count / total_sesi) * 100 if total_sesi > 0 else 0

# Rute untuk unduh rekapitulasi absensi
@app.route('/admin/unduh_rekapitulasi_absensi/<kelas_id>')
def unduh_rekapitulasi_absensi(kelas_id):
    if 'admin_logged_in' in session:
        # Ambil informasi kelas
        kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})
        dosen = db.dosen.find_one({"_id": kelas['dosen_pengampu']})
        absensi_list = db.absensi.find({'kelas_id': ObjectId(kelas_id)})

        # Siapkan data header untuk kelas
        kelas_info = [
            ['Nama Kelas:', kelas['nama_kelas']],
            ['Dosen Pengampu:', dosen['nama']],
            ['Jadwal:', f"{kelas['hari']} {kelas['jam_mulai']} - {kelas['jam_selesai']}"]
        ]

        # Ambil daftar mahasiswa
        mahasiswa_list = list(db.mahasiswa.find({"_id": {"$in": kelas['mahasiswa']}}))
        mahasiswa_dict = {str(mhs['_id']): mhs for mhs in mahasiswa_list}

        # Siapkan tanggal sesi dan kehadiran mahasiswa
        tanggal_list = []
        data_dict = {str(mhs['_id']): [] for mhs in mahasiswa_list}

        for absensi in absensi_list:
            tanggal = absensi['waktu_mulai'].strftime('%d-%m-%Y')
            tanggal_list.append(tanggal)
            for mhs_id in kelas['mahasiswa']:
                hadir = next((hadir for hadir in absensi['mahasiswa_hadir'] if hadir['mahasiswa_id'] == str(mhs_id)), None)
                nim = mahasiswa_dict[str(mhs_id)]['nim']
                if hadir:
                    if hadir['terlambat']:
                        data_dict[str(mhs_id)].append('Terlambat')
                    else:
                        data_dict[str(mhs_id)].append('Hadir')
                else:
                    data_dict[str(mhs_id)].append('Tidak Hadir')

        # Tambahkan kolom persentase kehadiran tanpa warna
        for mhs_id, kehadiran_list in data_dict.items():
            total_hadir = kehadiran_list.count('Hadir') + kehadiran_list.count('Terlambat')
            total_sesi = len(tanggal_list)
            persentase = (total_hadir / total_sesi) * 100 if total_sesi > 0 else 0
            data_dict[mhs_id].append(f"{persentase:.2f}%")

        # Buat DataFrame dengan sesi absensi sebagai kolom dan mahasiswa sebagai baris
        df = pd.DataFrame(data_dict, index=tanggal_list + ['Persentase']).T

        # Simpan ke Excel di memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Rekap Absensi')

            # Format header dan tabel
            header_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#d9ead3', 'border': 1})
            hadir_format = workbook.add_format({'bg_color': '#b6d7a8', 'border': 1})
            terlambat_format = workbook.add_format({'bg_color': '#f9cb9c', 'border': 1})
            tidak_hadir_format = workbook.add_format({'bg_color': '#e06666', 'border': 1})
            nomor_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})

            # Tulis informasi kelas di atas tabel tanpa border
            worksheet.write('A1', f"Daftar Hadir Kelas {kelas['nama_kelas']}")
            worksheet.write('A2', 'Dosen:')
            worksheet.merge_range('B2:D2', dosen['nama'])
            worksheet.write('A3', 'Jadwal:')
            worksheet.merge_range('B3:D3', f"{kelas['hari']} {kelas['jam_mulai']} - {kelas['jam_selesai']}")

            # Jarak tabel dari informasi kelas
            row_offset = len(kelas_info) + 2

            # Tulis header tabel dengan jarak ke bawah
            worksheet.write(row_offset, 0, "No", header_format)
            worksheet.write(row_offset, 1, "NIM", header_format)
            worksheet.write(row_offset, 2, "Nama Mahasiswa", header_format)
            for col_num, col_name in enumerate(tanggal_list):
                worksheet.write(row_offset, col_num + 3, col_name, header_format)
            worksheet.write(row_offset, len(tanggal_list) + 3, "Persentase Kehadiran", header_format)

            # Tulis daftar mahasiswa dan data absensi
            for row_num, (mhs_id, row_data) in enumerate(df.iterrows()):
                worksheet.write(row_offset + row_num + 1, 0, row_num + 1, nomor_format)  # No
                worksheet.write(row_offset + row_num + 1, 1, mahasiswa_dict[mhs_id]['nim'], nomor_format)  # NIM
                worksheet.write(row_offset + row_num + 1, 2, mahasiswa_dict[mhs_id]['nama'], nomor_format)  # Nama Mahasiswa
                for col_num, cell_value in enumerate(row_data[:-1]):  # Kolom terakhir adalah persentase, tidak ada warna
                    if cell_value == 'Hadir':
                        worksheet.write(row_offset + row_num + 1, col_num + 3, cell_value, hadir_format)
                    elif cell_value == 'Terlambat':
                        worksheet.write(row_offset + row_num + 1, col_num + 3, cell_value, terlambat_format)
                    else:
                        worksheet.write(row_offset + row_num + 1, col_num + 3, cell_value, tidak_hadir_format)
                # Tulis persentase kehadiran tanpa warna
                worksheet.write(row_offset + row_num + 1, len(tanggal_list) + 3, row_data[-1], nomor_format)

        # Setelah selesai menulis, pindahkan posisi pointer ke awal
        output.seek(0)

        return send_file(output, download_name=f'Rekapitulasi_Absensi_Kelas_{kelas["nama_kelas"]}.xlsx', as_attachment=True)
    else:
        return redirect(url_for('admin_login'))

#########################################
#Pada Bagian ini adalah rute untuk dosen#
#########################################

# Rute Login Dosen
@app.route('/dosen/login', methods=['GET', 'POST'])
def dosen_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Cari user dosen di database MongoDB
        dosen = db.dosen.find_one({"username": username})

        if dosen and dosen['password'] == password:  # Jika password tidak di-hash
            session['dosen_logged_in'] = True
            session['dosen_id'] = str(dosen['_id'])  # Simpan ID dosen ke session
            session['dosen_name'] = dosen['nama']    # Simpan nama dosen ke session
            return redirect(url_for('dosen_dashboard'))
        else:
            error = 'Login Gagal: Username atau Password salah.'
            return render_template('main/login.html', error=error)
    return render_template('main/login.html')

# Rute Logout Dosen
@app.route('/dosen/logout')
def dosen_logout():
    session.pop('dosen_logged_in', None)
    session.pop('dosen_id', None)
    session.pop('dosen_name', None)
    return redirect(url_for('dosen_login'))

# Rute Dashboard Dosen
@app.route('/dosen/dashboard')
def dosen_dashboard():
    if 'dosen_logged_in' in session:
        dosen_id = session.get('dosen_id')
        kelas_list = list(db.kelas.find({"dosen_pengampu": ObjectId(dosen_id)}))
        
        # Mengambil semua ObjectId mahasiswa dari kelas yang diajar
        mahasiswa_ids = [ObjectId(mahasiswa_id) for kelas in kelas_list for mahasiswa_id in kelas['mahasiswa']]
        
        # Menghitung jumlah mahasiswa berdasarkan mahasiswa_ids
        mahasiswa_count = db.mahasiswa.count_documents({"_id": {"$in": mahasiswa_ids}})
        
        # Menghitung jumlah absensi berdasarkan kelas yang diajar
        absensi_count = db.absensi.count_documents({"kelas_id": {"$in": [ObjectId(kelas['_id']) for kelas in kelas_list]}})
        
        return render_template('main/dashboard.html', 
                               kelas_list=kelas_list, 
                               mahasiswa_count=mahasiswa_count,
                               absensi_count=absensi_count, 
                               dosen_name=session.get('dosen_name'))
    else:
        return redirect(url_for('dosen_login'))

#rute list kelas
@app.route('/dosen/kelas')
def dosen_kelas():
    if 'dosen_logged_in' in session:
        dosen_id = session.get('dosen_id')
        kelas_list = list(db.kelas.find({"dosen_pengampu": ObjectId(dosen_id)}))
        return render_template('main/kelas/lihat_kelas.html', kelas_list=kelas_list)
    else:
        return redirect(url_for('dosen_login'))

# Rute untuk Melihat Detail Kelas yang Diajar oleh Dosen
@app.route('/dosen/kelas/<id>')
def dosen_detail_kelas(id):
    if 'dosen_logged_in' in session:
        kelas = db.kelas.find_one({"_id": ObjectId(id)})
        mahasiswa_list = db.mahasiswa.find({"_id": {"$in": kelas['mahasiswa']}})
        return render_template('main/kelas/detail_kelas.html', kelas=kelas, mahasiswa_list=mahasiswa_list)
    else:
        return redirect(url_for('dosen_login'))

# Rute untuk Melihat Daftar Mahasiswa yang Berkaitan dengan Dosen
@app.route('/dosen/mahasiswa')
def dosen_mahasiswa():
    if 'dosen_logged_in' in session:
        dosen_id = session.get('dosen_id')
        kelas_list = list(db.kelas.find({"dosen_pengampu": ObjectId(dosen_id)}))
        mahasiswa_ids = set()
        for kelas in kelas_list:
            mahasiswa_ids.update(kelas['mahasiswa'])
        mahasiswa_list = list(db.mahasiswa.find({"_id": {"$in": list(mahasiswa_ids)}}))
        return render_template('main/mahasiswa/lihat_mahasiswa.html', mahasiswa_list=mahasiswa_list)
    else:
        return redirect(url_for('dosen_login'))

# Rute untuk Melihat Detail Mahasiswa
@app.route('/dosen/mahasiswa/<id>')
def dosen_detail_mahasiswa(id):
    if 'dosen_logged_in' in session:
        mahasiswa = db.mahasiswa.find_one({"_id": ObjectId(id)})
        return render_template('main/mahasiswa/detail_mahasiswa.html', mahasiswa=mahasiswa)
    else:
        return redirect(url_for('dosen_login'))

# Rute untuk Melihat Rekap Absensi
@app.route('/dosen/absensi')
def dosen_absensi():
    if 'dosen_logged_in' in session:
        dosen_id = session.get('dosen_id')
        kelas_list = list(db.kelas.find({"dosen_pengampu": ObjectId(dosen_id)}))
        absensi_list = []
        for kelas in kelas_list:
            absensi_list.extend(list(db.absensi.find({"kelas_id": ObjectId(kelas['_id'])})))
        return render_template('main/absensi/lihat_absensi.html', absensi_list=absensi_list)
    else:
        return redirect(url_for('dosen_login'))

# Rute untuk Mengunduh Rekap Absensi
@app.route('/dosen/unduh_absensi')
def dosen_unduh_absensi():
    if 'dosen_logged_in' in session:
        dosen_id = session.get('dosen_id')
        kelas_list = list(db.kelas.find({"dosen_pengampu": ObjectId(dosen_id)}))
        absensi_list = []
        for kelas in kelas_list:
            absensi_list.extend(list(db.absensi.find({"kelas_id": ObjectId(kelas['_id'])})))
        
        # Buat laporan absensi ke Excel # testing fitur
        import pandas as pd
        data = [{
            "Tanggal": absensi['tanggal'],
            "Nama Kelas": db.kelas.find_one({"_id": ObjectId(absensi['kelas_id'])})['nama_kelas'],
            "Nama Mahasiswa": db.mahasiswa.find_one({"_id": ObjectId(absensi['mahasiswa_id'])})['nama'],
            "Status Kehadiran": absensi['status']
        } for absensi in absensi_list]

        df = pd.DataFrame(data)
        file_path = "/tmp/rekap_absensi.xlsx"
        df.to_excel(file_path, index=False)

        return send_file(file_path, as_attachment=True)
    else:
        return redirect(url_for('dosen_login'))

# rute start dan stop absensi

# variabel global rute absensi
face_recognition_process = None

# Route untuk memulai absensi oleh admin
@app.route('/admin/start_kelas/<kelas_id>', methods=['POST'])
def start_kelas(kelas_id):
    global face_recognition_process

    kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})

    # Periksa jika tidak ada mahasiswa
    if not kelas['mahasiswa']:
        return jsonify({"success": False, "message": "Tidak ada mahasiswa di kelas ini"})

    # Hentikan proses face recognition sebelumnya jika ada
    if face_recognition_process and face_recognition_process.poll() is None:
        face_recognition_process.terminate()
        face_recognition_process.wait()

    # Jalankan subprocess untuk face recognition
    face_recognition_process = subprocess.Popen(['python3', 'face_recognition.py', str(kelas_id)])

    # Update status kelas di MongoDB
    waktu_mulai_absensi = datetime.now()
    db.kelas.update_one({"_id": ObjectId(kelas_id)}, {"$set": {"status": "Berlangsung", "waktu_mulai_absensi": waktu_mulai_absensi}})

    return jsonify({"success": True, "message": f"Kelas {kelas['nama_kelas']} dimulai."})

# Route untuk menghentikan absensi
@app.route('/admin/stop_kelas/<kelas_id>', methods=['POST'])
def stop_kelas(kelas_id):
    global face_recognition_process

    print(f"Kelas ID yang diterima: {kelas_id}")

    # Jika ada proses face recognition yang berjalan, hentikan prosesnya
    if face_recognition_process is not None and face_recognition_process.poll() is None:
        face_recognition_process.terminate()
        face_recognition_process.wait()
        face_recognition_process = None
        print("Proses face recognition dihentikan.")

    # Update status kelas dan absensi di MongoDB
    waktu_selesai_absensi = datetime.now()
    db.absensi.update_one(
        {"kelas_id": ObjectId(kelas_id), "status": "Berlangsung"},
        {"$set": {"status": "Tidak Berlangsung", "waktu_selesai": waktu_selesai_absensi}}
    )
    db.kelas.update_one(
        {"_id": ObjectId(kelas_id)},
        {"$set": {"status": "Tidak Berlangsung"}}
    )

    return jsonify({"success": True, "message": f"Proses face recognition untuk kelas {kelas_id} dihentikan."})

if __name__ == '__main__':
    app.run(debug=True)

