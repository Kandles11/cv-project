from typing import Counter, Literal, TypedDict
from uuid import uuid4
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

DRAWER_TO_TOOL_MAP = {
    "drivers and bits": "ifixit",
    "clamps": "clamp"
}

@dataclass
class User:
    id: str
    name: str
    email: str
    imageUrl: str

@dataclass
class Tool:
    id: str
    name: str
    description: str
    imageUrl: str
    type: str
    cost: float


class InventoryUpdateLogEntry(TypedDict):
    id: str
    timestamp: int
    type: Literal["tool_checkin", "tool_checkout"]
    user: User
    tool: Tool
    eventImageUrl: str

@dataclass
class NoDrawerOpenState:
    state: Literal["no_drawer_open"] = "no_drawer_open"

MS_FROM_DRAWER_OPEN_TO_WATCHING_FOR_TOOL_CHECKIN_OR_CHECKOUT = 1000

@dataclass
class DrawerOpenState:
    drawer_identifier: str
    last_detected_user: User | None = None
    time_of_drawer_open: datetime = field(default_factory=datetime.now)

    initial_tool_detection_state: set[str] = field(default_factory=set)
    current_tool_detection_state: set[str] = field(default_factory=set)
    
    # Buffer to store timestamped snapshots of current_tool_detection_state
    # Each entry is (timestamp, tool_detection_state_copy, frame_base64)
    tool_detection_state_history: list[tuple[datetime, set[str], str]] = field(default_factory=list)

    state: Literal["drawer_open"] = "drawer_open"

    @property
    def detailed_state(self) -> Literal["waiting_for_initial_tool_detection", "watching_for_tool_checkin_or_checkout"]:
        drawer_open_delta = datetime.now() - self.time_of_drawer_open
        is_ready_for_tool_count_changes = drawer_open_delta.total_seconds() < MS_FROM_DRAWER_OPEN_TO_WATCHING_FOR_TOOL_CHECKIN_OR_CHECKOUT / 1000

        if is_ready_for_tool_count_changes:
            return "waiting_for_initial_tool_detection"
        else:
            return "watching_for_tool_checkin_or_checkout"
    
    def record_tool_detection_snapshot(self, frame_base64: str):
        """Record a snapshot of current_tool_detection_state with timestamp and cleanup old snapshots."""
        now = datetime.now()
        # Store snapshot with current timestamp
        self.tool_detection_state_history.append((now, self.current_tool_detection_state.copy(), frame_base64))
        
        # Clean up snapshots older than 2 seconds
        cutoff_time = now - timedelta(seconds=2)
        self.tool_detection_state_history = [
            (timestamp, state, frame) for timestamp, state, frame in self.tool_detection_state_history
            if timestamp > cutoff_time
        ]
    
    def _get_tool_detection_state_2_seconds_ago(self) -> tuple[set[str], str]:
        """
        Get the tool detection state from approximately 2 seconds ago.
        Falls back to the most recent non-empty snapshot, or current state if no snapshots exist.
        Returns a tuple of (state, frame_base64).
        """
        now = datetime.now()
        target_time = now - timedelta(seconds=2)
        
        # First, try to find snapshots at or before 2 seconds ago (preferred)
        candidates_at_or_before = []
        candidates_after = []
        
        for timestamp, state, frame in self.tool_detection_state_history:
            if timestamp <= target_time:
                candidates_at_or_before.append((timestamp, state, frame))
            else:
                candidates_after.append((timestamp, state, frame))
        
        # Prefer the most recent snapshot at or before 2 seconds ago
        if candidates_at_or_before:
            # Sort by timestamp descending to get the most recent
            candidates_at_or_before.sort(key=lambda x: x[0], reverse=True)
            return (candidates_at_or_before[0][1], candidates_at_or_before[0][2])
        
        # If no snapshot at or before 2 seconds, use the closest one overall
        if candidates_after:
            candidates_after.sort(key=lambda x: abs((x[0] - target_time).total_seconds()))
            return (candidates_after[0][1], candidates_after[0][2])
        
        # Fallback: use the most recent non-empty snapshot
        for timestamp, state, frame in reversed(self.tool_detection_state_history):
            if state:  # Non-empty set
                return (state, frame)
        
        # Final fallback: use current state (might be empty, but it's better than nothing)
        return (self.current_tool_detection_state, "")


