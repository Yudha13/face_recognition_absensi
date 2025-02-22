import cv2
import numpy as np
import os
import subprocess

# Fungsi untuk memperbaiki kualitas gambar dengan preprocessing
def enhance_image(image):
    """Fungsi untuk memperbaiki kualitas gambar dengan beberapa preprocessing."""
    image = cv2.equalizeHist(image)  # Histogram equalization untuk meningkatkan kontras
    return image

# Fungsi untuk augmentasi gambar
def augment_image(image):
    """Fungsi untuk melakukan augmentasi data sederhana."""
    augmented_images = [image]
    augmented_images.append(cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
    augmented_images.append(cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE))
    augmented_images.append(cv2.flip(image, 1))  # Flip horizontal
    return augmented_images

# Fungsi untuk menangkap frame dari kamera
def capture_frame_with_libcamera():
    """Memulai proses pengambilan frame dengan libcamera-vid."""
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
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
    return process

# Fungsi untuk melatih model secara langsung dari kamera
def live_train_model(mahasiswa_id, nim, nama, duration=60):
    """
    Fungsi untuk melatih model secara langsung menggunakan Raspberry Pi Camera.
    Args:
        mahasiswa_id: ID mahasiswa.
        nim: NIM mahasiswa.
        nama: Nama mahasiswa.
        duration: Durasi live training dalam detik.
    """
    print(f"[INFO] Memulai live training untuk mahasiswa: {nama} (ID: {mahasiswa_id}, NIM: {nim})")

    # Inisialisasi kamera
    camera_process = capture_frame_with_libcamera()
    face_cascade = cv2.CascadeClassifier('utils/haarcascade_frontalface_default.xml')
    images = []
    labels = []
    index = 0  # Label untuk mahasiswa ini

    start_time = cv2.getTickCount()
    fps = cv2.getTickFrequency()

    try:
        mjpeg_buffer = b""
        frame_count = 0
        while (cv2.getTickCount() - start_time) / fps < duration:
            raw_data = camera_process.stdout.read(1024)
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
                    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=8, minSize=(100, 100))

                    for (x, y, w, h) in faces:
                        face_roi = gray[y:y+h, x:x+w]
                        face_roi_resized = cv2.resize(face_roi, (150, 150))

                        # Enhance dan augmentasi gambar
                        enhanced_face = enhance_image(face_roi_resized)
                        augmented_faces = augment_image(enhanced_face)

                        for aug_face in augmented_faces:
                            images.append(aug_face)
                            labels.append(index)

                        # Gambarkan kotak wajah
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                    # Informasi pada frame
                    frame_count += 1
                    progress = (frame_count / (duration * 30)) * 100  # Perkiraan progres berdasarkan jumlah frame
                    cv2.putText(frame, f"Training: {nama} (NIM: {nim})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(frame, f"Progress: {progress:.2f}%", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    # Tampilkan frame
                    cv2.imshow("Live Training", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("[INFO] Proses live training dihentikan oleh pengguna.")
                    break

        if len(images) < 10:
            raise ValueError("[ERROR] Tidak cukup data untuk training. Dibutuhkan minimal 10 gambar.")

        print(f"[INFO] Jumlah gambar untuk training: {len(images)}")

        # Training dengan LBPHFaceRecognizer
        lbp = cv2.face.LBPHFaceRecognizer_create()
        lbp.train(images, np.array(labels, dtype=np.int32))

        # Simpan model dengan NIM sebagai nama file
        model_path = os.path.join('models', nim)
        if not os.path.exists(model_path):
            os.makedirs(model_path)

        model_filename = f'{nim}_model.yml'
        lbp.save(os.path.join(model_path, model_filename))
        print(f"[INFO] Model berhasil disimpan di {model_path} untuk NIM: {nim}")

    finally:
        camera_process.terminate()
        cv2.destroyAllWindows()
        print("[INFO] Kamera dilepaskan dan live training selesai.")
