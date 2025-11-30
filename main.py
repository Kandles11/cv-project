import freenect
import cv2
import numpy as np
import face_recognition
from ultralytics import YOLO
import supervision as sv
import threading
import uvicorn

from api import state_manager, update_annotated_frame, app

from tool_state import InventoryStateManager, DrawerOpenState
model = YOLO("tools_medium_480.pt")
tracker = sv.ByteTrack(track_activation_threshold=0.3, minimum_matching_threshold=0.2, lost_track_buffer=90)
box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()
trace_annotator = sv.TraceAnnotator()

video_capture = cv2.VideoCapture(0)


clicked_point = None
previous_drawer_identifier = None

def on_mouse(event, x, y, flags, param):
    global clicked_point
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_point = (x, y)
        print("Clicked at:", clicked_point)

print("setting up facial encodings")

mason_image = face_recognition.load_image_file("faces/mason.png")
mason_face_encoding = face_recognition.face_encodings(mason_image)[0]

gabriel_image = face_recognition.load_image_file("faces/gabe.jpg")
gabriel_face_encoding = face_recognition.face_encodings(gabriel_image)[0]

colin_image = face_recognition.load_image_file("faces/colin.jpg")
colin_face_encoding = face_recognition.face_encodings(colin_image)[0]

# carrie_image = face_recognition.load_image_file("faces/carrie.png")
# carrie_face_encoding = face_recognition.face_encodings(carrie_image)[0]

# mike_image = face_recognition.load_image_file("faces/mike.png")
# mike_face_encoding = face_recognition.face_encodings(mike_image)[0]

print("we have finished encodings")

known_face_encodings = [
    mason_face_encoding,
    gabriel_face_encoding,
    colin_face_encoding,
    # carrie_face_encoding,
    # mike_face_encoding
]
known_face_names = [
    "Mason Thomas - mgt210000",
    "Gabriel Burbach - gmb190004",
    "Colin Wong - csw220002",
    # "Carrie Thomas",
    # "Michael Thomas"
]

def get_video():
    frame, _ = freenect.sync_get_video()
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

def get_depth_frame():
    frame, _ = freenect.sync_get_depth()
    return frame

def get_depth_at_point(frame, x: int, y: int, max_variance: int = 150):
    """
    Get average depth value in a 50px square around the given point.
    Samples a 50x50 pixel region centered on (x, y).
    Filters out readings with high variance (mixed depths like drawer + floor).
    
    Args:
        frame: Depth frame
        x: X coordinate
        y: Y coordinate
        max_variance: Maximum allowed variance (default 100). Higher = more tolerance.
    
    Returns:
        Average depth value, or None if variance is too high (unreliable reading)
    """
    # 50px square means 25px radius on each side
    half_size = 15
    
    # Calculate bounds, ensuring we don't go outside the frame
    y_start = max(0, y - half_size)
    y_end = min(frame.shape[0], y + half_size)
    x_start = max(0, x - half_size)
    x_end = min(frame.shape[1], x + half_size)
    
    # Extract the region of interest
    roi = frame[y_start:y_end, x_start:x_end]
    
    # Calculate average depth, ignoring zero values (invalid depth readings)
    # Zero values typically indicate areas where depth couldn't be measured
    valid_depths = roi[roi > 0]
    
    if len(valid_depths) == 0:
        # If no valid depths, return None to indicate unreliable reading
        return None
    
    # Calculate variance to check if depths are uniform
    # High variance indicates mixed depths (e.g., drawer partially open with floor visible)
    variance = np.var(valid_depths)
    
    if variance > max_variance:
        # Variance too high - likely mixing drawer and floor/background
        # Return None to indicate unreliable reading
        return None
    
    # Return the average of valid depth values (variance is acceptable)
    return int(np.mean(valid_depths))

