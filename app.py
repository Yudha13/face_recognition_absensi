from cProfile import label
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, SECRET_KEY
from bson.objectid import ObjectId
import pandas as pd
from flask import send_file
from datetime import datetime
import os
import shutil
from werkzeug.utils import secure_filename
from training.train_model import train_model  # Fungsi untuk training model
from flask import session
import threading
import logging
import cv2

app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

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
    # Ambil status kelas yang sedang berlangsung dari database
    kelas_berlangsung = db.kelas.find_one({"kelas_berlangsung": True})

    if kelas_berlangsung:
        return {"status": "kelas_berlangsung", "nama_kelas": kelas_berlangsung["nama_kelas"]}
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
                return render_template('admin/mahasiswa/tambah_mahasiswa.html')  # Tetap di halaman tambah mahasiswa
            
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

            # Hanya proses jika ada file yang diunggah dan valid
            if foto_mahasiswa and foto_mahasiswa[0].filename != '':
                path = os.path.join('training/images', mahasiswa_id)
                if not os.path.exists(path):
                    os.makedirs(path)

                for foto in foto_mahasiswa:
                    if foto and foto.filename != '':  # Pastikan foto valid
                        filename = secure_filename(foto.filename)
                        foto.save(os.path.join(path, filename))

                # Mulai training jika ada minimal 10 foto
                if len(foto_mahasiswa) >= 10:
                    session['training_status'] = f"Training sedang berlangsung untuk mahasiswa NIM: {nim}"
                    train_model(mahasiswa_id)  # Lakukan training model
                    session['training_status'] = f"Training selesai untuk mahasiswa NIM: {nim}"
                    db.mahasiswa.update_one({'_id': ObjectId(mahasiswa_id)}, {"$set": {"trained": True}})
                    flash('Mahasiswa berhasil ditambahkan dan model berhasil di-train.', 'success')
                else:
                    flash('Mahasiswa berhasil ditambahkan, namun perlu upload minimal 10 foto untuk training.', 'warning')
            else:
                flash('Mahasiswa berhasil ditambahkan, namun tidak ada foto yang diunggah.', 'info')

            # Redirect setelah POST untuk memunculkan flash message
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
                    return render_template('admin/mahasiswa/edit_mahasiswa.html', mahasiswa=mahasiswa)  # Tetap di halaman edit mahasiswa
                
                # Update data mahasiswa di database
                db.mahasiswa.update_one({'_id': ObjectId(id)}, {
                    "$set": {
                        'nim': nim,
                        'nama': nama,
                        'email': email,
                        'nomor_hp': nomor_hp
                    }
                })

                # Proses unggah foto hanya jika ada file yang diunggah
                if foto_mahasiswa and foto_mahasiswa[0].filename != '':
                    folder_path = os.path.join('training/images', str(mahasiswa['_id']))

                    # Buat direktori jika belum ada
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)

                    # Simpan foto yang diunggah
                    for foto in foto_mahasiswa:
                        filename = secure_filename(foto.filename)
                        foto.save(os.path.join(folder_path, filename))

                # Proses training ulang
                if 'retrain' in request.form:
                    folder_path = os.path.join('training/images', str(mahasiswa['_id']))

                    # Cek apakah folder berisi foto
                    if not os.path.exists(folder_path) or len(os.listdir(folder_path)) < 10:
                        flash('Training gagal. Tidak ada cukup foto untuk mahasiswa ini. Minimal 10 foto diperlukan.', 'danger')
                    else:
                        try:
                            train_model(str(mahasiswa['_id']))
                            db.mahasiswa.update_one({'_id': ObjectId(id)}, {"$set": {"trained": True}})
                            flash('Training ulang berhasil.', 'success')
                        except Exception as e:
                            flash(f'Training ulang gagal: {str(e)}', 'danger')

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
                
                # Jalankan training di thread terpisah
                training_thread = threading.Thread(target=background_training, args=(str(mahasiswa['_id']),))
                training_thread.start()

                flash(f'Training sedang berlangsung untuk Mahasiswa ID {mahasiswa["_id"]}', 'info')
            except Exception as e:
                flash(f'Training gagal: {str(e)}', 'danger')

        else:
            flash('Mahasiswa tidak ditemukan.', 'danger')

        return redirect(url_for('kelola_mahasiswa'))
    else:
        return redirect(url_for('admin_login'))

