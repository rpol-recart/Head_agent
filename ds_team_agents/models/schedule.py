"""Models for day planning and the 60% rule."""

from __future__ import annotations

import enum
from datetime import date, datetime, time

from pydantic import BaseModel, Field


WORKING_DAY_MINUTES = 480  # 8 hours
MAX_PLANNED_RATIO = 0.60  # tasks ≤ 60 % of the day
MAX_PLANNED_MINUTES = int(WORKING_DAY_MINUTES * MAX_PLANNED_RATIO)  # 288 min = 4h 48m
BUFFER_MINUTES = WORKING_DAY_MINUTES - MAX_PLANNED_MINUTES  # 192 min = 3h 12m


class SlotKind(str, enum.Enum):
    DEEP_WORK = "deep_work"
    COMMUNICATION = "communication"
    QUICK_BATCH = "quick_batch"
    BUFFER = "buffer"


class TimeSlot(BaseModel):
    start: time
    end: time
    kind: SlotKind
    task_ids: list[str] = Field(default_factory=list)
    label: str = ""

    @property
    def duration_minutes(self) -> int:
        start_m = self.start.hour * 60 + self.start.minute
        end_m = self.end.hour * 60 + self.end.minute
        return end_m - start_m


class DayPlan(BaseModel):
    """Leader's day plan respecting the 60 % rule."""

    date: date
    slots: list[TimeSlot] = Field(default_factory=list)
    overflow_task_ids: list[str] = Field(
        default_factory=list,
        description="Tasks that did not fit into 60 % — queued for next day",
    )

    @property
    def total_planned_minutes(self) -> int:
        return sum(
            s.duration_minutes for s in self.slots if s.kind != SlotKind.BUFFER
        )

    @property
    def planned_ratio(self) -> float:
        return round(self.total_planned_minutes / WORKING_DAY_MINUTES, 2)

    @property
    def remaining_capacity_minutes(self) -> int:
        return max(0, MAX_PLANNED_MINUTES - self.total_planned_minutes)

    def can_fit(self, duration_minutes: int) -> bool:
        return self.total_planned_minutes + duration_minutes <= MAX_PLANNED_MINUTES
