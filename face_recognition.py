import cv2
import sys
import subprocess
import psutil
import numpy as np
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import os
import threading
import time

# Koneksi ke database MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['absensi_db']

# Fungsi untuk menghentikan semua proses libcamera-vid yang berjalan
def kill_existing_libcamera_processes():
    """Menghentikan semua proses libcamera-vid yang berjalan untuk mencegah konflik."""
    for process in psutil.process_iter(['pid', 'name']):
        if 'libcamera-vid' in process.info['name']:
            try:
                process.terminate()
                print(f"[INFO] Menghentikan proses libcamera-vid dengan PID {process.info['pid']}")
            except Exception as e:
                print(f"[ERROR] Gagal menghentikan proses libcamera-vid: {e}")

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
    print(f"[INFO] Kehadiran mahasiswa {mahasiswa_id} dicatat pada {waktu_hadir} {'(Terlambat)' if terlambat else ''}")

# Fungsi untuk memuat semua model dari folder models/
def load_all_models():
    recognizer_dict = {}
    nim_to_mahasiswa = {}

    def load_model(nim):
        model_path = os.path.join('models', nim, f'{nim}_model.yml')
        if os.path.exists(model_path):
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(model_path)
            mahasiswa = db.mahasiswa.find_one({"nim": nim})
            if mahasiswa:
                recognizer_dict[nim] = recognizer
                nim_to_mahasiswa[nim] = mahasiswa
                print(f"[INFO] Model mahasiswa {nim} ({mahasiswa['nama']}) dimuat.")
            else:
                print(f"[WARNING] Mahasiswa dengan NIM {nim} tidak ditemukan di database.")
        else:
            print(f"[WARNING] Model untuk NIM {nim} tidak ditemukan di {model_path}")

    # Load model menggunakan threading untuk mempercepat
    threads = []
    for nim in os.listdir('models'):
        t = threading.Thread(target=load_model, args=(nim,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    return recognizer_dict, nim_to_mahasiswa

# Fungsi untuk menangkap frame menggunakan Raspberry Pi Camera
def capture_frame_with_libcamera():
    command = [
        "libcamera-vid",
        "-n",
        "--codec", "mjpeg",
        "--width", "640",
        "--height", "480",
        "--framerate", "30",
        "-t", "0",
        "-o", "-"
    ]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
        time.sleep(2)  # Beri waktu proses kamera untuk inisialisasi
        print("[INFO] Proses libcamera-vid dimulai.")
        return process
    except Exception as e:
        print(f"[ERROR] Gagal memulai libcamera-vid: {e}")
        return None

def run_face_recognition(kelas_id):
    # Hentikan proses kamera yang berjalan sebelumnya
    kill_existing_libcamera_processes()

    kelas_id = ObjectId(kelas_id)

    # Cari kelas di database
    kelas = db.kelas.find_one({"_id": kelas_id})
    if not kelas:
        print(f"[ERROR] Kelas dengan ID {kelas_id} tidak ditemukan di database.")
        return

    print(f"[INFO] Proses face recognition dimulai untuk kelas: {kelas['nama_kelas']}")

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

    mahasiswa_ids = [str(mhs_id) for mhs_id in kelas.get('mahasiswa', [])]
    recognizer_dict, nim_to_mahasiswa = load_all_models()
    hadir_set = set()
    terlambat_limit = waktu_mulai_absensi + timedelta(minutes=10)

    camera_process = capture_frame_with_libcamera()
    if not camera_process:
        print("[ERROR] Proses kamera tidak dapat dimulai.")
        return

    mjpeg_buffer = b""
    face_cascade = cv2.CascadeClassifier('utils/haarcascade_frontalface_default.xml')

    try:
        while True:
            raw_data = camera_process.stdout.read(4096)
            if not raw_data:
                print("[ERROR] Gagal membaca frame dari kamera.")
                break

            mjpeg_buffer += raw_data
            start_marker = mjpeg_buffer.find(b"\xff\xd8")
            end_marker = mjpeg_buffer.find(b"\xff\xd9")

            if start_marker != -1 and end_marker != -1:
                jpeg_data = mjpeg_buffer[start_marker:end_marker + 2]
                mjpeg_buffer = mjpeg_buffer[end_marker + 2:]

                frame = cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)

                if frame is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

                    for (x, y, w, h) in faces:
                        face_roi = gray[y:y+h, x:x+w]
                        best_match_nim = None
                        best_confidence = float('inf')

                        for nim, recognizer in recognizer_dict.items():
                            label, confidence = recognizer.predict(face_roi)
                            if confidence < best_confidence:
                                best_confidence = confidence
                                best_match_nim = nim

                        if best_match_nim and best_confidence < 80:
                            mahasiswa = nim_to_mahasiswa[best_match_nim]
                            if best_match_nim not in hadir_set:
                                record_attendance(kelas_id, str(mahasiswa['_id']), datetime.now() > terlambat_limit)
                                hadir_set.add(best_match_nim)
                            label_text = f"{mahasiswa['nama']}"
                            color = (0, 255, 0)
                        else:
                            label_text = "Tidak Dikenal"
                            color = (0, 0, 255)

                        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                        cv2.putText(frame, label_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    cv2.imshow('Face Recognition', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    finally:
        kill_existing_libcamera_processes()
        camera_process.terminate()
        cv2.destroyAllWindows()
        print("[INFO] Proses face recognition selesai, kamera dimatikan.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        kelas_id = sys.argv[1]
        run_face_recognition(kelas_id)
    else:
        print("kelas_id tidak diberikan.")
