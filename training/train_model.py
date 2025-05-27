import cv2
import numpy as np
import os
import subprocess
import psutil
import logging
import time
import sys
import random

print("[INFO] Skrip `train_model.py` dimulai...", flush=True)

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Pastikan Haar Cascade tersedia
cascade_path = "utils/haarcascade_frontalface_default.xml"
if not os.path.exists(cascade_path):
    logging.error("[ERROR] File Haar Cascade tidak ditemukan!")
    sys.exit(1)

MAX_SELECTED_IMAGES = 15  # Maksimal 15 gambar sebelum augmentasi

def kill_existing_libcamera_processes():
    """Menghentikan semua proses `libcamera-vid` yang berjalan."""
    logging.debug("[DEBUG] Mengecek proses kamera yang masih berjalan...")
    for process in psutil.process_iter(['pid', 'name']):
        if 'libcamera-vid' in process.info['name']:
            try:
                process.terminate()
                process.wait()
                logging.info(f"[INFO] Proses libcamera-vid (PID: {process.info['pid']}) dihentikan.")
            except Exception as e:
                logging.error(f"[ERROR] Gagal menghentikan proses libcamera-vid: {e}")

def capture_frame_with_libcamera(duration=15):
    """Memulai proses pengambilan frame dengan `libcamera-vid`."""
    logging.debug("[DEBUG] Memulai `libcamera-vid`...")
    kill_existing_libcamera_processes()

    command = [
        "libcamera-vid",
        "-n",
        "--codec", "mjpeg",
        "--width", "320",
        "--height", "240",
        "--framerate", "10",
        "--timeout", str(duration * 1000),
        "-o", "-"
    ]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=4096)
        time.sleep(2)

        if process.poll() is not None:
            logging.error("[ERROR] `libcamera-vid` gagal dijalankan! Periksa apakah kamera terhubung.")
            return None

        logging.debug("[DEBUG] `libcamera-vid` berhasil dijalankan.")
        return process
    except Exception as e:
        logging.error(f"[ERROR] Gagal memulai `libcamera-vid`: {e}")
        return None

def select_best_faces(images):
    """Pilih 15 gambar terbaik berdasarkan ukuran dalam frame."""
    logging.info(f"[INFO] Mulai seleksi gambar, total sebelum seleksi: {len(images)}")
    
    if len(images) <= MAX_SELECTED_IMAGES:
        logging.info(f"[INFO] Tidak cukup gambar untuk seleksi, menggunakan semua ({len(images)} gambar).")
        return images

    # Urutkan berdasarkan ukuran wajah (besar lebih baik)
    images_sorted = sorted(images, key=lambda x: x.shape[0] * x.shape[1], reverse=True)
    
    # Pilih 15 gambar terbesar
    selected_images = images_sorted[:MAX_SELECTED_IMAGES]

    logging.info(f"[INFO] Total gambar setelah seleksi: {len(selected_images)}")
    return selected_images

def augment_images(images):
    """Melakukan augmentasi pada semua gambar yang dikumpulkan."""
    logging.info("[INFO] Sedang melakukan augmentasi gambar...")

    augmented_images = []
    
    logging.debug("[DEBUG] Rotasi gambar...")
    for img in images:
        for angle in [-10, 0, 10]:
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(img, M, (w, h))
            augmented_images.append(rotated)

    logging.debug("[DEBUG] Flip horizontal...")
    for img in images:
        augmented_images.append(cv2.flip(img, 1))

    logging.debug("[DEBUG] Enhancement (Brightness & Contrast)...")
    for img in images:
        alpha = random.uniform(0.8, 1.2)
        beta = random.randint(-30, 30)
        contrast_adjusted = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        augmented_images.append(contrast_adjusted)

    logging.debug("[DEBUG] Gaussian Blur...")
    for img in images:
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        augmented_images.append(blurred)

    return augmented_images

