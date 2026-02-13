"""Models for leader tasks, delegation, and task lifecycle."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class TaskType(str, enum.Enum):
    """How a task is scheduled in the leader's day."""

    QUICK = "quick"  # < 15 min — batched into 30-min packets
    COMMUNICATION = "communication"  # 15-60 min — calls, meetings, chats
    DEEP_WORK = "deep_work"  # > 1 hr — uninterrupted focus blocks


class TaskPriority(str, enum.Enum):
    P0 = "P0"  # Critical: blocks production / business process
    P1 = "P1"  # Urgent: deadline < 1 week, high business value
    P2 = "P2"  # Important: strategic, deadline > 1 week
    P3 = "P3"  # Planned: improvements, tech-debt, learning


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    POSTPONED = "postponed"
    DELEGATED = "delegated"
    CANCELLED = "cancelled"


class DelegationStatus(str, enum.Enum):
    FORMULATING = "formulating"  # leader is reviewing formulation
    ASSIGNED = "assigned"  # sent to employee
    IN_PROGRESS = "in_progress"
    REVIEW = "review"  # waiting for leader's review
    DONE = "done"
    OVERDUE = "overdue"


# ── Leader's own task ────────────────────────────────────────────────

class ParsedTask(BaseModel):
    """Structured representation extracted from free-form chat input."""

    action: str = Field(description="Verb: позвонить, подготовить, проверить …")
    subject: str = Field(description="What the task is about")
    people: list[str] = Field(default_factory=list, description="Mentioned people")
    project_id: str | None = Field(default=None, description="Auto-bound project id")


class TaskClassification(BaseModel):
    task_type: TaskType
    estimated_minutes: int = Field(ge=5)
    priority: TaskPriority


class TaskScheduling(BaseModel):
    planned_date: date | None = None
    planned_slot_start: datetime | None = None
    planned_slot_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None


class TaskOutcome(BaseModel):
    status: TaskStatus = TaskStatus.PENDING
    actual_minutes: int | None = None
    notes: str | None = None
    delegated_to: str | None = None
    follow_up_task_ids: list[str] = Field(default_factory=list)


class LeaderTask(BaseModel):
    """A single task entered by the leader via chat."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    raw_input: str = Field(description="Original text from chat")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    parsed: ParsedTask
    classification: TaskClassification
    scheduling: TaskScheduling = Field(default_factory=TaskScheduling)
    outcome: TaskOutcome = Field(default_factory=TaskOutcome)


# ── Delegated task (assigned to a team member) ───────────────────────

class DelegatedTask(BaseModel):
    """Task formulated by the system and assigned to an employee."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_task_id: str | None = Field(
        default=None, description="Leader task that spawned this delegation"
    )
    project_id: str | None = None

    # Formulation produced by the system / approved by leader
    title: str = Field(description="Clear, actionable task title")
    description: str = Field(description="Detailed description with acceptance criteria")
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Concrete checklist the employee must satisfy",
    )
    context_notes: str = Field(
        default="",
        description="Background info: why the task matters, links to docs/data",
    )

    assignee: str = Field(description="Employee name or id")
    priority: TaskPriority = TaskPriority.P2
    estimated_hours: float | None = None
    deadline: date | None = None

    status: DelegationStatus = DelegationStatus.FORMULATING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_at: datetime | None = None
    completed_at: datetime | None = None
    actual_hours: float | None = None

    # Control checkpoints
    next_checkpoint: date | None = Field(
        default=None, description="When to ask the employee for status update"
    )
    checkpoints_log: list[CheckpointEntry] = Field(default_factory=list)
    leader_notes: str = ""


class CheckpointEntry(BaseModel):
    date: date
    status_reported: str
    progress_pct: int = Field(ge=0, le=100)
    blockers: list[str] = Field(default_factory=list)
    leader_action: str = ""


# Rebuild model to resolve forward references
DelegatedTask.model_rebuild()
