# models.py
from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class User(BaseModel):
    id: str
    name: str
    email: str
    imageUrl: str

class Tool(BaseModel):
    id: str
    name: str
    description: str
    imageUrl: str
    type: str
    cost: float

class Event(BaseModel):
    id: str
    timestamp: int
    type: Literal["tool_checkin", "tool_checkout"]
    user: User
    tool: Tool
    eventImageUrl: str

class SystemOverview(BaseModel):
    toolsCount: int
    usersWithCheckedOutToolsCount: int
    toolsUnseenInLast7DaysCount: int