class InventoryStateManager:
    """
    Current inventory stores the what tools are stored in what drawers. The key is the tool class (from the model). The value at that key is another dict, where the key is the drawer identifier, and the value is the count of that class in that drawer.
    """
    current_inventory: dict[str, Counter[str]] = defaultdict(Counter)

    """
    Stores the user that is currently being detected by the facial detection task.
    """
    currently_detected_user: User | None = None

    """
    Event log stores the history of inventory updates.
    """
    event_log: list[InventoryUpdateLogEntry] = []


    tool_detection_state: NoDrawerOpenState | DrawerOpenState = NoDrawerOpenState(state="no_drawer_open")

    @staticmethod
    def make_user_from_string(user_string: str) -> User:
        split = user_string.split("-")
        if len(split) != 2:
            return User(
                id=user_string,
                name=user_string,
                email=f"{user_string}@utdallas.edu",
                imageUrl=f"https://picsum.photos/seed/{user_string}/500"
            )
        name, id = split
        name = name.strip()
        id = id.strip()
        return User(
            id=id,
            name=name,
            email=f"{id}@utdallas.edu",
            imageUrl=f"https://picsum.photos/seed/{id}/500"
        )

    def update_currently_detected_user(self, user: User | None):
        self.currently_detected_user = user
        if isinstance(self.tool_detection_state, DrawerOpenState) and user is not None:
            self.tool_detection_state.last_detected_user = user

    def transition_to_drawer_open(self, drawer_identifier: str):
        if isinstance(self.tool_detection_state, NoDrawerOpenState):
            print("Transitioning from no drawer open to drawer open")
        else:
            print(f"Transitioning from drawer open to drawer open. This means that we are still waiting for the initial tool detection to complete. In ${MS_FROM_DRAWER_OPEN_TO_WATCHING_FOR_TOOL_CHECKIN_OR_CHECKOUT}ms, we'll start watching for tool checkin or checkout, so you can take or return tools.")

        new_state = DrawerOpenState(drawer_identifier=drawer_identifier)
        print(f"prev state: {self.tool_detection_state}")
        print(f"new state: {new_state}")
        self.tool_detection_state = new_state

    def transition_to_no_drawer_open(self):
        assert isinstance(self.tool_detection_state, DrawerOpenState)
        print("Transitioning from drawer open to no drawer open.")


        DO_UPDATE = True
        if self.tool_detection_state.drawer_identifier not in DRAWER_TO_TOOL_MAP:
            DO_UPDATE = False
            print("skipping inventory update, drawer not in DRAWER_TO_TOOL_MAP")
        hardcode_tool = DRAWER_TO_TOOL_MAP[self.tool_detection_state.drawer_identifier]

        save_state: DrawerOpenState = self.tool_detection_state
        self.tool_detection_state = NoDrawerOpenState()

        # Use 2-second-old snapshot instead of current (potentially empty) state
        tool_detection_state_to_use, frame_base64 = save_state._get_tool_detection_state_2_seconds_ago()

        checked_out_tools = save_state.initial_tool_detection_state - tool_detection_state_to_use
        returned_tools = tool_detection_state_to_use - save_state.initial_tool_detection_state
        should_do_check_out = len(checked_out_tools) > 0
        if DO_UPDATE:
            if should_do_check_out:
                for tool in checked_out_tools:
                    tool = hardcode_tool
                    self.current_inventory[tool][save_state.drawer_identifier] -= 1
                    self._generate_event_log_entry(event_type="tool_checkout", user=save_state.last_detected_user, tool=self._generate_tool_from_class(tool), event_image_base64=frame_base64)
                    break
            else:
                for tool in returned_tools:
                    tool = hardcode_tool
                    self.current_inventory[tool][save_state.drawer_identifier] += 1
                    self._generate_event_log_entry(event_type="tool_checkin", user=save_state.last_detected_user, tool=self._generate_tool_from_class(tool), event_image_base64=frame_base64)
                    break

        print(f"prev state: {save_state}")
        print(f"new state: {self.tool_detection_state}")


    def _generate_tool_from_class(self, tool_class: str) -> Tool:
        # this is kinda unideal, might be able to do some better heuristic here
        return Tool(
            id=tool_class,
            name=tool_class,
            description=tool_class,
            imageUrl=f"https://picsum.photos/seed/{tool_class}/500",
            cost=0.0,
            type=tool_class,
        )

    def _generate_event_log_entry(self, event_type: Literal["tool_checkout", "tool_checkin"], user: User, tool: Tool, event_image_base64: str):
        now = datetime.now()
        timestamp = int(now.timestamp())
        self.event_log.append(InventoryUpdateLogEntry(
            id=str(uuid4()),
            timestamp=timestamp,
            type=event_type,
            user=user,
            tool=tool,
            eventImageUrl=event_image_base64 if event_image_base64 else f"https://picsum.photos/seed/{timestamp}/500"
        ))