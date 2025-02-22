import cv2
import numpy as np
import os
import subprocess
import psutil
import logging

# Konfigurasi logging untuk memantau aktivitas
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def kill_existing_libcamera_processes():
    """Menghentikan semua proses libcamera-vid yang berjalan."""
    for process in psutil.process_iter(['pid', 'name']):
        if 'libcamera-vid' in process.info['name']:
            try:
                process.terminate()
                process.wait()  # Menunggu proses benar-benar dihentikan
                logging.info(f"[INFO] Menghentikan proses libcamera-vid dengan PID {process.info['pid']}")
            except Exception as e:
                logging.error(f"[ERROR] Gagal menghentikan proses libcamera-vid: {e}")

def enhance_image(image):
    """Fungsi untuk memperbaiki kualitas gambar dengan preprocessing."""
    return cv2.equalizeHist(image)  # Histogram equalization untuk meningkatkan kontras

def augment_image(image):
    """Fungsi untuk melakukan augmentasi data sederhana."""
    augmented_images = [image, cv2.flip(image, 1)]  # Flip horizontal
    return augmented_images

def capture_frame_with_libcamera():
    """Memulai proses pengambilan frame dengan libcamera-vid."""
    kill_existing_libcamera_processes()  # Pastikan tidak ada proses kamera yang berjalan
    command = [
        "libcamera-vid",
        "-n",
        "--codec", "mjpeg",
        "--width", "320",  # Resolusi lebih rendah untuk meningkatkan performa
        "--height", "240",
        "--framerate", "30",
        "-t", "0",
        "-o", "-"
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
    return process

def live_train_model(mahasiswa_id, nim, nama, duration=30):
    """
    Fungsi untuk melatih model secara langsung menggunakan Raspberry Pi Camera.
    Args:
        mahasiswa_id: ID mahasiswa.
        nim: NIM mahasiswa.
        nama: Nama mahasiswa.
        duration: Durasi live training dalam detik.
    """
    logging.info(f"[INFO] Memulai live training untuk mahasiswa: {nama} (ID: {mahasiswa_id}, NPM: {nim})")

    # Inisialisasi kamera
    camera_process = capture_frame_with_libcamera()
    face_cascade = cv2.CascadeClassifier('utils/haarcascade_frontalface_default.xml')
    images = []
    labels = []
    index = 0  # Label untuk mahasiswa ini
    frame_count = 0

    start_time = cv2.getTickCount()
    fps = cv2.getTickFrequency()

    try:
        mjpeg_buffer = b""
        while (cv2.getTickCount() - start_time) / fps < duration:
            raw_data = camera_process.stdout.read(2048)
            if not raw_data:
                logging.error("[ERROR] Gagal membaca frame dari kamera.")
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
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50))

                    for (x, y, w, h) in faces:
                        face_roi = cv2.resize(gray[y:y+h, x:x+w], (100, 100))
                        enhanced_face = enhance_image(face_roi)
                        augmented_faces = augment_image(enhanced_face)

                        for aug_face in augmented_faces:
                            images.append(aug_face)
                            labels.append(index)

                        # Gambarkan kotak wajah
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, f"Training: {nama} ({nim})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    frame_count += 1
                    if frame_count % 10 == 0:
                        progress = (frame_count / (duration * 30)) * 100
                        cv2.putText(frame, f"Progress: {progress:.2f}%", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                    cv2.imshow("Live Training", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logging.info("[INFO] Proses live training dihentikan oleh pengguna.")
                    break

        if len(images) < 10:
            raise ValueError("[ERROR] Data training kurang dari 10 gambar.")

        logging.info(f"[INFO] Jumlah gambar untuk training: {len(images)}")

        # Training dengan LBPHFaceRecognizer dengan parameter optimal
        lbp = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
        lbp.train(images, np.array(labels, dtype=np.int32))

        # Simpan model dengan NIM sebagai nama file
        model_path = os.path.join('models', nim)
        if not os.path.exists(model_path):
            os.makedirs(model_path)

        model_filename = f'{nim}_model.yml'
        lbp.save(os.path.join(model_path, model_filename))
        logging.info(f"[INFO] Model berhasil disimpan di {model_path} untuk NIM: {nim}")

    except Exception as e:
        logging.error(f"[ERROR] Live training gagal: {e}")

    finally:
        camera_process.terminate()
        camera_process.wait()
        kill_existing_libcamera_processes()
        cv2.destroyAllWindows()
        logging.info("[INFO] Kamera ditutup, training selesai.")
