from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class WellnessTip(BaseModel):
    """Simple wellness tip / hack resource."""

    id: int = Field(..., description="Stable identifier for the tip")
    title: str = Field(..., description="Short title for the wellness tip")
    description: str = Field(..., description="Detailed guidance for the tip")
    category: Optional[str] = Field(None, description="Category such as wellness/productivity")
    tags: List[str] = Field(default_factory=list, description="Searchable tags for this tip")


# Static set of wellness tips that can be shown in the app and converted to tasks.
WELLNESS_TIPS: List[WellnessTip] = [
    WellnessTip(
        id=1,
        title="2-Minute Reset for Overwhelm",
        description=(
            "Stand up, take 10 slow breaths, and name one small win from today. "
            "This interrupts the stress loop and clears your head before the next task."
        ),
        category="wellness",
        tags=["anxiety", "breathing", "reset"],
    ),
    WellnessTip(
        id=2,
        title="The 25/5 Focus Sprint",
        description=(
            "Work for 25 minutes with all notifications off, then take a 5-minute break. "
            "Stack three sprints to finish one meaningful chunk."
        ),
        category="productivity",
        tags=["focus", "pomodoro", "deep work"],
    ),
    WellnessTip(
        id=3,
        title="Write the First Messy Draft",
        description=(
            "When stuck, commit to writing the worst version in 10 minutes. "
            "Momentum beats perfection; you can edit after you see it on the page."
        ),
        category="creativity",
        tags=["writer's block", "procrastination"],
    ),
    WellnessTip(
        id=4,
        title="Micro-Plan Tomorrow Tonight",
        description=(
            "Before bed, pick your single most important task and the first 2 steps. "
            "Your morning brain follows a clear script instead of negotiating."
        ),
        category="planning",
        tags=["morning routine", "priorities"],
    ),
    WellnessTip(
        id=5,
        title="Calm Body, Calm Mind",
        description=(
            "Relax your jaw, drop your shoulders, and unclench your hands. "
            "Physical tension fuels anxious thoughts; releasing it gives you more control."
        ),
        category="wellness",
        tags=["grounding", "stress"],
    ),
]


@router.get("/wellness", response_model=List[WellnessTip])
def get_wellness_tips() -> List[WellnessTip]:
    """
    Return a static list of wellness tips / hacks.

    The mobile app can display each item with a button that calls the /tasks/
    endpoint to instantly add it to the user's task list.
    """
    return WELLNESS_TIPS
