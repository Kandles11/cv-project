# event_tracker.py
import time
import uuid
import threading
from typing import Dict, List, Optional
from models import Event, User, Tool, SystemOverview
from datetime import datetime, timedelta

# Tool database - maps drawer/bin to tool information
# You can expand this with actual tool data matching your inventory
TOOL_DATABASE: Dict[str, Tool] = {
    # Right drawer bins
    "right_bin_1": Tool(
        id="tool_1",
        name="Sanding Tools and Scales",
        description="Sanding tools and measurement scales",
        imageUrl="https://picsum.photos/seed/tool1/500",
        type="Tool",
        cost=49.99
    ),
    "right_bin_2": Tool(
        id="tool_2",
        name="Clamps",
        description="Various clamps for holding workpieces",
        imageUrl="https://picsum.photos/seed/tool2/500",
        type="Tool",
        cost=34.99
    ),
    "right_bin_3": Tool(
        id="tool_3",
        name="Electrical and Hot Glue",
        description="Electrical components and hot glue supplies",
        imageUrl="https://picsum.photos/seed/tool3/500",
        type="Electronics",
        cost=24.99
    ),
    "right_bin_4": Tool(
        id="tool_4",
        name="Sockets and Allen Keys",
        description="Socket set and hex key set",
        imageUrl="https://picsum.photos/seed/tool4/500",
        type="Tool",
        cost=39.99
    ),
    "right_bin_5": Tool(
        id="tool_5",
        name="Drivers and Bits",
        description="Screwdriver set with various bits",
        imageUrl="https://picsum.photos/seed/tool5/500",
        type="Tool",
        cost=29.99
    ),
    # Left drawer bins
    "left_bin_1": Tool(
        id="tool_6",
        name="Drill and Dremel",
        description="Drill and Dremel rotary tool",
        imageUrl="https://picsum.photos/seed/tool6/500",
        type="Tool",
        cost=79.99
    ),
    "left_bin_2": Tool(
        id="tool_7",
        name="Measuring Tools",
        description="Calipers, rulers, and measuring instruments",
        imageUrl="https://picsum.photos/seed/tool7/500",
        type="Tool",
        cost=19.99
    ),
    "left_bin_3": Tool(
        id="tool_8",
        name="Hammers",
        description="Various hammers for different applications",
        imageUrl="https://picsum.photos/seed/tool8/500",
        type="Tool",
        cost=24.99
    ),
    "left_bin_4": Tool(
        id="tool_9",
        name="Pliers and Cutters",
        description="Pliers, wire cutters, and similar tools",
        imageUrl="https://picsum.photos/seed/tool9/500",
        type="Tool",
        cost=24.99
    ),
    "left_bin_5": Tool(
        id="tool_10",
        name="Drivers and Bits",
        description="Screwdriver set with various bits",
        imageUrl="https://picsum.photos/seed/tool10/500",
        type="Tool",
        cost=29.99
    ),
}

# User database - maps face recognition names to user info
USER_DATABASE: Dict[str, User] = {
    "Mason Thomas - mgt210000": User(
        id="user_2",
        name="Mason Thomas",
        email="mason.thomas@utdallas.edu",
        imageUrl="https://picsum.photos/seed/user2/500"
    ),
    "Kynlee Thomas": User(
        id="user_15",
        name="Kynlee Thomas",
        email="kynlee.thomas@utdallas.edu",
        imageUrl="https://picsum.photos/seed/user15/500"
    ),
}

