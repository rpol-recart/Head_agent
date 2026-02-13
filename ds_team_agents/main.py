"""Entry point — run the orchestrator agent with demo team context."""

from __future__ import annotations

import asyncio
from datetime import date

from agents import Runner

from ds_team_agents.agents import orchestrator_agent
from ds_team_agents.models.context import TeamContext
from ds_team_agents.models.team import Employee, EmployeeSkill, SkillDomain, SkillLevel, WorkloadEntry
from ds_team_agents.models.projects import Project, ProjectStatus


def build_demo_context() -> TeamContext:
    """Pre-populate context with realistic team and project data."""

    employees = [
        Employee(
            id="ivanov", name="Иванов Алексей", role="Senior ML Engineer",
            skills=[
                EmployeeSkill(domain=SkillDomain.DEEP_LEARNING, level=SkillLevel.SENIOR),
                EmployeeSkill(domain=SkillDomain.COMPUTER_VISION, level=SkillLevel.SENIOR),
                EmployeeSkill(domain=SkillDomain.MLOPS, level=SkillLevel.MIDDLE),
            ],
            current_projects=["pred_quality"],
        ),
        Employee(
            id="petrova", name="Петрова Мария", role="ML Engineer",
            skills=[
                EmployeeSkill(domain=SkillDomain.NLP, level=SkillLevel.SENIOR),
                EmployeeSkill(domain=SkillDomain.ML_CLASSICAL, level=SkillLevel.MIDDLE),
            ],
            current_projects=["nlp_defects"],
        ),
        Employee(
            id="sidorov", name="Сидоров Дмитрий", role="Senior DS",
            skills=[
                EmployeeSkill(domain=SkillDomain.OPTIMIZATION, level=SkillLevel.EXPERT),
                EmployeeSkill(domain=SkillDomain.ML_CLASSICAL, level=SkillLevel.SENIOR),
                EmployeeSkill(domain=SkillDomain.COMPUTER_VISION, level=SkillLevel.MIDDLE),
            ],
            current_projects=["opt_shihta"],
        ),
        Employee(
            id="kozlov", name="Козлов Игорь", role="Data Analyst",
            skills=[
                EmployeeSkill(domain=SkillDomain.ANALYTICS, level=SkillLevel.SENIOR),
                EmployeeSkill(domain=SkillDomain.TIME_SERIES, level=SkillLevel.MIDDLE),
                EmployeeSkill(domain=SkillDomain.DATA_ENGINEERING, level=SkillLevel.MIDDLE),
            ],
            current_projects=["analytics_downtime"],
        ),
        Employee(
            id="volkova", name="Волкова Анна", role="ML Engineer",
            skills=[
                EmployeeSkill(domain=SkillDomain.TIME_SERIES, level=SkillLevel.SENIOR),
                EmployeeSkill(domain=SkillDomain.STATISTICS, level=SkillLevel.SENIOR),
            ],
            current_projects=["pred_quality"],
        ),
        Employee(
            id="novikov", name="Новиков Сергей", role="DS / MLOps",
            skills=[
                EmployeeSkill(domain=SkillDomain.MLOPS, level=SkillLevel.EXPERT),
                EmployeeSkill(domain=SkillDomain.DATA_ENGINEERING, level=SkillLevel.SENIOR),
                EmployeeSkill(domain=SkillDomain.ML_CLASSICAL, level=SkillLevel.MIDDLE),
            ],
            current_projects=["mlops_platform"],
        ),
        Employee(
            id="egorova", name="Егорова Ольга", role="Junior DS",
            skills=[
                EmployeeSkill(domain=SkillDomain.ML_CLASSICAL, level=SkillLevel.JUNIOR),
                EmployeeSkill(domain=SkillDomain.ANALYTICS, level=SkillLevel.MIDDLE),
            ],
            current_projects=["analytics_downtime"],
        ),
        Employee(
            id="morozov", name="Морозов Павел", role="Data Engineer",
            skills=[
                EmployeeSkill(domain=SkillDomain.DATA_ENGINEERING, level=SkillLevel.EXPERT),
                EmployeeSkill(domain=SkillDomain.ANALYTICS, level=SkillLevel.MIDDLE),
            ],
            current_projects=["data_lake"],
        ),
    ]

    projects = [
        Project(
            id="pred_quality", name="Предиктивное качество проката",
            customer="Прокатный цех", status=ProjectStatus.IN_PROGRESS,
            assigned_employees=["ivanov", "volkova"],
            start_date=date(2026, 1, 6), deadline=date(2026, 2, 15),
            estimated_hours=96, actual_hours=72, progress_pct=75,
            tags=["cv", "quality", "прокат", "датчики"],
        ),
        Project(
            id="nlp_defects", name="NLP-классификатор дефектов",
            customer="ОТК", status=ProjectStatus.REVIEW,
            assigned_employees=["petrova"],
            start_date=date(2026, 1, 13), deadline=date(2026, 2, 21),
            estimated_hours=64, actual_hours=56, progress_pct=90,
            tags=["nlp", "дефекты", "классификация"],
        ),
        Project(
            id="opt_shihta", name="Оптимизация шихты",
            customer="Доменный цех", status=ProjectStatus.IN_PROGRESS,
            assigned_employees=["sidorov"],
            start_date=date(2025, 12, 1), deadline=date(2026, 3, 1),
            estimated_hours=200, actual_hours=120, progress_pct=55,
            tags=["optimization", "шихта", "домна"],
        ),
        Project(
            id="analytics_downtime", name="Аналитика простоев оборудования",
            customer="Службы главного механика", status=ProjectStatus.IN_PROGRESS,
            assigned_employees=["kozlov", "egorova"],
            start_date=date(2026, 1, 20), deadline=date(2026, 3, 15),
            estimated_hours=80, actual_hours=20, progress_pct=25,
            tags=["analytics", "простои", "time_series"],
        ),
        Project(
            id="mlops_platform", name="MLOps платформа",
            customer="DS отдел (внутренний)", status=ProjectStatus.IN_PROGRESS,
            assigned_employees=["novikov"],
            estimated_hours=160, actual_hours=80, progress_pct=50,
            tags=["mlops", "инфраструктура", "ci/cd"],
        ),
        Project(
            id="data_lake", name="Интеграция Data Lake",
            customer="IT Департамент", status=ProjectStatus.IN_PROGRESS,
            assigned_employees=["morozov"],
            start_date=date(2026, 1, 1), deadline=date(2026, 4, 1),
            estimated_hours=120, actual_hours=40, progress_pct=30,
            tags=["data_engineering", "озеро данных", "интеграция"],
        ),
        # Completed project for calibration
        Project(
            id="pred_quality_old", name="Предсказание качества проката (пилот)",
            customer="Прокатный цех", status=ProjectStatus.COMPLETED,
            assigned_employees=["ivanov"],
            estimated_hours=96, actual_hours=124, progress_pct=100,
            tags=["cv", "quality", "прокат"],
        ),
    ]

    workload = [
        WorkloadEntry(employee_id="ivanov", week_start=date(2026, 2, 10), planned_hours=38,
                      projects_breakdown={"pred_quality": 38}),
        WorkloadEntry(employee_id="petrova", week_start=date(2026, 2, 10), planned_hours=32,
                      projects_breakdown={"nlp_defects": 24, "code_review": 8}),
        WorkloadEntry(employee_id="sidorov", week_start=date(2026, 2, 10), planned_hours=40,
                      projects_breakdown={"opt_shihta": 40}),
        WorkloadEntry(employee_id="kozlov", week_start=date(2026, 2, 10), planned_hours=24,
                      projects_breakdown={"analytics_downtime": 24}),
        WorkloadEntry(employee_id="volkova", week_start=date(2026, 2, 10), planned_hours=36,
                      projects_breakdown={"pred_quality": 36}),
        WorkloadEntry(employee_id="novikov", week_start=date(2026, 2, 10), planned_hours=32,
                      projects_breakdown={"mlops_platform": 32}),
        WorkloadEntry(employee_id="egorova", week_start=date(2026, 2, 10), planned_hours=30,
                      projects_breakdown={"analytics_downtime": 30}),
        WorkloadEntry(employee_id="morozov", week_start=date(2026, 2, 10), planned_hours=28,
                      projects_breakdown={"data_lake": 28}),
    ]

    return TeamContext(
        leader_name="Руководитель DS отдела",
        employees=employees,
        projects=projects,
        workload=workload,
        person_project_map={
            "краснов": "pred_defects_ceh3",
            "иванов": "pred_quality",
            "петрова": "nlp_defects",
            "сидоров": "opt_shihta",
            "козлов": "analytics_downtime",
        },
    )


async def run_chat():
    """Interactive chat loop with the orchestrator."""
    ctx = build_demo_context()
    print("=" * 60)
    print("  DS Team Management Agent")
    print("  Введите сообщение (или 'выход' для завершения)")
    print("=" * 60)

    input_items: list = []

    while True:
        try:
            user_input = input("\nВы: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input or user_input.lower() in ("выход", "exit", "quit"):
            print("До свидания!")
            break

        result = await Runner.run(
            starting_agent=orchestrator_agent,
            input=input_items + [{"role": "user", "content": user_input}],
            context=ctx,
        )

        # Accumulate conversation history
        input_items = result.to_input_list()

        print(f"\nСистема: {result.final_output}")


def main():
    asyncio.run(run_chat())


if __name__ == "__main__":
    main()
