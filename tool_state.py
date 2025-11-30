from typing import Counter, Literal, TypedDict
from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass

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

MS_FROM_DRAWER_OPEN_TO_WATCHING_FOR_TOOL_CHECKIN_OR_CHECKOUT = 500

@dataclass
class DrawerOpenState:
    drawer_identifier: str
    last_detected_user: User | None = None
    time_of_drawer_open: datetime = datetime.now()

    initial_tool_detection_state: set[str] = set()
    current_tool_detection_state: set[str] = set()

    state: Literal["drawer_open"] = "drawer_open"

    @property
    def detailed_state(self) -> Literal["waiting_for_initial_tool_detection", "watching_for_tool_checkin_or_checkout"]:
        drawer_open_delta = datetime.now() - self.time_of_drawer_open
        is_ready_for_tool_count_changes = drawer_open_delta.total_seconds() < MS_FROM_DRAWER_OPEN_TO_WATCHING_FOR_TOOL_CHECKIN_OR_CHECKOUT / 1000

        if is_ready_for_tool_count_changes:
            return "waiting_for_initial_tool_detection"
        else:
            return "watching_for_tool_checkin_or_checkout"


class InventoryStateManager:
    """
    Current inventory stores the what tools are stored in what drawers. The key is the tool class (from the model). The value at that key is another dict, where the key is the drawer identifier, and the value is the count of that class in that drawer.
    """
    current_inventory: dict[str, Counter[str]] = {}

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
            print("Transitioning to drawer open from no drawer open")
        else:
            print(f"Transitioning to drawer open from drawer open. This means that we are still waiting for the initial tool detection to complete. In ${MS_FROM_DRAWER_OPEN_TO_WATCHING_FOR_TOOL_CHECKIN_OR_CHECKOUT}ms, we'll start watching for tool checkin or checkout, so you can take or return tools.")

        new_state = DrawerOpenState(drawer_identifier=drawer_identifier)
        print(f"prev state: {self.tool_detection_state}")
        print(f"new state: {new_state}")
        self.tool_detection_state = new_state

    def transition_to_no_drawer_open(self):
        assert isinstance(self.tool_detection_state, DrawerOpenState)
        print("Transitioning to no drawer open from drawer open.")

        save_state: DrawerOpenState = self.tool_detection_state
        self.tool_detection_state = NoDrawerOpenState()

        checked_out_tools = save_state.initial_tool_detection_state - save_state.current_tool_detection_state
        returned_tools = save_state.current_tool_detection_state - save_state.initial_tool_detection_state
        for tool in checked_out_tools:
            self.current_inventory[tool][save_state.drawer_identifier] -= 1
            self._generate_event_log_entry(event_type="tool_checkout", user=save_state.last_detected_user, tool=self._generate_tool_from_class(tool))
        for tool in returned_tools:
            self.current_inventory[tool][save_state.drawer_identifier] += 1
            self._generate_event_log_entry(event_type="tool_checkin", user=save_state.last_detected_user, tool=self._generate_tool_from_class(tool))

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

    def _generate_event_log_entry(self, event_type: Literal["tool_checkout", "tool_checkin"], user: User, tool: Tool):
        now = datetime.now()
        timestamp = int(now.timestamp())
        self.event_log.append(InventoryUpdateLogEntry(
            id=str(uuid4()),
            timestamp=timestamp,
            type=event_type,
            user=user,
            tool=tool,
            eventImageUrl=f"https://picsum.photos/seed/{timestamp}/500"
        ))