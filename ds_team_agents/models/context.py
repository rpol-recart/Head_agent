"""Shared RunContext passed to every agent, tool, and handoff."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from .tasks import LeaderTask, DelegatedTask
from .team import Employee, WorkloadEntry
from .projects import Project
from .schedule import DayPlan


class TeamContext(BaseModel):
    """
    Dependency-injection context shared across all agents in a single run.

    Passed to ``Runner.run(context=ctx)`` and available in every tool via
    ``RunContextWrapper[TeamContext].context``.
    """

    # ── Current state ────────────────────────────────────────────
    today: date = Field(default_factory=date.today)
    leader_name: str = "Руководитель"

    # Team roster (loaded at startup from DB / config)
    employees: list[Employee] = Field(default_factory=list)

    # Active projects
    projects: list[Project] = Field(default_factory=list)

    # Workload snapshots for current week
    workload: list[WorkloadEntry] = Field(default_factory=list)

    # ── Leader task log (in-session accumulator) ─────────────────
    leader_tasks: list[LeaderTask] = Field(default_factory=list)
    delegated_tasks: list[DelegatedTask] = Field(default_factory=list)

    # Today's plan
    day_plan: DayPlan | None = None

    # ── Person → project association cache (learning) ────────────
    person_project_map: dict[str, str] = Field(
        default_factory=dict,
        description="Cached association: person name → project id",
    )

    # ── Helpers ──────────────────────────────────────────────────

    def find_project(self, query: str) -> Project | None:
        """Fuzzy search projects by name, customer, or tags."""
        q = query.lower()
        for p in self.projects:
            if q in p.name.lower() or q in p.customer.lower():
                return p
            if any(q in t.lower() for t in p.tags):
                return p
        return None

    def find_employee(self, name: str) -> Employee | None:
        n = name.lower()
        for e in self.employees:
            if n in e.name.lower():
                return e
        return None

    def get_employee_load(self, employee_id: str) -> WorkloadEntry | None:
        for w in self.workload:
            if w.employee_id == employee_id:
                return w
        return None
