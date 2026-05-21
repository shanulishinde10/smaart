import base64
import io
import json
import os
import numpy as np
from PIL import Image
import cv2

FACE_SIZE = (150, 150)
SIMILARITY_THRESHOLD = 0.50

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

def load_image_from_base64(data_url):
    if ',' in data_url:
        data_url = data_url.split(',')[1]
    image_bytes = base64.b64decode(data_url)
    image = Image.open(io.BytesIO(image_bytes))
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

def save_uploaded_image(file_storage, upload_path):
    file_storage.save(upload_path)

def _preprocess_gray(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)

def detect_and_align_face(image):
    gray = _preprocess_gray(image)

    # Try progressively more permissive parameters
    for (scale, neighbors, min_sz) in [
        (1.1, 5, (80, 80)),
        (1.1, 3, (50, 50)),
        (1.05, 3, (30, 30)),
    ]:
        faces = face_cascade.detectMultiScale(gray, scaleFactor=scale, minNeighbors=neighbors, minSize=min_sz)
        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            face = gray[y:y+h, x:x+w]
            return cv2.resize(face, FACE_SIZE)
    return None

def get_face_encoding(image):
    face = detect_and_align_face(image)
    if face is None:
        return None
    face_blur = cv2.GaussianBlur(face, (3, 3), 0)
    hog = _compute_hog(face_blur)
    return hog

def _compute_hog(face_gray):
    gx = cv2.Sobel(face_gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(face_gray, cv2.CV_32F, 0, 1, ksize=3)
    mag, ang = cv2.cartToPolar(gx, gy)
    bins = np.int32(ang * 9 / (2 * np.pi)) % 9
    cell_size = 8
    h, w = face_gray.shape
    cells_h, cells_w = h // cell_size, w // cell_size
    hog = np.zeros((cells_h, cells_w, 9), dtype=np.float32)
    for i in range(cells_h):
        for j in range(cells_w):
            cell_mag = mag[i*cell_size:(i+1)*cell_size, j*cell_size:(j+1)*cell_size]
            cell_bins = bins[i*cell_size:(i+1)*cell_size, j*cell_size:(j+1)*cell_size]
            for b in range(9):
                hog[i, j, b] = np.sum(cell_mag[cell_bins == b])
    hog_vector = hog.flatten()
    norm = np.linalg.norm(hog_vector)
    if norm > 0:
        hog_vector = hog_vector / norm
    return hog_vector

def encode_face_encoding(encoding):
    return json.dumps(encoding.tolist())

def decode_face_encoding(encoding_str):
    return np.array(json.loads(encoding_str))

def compare_faces(known_encodings, target_encoding, tolerance=SIMILARITY_THRESHOLD):
    if not known_encodings or target_encoding is None:
        return False, None, None
    best_match_idx = None
    best_similarity = -1
    for i, known in enumerate(known_encodings):
        sim = _cosine_similarity(known, target_encoding)
        if sim > best_similarity:
            best_similarity = sim
            best_match_idx = i
    if best_similarity >= tolerance:
        return True, best_match_idx, float(best_similarity)
    return False, None, None

def _cosine_similarity(a, b):
    dot = np.dot(a, b)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0
    return dot / (na * nb)
