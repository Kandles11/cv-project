from typing import Literal, TypedDict


class InventoryUpdateLogEntry(TypedDict):
    pass

class User(TypedDict):
    id: str
    name: str
    email: str
    image_url: str

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
            image_url=f"https://picsum.photos/seed/{id}/500"
        )

    def update_currently_detected_user(self, user: User):
        self.currently_detected_user = user

    def transition_to_drawer_open(self, drawer_identifier: str):
        self.tool_detection_state = DrawerOpenState(state="drawer_open", drawer_identifier=drawer_identifier, tool_detection_state="waiting_for_initial_tool_detection", initial_tool_detection_state=set(), current_tool_detection_state=set())
