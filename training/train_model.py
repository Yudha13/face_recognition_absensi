import os
import cv2
import numpy as np
from bson import ObjectId

def enhance_image(image):
    """Fungsi untuk memperbaiki kualitas gambar dengan beberapa preprocessing."""
    image = cv2.equalizeHist(image)
    return image

def augment_image(image):
    """Fungsi untuk melakukan augmentasi data sederhana."""
    augmented_images = [image]
    augmented_images.append(cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
    augmented_images.append(cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE))
    augmented_images.append(cv2.flip(image, 1))  # Flip horizontal
    return augmented_images

def train_model(mahasiswa_id):
    """Melatih model dengan Mahasiswa ID sebagai label"""

    if not ObjectId.is_valid(mahasiswa_id):
        raise ValueError(f"ID Mahasiswa {mahasiswa_id} tidak valid.")
    
    mahasiswa_id_str = str(mahasiswa_id)
    path = os.path.join('training/images', mahasiswa_id_str)
    images = []
    labels = []
    
    face_cascade = cv2.CascadeClassifier('utils/haarcascade_frontalface_default.xml')
    processed_faces = set()

    for filename in os.listdir(path):
        img_path = os.path.join(path, filename)
        img = cv2.imread(img_path)
        if img is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Deteksi wajah
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=8, minSize=(720, 720))
            
            if len(faces) == 0:
                print(f"[WARNING] Tidak ditemukan wajah di {filename}, melewatkan gambar ini.")
                continue
            
            for (x, y, w, h) in faces:
                if x + w > gray.shape[1] or y + h > gray.shape[0]:
                    print(f"[ERROR] Wajah yang terdeteksi di {filename} berada di luar batas gambar, melewatkan.")
                    continue

                face_roi = gray[y:y+h, x:x+w]
                face_roi = enhance_image(face_roi)
                face_roi_resized = cv2.resize(face_roi, (150, 150))
                augmented_faces = augment_image(face_roi_resized)
                
                for aug_face in augmented_faces:
                    face_hash = hash(aug_face.tobytes())
                    
                    if face_hash in processed_faces:
                        print(f"[INFO] Wajah di {filename} sudah diproses sebelumnya, melewatkan duplikasi.")
                        continue

                    # Gunakan label numerik berdasarkan urutan mahasiswa
                    images.append(aug_face)
                    labels.append(0)  # Ubah menjadi 0 karena hanya satu mahasiswa

                    processed_faces.add(face_hash)
                    
                    print(f"Loaded {filename} with detected face for Mahasiswa ID {mahasiswa_id_str}")

        else:
            print(f"Gagal membaca gambar {filename}")
            continue

    if len(images) < 10:
        raise ValueError("Tidak cukup foto untuk training. Dibutuhkan minimal 10 foto.")

    print(f"Jumlah gambar yang digunakan untuk training (termasuk augmentasi): {len(images)}")

    # Training LBP
    lbp = cv2.face.LBPHFaceRecognizer_create()
    lbp.train(images, np.array(labels, dtype=np.int32))  # Pastikan labels berupa array int32

    model_path = os.path.join('models', mahasiswa_id_str)
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    lbp.save(os.path.join(model_path, f'{mahasiswa_id_str}_model.yml'))
    print(f'Model untuk mahasiswa dengan ID {mahasiswa_id_str} berhasil dilatih dan disimpan di {model_path}')
