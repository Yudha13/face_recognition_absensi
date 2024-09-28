import os
import cv2
import numpy as np
import shutil
from bson import ObjectId

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

# Fungsi untuk pengecekan duplikasi wajah
def check_if_face_exists(face_roi):
    """Fungsi untuk mengecek apakah wajah sudah ada di model mahasiswa lain."""
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    model_path = 'models/'
    mahasiswa_models = os.listdir(model_path)

    print(f"[DEBUG] Mulai pengecekan wajah di {len(mahasiswa_models)} model yang ada.")
    
    for model in mahasiswa_models:
        model_full_path = os.path.join(model_path, model)
        if os.path.isfile(model_full_path):
            print(f"[DEBUG] Memuat model dari {model_full_path}")
            recognizer.read(model_full_path)
            
            # Prediksi wajah menggunakan model yang ada
            try:
                label, confidence = recognizer.predict(face_roi)
                print(f"[DEBUG] Hasil prediksi di model {model}: Label={label}, Confidence={confidence}")

                # Jika confidence di bawah threshold, wajah sudah dikenali
                if confidence < 80:  # Threshold dapat disesuaikan
                    print(f"[ERROR] Wajah sudah dikenali dalam model {model} dengan confidence {confidence}. Training ditolak.")
                    return True  # Duplikasi ditemukan, training ditolak
                else:
                    print(f"[INFO] Wajah tidak dikenali di model {model}, confidence terlalu tinggi: {confidence}")
            except Exception as e:
                print(f"[ERROR] Gagal melakukan prediksi di model {model}: {e}")
    
    return False

# Fungsi untuk menghapus direktori foto
def hapus_direktori_foto(mahasiswa_id):
    """Menghapus direktori foto mahasiswa."""
    folder_path = os.path.join('training/images', mahasiswa_id)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)  # Hapus folder beserta isinya
        print(f"[INFO] Folder foto untuk mahasiswa ID {mahasiswa_id} telah dihapus.")

# Fungsi untuk melakukan training model
def train_model(mahasiswa_id, nim, index):
    """Melatih model dengan ObjectId sebagai label dan menggunakan NIM untuk penyimpanan file"""

    if not ObjectId.is_valid(mahasiswa_id):
        raise ValueError(f"ID Mahasiswa {mahasiswa_id} tidak valid.")
    
    mahasiswa_id_str = str(mahasiswa_id)
    path = os.path.join('training/images', mahasiswa_id_str)
    images = []
    labels = []
    
    face_cascade = cv2.CascadeClassifier('utils/haarcascade_frontalface_default.xml')
    processed_faces = set()

    if not os.path.exists(path):
        print(f"[ERROR] Path gambar tidak ditemukan: {path}")
        return

    for filename in os.listdir(path):
        img_path = os.path.join(path, filename)
        img = cv2.imread(img_path)

        if img is not None:
            print(f"[DEBUG] Memproses gambar: {filename}")
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=8, minSize=(720, 720))

            if len(faces) == 0:
                print(f"[WARNING] Tidak ditemukan wajah di {filename}, melewatkan gambar ini.")
                continue

            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                face_roi_resized = cv2.resize(face_roi, (720, 720))

                print(f"[DEBUG] Memulai pengecekan wajah untuk file {filename}")

                # Cek apakah wajah sudah ada di model mahasiswa lain
                if check_if_face_exists(face_roi_resized):
                    print(f"[ERROR] Proses training dihentikan karena wajah sudah ada di database untuk mahasiswa lain.")
                    
                    # Hapus direktori foto mahasiswa jika training gagal
                    hapus_direktori_foto(mahasiswa_id_str)
                    
                    # Berikan pesan untuk mengunggah ulang foto
                    raise ValueError(f"Training dihentikan karena duplikasi wajah. Silakan upload ulang foto.")
                
                # Enhance gambar sebelum augmentasi
                enhanced_face = enhance_image(face_roi_resized)
                
                # Augmentasi dan tambahkan ke dataset
                augmented_faces = augment_image(enhanced_face)
                for aug_face in augmented_faces:
                    face_hash = hash(aug_face.tobytes())

                    if face_hash in processed_faces:
                        print(f"[INFO] Wajah di {filename} sudah diproses sebelumnya, melewatkan duplikasi.")
                        continue

                    images.append(aug_face)
                    labels.append(index)
                    processed_faces.add(face_hash)

                    print(f"[DEBUG] Gambar berhasil diproses dan ditambahkan untuk training: {filename}")
        else:
            print(f"[ERROR] Gagal membaca gambar {filename}")
            continue

    if len(images) < 10:
        # Jika foto kurang dari 10, hapus direktori foto mahasiswa dan berikan pesan error
        hapus_direktori_foto(mahasiswa_id_str)
        raise ValueError("Tidak cukup foto untuk training. Dibutuhkan minimal 10 foto. Silakan upload ulang.")

    print(f"[DEBUG] Jumlah gambar yang digunakan untuk training (termasuk augmentasi): {len(images)}")

    # Training dengan LBPHFaceRecognizer
    lbp = cv2.face.LBPHFaceRecognizer_create()
    lbp.train(images, np.array(labels, dtype=np.int32))

    # Simpan model dengan NIM sebagai nama file
    model_path = os.path.join('models', nim)
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    model_filename = f'{nim}_model.yml'
    lbp.save(os.path.join(model_path, model_filename))
    print(f"[INFO] Model untuk mahasiswa dengan NIM {nim} berhasil dilatih dan disimpan di {model_path}")
