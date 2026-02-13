"""Models for team members, skills, and workload."""

from __future__ import annotations

import enum
from datetime import date

from pydantic import BaseModel, Field


class SkillDomain(str, enum.Enum):
    ML_CLASSICAL = "ml_classical"
    DEEP_LEARNING = "deep_learning"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    TIME_SERIES = "time_series"
    OPTIMIZATION = "optimization"
    DATA_ENGINEERING = "data_engineering"
    ANALYTICS = "analytics"
    MLOPS = "mlops"
    STATISTICS = "statistics"


class SkillLevel(str, enum.Enum):
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    EXPERT = "expert"


class EmployeeSkill(BaseModel):
    domain: SkillDomain
    level: SkillLevel


class Employee(BaseModel):
    id: str
    name: str
    role: str = Field(description="DS, ML-engineer, analyst, etc.")
    skills: list[EmployeeSkill] = Field(default_factory=list)
    weekly_capacity_hours: float = 40.0
    current_projects: list[str] = Field(
        default_factory=list, description="Active project ids"
    )


class WorkloadEntry(BaseModel):
    """Snapshot of one employee's load for a given week."""

    employee_id: str
    week_start: date
    planned_hours: float
    actual_hours: float | None = None
    projects_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="project_id → hours allocated",
    )

    @property
    def utilization_pct(self) -> float:
        return round(self.planned_hours / 40.0 * 100, 1)
