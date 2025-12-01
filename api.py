"""
FastAPI application for serving inventory state, event logs, and annotated images.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import cv2
import numpy as np
import io
from PIL import Image
import base64

from tool_state import InventoryStateManager

# Create shared state manager instance
# This will be imported and used by main.py
state_manager = InventoryStateManager()

app = FastAPI(title="Tool Inventory API", version="1.0.0")

# Add CORS middleware to allow frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store the latest annotated frame
# This will be updated by main.py
latest_annotated_frame: Optional[np.ndarray] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Tool Inventory API", "version": "1.0.0"}


@app.get("/api/inventory")
async def get_inventory():
    """
    Get current inventory state.
    Returns a dict where keys are tool classes and values are dicts
    mapping drawer identifiers to counts.
    """
    return {
        "inventory": state_manager.current_inventory,
        "current_user": state_manager.currently_detected_user,
        "state": state_manager.tool_detection_state
    }


@app.get("/api/audit-logs/events")
async def get_events():
    """
    Get event log entries matching the frontend schema.
    Returns array of events with tool checkin/checkout information.
    Matches the frontend Event type from dummy.auditlogs.ts
    """
    events = state_manager.event_log
    
    # Convert to format matching frontend schema
    # Frontend expects: Event[] (array directly, not wrapped)
    formatted_events = []
    for event in events:
        # For now, we need to extract tool info from the tool string format
        # Tool format in state is: f"{class_name} {tracker_id}"
        
        formatted_event = {
            "id": event.id,
            "timestamp": event.timestamp,
            "type": event.type,
            "user": event.user,
            "tool": event.tool,
            "eventImageUrl": event.eventImageUrl
        }
        formatted_events.append(formatted_event)
    
    # Return array directly (not wrapped) to match frontend expectation
    return formatted_events


@app.get("/api/audit-logs/overview")
async def get_overview():
    """
    Get system overview statistics.
    Returns counts for tools, users with checked out tools, etc.
    """
    # Calculate total tools count from inventory
    total_tools = 0
    for tool_class, drawer_counts in state_manager.current_inventory.items():
        total_tools += sum(drawer_counts.values())
    
    # Count users with checked out tools
    # Tools that are checked out are those in events with type "tool_checkout"
    # that don't have a corresponding "tool_checkin"
    checked_out_tools = {}
    for event in state_manager.event_log:
        if event.user is None:
            continue
        if event.type == "tool_checkout":
            # For now, we'll use a simple count
            # TODO: Track specific tools when tool information is added
            user_id = event.user.id
            checked_out_tools[user_id] = checked_out_tools.get(user_id, 0) + 1
        elif event.type == "tool_checkin":
            user_id = event.user.id
            if user_id in checked_out_tools:
                checked_out_tools[user_id] = max(0, checked_out_tools[user_id] - 1)
    
    users_with_checked_out_tools = sum(1 for count in checked_out_tools.values() if count > 0)
    
    # For now, we'll return 0 for tools unseen in last 7 days
    # TODO: Implement this when we have tool tracking
    tools_unseen_in_last_7_days = 0
    
    return {
        "toolsCount": total_tools,
        "usersWithCheckedOutToolsCount": users_with_checked_out_tools,
        "toolsUnseenInLast7DaysCount": tools_unseen_in_last_7_days
    }


@app.get("/api/get-annotated-live-frame")
async def get_annotated_image():
    """
    Serve the latest annotated image with tool detections.
    Returns a PNG image with bounding boxes and labels.
    Matches the frontend route /api/get-annotated-live-frame
    """
    global latest_annotated_frame
    
    if latest_annotated_frame is None:
        raise HTTPException(status_code=404, detail="No annotated frame available")
    
    try:
        # Convert BGR to RGB for PIL
        rgb_frame = cv2.cvtColor(latest_annotated_frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)
        
        # Convert to PNG bytes (matching frontend expectation)
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        return StreamingResponse(
            img_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.get("/api/annotated-image-base64")
async def get_annotated_image_base64():
    """
    Serve the latest annotated image as base64 encoded string.
    Useful for embedding in JSON responses.
    """
    global latest_annotated_frame
    
    if latest_annotated_frame is None:
        raise HTTPException(status_code=404, detail="No annotated frame available")
    
    try:
        # Convert BGR to RGB for PIL
        rgb_frame = cv2.cvtColor(latest_annotated_frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)
        
        # Convert to JPEG bytes
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format="JPEG", quality=85)
        img_bytes.seek(0)
        
        # Encode to base64
        base64_image = base64.b64encode(img_bytes.getvalue()).decode("utf-8")
        
        return {
            "image": f"data:image/jpeg;base64,{base64_image}",
            "timestamp": state_manager.event_log[-1]["timestamp"] if state_manager.event_log else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


def update_annotated_frame(frame: np.ndarray):
    """
    Update the latest annotated frame.
    This function should be called from main.py after processing each frame.
    """
    global latest_annotated_frame
    latest_annotated_frame = frame.copy()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

