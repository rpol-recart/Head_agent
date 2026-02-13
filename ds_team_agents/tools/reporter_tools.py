"""Tools for Reporter Agent — digest and report generation."""

from __future__ import annotations

from datetime import date

from agents import function_tool, RunContextWrapper

from ds_team_agents.models.context import TeamContext
from ds_team_agents.models.projects import ProjectStatus
from ds_team_agents.models.tasks import DelegationStatus


@function_tool
def generate_morning_digest(ctx: RunContextWrapper[TeamContext]) -> str:
    """Generate the morning digest: events, tasks, alerts, day plan summary."""
    sections: list[str] = []

    # Events & deadlines
    events = []
    for p in ctx.context.projects:
        if p.status == ProjectStatus.COMPLETED:
            continue
        if p.deadline:
            days_left = (p.deadline - date.today()).days
            if days_left <= 3:
                events.append(
                    f"  {'⚠ OVERDUE' if days_left < 0 else f'{days_left}d left'}: "
                    f"{p.name} ({p.progress_pct}%)"
                )
    if events:
        sections.append("DEADLINES:\n" + "\n".join(events))

    # Delegation checkpoints due
    checkpoints = []
    for dt in ctx.context.delegated_tasks:
        if dt.next_checkpoint and dt.next_checkpoint <= date.today():
            checkpoints.append(f"  🔔 {dt.title} → {dt.assignee}")
    if checkpoints:
        sections.append("DELEGATION CHECKPOINTS DUE:\n" + "\n".join(checkpoints))

    # Day plan summary
    plan = ctx.context.day_plan
    if plan:
        sections.append(
            f"DAY PLAN: {plan.total_planned_minutes} min scheduled "
            f"({plan.planned_ratio * 100:.0f}% of 60% limit), "
            f"{plan.remaining_capacity_minutes} min remaining capacity"
        )

    # Pending leader tasks
    pending = [t for t in ctx.context.leader_tasks if t.outcome.status.value == "pending"]
    if pending:
        sections.append(f"PENDING TASKS: {len(pending)} task(s) not yet scheduled")

    return "\n\n".join(sections) if sections else "All clear — no urgent items today."


@function_tool
def generate_weekly_team_report(ctx: RunContextWrapper[TeamContext]) -> str:
    """Generate a weekly team summary: project progress, workload, delegations."""
    sections: list[str] = []

    # Projects
    active = [p for p in ctx.context.projects if p.status != ProjectStatus.COMPLETED]
    if active:
        lines = ["PROJECTS:"]
        for p in active:
            lines.append(f"  {p.name}: {p.progress_pct}% [{p.status.value}]")
        sections.append("\n".join(lines))

    # Workload
    if ctx.context.workload:
        lines = ["WORKLOAD:"]
        for w in ctx.context.workload:
            emp = ctx.context.find_employee(w.employee_id)
            name = emp.name if emp else w.employee_id
            lines.append(f"  {name}: {w.planned_hours}h ({w.utilization_pct}%)")
        sections.append("\n".join(lines))

    # Delegations
    active_del = [
        dt for dt in ctx.context.delegated_tasks
        if dt.status not in (DelegationStatus.DONE,)
    ]
    if active_del:
        lines = ["ACTIVE DELEGATIONS:"]
        for dt in active_del:
            lines.append(f"  [{dt.status.value}] {dt.title} → {dt.assignee}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections) if sections else "No data for weekly report."
