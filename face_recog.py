# face_recog.py
import cv2
import face_recognition
import numpy as np

# Load known faces (do this at import-time so it is cached)
print("Loading face encodings...")
_known_encodings = []
_known_names = []

def _load_face(path, name):
    img = face_recognition.load_image_file(path)
    encs = face_recognition.face_encodings(img)
    if len(encs) == 0:
        print(f"Warning: no face found in {path}")
        return
    _known_encodings.append(encs[0])
    _known_names.append(name)

# change these to match the files you have
try:
    _load_face("faces/mason.png", "Mason Thomas - mgt210000")
    _load_face("faces/kynlee.png", "Kynlee Thomas")
except Exception as e:
    print("Error loading face files:", e)

print(f"Loaded {_known_encodings.__len__()} known faces.")

def match_faces(frame_bgr):
    """
    Returns a list of detections: {"box": [left, top, right, bottom], "name": "..."}
    Expects an OpenCV BGR frame.
    """
    if frame_bgr is None:
        return []
    rgb_frame = frame_bgr[:, :, ::-1]
    small = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)

    locations = face_recognition.face_locations(small)
    encodings = face_recognition.face_encodings(small, locations)

    results = []
    for loc, enc in zip(locations, encodings):
        top, right, bottom, left = [v * 4 for v in loc]
        name = "Unknown"
        if len(_known_encodings) > 0:
            matches = face_recognition.compare_faces(_known_encodings, enc)
            distances = face_recognition.face_distance(_known_encodings, enc)
            best_idx = np.argmin(distances)
            if matches[best_idx]:
                name = _known_names[best_idx]
        results.append({"box": [left, top, right, bottom], "name": name})
    return results