def get_drawer_identifier_from_depth(left_depth: int, right_depth: int) -> str | None:
    """
    Maps depth values to drawer identifiers based on depth ranges.
    Returns drawer identifier string or None if no drawer is open.
    """
    # Check right drawer first
    if 890 > right_depth > 861:
        return "sanding and scales"
    if 860 > right_depth > 841:
        return "clamps"
    if 840 > right_depth > 826:
        return "electrical and hot glue"
    if 825 > right_depth > 801:
        return "sockets and allen keys"
    if 800 > right_depth > 780:
        return "drivers and bits"
    
    # Check left drawer
    if 890 > left_depth > 851:
        return "drill and dremmel"
    if 850 > left_depth > 841:
        return "measruing"
    if 840 > left_depth > 826:
        return "hammers"
    if 825 > left_depth > 801:
        return "pliers and cutters"
    if 800 > left_depth > 780:
        return "drivers and bits"
    
    # No drawer open (depth indicates closed state)
    if 920 > right_depth > 891 or 920 > left_depth > 891:
        return None
    
    # Default: no drawer open if depth doesn't match any range
    return None

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
    if not ret:
        continue
    
    # Get tracked detections for tool state management
    tracked_results = model(kinect_color_frame, verbose=False)[0]
    tracked_detections = sv.Detections.from_ultralytics(tracked_results)
    tracked_detections = tracker.update_with_detections(tracked_detections)
    
    # Extract tool detections in format "{class_name} {tracker_id}"
    tool_detection_set = set()
    if "class_name" in tracked_detections.data and tracked_detections.tracker_id is not None:
        tracker_ids = tracked_detections.tracker_id
        for class_name, tracker_id in zip(tracked_detections.data["class_name"], tracker_ids):
            if tracker_id is not None:
                tool_detection_set.add(f"{class_name} {tracker_id}")
    
    # Update tool detection state if drawer is open
    if isinstance(state_manager.tool_detection_state, DrawerOpenState):
        drawer_state = state_manager.tool_detection_state
        if drawer_state.detailed_state == "waiting_for_initial_tool_detection":
            # Update initial tool detection state
            drawer_state.initial_tool_detection_state = tool_detection_set.copy()
        elif drawer_state.detailed_state == "watching_for_tool_checkin_or_checkout":
            # Update current tool detection state
            drawer_state.current_tool_detection_state = tool_detection_set.copy()
            # Record snapshot for 2-second buffer
            drawer_state.record_tool_detection_snapshot()
    
    rgb_frame = frame[:, :, ::-1]
    small = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
    
    if clicked_point is not None:
        cx, cy = clicked_point
        if 0 <= cx < depth_frame.shape[1] and 0 <= cy < depth_frame.shape[0]:
            depth_value = get_depth_at_point(depth_frame, cx, cy)
            if depth_value is not None:
                print(f"Depth at {clicked_point}: {depth_value} (averaged over 50px square)")
            else:
                print(f"Depth at {clicked_point}: Unreliable (high variance - likely mixed depths)")
        clicked_point = None
    
    face_locations = face_recognition.face_locations(small)
    face_encodings = face_recognition.face_encodings(small, face_locations)
    
    # Track detected user for this frame
    detected_user = None
    
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
            name = user.name

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
    
    # Update state manager with detected user (or None if no face detected)
    state_manager.update_currently_detected_user(detected_user)

    # Get annotated frame with object tracking
    annotated_frame = object_tracking_annotated_frame(kinect_color_frame.copy())
    
    # Update the annotated frame for the API
    update_annotated_frame(annotated_frame)
    
    cv2.imshow('Video', frame)
    cv2.imshow('RGB', kinect_color_frame)
    cv2.imshow('Depth', depth_frame / 2048)  # simple visualization
    cv2.imshow('Detections', annotated_frame)
    
    left_depth = get_depth_at_point(depth_frame, 500, 366)
    right_depth = get_depth_at_point(depth_frame, 243, 371)
    
    # If depth readings are unreliable (None), treat as no drawer open
    # This happens when variance is too high (e.g., drawer partially open mixing with floor)
    if left_depth is None:
        left_depth = 1000  # Default to "no drawer open" depth
    if right_depth is None:
        right_depth = 1000  # Default to "no drawer open" depth
    
    # Get current drawer identifier from depth
    current_drawer_identifier = get_drawer_identifier_from_depth(left_depth, right_depth)
    
    # Handle drawer state transitions
    if previous_drawer_identifier != current_drawer_identifier:
        # Transition from no drawer to drawer open
        if previous_drawer_identifier is None and current_drawer_identifier is not None:
            state_manager.transition_to_drawer_open(current_drawer_identifier)
        # Transition from drawer open to no drawer
        elif previous_drawer_identifier is not None and current_drawer_identifier is None:
            state_manager.transition_to_no_drawer_open()
        # Transition from one drawer to different drawer
        elif previous_drawer_identifier is not None and current_drawer_identifier is not None and previous_drawer_identifier != current_drawer_identifier:
            state_manager.transition_to_no_drawer_open()
            state_manager.transition_to_drawer_open(current_drawer_identifier)
        
        previous_drawer_identifier = current_drawer_identifier
    
    # Debug output (keeping original print statements for reference)
    print(left_depth, right_depth, end=" - ")
    
    if current_drawer_identifier is None:
        print("no drawer open")
    else:
        print(current_drawer_identifier)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