# Fungsi untuk menjalankan training di latar belakang
def background_training(mahasiswa_id):
    try:
        logging.info(f'Training dimulai untuk Mahasiswa ID {mahasiswa_id}')
        train_model(mahasiswa_id)  # Fungsi training model
        db.mahasiswa.update_one({'_id': ObjectId(mahasiswa_id)}, {"$set": {"trained": True, "training_in_progress": False}})
        logging.info(f'Training selesai untuk Mahasiswa ID {mahasiswa_id}')
    except Exception as e:
        logging.error(f'Training gagal untuk Mahasiswa ID {mahasiswa_id}: {str(e)}')

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
            mahasiswa_id = str(mahasiswa['_id'])

            # Hapus data mahasiswa dari database
            db.mahasiswa.delete_one({"_id": ObjectId(id)})
            flash('Mahasiswa berhasil dihapus.', 'success')

            # Hapus foto dari folder training/images
            image_path = os.path.join('training/images', mahasiswa_id)
            if os.path.exists(image_path):
                shutil.rmtree(image_path)  # Hapus seluruh folder beserta foto

            # Hapus model mahasiswa dari folder models
            model_path = os.path.join('models', mahasiswa_id)
            if os.path.exists(model_path):
                shutil.rmtree(model_path)  # Hapus seluruh folder beserta model
            
            # Pastikan status 'trained' tidak aktif
            db.mahasiswa.update_one({'_id': ObjectId(id)}, {"$set": {"trained": False}})

            # Perbarui data kelas yang berhubungan dengan mahasiswa ini
            db.kelas.update_many({}, {"$pull": {"mahasiswa": ObjectId(id)}})

        else:
            flash('Mahasiswa tidak ditemukan.', 'danger')

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
            nama = request.form['nama']
            email = request.form['email']
            nomor_hp = request.form['nomor_hp']
            db.dosen.insert_one({
                "username": username,
                "password": password,
                "nama": nama,
                "email": email,
                "nomor_hp": nomor_hp
            })
            return redirect(url_for('kelola_dosen'))
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
            password = request.form['password']
            nama = request.form['nama']
            email = request.form['email']
            nomor_hp = request.form['nomor_hp']
            db.dosen.update_one({"_id": ObjectId(id)}, {
                "$set": {
                    "username": username,
                    "password": password,
                    "nama": nama,
                    "email": email,
                    "nomor_hp": nomor_hp
                }
            })
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

        # Kirim pesan flash untuk konfirmasi penghapusan
        flash('Kelas berhasil dihapus.', 'success')

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

#rute lihat absensi
@app.route('/admin/lihat_absensi/<kelas_id>')
def lihat_absensi(kelas_id):
    if 'admin_logged_in' in session:
        # Ambil data absensi berdasarkan kelas yang dipilih
        absensi_list = list(db.absensi.aggregate([
            {
                '$match': {
                    'kelas_id': ObjectId(kelas_id)
                }
            },
            {
                '$group': {
                    '_id': {'$dateToString': { 'format': '%d-%m-%Y', 'date': '$waktu' }},  # Ekstrak tanggal dari waktu
                    'jumlah_hadir': {'$sum': 1}
                }
            }
        ]))

        kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})

        return render_template('admin/absensi/lihat_absensi.html', absensi_list=absensi_list, kelas=kelas)
    else:
        return redirect(url_for('admin_login'))

