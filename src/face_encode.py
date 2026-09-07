"""Face detection and encoding — embeddings stay in memory only."""

import hashlib
import sys
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

# Embedding lives only for the duration of this function call; never written to disk.


def _encode_with_deepface(image_path: Path) -> np.ndarray:
    from deepface import DeepFace

    result = DeepFace.represent(
        img_path=str(image_path),
        model_name="Facenet",
        enforce_detection=True,
        detector_backend="opencv",
    )
    if not result:
        raise ValueError("No face detected in image.")
    return np.array(result[0]["embedding"], dtype=np.float64)


def _encode_with_face_recognition(image_path: Path) -> np.ndarray:
    import face_recognition as fr

    image = fr.load_image_file(str(image_path))
    encodings = fr.face_encodings(image)
    if not encodings:
        raise ValueError("No face detected in image.")
    return encodings[0]


def _encode_with_opencv(image_path: Path) -> np.ndarray:
    """Lightweight fallback: Haar-detected face region or normalized pixel embedding."""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face = gray
    
    if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data"):
        try:
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                face = gray[y : y + h, x : x + w]
        except Exception:
            pass

    face = cv2.resize(face, (128, 128))
    face = face.astype(np.float64) / 255.0
    embedding = face.flatten()
    # L2-normalize so distance comparisons are meaningful
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding


def detect_and_encode_face(image_path: Path) -> dict:
    """
    Detect and encode face from image with bounding box metadata for UI visualization.
    Embedding is kept in memory only and returned as float list & sha256 hash.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    h_img, w_img = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bbox = None
    faces = []
    if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data"):
        try:
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
        except Exception:
            faces = []
    
    if len(faces) > 0:
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        bbox = {
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h),
            "norm_x": float(x) / w_img,
            "norm_y": float(y) / h_img,
            "norm_w": float(w) / w_img,
            "norm_h": float(h) / h_img,
        }
        face_crop = gray[y : y + h, x : x + w]
        face_crop = cv2.resize(face_crop, (128, 128))
        face_crop = face_crop.astype(np.float64) / 255.0
        embedding = face_crop.flatten()
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
    else:
        # Fallback to center-weighted frame
        resized = cv2.resize(gray, (128, 128)).astype(np.float64) / 255.0
        embedding = resized.flatten()
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        bbox = {
            "x": 0,
            "y": 0,
            "w": int(w_img),
            "h": int(h_img),
            "norm_x": 0.0,
            "norm_y": 0.0,
            "norm_w": 1.0,
            "norm_h": 1.0,
        }

    embedding_bytes = embedding.tobytes()
    embedding_hash = hashlib.sha256(embedding_bytes).hexdigest()
    
    return {
        "dimensions": len(embedding),
        "fingerprint": embedding_hash,
        "bbox": bbox,
        "backend": "opencv_haar",
        "image_size": {"width": w_img, "height": h_img},
    }


def encode_face(image_path: Path) -> Tuple[np.ndarray, str]:
    """
    Detect and encode face from image.
    Returns (embedding_array, embedding_hash) — hash is for debug logging only.
    """
    backends = [
        ("deepface", _encode_with_deepface),
        ("face_recognition", _encode_with_face_recognition),
        ("opencv", _encode_with_opencv),
    ]

    last_error: Optional[Exception] = None
    used = None
    embedding = None

    for name, fn in backends:
        try:
            embedding = fn(image_path)
            used = name
            break
        except ImportError:
            continue
        except Exception as e:
            last_error = e
            continue

    if embedding is None:
        if last_error:
            print(f"[FACE] ERROR: {last_error}", file=sys.stderr)
        else:
            print(
                "[FACE] ERROR: No face backend available. "
                "Install deepface or face_recognition, or use opencv fallback.",
                file=sys.stderr,
            )
        sys.exit(1)

    embedding_bytes = embedding.tobytes()
    embedding_hash = hashlib.sha256(embedding_bytes).hexdigest()
    return embedding, embedding_hash

