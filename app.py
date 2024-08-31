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
        db.mahasiswa.delete_one({"_id": ObjectId(id)})
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
        kelas = db.kelas.find_one({"_id": ObjectId(id)})
        
        if request.method == 'POST':
            nama_kelas = request.form['nama_kelas']
            dosen_pengampu = ObjectId(request.form['dosen_pengampu'])
            jadwal_kelas = request.form['jadwal_kelas']
            mahasiswa = [ObjectId(mhs_id) for mhs_id in request.form.getlist('mahasiswa[]')]
            
            db.kelas.update_one({"_id": ObjectId(id)}, {
                "$set": {
                    "nama_kelas": nama_kelas,
                    "dosen_pengampu": dosen_pengampu,
                    "jadwal_kelas": jadwal_kelas,
                    "mahasiswa": mahasiswa
                }
            })
            return redirect(url_for('kelola_kelas'))
        
        daftar_dosen = db.dosen.find()
        daftar_mahasiswa = db.mahasiswa.find()
        return render_template('admin/kelas/edit_kelas.html', kelas=kelas, daftar_dosen=daftar_dosen, daftar_mahasiswa=daftar_mahasiswa)
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
@app.route('/admin/kelola_mahasiswa_kelas/<id>', methods=['GET', 'POST'])
def kelola_mahasiswa_kelas(id):
    if 'admin_logged_in' in session:
        kelas = db.kelas.find_one({"_id": ObjectId(id)})
        daftar_mahasiswa = db.mahasiswa.find({"_id": {"$in": kelas["mahasiswa"]}})
        
        if request.method == 'POST':
            mahasiswa = [ObjectId(mhs_id) for mhs_id in request.form.getlist('mahasiswa[]')]
            db.kelas.update_one({"_id": ObjectId(id)}, {
                "$set": {"mahasiswa": mahasiswa}
            })
            return redirect(url_for('kelola_kelas'))
        
        semua_mahasiswa = db.mahasiswa.find()
        return render_template('admin/kelas/kelola_mahasiswa_kelas.html', kelas=kelas, daftar_mahasiswa=daftar_mahasiswa, semua_mahasiswa=semua_mahasiswa)
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


if __name__ == '__main__':
    app.run(debug=True)