#rute detail absensi
@app.route('/admin/lihat_detail_absensi/<kelas_id>/<tanggal>')
def lihat_detail_absensi(kelas_id, tanggal):
    if 'admin_logged_in' in session:
        from datetime import datetime
        try:
            # Parse tanggal dengan format yang sesuai
            tanggal_awal = datetime.strptime(tanggal, '%d-%m-%Y')
            tanggal_akhir = tanggal_awal.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash("Format tanggal tidak valid", "danger")
            return redirect(url_for('laporan_absensi'))

        # Ambil data absensi untuk kelas_id dan tanggal yang sesuai
        absensi_list = list(db.absensi.find({
            'kelas_id': ObjectId(kelas_id),
            'waktu': {'$gte': tanggal_awal, '$lte': tanggal_akhir}
        }))

        if not absensi_list:
            flash("Tidak ada absensi ditemukan untuk tanggal ini", "danger")
            return redirect(url_for('lihat_absensi', kelas_id=kelas_id))

        # Ambil data mahasiswa yang hadir pada absensi tersebut
        mahasiswa_ids = list(set(ObjectId(absensi['mahasiswa_id']) for absensi in absensi_list))
        mahasiswa_list = list(db.mahasiswa.find({"_id": {"$in": mahasiswa_ids}}, {'nama': 1, 'nim': 1}))

        # Gabungkan data absensi dan mahasiswa untuk ditampilkan
        detail_absensi = []
        for absensi in absensi_list:
            mahasiswa = next((mhs for mhs in mahasiswa_list if str(mhs['_id']) == absensi['mahasiswa_id']), None)
            if mahasiswa:
                detail_absensi.append({
                    'nama': mahasiswa['nama'],
                    'nim': mahasiswa.get('nim', 'N/A'),  # NIM jika ada, jika tidak tampilkan 'N/A'
                    'status': absensi['status'],
                    'waktu': absensi['waktu'].strftime('%d-%m-%Y %H:%M:%S')
                })

        return render_template('admin/absensi/lihat_detail_absensi.html', detail_absensi=detail_absensi, tanggal=tanggal, kelas_id=kelas_id)
    else:
        return redirect(url_for('admin_login'))

#mengunduh laporan absensi
@app.route('/admin/unduh_laporan_absensi')
def unduh_laporan_absensi():
    if 'admin_logged_in' in session:
        laporan_absensi = list(db.absensi.find())

        # Membuat DataFrame untuk laporan absensi
        data = []
        for absensi in laporan_absensi:
            data.append({
                "Tanggal": absensi['tanggal'],
                "Nama Kelas": absensi['nama_kelas'],
                "Nama Mahasiswa": absensi['nama_mahasiswa'],
                "Status Kehadiran": absensi['status']
            })
        
        df = pd.DataFrame(data)

        # Menyimpan DataFrame ke file Excel
        file_path = "/tmp/laporan_absensi.xlsx"
        df.to_excel(file_path, index=False)

        return send_file(file_path, as_attachment=True)
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

#########################
#FUNGSI FACE RECOGNITION#
#########################

# Inisialisasi variabel flag global untuk menghentikan loop kamera
running = False
capture = None  # Tambahkan variabel capture global agar bisa diakses dari berbagai fungsi

