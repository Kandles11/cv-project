# app.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
import cv2
import numpy as np
import io
from camera import state, init_kinect_once, start_camera_thread, stop_camera_thread
from event_tracker import event_tracker
from models import Event, SystemOverview
import time

app = FastAPI(title="Kinect CV Server")

@app.on_event("startup")
def on_startup():
    # Try to initialize the Kinect from the main thread first
    ok = init_kinect_once(timeout=6.0)
    if not ok:
        # Warn but continue — server will still run and webcam/face recog may work
        print("Warning: Kinect failed to initialize during startup. Server will run but Kinect data may be missing.")
    # Start background processing thread (reads frames and runs face rec)
    start_camera_thread(webcam_index=1, fps=8.0)
    print("Server startup complete.")

@app.on_event("shutdown")
def on_shutdown():
    stop_camera_thread()
    print("Server shutdown complete.")

@app.get("/ping")
def ping():
    return {"status": "ok", "ts": time.time()}

@app.get("/faces")
def get_faces():
    with state.lock:
        # copy to avoid mutation while serializing
        faces = [f.copy() for f in state.faces]
    return {"faces": faces}

@app.get("/drawers")
def get_drawers():
    with state.lock:
        drawers = state.drawers.copy()
    return drawers

@app.get("/depth_at")
def depth_at(x: int = Query(...), y: int = Query(...)):
    with state.lock:
        if state.depth_frame is None:
            raise HTTPException(status_code=503, detail="Depth frame not available")
        h, w = state.depth_frame.shape[:2]
        if not (0 <= x < w and 0 <= y < h):
            raise HTTPException(status_code=400, detail=f"Coordinates out of range (w={w},h={h})")
        d = int(state.depth_frame[y, x])
    return {"x": int(x), "y": int(y), "depth": d}

def _encode_jpeg_from_bgr(frame_bgr):
    if frame_bgr is None:
        return None
    ret, buf = cv2.imencode(".jpg", frame_bgr)
    if not ret:
        return None
    return buf.tobytes()

@app.get("/rgb.jpg")
def rgb_jpg():
    with state.lock:
        frame = None if state.rgb_frame is None else state.rgb_frame.copy()
    jpg = _encode_jpeg_from_bgr(frame)
    if jpg is None:
        raise HTTPException(status_code=503, detail="RGB frame not available")
    return StreamingResponse(io.BytesIO(jpg), media_type="image/jpeg")

@app.get("/video.jpg")
def video_jpg():
    with state.lock:
        frame = None if state.video_frame is None else state.video_frame.copy()
    jpg = _encode_jpeg_from_bgr(frame)
    if jpg is None:
        raise HTTPException(status_code=503, detail="Video frame not available")
    return StreamingResponse(io.BytesIO(jpg), media_type="image/jpeg")

@app.get("/depth.npy")
def depth_raw():
    with state.lock:
        if state.depth_frame is None:
            raise HTTPException(status_code=503, detail="Depth frame not available")
        arr = state.depth_frame.copy()
    # send as nested list (JSON) — not ideal for big arrays, but simple
    return JSONResponse(content={"shape": arr.shape, "depth": arr.tolist()})

# API endpoints matching the TypeScript schema
@app.get("/api/events", response_model=list[Event])
def get_events(limit: Optional[int] = Query(None, ge=1, le=1000)):
    """Get tool checkin/checkout events"""
    events = event_tracker.get_events(limit=limit)
    return events

@app.get("/api/events/{event_id}", response_model=Event)
def get_event(event_id: str):
    """Get a specific event by ID"""
    events = event_tracker.get_events()
    for event in events:
        if event.id == event_id:
            return event
    raise HTTPException(status_code=404, detail="Event not found")

@app.get("/api/system/overview", response_model=SystemOverview)
def get_system_overview():
    """Get system overview statistics"""
    return event_tracker.get_system_overview()