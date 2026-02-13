"""Tools for TZ Analyst Agent — estimation helpers and risk framework."""

from __future__ import annotations

from agents import function_tool, RunContextWrapper

from ds_team_agents.models.context import TeamContext


@function_tool
def compute_pert_estimate(
    optimistic: float,
    realistic: float,
    pessimistic: float,
) -> str:
    """Calculate PERT weighted estimate: (O + 4M + P) / 6.

    Args:
        optimistic: Best-case hours.
        realistic: Most likely hours.
        pessimistic: Worst-case hours.
    """
    expected = round((optimistic + 4 * realistic + pessimistic) / 6, 1)
    return (
        f"PERT estimate: {expected}h\n"
        f"  Optimistic: {optimistic}h\n"
        f"  Realistic:  {realistic}h\n"
        f"  Pessimistic: {pessimistic}h"
    )


@function_tool
def get_estimation_calibration(
    ctx: RunContextWrapper[TeamContext],
    task_domain: str,
) -> str:
    """Get historical calibration coefficient for a task domain.

    Compares past estimates vs actuals to suggest correction factor.

    Args:
        task_domain: Domain keyword (e.g. 'cv', 'nlp', 'tabular', 'optimization').
    """
    domain_lower = task_domain.lower()
    relevant = []
    for p in ctx.context.projects:
        if p.estimated_hours and p.actual_hours:
            text = f"{p.name} {' '.join(p.tags)}".lower()
            if domain_lower in text:
                ratio = p.actual_hours / p.estimated_hours
                relevant.append((p.name, p.estimated_hours, p.actual_hours, ratio))

    if not relevant:
        return (
            f"No completed projects in domain '{task_domain}' for calibration. "
            f"Using default factor 1.0."
        )

    avg_ratio = sum(r[3] for r in relevant) / len(relevant)
    lines = [f"Calibration for '{task_domain}' (based on {len(relevant)} project(s)):"]
    for name, est, act, ratio in relevant:
        lines.append(f"  {name}: est={est}h, actual={act}h (×{ratio:.2f})")
    lines.append(f"\n  Recommended correction factor: ×{avg_ratio:.2f}")
    return "\n".join(lines)
