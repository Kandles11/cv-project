import freenect
import cv2
import numpy as np
import face_recognition
from ultralytics import YOLO

model = YOLO("tools_med.pt")

video_capture = cv2.VideoCapture(1)

clicked_point = None

def on_mouse(event, x, y, flags, param):
    global clicked_point
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_point = (x, y)
        print("Clicked at:", clicked_point)

print("setting up facial encodings")

mason_image = face_recognition.load_image_file("faces/mason.png")
mason_face_encoding = face_recognition.face_encodings(mason_image)[0]

kynlee_image = face_recognition.load_image_file("faces/kynlee.png")
kynlee_face_encoding = face_recognition.face_encodings(kynlee_image)[0]

# carrie_image = face_recognition.load_image_file("faces/carrie.png")
# carrie_face_encoding = face_recognition.face_encodings(carrie_image)[0]

# mike_image = face_recognition.load_image_file("faces/mike.png")
# mike_face_encoding = face_recognition.face_encodings(mike_image)[0]

print("we have finished encodings")

known_face_encodings = [
    mason_face_encoding,
    kynlee_face_encoding,
    # carrie_face_encoding,
    # mike_face_encoding
]
known_face_names = [
    "Mason Thomas - mgt210000",
    "Kynlee Thomas",
    # "Carrie Thomas",
    # "Michael Thomas"
]

def get_video():
    frame, _ = freenect.sync_get_video()
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

def get_depth_frame():
    frame, _ = freenect.sync_get_depth()
    return frame

def get_depth_at_point(frame, x: int, y:int):
    
    depth = frame[y, x]
    return depth

cv2.namedWindow("Depth")
cv2.setMouseCallback("Depth", on_mouse)

while True:
    depth_frame = get_depth_frame()
    kinect_color_frame = get_video()
    ret, frame = video_capture.read()
    
    results = model.predict(kinect_color_frame)
    detection_frame = kinect_color_frame.copy()
    for result in results:
        detection_frame = result.plot(img=detection_frame)
    
    rgb_frame = frame[:, :, ::-1]
    small = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
    
    if clicked_point is not None:
        cx, cy = clicked_point
        if 0 <= cx < depth_frame.shape[1] and 0 <= cy < depth_frame.shape[0]:
            depth_value = depth_frame[cy, cx]
            print(f"Depth at {clicked_point}: {depth_value}")
        clicked_point = None
    
    face_locations = face_recognition.face_locations(small)
    face_encodings = face_recognition.face_encodings(small, face_locations)
    
       # Loop through each face in this frame of video
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

        name = "Unknown"

        # If a match was found in known_face_encodings, just use the first one.
        # if True in matches:
        #     first_match_index = matches.index(True)
        #     name = known_face_names[first_match_index]

        # Or instead, use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    cv2.imshow('RGB', kinect_color_frame)
    cv2.imshow('Depth', depth_frame / 2048)  # simple visualization
    cv2.imshow('Detections', detection_frame)
    cv2.imshow('Video', frame)
    
    left_depth = get_depth_at_point(depth_frame, 485, 367)
    right_depth = get_depth_at_point(depth_frame, 243,385)
    
    
    # print(left_depth)
    print(right_depth)
    
    if  920 > right_depth > 891:
        print("no drawer open")
    if 890 > right_depth > 861:
        print("sanding and scales")
    if 860 > right_depth > 841:
        print("clamps")
    if 840 > right_depth > 826:
        print("electrical and hot glue")
    if 825 > right_depth > 801:
        print("sockets and allen keys")
    if 800 > right_depth > 780:
        print("drivers and bits")
        
    if  920 > left_depth > 891:
        print("no drawer open")
    if 890 > left_depth > 861:
        print("drill and dremmel")
    if 860 > left_depth > 841:
        print("measruing")
    if 840 > left_depth > 826:
        print("hammers")
    if 825 > left_depth > 801:
        print("pliers and cutters")
    if 800 > left_depth > 780:
        print("drivers and bits")

    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
