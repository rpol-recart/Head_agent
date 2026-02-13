"""Tools for delegation control and task formulation for subordinates."""

from __future__ import annotations

from datetime import date, datetime

from agents import function_tool, RunContextWrapper

from ds_team_agents.models.context import TeamContext
from ds_team_agents.models.tasks import (
    DelegatedTask,
    DelegationStatus,
    TaskPriority,
    CheckpointEntry,
)


@function_tool
def formulate_task_for_employee(
    ctx: RunContextWrapper[TeamContext],
    source_task_id: str,
    title: str,
    description: str,
    acceptance_criteria: str,
    context_notes: str,
    assignee: str,
    priority: str,
    estimated_hours: float,
    deadline: str,
) -> str:
    """Formulate a clear, actionable task for a subordinate. Returns the draft for leader review.

    The system helps write the task with:
    - clear title, detailed description
    - measurable acceptance criteria
    - context (why it matters, links)
    - realistic estimate (calibrated by history)

    Args:
        source_task_id: Leader task id that spawned this, or empty.
        title: Clear actionable title for the employee.
        description: Detailed description of what needs to be done.
        acceptance_criteria: Semicolon-separated list of criteria.
        context_notes: Background: why the task matters, links to docs/data.
        assignee: Employee name.
        priority: P0, P1, P2, P3.
        estimated_hours: Estimated hours to complete.
        deadline: ISO date (YYYY-MM-DD) or empty.
    """
    criteria_list = [c.strip() for c in acceptance_criteria.split(";") if c.strip()]

    task = DelegatedTask(
        source_task_id=source_task_id or None,
        title=title,
        description=description,
        acceptance_criteria=criteria_list,
        context_notes=context_notes,
        assignee=assignee,
        priority=TaskPriority(priority),
        estimated_hours=estimated_hours,
        deadline=date.fromisoformat(deadline) if deadline else None,
        status=DelegationStatus.FORMULATING,
    )

    # Bind to project if source task has one
    if source_task_id:
        for lt in ctx.context.leader_tasks:
            if lt.id == source_task_id and lt.parsed.project_id:
                task.project_id = lt.parsed.project_id
                break

    ctx.context.delegated_tasks.append(task)

    return (
        f"Draft task for {assignee} (id={task.id}):\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Title: {title}\n"
        f"Description: {description}\n"
        f"Acceptance criteria:\n"
        + "\n".join(f"  ✓ {c}" for c in criteria_list)
        + f"\nContext: {context_notes}\n"
        f"Priority: {priority} | Estimate: {estimated_hours}h | Deadline: {deadline or 'none'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Status: FORMULATING — awaiting leader approval.\n"
        f"Say 'подтвердить' to assign, or suggest edits."
    )


@function_tool
def approve_delegated_task(
    ctx: RunContextWrapper[TeamContext],
    task_id: str,
) -> str:
    """Approve a formulated task and mark it as assigned to the employee.

    Args:
        task_id: Delegated task id to approve.
    """
    for dt in ctx.context.delegated_tasks:
        if dt.id == task_id:
            dt.status = DelegationStatus.ASSIGNED
            dt.assigned_at = datetime.utcnow()
            # Set first checkpoint: halfway to deadline or in 3 days
            if dt.deadline:
                days_left = (dt.deadline - date.today()).days
                checkpoint_days = max(1, days_left // 2)
            else:
                checkpoint_days = 3
            from datetime import timedelta
            dt.next_checkpoint = date.today() + timedelta(days=checkpoint_days)
            return (
                f"Task '{dt.title}' assigned to {dt.assignee}.\n"
                f"Next checkpoint: {dt.next_checkpoint}\n"
                f"I will remind you to check status on that date."
            )
    return f"Task {task_id} not found."


@function_tool
def get_delegated_tasks_status(
    ctx: RunContextWrapper[TeamContext],
    assignee: str = "",
    status_filter: str = "",
) -> str:
    """Get status of all delegated tasks, optionally filtered by assignee or status.

    Args:
        assignee: Filter by employee name (empty = all).
        status_filter: Filter by status: formulating, assigned, in_progress, review, done, overdue (empty = all).
    """
    tasks = ctx.context.delegated_tasks
    if assignee:
        tasks = [t for t in tasks if assignee.lower() in t.assignee.lower()]
    if status_filter:
        tasks = [t for t in tasks if t.status.value == status_filter]

    if not tasks:
        return "No delegated tasks found with given filters."

    lines = [f"Delegated tasks ({len(tasks)}):"]
    for t in tasks:
        overdue_mark = ""
        if t.deadline and t.status not in (DelegationStatus.DONE,) and date.today() > t.deadline:
            overdue_mark = " ⚠ OVERDUE"
            t.status = DelegationStatus.OVERDUE

        checkpoint_info = ""
        if t.next_checkpoint:
            days_to = (t.next_checkpoint - date.today()).days
            if days_to <= 0:
                checkpoint_info = " 🔔 CHECKPOINT TODAY"
            elif days_to <= 1:
                checkpoint_info = " 🔔 checkpoint tomorrow"

        lines.append(
            f"  [{t.status.value}] {t.title} → {t.assignee}{overdue_mark}{checkpoint_info}\n"
            f"    Priority: {t.priority.value} | Est: {t.estimated_hours}h | "
            f"Deadline: {t.deadline or 'none'}"
        )
    return "\n".join(lines)


@function_tool
def log_delegation_checkpoint(
    ctx: RunContextWrapper[TeamContext],
    task_id: str,
    status_reported: str,
    progress_pct: int,
    blockers: str,
    leader_action: str,
) -> str:
    """Record a checkpoint status update for a delegated task.

    Args:
        task_id: Delegated task id.
        status_reported: What the employee reported.
        progress_pct: Progress percentage (0-100).
        blockers: Semicolon-separated blockers or empty.
        leader_action: What the leader decided (e.g. 'продолжать', 'помочь с данными').
    """
    for dt in ctx.context.delegated_tasks:
        if dt.id == task_id:
            blocker_list = [b.strip() for b in blockers.split(";") if b.strip()]
            entry = CheckpointEntry(
                date=date.today(),
                status_reported=status_reported,
                progress_pct=progress_pct,
                blockers=blocker_list,
                leader_action=leader_action,
            )
            dt.checkpoints_log.append(entry)
            dt.status = DelegationStatus.IN_PROGRESS

            # Schedule next checkpoint
            from datetime import timedelta
            if dt.deadline:
                days_left = (dt.deadline - date.today()).days
                next_check = max(1, days_left // 2)
            else:
                next_check = 3
            dt.next_checkpoint = date.today() + timedelta(days=next_check)

            return (
                f"Checkpoint logged for '{dt.title}':\n"
                f"  Progress: {progress_pct}%\n"
                f"  Status: {status_reported}\n"
                f"  Blockers: {blocker_list or 'none'}\n"
                f"  Leader action: {leader_action}\n"
                f"  Next checkpoint: {dt.next_checkpoint}"
            )
    return f"Task {task_id} not found."