# Fungsi untuk proses absensi
def start_class(kelas_id):
    global running, capture
    running = True
    print(f"Memulai absensi untuk kelas {kelas_id}")

    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        print("Kamera tidak bisa dibuka")
        return

    # Buat jendela kamera dengan opsi fleksibel
    cv2.namedWindow('Camera', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Camera', 640, 480)

    # Path ke file haarcascade dan model
    face_cascade = cv2.CascadeClassifier('utils/haarcascade_frontalface_default.xml')

    # Ambil mahasiswa yang terdaftar di kelas ini
    kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})
    mahasiswa_ids = kelas['mahasiswa']
    mahasiswa_list = db.mahasiswa.find({"_id": {"$in": mahasiswa_ids}})
    
    # Cache model mahasiswa untuk menghindari loading berulang
    recognizer_dict = {}
    id_to_mahasiswa = {}  # Mapping dari label ke Mahasiswa ID
    for index, mahasiswa in enumerate(mahasiswa_list):
        mahasiswa_id = str(mahasiswa['_id'])  # Menggunakan ObjectId sebagai string
        model_path = os.path.join('models', mahasiswa_id, f'{mahasiswa_id}_model.yml')
        if os.path.exists(model_path):
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(model_path)
            recognizer_dict[index] = recognizer  # Gunakan index sebagai label
            id_to_mahasiswa[index] = mahasiswa_id  # Mapping label (index) ke Mahasiswa ID
            print(f"Model untuk Mahasiswa ID {mahasiswa_id} berhasil dimuat.")  # Log untuk model yang dimuat

    # Set untuk menyimpan Mahasiswa ID yang sudah terdaftar hadir
    hadir_set = set()

    while running:  # Loop berdasarkan flag running
        ret, frame = capture.read()

        if not ret:
            print("[ERROR] Tidak dapat membaca frame dari kamera")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))

        if len(faces) == 0:
            print("[INFO] Tidak ada wajah terdeteksi pada frame ini.")
        
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]

            # Kotak merah default untuk wajah yang tidak dikenali
            color = (0, 0, 255)  # Merah

            # Loop melalui semua mahasiswa untuk memproses model masing-masing
            recognized = False  # Flag untuk menandai apakah wajah dikenali
            for label, recognizer in recognizer_dict.items():
                predicted_label, confidence = recognizer.predict(face_roi)

                # Validasi label yang dihasilkan dan confidence
                if confidence < 80 and predicted_label == label:  # Cocokkan label dengan index yang benar
                    mahasiswa_id = id_to_mahasiswa[label]  # Ambil Mahasiswa ID berdasarkan label

                    if label not in hadir_set:
                        print(f"[INFO] Wajah dengan ID {mahasiswa_id} dikenali dengan confidence {confidence}")

                        # Tandai bahwa wajah terdeteksi
                        color = (0, 255, 0)  # Hijau untuk wajah yang sudah hadir
                        cv2.putText(frame, f"ID: {mahasiswa_id}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                        cv2.putText(frame, "Hadir", (x, y+h+30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

                        # Simpan absensi dengan informasi kelas jika belum tercatat
                        db.absensi.insert_one({
                            'mahasiswa_id': mahasiswa_id,
                            'kelas_id': ObjectId(kelas_id),  # Tambahkan ID kelas
                            'waktu': datetime.now(),
                            'status': 'Hadir'
                        })
                        print(f"[INFO] Mahasiswa ID {mahasiswa_id} ditambahkan ke database sebagai 'Hadir'.")  # Log ke database
                        
                        # Tambahkan ID ke set hadir untuk menghindari pencatatan ganda
                        hadir_set.add(label)
                    else:
                        print(f"[INFO] Wajah dengan ID {mahasiswa_id} sudah terdeteksi sebagai hadir.")
                        color = (0, 255, 0)  # Tetap hijau jika sudah hadir
                        cv2.putText(frame, f"ID: {mahasiswa_id}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                        cv2.putText(frame, "Sudah Hadir", (x, y+h+30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

                    recognized = True
                    break

            if not recognized:
                # Jika wajah dikenali tapi bukan dari kelas ini
                if confidence < 80:
                    color = (255, 0, 0)  # Biru untuk wajah yang bukan dari kelas ini
                    cv2.putText(frame, "Bukan dari kelas ini", (x, y+h+30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

            # Gambar kotak sesuai hasil deteksi
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

        # Tampilkan frame di jendela kamera
        cv2.imshow('Camera', frame)

        # Periksa apakah jendela perlu diubah ukuran secara manual
        if cv2.getWindowProperty('Camera', cv2.WND_PROP_VISIBLE) < 1:
            break

        # Keluar dari loop jika tombol 'q' ditekan
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.release()
    cv2.destroyAllWindows()
    print("[INFO] Proses absensi kelas dihentikan.")

# Route untuk memulai kelas oleh admin
@app.route('/admin/start_kelas/<kelas_id>', methods=['POST'])
def start_kelas(kelas_id):
    if 'admin_logged_in' in session:
        kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})

        if kelas:
            # Tandai bahwa kelas sedang berlangsung
            db.kelas.update_one({"_id": ObjectId(kelas_id)}, {"$set": {"kelas_berlangsung": True}})
            
            # Mulai proses absensi untuk seluruh mahasiswa dalam satu kelas
            threading.Thread(target=start_class, args=(kelas_id,)).start()  # Mulai kelas untuk semua mahasiswa di kelas
            
            flash(f"Kelas {kelas['nama_kelas']} dimulai.", "success")
        else:
            flash("Kelas tidak ditemukan.", "danger")

        return redirect(url_for('kelola_kelas'))
    else:
        return redirect(url_for('admin_login'))

# Route untuk menghentikan kelas
@app.route('/stop_class', methods=['POST'])
def stop_class():
    global running, capture
    running = False  # Atur flag running menjadi False untuk menghentikan loop kamera

    # Hentikan kamera jika masih terbuka di thread
    try:
        if capture and capture.isOpened():
            capture.release()
        cv2.destroyAllWindows()

        # Update status kelas di database menjadi tidak berlangsung
        db.kelas.update_many({}, {"$set": {"kelas_berlangsung": False}})
        
        return {"success": True, "message": "Kelas berhasil dihentikan."}
    except Exception as e:
        return {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}

if __name__ == '__main__':
    app.run(debug=True)


