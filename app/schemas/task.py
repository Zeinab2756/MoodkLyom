from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Priority = Priority.MEDIUM
    deadline: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class ProposedTask(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Priority = Priority.MEDIUM
    source_mood: str


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[Priority] = None
    deadline: Optional[datetime] = None
    is_completed: Optional[bool] = None


class TaskResponse(TaskBase):
    id: int
    user_id: str
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    success: bool = True
    data: list[TaskResponse]
    total: int
    completed: int
    pending: int


class TaskSingleResponse(BaseModel):
    success: bool = True
    data: TaskResponse


class ProposedTaskListResponse(BaseModel):
    success: bool = True
    data: list[ProposedTask]


class TaskStatsData(BaseModel):
    total: int
    completed: int
    pending: int
    overdue: int
    by_priority: dict[str, int]


class TaskStatsResponse(BaseModel):
    success: bool = True
    data: TaskStatsData
