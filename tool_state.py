from typing import Literal, TypedDict
from uuid import uuid4
from datetime import datetime
class User(TypedDict):
    id: str
    name: str
    email: str
    imageUrl: str

class InventoryUpdateLogEntry(TypedDict):
    id: str
    timestamp: int
    type: Literal["tool_checkin", "tool_checkout"]
    user: User
    # TODO: tool...
    # tool: Tool
    eventImageUrl: str

class NoDrawerOpenState(TypedDict):
    state: Literal["no_drawer_open"]

class DrawerOpenState(TypedDict):
    state: Literal["drawer_open"]
    drawer_identifier: str
    tool_detection_state: Literal["waiting_for_initial_tool_detection", "watching_for_tool_checkin_or_checkout"]

    initial_tool_detection_state: set[str]
    current_tool_detection_state: set[str]

class InventoryStateManager:
    """
    Current inventory stores the what tools are stored in what drawers. The key is the tool class (from the model). The value at that key is another dict, where the key is the drawer identifier, and the value is the count of that class in that drawer.
    """
    current_inventory: dict[str, dict[str, int]] = {}

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
        name, id = user_string.split("-")
        name = name.strip()
        id = id.strip()
        return User(
            id=id,
            name=name,
            email=f"{id}@utdallas.edu",
            imageUrl=f"https://picsum.photos/seed/{id}/500"
        )

    def update_currently_detected_user(self, user: User):
        self.currently_detected_user = user

    def transition_to_drawer_open(self, drawer_identifier: str):
        assert self.tool_detection_state == NoDrawerOpenState(state="no_drawer_open")

        self.tool_detection_state = DrawerOpenState(state="drawer_open", drawer_identifier=drawer_identifier, tool_detection_state="waiting_for_initial_tool_detection", initial_tool_detection_state=set(), current_tool_detection_state=set())

    def transition_to_no_drawer_open(self):
        assert self.tool_detection_state == DrawerOpenState(state="drawer_open")

        diff = self.tool_detection_state["initial_tool_detection_state"] - self.tool_detection_state["current_tool_detection_state"]
        for tool in diff:
            now = datetime.now()
            timestamp = int(now.timestamp())
            self.event_log.append(InventoryUpdateLogEntry(
                id=str(uuid4()),
                timestamp=timestamp,
                type="tool_checkout",
                user=self.currently_detected_user,
                # tool=tool,
                eventImageUrl=f"https://picsum.photos/seed/{timestamp}/500"
            ))
        self.tool_detection_state = NoDrawerOpenState(state="no_drawer_open")
