import os
import cv2
import numpy as np

def train_model(nim):
    path = os.path.join('training/images', nim)  # Path folder mahasiswa berdasarkan NIM
    images = []
    labels = []
    label_id = 0  # Label untuk mahasiswa

    # Loop untuk mengambil semua foto di folder mahasiswa
    for filename in os.listdir(path):
        img_path = os.path.join(path, filename)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)  # Membaca gambar dalam format grayscale
        if img is not None:
            images.append(img)
            labels.append(label_id)

    # Validasi jumlah data
    if len(images) < 5:
        raise ValueError("Tidak cukup foto untuk training. Dibutuhkan minimal 5 foto.")

    # Training LBP
    lbp = cv2.face.LBPHFaceRecognizer_create()  # Membuat instance LBP recognizer
    lbp.train(images, np.array(labels))  # traini model dengan foto yang ada

    # buat dir jika tidak ada
    model_path = os.path.join('models', nim)
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    # Simpan model yang telah ditrain ke folder models/[nim_mahasiswa]
    lbp.save(os.path.join(model_path, f'{nim}_model.yml'))

    print(f'Model untuk mahasiswa dengan NIM {nim} berhasil dilatih dan disimpan di {model_path}')
