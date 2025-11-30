import freenect
import cv2
import numpy as np
import face_recognition
from ultralytics import YOLO
import supervision as sv
import threading
import uvicorn

from tool_state import InventoryStateManager
from api import state_manager, update_annotated_frame, app

model = YOLO("tools_medium_480.pt")
tracker = sv.ByteTrack(track_activation_threshold=0.2, minimum_matching_threshold=0.7, lost_track_buffer=90)
box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()
trace_annotator = sv.TraceAnnotator()

video_capture = cv2.VideoCapture(0)

"""
# key is the class, value is a dict where the key is the drawer identifier and the value is the count of that class in that drawer
current_inventory: dict[str, dict[str, int]] = {}

# using existing face recognition model to detect the user
currently_detected_user: str | None

event_log: list of Events that matches the schema in audit-frontend/src/data/dummy.auditlogs.ts as closely as possible

global_states:
  - no_drawer_open
  - drawer_open:
        drawer_identifier
        tool_detection_state: 
            - drawer_opened_waiting_for_initial_tool_detection: # getting initial drawer state on open so we can diff against the state when the drawer closes. for this, we should wait for the list of tools to be stable for 1 second before auto transitioning to drawer_opened_tools_detected state.
                initial_tool_detection_state: set of f"{class_name} {tracker_id}"
            - drawer_opened_watching_for_tool_checkin_or_checkout # now people can add or remove tools to the drawer. need to have some heuristic for this to handle the drawer closing, so that tool_detection_state is not updated when the drawer is closing since that could incorrectly indicate that all the tools were removed.
                tool_detection_state: set of f"{class_name} {tracker_id}"

side effects:
on transition from drawer_opened_tools_detected to no_drawer_open, diff the initial_tool_detection_state and the tool_detection_state to get the list of tools that were added or removed. then "commit" the new state to the current inventory with the new state. when w
"""

# state_manager is now imported from api.py to share state with FastAPI

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

def run_api_server():
    """Run the FastAPI server in a background thread"""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

# Start the API server in a background thread
print("Starting API server on http://0.0.0.0:8000")
api_thread = threading.Thread(target=run_api_server, daemon=True)
api_thread.start()
print("API server started. Camera loop starting...")

def object_tracking_annotated_frame(frame: np.ndarray):
    results = model(frame)[0]
    detections = sv.Detections.from_ultralytics(results)
    detections = tracker.update_with_detections(detections)

    if "class_name" not in detections.data:
        return frame
        
    labels = [
        f"#{tracker_id} {class_name}"
        for class_name, tracker_id
        in zip(detections.data["class_name"], detections.tracker_id)
    ]

    annotated_frame = box_annotator.annotate(
        frame.copy(), detections=detections)
    annotated_frame = label_annotator.annotate(
        annotated_frame, detections=detections, labels=labels)
    return trace_annotator.annotate(
        annotated_frame, detections=detections)


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
            # Update state manager with detected user
            user = InventoryStateManager.make_user_from_string(name)
            state_manager.update_currently_detected_user(user)

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Get annotated frame with object tracking
    annotated_frame = object_tracking_annotated_frame(kinect_color_frame.copy())
    
    # Update the annotated frame for the API
    update_annotated_frame(annotated_frame)
    
    cv2.imshow('RGB', kinect_color_frame)
    cv2.imshow('Depth', depth_frame / 2048)  # simple visualization
    cv2.imshow('Detections', annotated_frame)
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
