import cv2
import sys
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import os


client = MongoClient('mongodb://localhost:27017/')
db = client['absensi_db']

# Fungsi untuk mencatat kehadiran mahasiswa
def record_attendance(kelas_id, mahasiswa_id, terlambat=False):
    waktu_hadir = datetime.now()
    db.absensi.update_one(
        {"kelas_id": kelas_id, "status": "Berlangsung"},
        {"$push": {"mahasiswa_hadir": {
            "mahasiswa_id": mahasiswa_id,
            "waktu_hadir": waktu_hadir,
            "terlambat": terlambat
        }}}
    )
    print(f"Kehadiran mahasiswa {mahasiswa_id} dicatat pada {waktu_hadir} {'(Terlambat)' if terlambat else ''}")

# Fungsi untuk memuat semua model dari folder models/
def load_all_models():
    recognizer_dict = {}
    nim_to_mahasiswa = {}

    # Dapatkan daftar semua folder (nim) dalam folder models/
    for nim in os.listdir('models'):
        model_path = os.path.join('models', nim, f'{nim}_model.yml')
        if os.path.exists(model_path):
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(model_path)
            mahasiswa = db.mahasiswa.find_one({"nim": nim})
            if mahasiswa:
                recognizer_dict[nim] = recognizer
                nim_to_mahasiswa[nim] = mahasiswa  # Simpan data mahasiswa untuk setiap NIM
                print(f"Model mahasiswa {nim} ({mahasiswa['nama']}) dimuat.")
            else:
                print(f"Mahasiswa dengan NIM {nim} tidak ditemukan di database.")
        else:
            print(f"Model untuk NIM {nim} tidak ditemukan di {model_path}")

    return recognizer_dict, nim_to_mahasiswa

def run_face_recognition(kelas_id):
    kelas_id = ObjectId(kelas_id)

    # Cari kelas di database
    kelas = db.kelas.find_one({"_id": kelas_id})
    
    if kelas is None:
        print(f"Kelas dengan ID {kelas_id} tidak ditemukan di database.")
        return  # Keluar jika kelas tidak ditemukan

    # Debugging: Tampilkan data kelas
    print(f"Data kelas: {kelas}")

    # Catat waktu mulai absensi
    waktu_mulai_absensi = datetime.now()
    db.absensi.insert_one({
        "kelas_id": kelas_id,
        "nama_kelas": kelas['nama_kelas'],
        "waktu_mulai": waktu_mulai_absensi,
        "waktu_selesai": None,
        "mahasiswa_hadir": [],
        "status": "Berlangsung"
    })

    # Ambil daftar mahasiswa yang terdaftar di kelas ini (disimpan sebagai ObjectId)
    mahasiswa_ids = [str(mhs_id) for mhs_id in kelas.get('mahasiswa', [])]
    
    if not mahasiswa_ids:
        print(f"Tidak ada mahasiswa terdaftar untuk kelas {kelas_id}.")
        return

    print(f"Mahasiswa terdaftar di kelas {kelas['nama_kelas']}: {mahasiswa_ids}")

    # Load semua model mahasiswa
    recognizer_dict, nim_to_mahasiswa = load_all_models()

    hadir_set = set()

    # Inisialisasi kamera
    capture = cv2.VideoCapture(0)
    
    if not capture.isOpened():
        print("Kamera tidak bisa dibuka.")
        return

    print(f"Proses face recognition dimulai untuk kelas {kelas['nama_kelas']}")
    terlambat_limit = waktu_mulai_absensi + timedelta(minutes=10)  # Anggap terlambat jika hadir lebih dari 10 menit

    while True:
        ret, frame = capture.read()
        if not ret:
            print("Gagal membaca frame dari kamera.")
            break

        # Tampilkan info sesi kelas di frame
        cv2.putText(frame, f"Sesi: {kelas['nama_kelas']}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        face_cascade = cv2.CascadeClassifier('utils/haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))

        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            color = (0, 0, 255)  # Default warna merah (tidak dikenali)
            label_top = "Tidak Dikenal"
            label_bottom = ""

            for nim, recognizer in recognizer_dict.items():
                predicted_label, confidence = recognizer.predict(face_roi)
                print(f"Predicted NIM: {nim}, Confidence: {confidence}")  # Debugging output

                mahasiswa_obj_id = str(nim_to_mahasiswa[nim]['_id'])  # Ambil ObjectId mahasiswa dari database dan ubah menjadi string

                # Cocokkan berdasarkan NIM dan ObjectId (konversi ObjectId ke string untuk pencocokan)
                if confidence < 75:
                    if mahasiswa_obj_id in [str(mhs_id) for mhs_id in mahasiswa_ids]:  # Cek jika mahasiswa ada di kelas yang sedang berlangsung
                        if nim not in hadir_set:
                            color = (0, 255, 0)  # Box hijau jika dikenali dan belum dicatat
                            label_top = f"{nim_to_mahasiswa[nim]['nama']}"  # Nama mahasiswa di atas box
                            label_bottom = "Sudah Hadir"  # Teks "Sudah Hadir" di bawah box
                            terlambat = datetime.now() > terlambat_limit
                            record_attendance(kelas_id, mahasiswa_obj_id, terlambat)
                            hadir_set.add(nim)
                        else:
                            color = (0, 255, 0)  # Pastikan box tetap hijau jika sudah hadir
                            label_top = f"{nim_to_mahasiswa[nim]['nama']}"
                            label_bottom = "Sudah Hadir"
                    else:
                        # Jika mahasiswa dikenali tetapi tidak terdaftar di kelas ini
                        label_top = f"{nim_to_mahasiswa[nim]['nama']}"  # Nama mahasiswa di atas box
                        label_bottom = "Bukan dari sesi ini"
                        color = (255, 0, 0)  # Box biru untuk wajah dikenal tapi bukan bagian dari sesi ini
                    break
                else:
                    label_top = "Tidak Dikenal"
                    label_bottom = ""
                    color = (0, 0, 255)  # Box merah untuk wajah tidak dikenali


            # Gambar box wajah
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

            # Tampilkan teks nama di atas box
            cv2.putText(frame, label_top, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Tampilkan teks status di bawah box
            if label_bottom:
                cv2.putText(frame, label_bottom, (x, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Tampilkan frame
        cv2.imshow('Face Recognition', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Catat waktu selesai absensi
    waktu_selesai_absensi = datetime.now()
    db.absensi.update_one(
        {"kelas_id": kelas_id, "status": "Berlangsung"},
        {"$set": {"waktu_selesai": waktu_selesai_absensi, "status": "Tidak Berlangsung"}}
    )

    capture.release()
    cv2.destroyAllWindows()
    print("Proses face recognition dihentikan.")

if __name__ == "__main__":
    # Pastikan kelas_id diberikan sebagai argumen
    if len(sys.argv) > 1:
        kelas_id = sys.argv[1]  # Dapatkan kelas_id dari argumen command line
        run_face_recognition(kelas_id)
    else:
        print("kelas_id tidak diberikan.")