def live_train_model(mahasiswa_id, nim, nama, duration=15):
    """Melatih model mahasiswa menggunakan kamera Raspberry Pi."""
    logging.info(f"[INFO] Mulai training: {nama} (NPM: {nim})")

    kill_existing_libcamera_processes()
    cv2.destroyAllWindows()
    time.sleep(2)

    logging.info("[INFO] Sedang mengambil frame...")
    camera_process = capture_frame_with_libcamera(duration)
    
    if camera_process is None:
        logging.error("[ERROR] Kamera gagal dinyalakan, cek `libcamera-vid`!")
        sys.exit(1)

    face_cascade = cv2.CascadeClassifier(cascade_path)
    images = []
    start_time = time.time()

    cv2.namedWindow("Live Training", cv2.WINDOW_NORMAL)

    try:
        mjpeg_buffer = b""
        frame_count = 0  # Untuk mencatat jumlah frame yang diterima

        while (time.time() - start_time) < duration:
            raw_data = camera_process.stdout.read(4096)
            if not raw_data:
                logging.warning("[WARNING] Kamera berhenti mengirim frame, menunggu...")
                time.sleep(2)
                continue

            mjpeg_buffer += raw_data
            start_marker = mjpeg_buffer.find(b"\xff\xd8")
            end_marker = mjpeg_buffer.find(b"\xff\xd9")

            if start_marker != -1 and end_marker != -1:
                jpeg_data = mjpeg_buffer[start_marker:end_marker + 2]
                mjpeg_buffer = mjpeg_buffer[end_marker + 2:]
                frame = cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)

                if frame is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50))

                    for (x, y, w, h) in faces:
                        face_roi = cv2.resize(gray[y:y+h, x:x+w], (100, 100))
                        images.append(face_roi)

                        # Tampilkan di layar untuk real-time preview
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, f"{nama} ({nim})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    frame_count += 1
                    logging.info(f"[INFO] Frame {frame_count} diterima dari kamera")

                    cv2.imshow("Live Training", frame)
                    cv2.waitKey(1)

        logging.info(f"[INFO] Total gambar yang diambil: {len(images)}")

        selected_images = select_best_faces(images)

        # **🔴 Hanya gambar terbaik yang akan di-augmentasi dan di-training**
        augmented_images = augment_images(selected_images)

        logging.info(f"[INFO] Total gambar setelah augmentasi: {len(augmented_images)}")

        # ? Training Model & Simpan Model
        logging.info("[INFO] Sedang melakukan training model...")

        if not hasattr(cv2, "face"):
            logging.error("[ERROR] OpenCV tidak memiliki modul `cv2.face`. Pastikan `opencv-contrib-python` terinstall!")
            sys.exit(1)

        if len(augmented_images) < 5:
            logging.error("[ERROR] Dataset terlalu kecil untuk training! Tambahkan lebih banyak gambar.")
            sys.exit(1)

        lbp = cv2.face.LBPHFaceRecognizer_create()
        lbp.train(augmented_images, np.array([0] * len(augmented_images), dtype=np.int32))

        model_path = os.path.join("models", nim)
        if not os.path.exists(model_path):
            os.makedirs(model_path)

        model_file = os.path.join(model_path, f"{nim}_model.yml")

        try:
            lbp.save(model_file)
            logging.info(f"[INFO] Model berhasil disimpan di {model_file}")
        except Exception as e:
            logging.error(f"[ERROR] Gagal menyimpan model: {e}")
            sys.exit(1)

        logging.info("[INFO] Training model selesai.")

        logging.info("[INFO] Training model selesai.")

    except Exception as e:
        logging.error(f"[ERROR] Live training gagal: {e}")
        sys.exit(1)

    finally:
        kill_existing_libcamera_processes()
        cv2.destroyAllWindows()
        logging.info("[INFO] Kamera dimatikan, training selesai.")

if __name__ == "__main__":
    print("[INFO] Skrip `train_model.py` dimulai...", flush=True)

    # 🔴 Pastikan logging langsung aktif
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', force=True)

    logging.info("[INFO] Program `train_model.py` mulai dieksekusi.")

    # 🔴 Pastikan jumlah argumen benar
    if len(sys.argv) != 4:
        logging.error("[ERROR] Argumen tidak sesuai! Format: python train_model.py <mahasiswa_id> <nim> <nama>")
        sys.exit(1)

    # 🔴 Ambil argumen dari terminal
    try:
        mahasiswa_id = sys.argv[1]
        nim = sys.argv[2]
        nama = sys.argv[3]

        logging.info(f"[INFO] Training untuk: {nama} (NPM: {nim})")

    except Exception as e:
        logging.error(f"[ERROR] Terjadi kesalahan saat membaca argumen: {e}")
        sys.exit(1)

    # 🔴 Pastikan file Haar Cascade ada
    cascade_path = "utils/haarcascade_frontalface_default.xml"
    if not os.path.exists(cascade_path):
        logging.error("[ERROR] File Haar Cascade tidak ditemukan! Periksa path `utils/haarcascade_frontalface_default.xml`")
        sys.exit(1)

    logging.info("[INFO] Semua pengecekan awal berhasil. Memulai fungsi `live_train_model`...")

    try:
        # 🔴 Panggil fungsi training
        live_train_model(mahasiswa_id, nim, nama)
    except Exception as e:
        logging.error(f"[ERROR] Program berhenti karena error: {e}")
        sys.exit(1)

    logging.info("[INFO] Skrip `train_model.py` selesai tanpa error.")
