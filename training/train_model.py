import os
import cv2
import numpy as np

def train_model(nim):
    print(f"Training model for NIM: {nim}")  # Pastikan NIM yang dilatih benar
    path = os.path.join('training/images', nim)  # Path folder mahasiswa berdasarkan NIM
    images = []
    labels = []

    # Loop untuk mengambil semua foto di folder mahasiswa
    for filename in os.listdir(path):
        img_path = os.path.join(path, filename)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)  # Membaca gambar dalam format grayscale
        if img is not None:
            # Pastikan ukuran gambar konsisten
            img = cv2.resize(img, (200, 200))  # Resize jika diperlukan
            images.append(img)
            labels.append(int(nim))  # Gunakan NIM sebagai label yang unik
            print(f"Loaded {filename} for NIM {nim}")  # Tambahkan log untuk setiap gambar
        else:
            print(f"Gagal membaca gambar {filename}")
            continue  # Lewatkan gambar yang tidak bisa dibaca

    # Validasi jumlah data
    if len(images) < 5:
        raise ValueError("Tidak cukup foto untuk training. Dibutuhkan minimal 5 foto.")

    # Training LBP
    lbp = cv2.face.LBPHFaceRecognizer_create()  # Membuat instance LBP recognizer
    lbp.train(images, np.array(labels))  # Train model dengan foto dan label yang ada

    # Buat dir jika tidak ada
    model_path = os.path.join('models', nim)
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    # Simpan model yang telah ditrain ke folder models/[nim_mahasiswa]
    lbp.save(os.path.join(model_path, f'{nim}_model.yml'))

    print(f'Model untuk mahasiswa dengan NIM {nim} berhasil dilatih dan disimpan di {model_path}')
