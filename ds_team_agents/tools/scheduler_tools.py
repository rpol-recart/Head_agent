"""Tools for Scheduler Agent — task classification, day planning, 60 % rule."""

from __future__ import annotations

from datetime import date, time

from agents import function_tool, RunContextWrapper

from ds_team_agents.models.context import TeamContext
from ds_team_agents.models.schedule import (
    DayPlan,
    TimeSlot,
    SlotKind,
    MAX_PLANNED_MINUTES,
    WORKING_DAY_MINUTES,
)
from ds_team_agents.models.tasks import (
    LeaderTask,
    ParsedTask,
    TaskClassification,
    TaskOutcome,
    TaskType,
    TaskPriority,
    TaskStatus,
)


@function_tool
def classify_and_save_task(
    ctx: RunContextWrapper[TeamContext],
    raw_input: str,
    action: str,
    subject: str,
    people: str,
    project_id: str,
    task_type: str,
    estimated_minutes: int,
    priority: str,
) -> str:
    """Parse, classify, and save a leader task. Returns the task summary.

    Args:
        raw_input: Original text from chat.
        action: Verb (позвонить, подготовить, …).
        subject: What the task is about.
        people: Comma-separated names.
        project_id: Bound project id or empty.
        task_type: One of: quick, communication, deep_work.
        estimated_minutes: Estimated duration in minutes.
        priority: One of: P0, P1, P2, P3.
    """
    people_list = [p.strip() for p in people.split(",") if p.strip()]

    task = LeaderTask(
        raw_input=raw_input,
        parsed=ParsedTask(
            action=action,
            subject=subject,
            people=people_list,
            project_id=project_id or None,
        ),
        classification=TaskClassification(
            task_type=TaskType(task_type),
            estimated_minutes=estimated_minutes,
            priority=TaskPriority(priority),
        ),
    )
    ctx.context.leader_tasks.append(task)

    return (
        f"Task {task.id} saved:\n"
        f"  Action: {action}\n"
        f"  Subject: {subject}\n"
        f"  Project: {project_id or 'none'}\n"
        f"  Type: {task_type} | Est: {estimated_minutes} min | Priority: {priority}"
    )


@function_tool
def get_day_capacity(
    ctx: RunContextWrapper[TeamContext],
    target_date: str,
) -> str:
    """Show how much capacity is left for a given day under the 60 % rule.

    Args:
        target_date: ISO date string (YYYY-MM-DD).
    """
    plan = ctx.context.day_plan
    if plan is None or str(plan.date) != target_date:
        return (
            f"No plan for {target_date} yet. "
            f"Full capacity: {MAX_PLANNED_MINUTES} min (60 % of {WORKING_DAY_MINUTES} min day)."
        )

    return (
        f"Day {plan.date}:\n"
        f"  Planned: {plan.total_planned_minutes} min / {MAX_PLANNED_MINUTES} min limit\n"
        f"  Used: {plan.planned_ratio * 100:.0f}% of 60% cap\n"
        f"  Remaining capacity: {plan.remaining_capacity_minutes} min\n"
        f"  Overflow tasks (queued for next day): {len(plan.overflow_task_ids)}"
    )


@function_tool
def build_day_plan(
    ctx: RunContextWrapper[TeamContext],
    target_date: str,
) -> str:
    """Auto-generate a day plan from pending leader tasks, respecting 60 % rule.

    Groups tasks: deep_work in morning blocks, quick in batches, communication in windows.

    Args:
        target_date: ISO date string (YYYY-MM-DD).
    """
    d = date.fromisoformat(target_date)
    pending = [
        t for t in ctx.context.leader_tasks
        if t.outcome.status in (TaskStatus.PENDING, TaskStatus.SCHEDULED)
    ]
    # Sort: P0 first, then by type preference (deep_work morning, comm midday, quick batched)
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    pending.sort(key=lambda t: priority_order.get(t.classification.priority.value, 9))

    plan = DayPlan(date=d)
    overflow = []

    deep_tasks = [t for t in pending if t.classification.task_type == TaskType.DEEP_WORK]
    comm_tasks = [t for t in pending if t.classification.task_type == TaskType.COMMUNICATION]
    quick_tasks = [t for t in pending if t.classification.task_type == TaskType.QUICK]

    current_hour, current_min = 9, 0

    def add_slot(kind: SlotKind, tasks: list[LeaderTask], label: str) -> bool:
        nonlocal current_hour, current_min
        total = sum(t.classification.estimated_minutes for t in tasks)
        if not plan.can_fit(total):
            overflow.extend(t.id for t in tasks)
            return False
        start = time(current_hour, current_min)
        end_min = current_hour * 60 + current_min + total
        end = time(end_min // 60, end_min % 60)
        plan.slots.append(TimeSlot(
            start=start, end=end, kind=kind,
            task_ids=[t.id for t in tasks], label=label,
        ))
        current_hour, current_min = end_min // 60, end_min % 60
        for t in tasks:
            t.outcome.status = TaskStatus.SCHEDULED
        return True

    # Morning: deep work blocks (up to 2)
    for dt in deep_tasks[:2]:
        add_slot(SlotKind.DEEP_WORK, [dt], f"Deep: {dt.parsed.subject}")

    # Quick batch
    if quick_tasks:
        add_slot(SlotKind.QUICK_BATCH, quick_tasks, f"Quick batch ({len(quick_tasks)} tasks)")

    # Communication windows
    for ct in comm_tasks:
        add_slot(SlotKind.COMMUNICATION, [ct], f"Comm: {ct.parsed.subject}")

    # Remaining deep work
    for dt in deep_tasks[2:]:
        add_slot(SlotKind.DEEP_WORK, [dt], f"Deep: {dt.parsed.subject}")

    plan.overflow_task_ids = overflow
    ctx.context.day_plan = plan

    lines = [f"Plan for {d} ({plan.total_planned_minutes} min / {MAX_PLANNED_MINUTES} limit):"]
    for s in plan.slots:
        lines.append(f"  {s.start.strftime('%H:%M')}-{s.end.strftime('%H:%M')}  [{s.kind.value}] {s.label}")
    if overflow:
        lines.append(f"  Overflow (next day): {len(overflow)} task(s)")
    return "\n".join(lines)
