"""Tools for Task Monitor Agent — project tracking and alerts."""

from __future__ import annotations

from datetime import date

from agents import function_tool, RunContextWrapper

from ds_team_agents.models.context import TeamContext
from ds_team_agents.models.projects import ProjectStatus


@function_tool
def get_project_status(
    ctx: RunContextWrapper[TeamContext],
    project_name: str,
) -> str:
    """Get detailed status of a specific project.

    Args:
        project_name: Project name or keyword to search.
    """
    project = ctx.context.find_project(project_name)
    if not project:
        return f"Project matching '{project_name}' not found."

    hours_info = ""
    if project.estimated_hours:
        actual = project.actual_hours or 0
        pct = round(actual / project.estimated_hours * 100) if project.estimated_hours else 0
        hours_info = f"\n  Hours: {actual}/{project.estimated_hours} ({pct}% of budget)"

    deadline_info = ""
    if project.deadline:
        days_left = (project.deadline - date.today()).days
        urgency = " ⚠ OVERDUE" if days_left < 0 else f" ({days_left} days left)"
        deadline_info = f"\n  Deadline: {project.deadline}{urgency}"

    team_str = ", ".join(project.assigned_employees) or "unassigned"

    return (
        f"Project: {project.name}\n"
        f"  Status: {project.status.value}\n"
        f"  Progress: {project.progress_pct}%\n"
        f"  Team: {team_str}"
        f"{hours_info}{deadline_info}"
    )


@function_tool
def get_all_projects_summary(ctx: RunContextWrapper[TeamContext]) -> str:
    """Return a summary table of all active projects."""
    active = [
        p for p in ctx.context.projects
        if p.status not in (ProjectStatus.COMPLETED,)
    ]
    if not active:
        return "No active projects."

    lines = [f"Active projects ({len(active)}):"]
    for p in active:
        bar_len = p.progress_pct // 10
        bar = "█" * bar_len + "░" * (10 - bar_len)
        deadline_str = str(p.deadline) if p.deadline else "no deadline"
        lines.append(
            f"  {bar} {p.name:30s} {p.progress_pct:3d}% [{p.status.value}] {deadline_str}"
        )
    return "\n".join(lines)


@function_tool
def check_alerts(ctx: RunContextWrapper[TeamContext]) -> str:
    """Check for critical alerts: overdue projects, overloaded employees, approaching deadlines."""
    alerts: list[str] = []

    for p in ctx.context.projects:
        if p.deadline and p.status not in (ProjectStatus.COMPLETED,):
            days_left = (p.deadline - date.today()).days
            if days_left < 0:
                alerts.append(f"🔴 OVERDUE: {p.name} — deadline was {p.deadline}")
            elif days_left <= 3:
                alerts.append(
                    f"🟡 APPROACHING: {p.name} — {days_left} day(s) left, progress {p.progress_pct}%"
                )

    for w in ctx.context.workload:
        if w.utilization_pct >= 100:
            emp = ctx.context.find_employee(w.employee_id)
            name = emp.name if emp else w.employee_id
            alerts.append(f"🔴 OVERLOADED: {name} — {w.utilization_pct}% utilization")
        elif w.utilization_pct >= 90:
            emp = ctx.context.find_employee(w.employee_id)
            name = emp.name if emp else w.employee_id
            alerts.append(f"🟡 HIGH LOAD: {name} — {w.utilization_pct}%")

    # Check delegated tasks
    for dt in ctx.context.delegated_tasks:
        if dt.deadline and dt.status.value not in ("done",) and date.today() > dt.deadline:
            alerts.append(f"🔴 DELEGATED OVERDUE: '{dt.title}' → {dt.assignee}")
        if dt.next_checkpoint and dt.next_checkpoint <= date.today():
            alerts.append(f"🔔 CHECKPOINT DUE: '{dt.title}' → {dt.assignee}")

    return "\n".join(alerts) if alerts else "No critical alerts."
