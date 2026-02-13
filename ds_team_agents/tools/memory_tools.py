"""Tools for Memory Agent — long-term storage and retrieval."""

from __future__ import annotations

from agents import function_tool, RunContextWrapper

from ds_team_agents.models.context import TeamContext


@function_tool
def store_leader_task(
    ctx: RunContextWrapper[TeamContext],
    raw_input: str,
    action: str,
    subject: str,
    people: str,
    project_hint: str,
) -> str:
    """Save a new leader task into the task log and update person↔project associations.

    Args:
        raw_input: Original text from chat.
        action: Verb extracted (позвонить, подготовить, …).
        subject: What the task is about.
        people: Comma-separated names of mentioned people.
        project_hint: Best-guess project name or empty string.
    """
    people_list = [p.strip() for p in people.split(",") if p.strip()]

    # Update person → project cache
    if project_hint:
        for person in people_list:
            ctx.context.person_project_map[person.lower()] = project_hint

    return (
        f"Stored task: action={action}, subject={subject}, "
        f"people={people_list}, project={project_hint or 'unbound'}"
    )


@function_tool
def recall_person_context(
    ctx: RunContextWrapper[TeamContext],
    person_name: str,
) -> str:
    """Look up everything the system knows about a person: associated project, role, past interactions.

    Args:
        person_name: Name (or part of name) to look up.
    """
    key = person_name.lower()

    # Check employee roster
    emp = ctx.context.find_employee(person_name)
    emp_info = (
        f"Employee: {emp.name}, role={emp.role}, skills={[s.domain.value for s in emp.skills]}"
        if emp
        else "Not found in team roster (external contact)."
    )

    # Check person→project cache
    project_id = ctx.context.person_project_map.get(key)
    proj_info = f"Associated project: {project_id}" if project_id else "No project association yet."

    return f"{emp_info}\n{proj_info}"


@function_tool
def recall_similar_projects(
    ctx: RunContextWrapper[TeamContext],
    keywords: str,
) -> str:
    """Search completed and active projects by keywords for analogies and estimation calibration.

    Args:
        keywords: Space-separated search terms (e.g. 'дефекты литьё CV').
    """
    terms = keywords.lower().split()
    matches = []
    for p in ctx.context.projects:
        text = f"{p.name} {p.customer} {' '.join(p.tags)}".lower()
        score = sum(1 for t in terms if t in text)
        if score > 0:
            matches.append((score, p))
    matches.sort(key=lambda x: -x[0])

    if not matches:
        return "No similar projects found."

    lines = []
    for score, p in matches[:5]:
        hours_info = ""
        if p.estimated_hours and p.actual_hours:
            delta = round((p.actual_hours - p.estimated_hours) / p.estimated_hours * 100)
            hours_info = f", estimate={p.estimated_hours}h, actual={p.actual_hours}h ({delta:+d}%)"
        lines.append(
            f"- {p.name} [{p.status.value}] (customer={p.customer}{hours_info})"
        )
    return "Similar projects:\n" + "\n".join(lines)


@function_tool
def get_leader_task_history(
    ctx: RunContextWrapper[TeamContext],
    limit: int = 20,
) -> str:
    """Return the most recent leader tasks for context and pattern analysis.

    Args:
        limit: Max number of tasks to return.
    """
    tasks = ctx.context.leader_tasks[-limit:]
    if not tasks:
        return "No tasks in history yet."

    lines = []
    for t in reversed(tasks):
        lines.append(
            f"- [{t.classification.task_type.value}] {t.parsed.action}: {t.parsed.subject} "
            f"({t.classification.estimated_minutes}min, {t.outcome.status.value})"
        )
    return "\n".join(lines)
