"""Models for projects, TZ analysis, and risk assessment."""

from __future__ import annotations

import enum
from datetime import date

from pydantic import BaseModel, Field


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ANALYSIS = "analysis"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class ProjectComplexity(str, enum.Enum):
    S = "S"  # < 40 hrs
    M = "M"  # 40-120 hrs
    L = "L"  # 120-320 hrs
    XL = "XL"  # > 320 hrs


class RiskProbability(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskItem(BaseModel):
    category: str
    description: str
    probability: RiskProbability
    impact: RiskProbability
    mitigation: str = ""


class TaskDecomposition(BaseModel):
    task: str
    hours_optimistic: float
    hours_realistic: float
    hours_pessimistic: float

    @property
    def pert_estimate(self) -> float:
        """PERT weighted estimate: (O + 4M + P) / 6"""
        return round(
            (self.hours_optimistic + 4 * self.hours_realistic + self.hours_pessimistic) / 6,
            1,
        )


class TotalEstimate(BaseModel):
    hours_min: float
    hours_expected: float = Field(description="PERT-weighted estimate")
    hours_max: float


class TZAnalysis(BaseModel):
    """Output of TZ Analyst Agent — full technical specification analysis."""

    project_name: str
    summary: str
    complexity: ProjectComplexity
    decomposition: list[TaskDecomposition]
    total_estimate: TotalEstimate
    risks: list[RiskItem] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    recommended_team: list[str] = Field(default_factory=list)
    similar_projects: list[str] = Field(default_factory=list)
    data_requirements: str = ""


class Project(BaseModel):
    id: str
    name: str
    customer: str = Field(description="Internal stakeholder / department")
    status: ProjectStatus = ProjectStatus.DRAFT
    assigned_employees: list[str] = Field(default_factory=list)
    start_date: date | None = None
    deadline: date | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    progress_pct: int = Field(default=0, ge=0, le=100)
    tz_analysis: TZAnalysis | None = None
    tags: list[str] = Field(default_factory=list)
