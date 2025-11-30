# camera.py
import threading
import time
import cv2
import numpy as np
import freenect
from face_recog import match_faces
from drawer_logic import detect_drawer
from event_tracker import event_tracker

class CameraState:
    def __init__(self):
        self.rgb_frame = None        # Kinect RGB (BGR)
        self.depth_frame = None      # Kinect depth (raw)
        self.video_frame = None      # USB webcam frame (BGR)
        self.faces = []              # list of face detections
        self.drawers = {"left": "unknown", "right": "unknown"}
        self.lock = threading.Lock()

state = CameraState()

# control objects for the background thread
_kinect_lock = threading.Lock()
_stop_event = threading.Event()
_thread = None

def init_kinect_once(timeout: float = 5.0, retry_interval: float = 0.5) -> bool:
    """
    Attempt a one-time Kinect initialization from the main thread.
    This calls sync_get_video / sync_get_depth until a valid frame is returned or timeout.
    Returns True on success, False on failure.
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            res = freenect.sync_get_video()
            if res is None:
                time.sleep(retry_interval)
                continue
            frame, _ = res
            depth_res = freenect.sync_get_depth()
            if depth_res is None:
                time.sleep(retry_interval)
                continue
            depth_frame, _ = depth_res

            # store initial frames
            with state.lock:
                state.rgb_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                state.depth_frame = depth_frame.copy()
            return True
        except Exception as e:
            # libfreenect can throw low-level errors; keep trying a bit
            print("Kinect init attempt error:", e)
            time.sleep(retry_interval)
    print("Kinect initialization timed out / failed.")
    return False

def _read_kinect_frames():
    """
    Read Kinect frames using the sync API. Calls must be protected by _kinect_lock.
    Returns (rgb_bgr, depth) or (None, None) on error.
    """
    try:
        with _kinect_lock:
            res = freenect.sync_get_video()
            if res is None:
                return None, None
            frame, _ = res
            # convert to BGR for OpenCV usage
            rgb_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            depth_res = freenect.sync_get_depth()
            if depth_res is None:
                return rgb_bgr, None
            depth_frame, _ = depth_res
        return rgb_bgr, depth_frame
    except Exception as e:
        print("Error reading kinect frames:", e)
        return None, None

def processing_loop(webcam_index: int = 1, fps: float = 10.0):
    """
    Background loop: reads Kinect frames (protected), reads webcam, runs face matching
    and drawer detection, then stores results into state.
    """
    global _stop_event
    # open webcam
    video_capture = cv2.VideoCapture(webcam_index)
    if not video_capture.isOpened():
        print(f"Warning: webcam index {webcam_index} couldn't be opened.")

    interval = 1.0 / max(1.0, fps)

    while not _stop_event.is_set():
        t_start = time.time()

        # Kinect frames (protected by _kinect_lock inside helper)
        k_rgb, k_depth = _read_kinect_frames()

        # Webcam frame
        ret, vframe = video_capture.read()
        if not ret:
            vframe = None

        # face matching uses the webcam frame (or Kinect rgb/frame if you prefer)
        faces = []
        if vframe is not None:
            try:
                faces = match_faces(vframe)
            except Exception as e:
                print("face recognition error:", e)

        # drawer detection uses the depth frame
        drawers = state.drawers
        if k_depth is not None:
            try:
                drawer_result = detect_drawer(k_depth)
                drawers = {
                    "left": drawer_result.get("left", "unknown"),
                    "right": drawer_result.get("right", "unknown")
                }
            except Exception as e:
                print("drawer detection error:", e)

        # store results thread-safely
        with state.lock:
            if k_rgb is not None:
                state.rgb_frame = k_rgb
            if k_depth is not None:
                state.depth_frame = k_depth
            if vframe is not None:
                state.video_frame = vframe
            state.faces = faces
            state.drawers = drawers
        
        # Process drawer changes and create events
        try:
            # Generate event image URL (you could save actual images here)
            event_image_url = f"https://picsum.photos/seed/event{int(time.time())}/500"
            event_tracker.process_drawer_changes(drawers, faces, event_image_url)
        except Exception as e:
            print("event tracking error:", e)

        # sleep to keep desired fps
        elapsed = time.time() - t_start
        to_sleep = interval - elapsed
        if to_sleep > 0:
            time.sleep(to_sleep)

    # cleanup
    try:
        video_capture.release()
    except Exception:
        pass
    print("processing_loop stopped.")

def start_camera_thread(webcam_index: int = 1, fps: float = 10.0):
    """
    Start the background processing thread (if not already started).
    Assumes init_kinect_once() was called successfully before this.
    """
    global _thread, _stop_event
    if _thread and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=processing_loop, kwargs={"webcam_index": webcam_index, "fps": fps}, daemon=True)
    _thread.start()
    print("Camera thread started.")

def stop_camera_thread():
    global _stop_event, _thread
    _stop_event.set()
    if _thread:
        _thread.join(timeout=2.0)
    print("Camera thread stopped.")