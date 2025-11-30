# Tool Inventory API

FastAPI application for serving inventory state, event logs, and annotated images to the frontend.

## Setup

1. Install dependencies:
```bash
uv sync
# or
pip install -r requirements.txt
```

2. Start the API server:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

Or run directly:
```bash
python api.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### `GET /`
Root endpoint - returns API information.

### `GET /api/inventory`
Get current inventory state.
- Returns: Current inventory (tool classes -> drawer -> count), current user, and state machine state

**Response:**
```json
{
  "inventory": {
    "hammer": {
      "drawer_1": 3,
      "drawer_2": 1
    }
  },
  "current_user": {
    "id": "mgt210000",
    "name": "Mason Thomas",
    "email": "mgt210000@utdallas.edu",
    "imageUrl": "https://..."
  },
  "state": {
    "state": "no_drawer_open"
  }
}
```

### `GET /api/events`
Get event log entries (tool checkin/checkout history).
- Query parameters:
  - `limit` (optional): Maximum number of events to return
  - `offset` (optional): Number of events to skip

**Response:**
```json
{
  "events": [
    {
      "id": "uuid",
      "timestamp": 1234567890,
      "type": "tool_checkout",
      "user": {
        "id": "mgt210000",
        "name": "Mason Thomas",
        "email": "mgt210000@utdallas.edu",
        "imageUrl": "https://..."
      },
      "tool": {
        "id": "unknown",
        "name": "Unknown Tool",
        "description": "Tool information not yet implemented",
        "imageUrl": "https://...",
        "type": "Unknown",
        "cost": 0.0
      },
      "eventImageUrl": "https://..."
    }
  ],
  "total": 42
}
```

### `GET /api/overview`
Get system overview statistics.

**Response:**
```json
{
  "toolsCount": 143,
  "usersWithCheckedOutToolsCount": 12,
  "toolsUnseenInLast7DaysCount": 7
}
```

### `GET /api/annotated-image`
Serve the latest annotated image with tool detections.
- Returns: JPEG image with bounding boxes and labels
- Content-Type: `image/jpeg`

### `GET /api/annotated-image-base64`
Serve the latest annotated image as base64 encoded string.
- Returns: JSON with base64-encoded image and timestamp

**Response:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "timestamp": 1234567890
}
```

## Integration with main.py

The `main.py` script imports the shared `state_manager` from `api.py`:
- Updates detected users automatically
- Updates annotated frames for the API
- Both processes share the same state

## Running the Application

The application can now be started with a single command. The `main.py` script automatically starts the API server in a background thread:

```bash
python main.py
```

This will:
1. Start the FastAPI server on `http://0.0.0.0:8000` in a background thread
2. Start the camera loop for face recognition and tool detection

**Alternative: Run API Server Separately**

If you prefer to run the API server separately (useful for development with auto-reload):

**Terminal 1 - API Server:**
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Main CV Loop:**
```bash
python main.py
```

Note: If you run them separately, make sure to comment out the API server startup code in `main.py` to avoid port conflicts.

## CORS

CORS is enabled for all origins. In production, update the `allow_origins` in `api.py` to specify your frontend URL.

## API Documentation

FastAPI automatically generates interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

