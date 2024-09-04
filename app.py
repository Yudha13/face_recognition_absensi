from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, SECRET_KEY
from bson.objectid import ObjectId
import pandas as pd
from flask import send_file

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
        jumlah_laporan_absensi = db.absensi.count_documents({})
        return render_template('admin/dashboard.html', 
                               jumlah_mahasiswa=jumlah_mahasiswa, 
                               jumlah_dosen=jumlah_dosen, 
                               jumlah_kelas=jumlah_kelas, 
                               jumlah_laporan_absensi=jumlah_laporan_absensi)
    else:
        return redirect(url_for('admin_login'))

# Kelola Mahasiswa
@app.route('/admin/kelola_mahasiswa', methods=['GET', 'POST'])
def kelola_mahasiswa():
    if 'admin_logged_in' in session:
        mahasiswa = db.mahasiswa.find()
        return render_template('admin/mahasiswa/kelola_mahasiswa.html', mahasiswa=mahasiswa)
    else:
        return redirect(url_for('admin_login'))

# Tambah Mahasiswa
@app.route('/admin/tambah_mahasiswa', methods=['GET', 'POST'])
def tambah_mahasiswa():
    if 'admin_logged_in' in session:
        if request.method == 'POST':
            nim = request.form['nim']
            nama = request.form['nama']
            email = request.form['email']
            nomor_hp = request.form['nomor_hp']
            db.mahasiswa.insert_one({
                "nim": nim,
                "nama": nama,
                "email": email,
                "nomor_hp": nomor_hp
            })
            return redirect(url_for('kelola_mahasiswa'))
        return render_template('admin/mahasiswa/tambah_mahasiswa.html')
    else:
        return redirect(url_for('admin_login'))

# Edit Mahasiswa
@app.route('/admin/edit_mahasiswa/<id>', methods=['GET', 'POST'])
def edit_mahasiswa(id):
    if 'admin_logged_in' in session:
        mahasiswa = db.mahasiswa.find_one({"_id": ObjectId(id)})
        if request.method == 'POST':
            nim = request.form['nim']
            nama = request.form['nama']
            email = request.form['email']
            nomor_hp = request.form['nomor_hp']
            db.mahasiswa.update_one({"_id": ObjectId(id)}, {
                "$set": {
                    "nim": nim,
                    "nama": nama,
                    "email": email,
                    "nomor_hp": nomor_hp
                }
            })
            return redirect(url_for('kelola_mahasiswa'))
        return render_template('admin/mahasiswa/edit_mahasiswa.html', mahasiswa=mahasiswa)
    else:
        return redirect(url_for('admin_login'))

# Hapus Mahasiswa
@app.route('/admin/hapus_mahasiswa/<id>', methods=['POST'])
def hapus_mahasiswa(id):
    if 'admin_logged_in' in session:
        # Hapus mahasiswa dari koleksi mahasiswa
        db.mahasiswa.delete_one({"_id": ObjectId(id)})

        # Perbarui semua kelas yang memiliki mahasiswa ini
        db.kelas.update_many({}, {"$pull": {"mahasiswa": ObjectId(id)}})

        return redirect(url_for('kelola_mahasiswa'))
    else:
        return redirect(url_for('admin_login'))

# Kelola Dosen
@app.route('/admin/kelola_dosen', methods=['GET', 'POST'])
def kelola_dosen():
    if 'admin_logged_in' in session:
        dosen = db.dosen.find()
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
@app.route('/admin/hapus_dosen/<id>', methods=['POST'])
def hapus_dosen(id):
    if 'admin_logged_in' in session:
        db.dosen.delete_one({"_id": ObjectId(id)})
        return redirect(url_for('kelola_dosen'))
    else:
        return redirect(url_for('admin_login'))

# Kelola Kelas
@app.route('/admin/kelola_kelas', methods=['GET', 'POST'])
def kelola_kelas():
    if 'admin_logged_in' in session:
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
                '$unwind': '$dosen'
            }
        ])
        return render_template('admin/kelas/kelola_kelas.html', kelas_list=kelas_list)
    else:
        return redirect(url_for('admin_login'))

# Tambah Kelas
@app.route('/admin/tambah_kelas', methods=['GET', 'POST'])
def tambah_kelas():
    if 'admin_logged_in' in session:
        if request.method == 'POST':
            nama_kelas = request.form['nama_kelas']
            dosen_pengampu = ObjectId(request.form['dosen_pengampu'])
            jadwal_kelas = request.form['jadwal_kelas']
            mahasiswa = [ObjectId(mhs_id) for mhs_id in request.form.getlist('mahasiswa[]')]
            
            db.kelas.insert_one({
                "nama_kelas": nama_kelas,
                "dosen_pengampu": dosen_pengampu,
                "jadwal_kelas": jadwal_kelas,
                "mahasiswa": mahasiswa
            })
            return redirect(url_for('kelola_kelas'))
        
        daftar_dosen = db.dosen.find()
        daftar_mahasiswa = db.mahasiswa.find()
        return render_template('admin/kelas/tambah_kelas.html', daftar_dosen=daftar_dosen, daftar_mahasiswa=daftar_mahasiswa)
    else:
        return redirect(url_for('admin_login'))

# Edit Kelas
@app.route('/admin/edit_kelas/<id>', methods=['GET', 'POST'])
def edit_kelas(id):
    if 'admin_logged_in' in session:
        # Ambil data kelas berdasarkan ID
        kelas = db.kelas.find_one({"_id": ObjectId(id)})
        
        if request.method == 'POST':
            # Ambil data dari form yang diinputkan user
            nama_kelas = request.form['nama_kelas']
            dosen_pengampu = request.form['dosen_pengampu']
            jadwal_kelas = request.form['jadwal_kelas']

            # Periksa apakah dosen_pengampu valid sebelum mengubah menjadi ObjectId
            if dosen_pengampu:
                dosen_pengampu = ObjectId(dosen_pengampu)

            # Update data kelas di database
            db.kelas.update_one({"_id": ObjectId(id)}, {
                "$set": {
                    "nama_kelas": nama_kelas,
                    "dosen_pengampu": dosen_pengampu,
                    "jadwal_kelas": jadwal_kelas
                }
            })
            return redirect(url_for('kelola_kelas'))

        # Ambil daftar dosen untuk dropdown list di menu
        daftar_dosen = list(db.dosen.find())  # Mengonversi cursor ke list

        # Debugging untuk memastikan daftar dosen diambil dengan benar
        print(f"Debug: Daftar Dosen - {daftar_dosen}")
        print(f"Debug: Kelas - {kelas}")

        return render_template('admin/kelas/edit_kelas.html', kelas=kelas, daftar_dosen=daftar_dosen)
    else:
        return redirect(url_for('admin_login'))

# Hapus Kelas
@app.route('/admin/hapus_kelas/<id>', methods=['POST'])
def hapus_kelas(id):
    if 'admin_logged_in' in session:
        db.kelas.delete_one({"_id": ObjectId(id)})
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

#laporan absensi  
@app.route('/admin/laporan_absensi')
def laporan_absensi():
    if 'admin_logged_in' in session:
        laporan_absensi = db.absensi.find()
        return render_template('admin/absensi/laporan_absensi.html', laporan_absensi=laporan_absensi)
    else:
        return redirect(url_for('admin_login'))

#unduh laporan absensi
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

# sudah di ujung aspal

if __name__ == '__main__':
    app.run(debug=True)