class EventTracker:
    def __init__(self):
        self.events: List[Event] = []
        self.lock = threading.Lock()
        self.previous_drawer_state: Dict[str, str] = {"left": "no drawer open", "right": "no drawer open"}
        self.checked_out_tools: Dict[str, Dict] = {}  # tool_id -> {user_id, timestamp, drawer_key}
    
    def _bin_to_tool_key(self, drawer: str, bin_name: str) -> Optional[str]:
        """Convert drawer position and bin name to tool database key"""
        if bin_name == "no drawer open" or bin_name == "unknown":
            return None
        
        # Map bin names to keys
        bin_mapping = {
            "bin 1": "bin_1",
            "bin 2": "bin_2",
            "bin 3": "bin_3",
            "bin 4": "bin_4",
            "bin 5": "bin_5",
        }
        
        bin_key = bin_mapping.get(bin_name)
        if bin_key:
            return f"{drawer}_{bin_key}"
        return None
    
    def _get_current_user(self, faces: List[Dict]) -> Optional[User]:
        """Get the first recognized user from face detections"""
        if not faces:
            return None
        
        for face in faces:
            name = face.get("name", "")
            if name != "Unknown" and name in USER_DATABASE:
                return USER_DATABASE[name]
        
        # Return a default "Unknown" user if no match
        return User(
            id="user_unknown",
            name="Unknown User",
            email="unknown@utdallas.edu",
            imageUrl="https://picsum.photos/seed/unknown/500"
        )
    
    def _create_event(self, event_type: str, user: User, tool: Tool, event_image_url: str) -> Event:
        """Create a new event"""
        return Event(
            id=str(uuid.uuid4()),
            timestamp=int(time.time()),
            type=event_type,
            user=user,
            tool=tool,
            eventImageUrl=event_image_url
        )
    
    def process_drawer_changes(self, current_drawers: Dict[str, str], faces: List[Dict], event_image_url: str = ""):
        """
        Process drawer state changes and create checkin/checkout events.
        current_drawers: {"left": "bin 1", "right": "no drawer open"}
        faces: List of face detections from face recognition
        """
        with self.lock:
            user = self._get_current_user(faces)
            if not user:
                # No user detected, can't create events
                self.previous_drawer_state = current_drawers.copy()
                return
            
            # Check each drawer for state changes
            for drawer in ["left", "right"]:
                prev_state = self.previous_drawer_state.get(drawer, "no drawer open")
                curr_state = current_drawers.get(drawer, "no drawer open")
                
                # Drawer opened (checkout)
                if prev_state == "no drawer open" and curr_state != "no drawer open" and curr_state != "unknown":
                    tool_key = self._bin_to_tool_key(drawer, curr_state)
                    if tool_key and tool_key in TOOL_DATABASE:
                        tool = TOOL_DATABASE[tool_key]
                        event = self._create_event("tool_checkout", user, tool, event_image_url)
                        self.events.append(event)
                        self.checked_out_tools[tool.id] = {
                            "user_id": user.id,
                            "timestamp": event.timestamp,
                            "drawer_key": tool_key
                        }
                
                # Drawer closed (checkin)
                elif prev_state != "no drawer open" and prev_state != "unknown" and curr_state == "no drawer open":
                    tool_key = self._bin_to_tool_key(drawer, prev_state)
                    if tool_key and tool_key in TOOL_DATABASE:
                        tool = TOOL_DATABASE[tool_key]
                        # Find if this tool was checked out
                        if tool.id in self.checked_out_tools:
                            event = self._create_event("tool_checkin", user, tool, event_image_url)
                            self.events.append(event)
                            del self.checked_out_tools[tool.id]
            
            self.previous_drawer_state = current_drawers.copy()
    
    def get_events(self, limit: Optional[int] = None) -> List[Event]:
        """Get all events, optionally limited"""
        with self.lock:
            events = sorted(self.events, key=lambda e: e.timestamp, reverse=True)
            if limit:
                return events[:limit]
            return events
    
    def get_system_overview(self) -> SystemOverview:
        """Calculate system overview statistics"""
        with self.lock:
            # Count unique tools
            tools_count = len(TOOL_DATABASE)
            
            # Count users with checked out tools
            unique_users = set()
            for checkout in self.checked_out_tools.values():
                unique_users.add(checkout["user_id"])
            users_with_checked_out_tools = len(unique_users)
            
            # Count tools unseen in last 7 days
            seven_days_ago = int(time.time()) - (7 * 24 * 60 * 60)
            seen_tool_ids = set()
            for event in self.events:
                if event.timestamp >= seven_days_ago:
                    seen_tool_ids.add(event.tool.id)
            tools_unseen = tools_count - len(seen_tool_ids)
            
            return SystemOverview(
                toolsCount=tools_count,
                usersWithCheckedOutToolsCount=users_with_checked_out_tools,
                toolsUnseenInLast7DaysCount=max(0, tools_unseen)
            )

# Global event tracker instance
event_tracker = EventTracker()

