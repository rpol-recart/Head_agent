"""Tools for Team Analytics Agent — workload analysis and skill matrix."""

from __future__ import annotations

from agents import function_tool, RunContextWrapper

from ds_team_agents.models.context import TeamContext


@function_tool
def get_team_workload(ctx: RunContextWrapper[TeamContext]) -> str:
    """Show workload heatmap for all team members this week."""
    if not ctx.context.workload:
        return "No workload data available."

    lines = ["Team workload:"]
    for w in ctx.context.workload:
        emp = ctx.context.find_employee(w.employee_id)
        name = emp.name if emp else w.employee_id
        bar_len = min(10, int(w.utilization_pct / 10))
        bar = "█" * bar_len + "░" * (10 - bar_len)
        warning = ""
        if w.utilization_pct >= 100:
            warning = " ⚠ overloaded"
        elif w.utilization_pct >= 90:
            warning = " ⚡ high"
        lines.append(
            f"  {bar} {name:15s} {w.planned_hours}/{emp.weekly_capacity_hours if emp else 40}h "
            f"({w.utilization_pct}%){warning}"
        )
    return "\n".join(lines)


@function_tool
def find_available_employee(
    ctx: RunContextWrapper[TeamContext],
    required_skill: str,
    min_free_hours: float = 8.0,
) -> str:
    """Find employees with a given skill who have available capacity.

    Args:
        required_skill: Skill domain to search for (e.g. 'nlp', 'computer_vision').
        min_free_hours: Minimum free hours needed.
    """
    candidates = []
    for emp in ctx.context.employees:
        has_skill = any(s.domain.value == required_skill for s in emp.skills)
        if not has_skill:
            continue
        load = ctx.context.get_employee_load(emp.id)
        free_hours = emp.weekly_capacity_hours - (load.planned_hours if load else 0)
        if free_hours >= min_free_hours:
            skill_level = next(
                (s.level.value for s in emp.skills if s.domain.value == required_skill),
                "unknown",
            )
            candidates.append((free_hours, emp.name, skill_level))

    if not candidates:
        return f"No available employees with skill '{required_skill}' and {min_free_hours}+ free hours."

    candidates.sort(key=lambda x: -x[0])
    lines = [f"Available employees with '{required_skill}':"]
    for free_h, name, level in candidates:
        lines.append(f"  {name} — {level}, {free_h}h free this week")
    return "\n".join(lines)


@function_tool
def get_skill_matrix(ctx: RunContextWrapper[TeamContext]) -> str:
    """Show the team's skill matrix: who knows what and at what level."""
    if not ctx.context.employees:
        return "No employee data available."

    lines = ["Skill matrix:"]
    for emp in ctx.context.employees:
        skills_str = ", ".join(
            f"{s.domain.value}({s.level.value})" for s in emp.skills
        )
        lines.append(f"  {emp.name:15s} [{emp.role}]: {skills_str}")
    return "\n".join(lines)
