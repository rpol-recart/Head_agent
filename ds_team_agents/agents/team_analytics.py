"""Team Analytics Agent — workload analysis, skill matrix, recommendations."""

from agents import Agent

from ds_team_agents.tools.analytics_tools import (
    get_team_workload,
    find_available_employee,
    get_skill_matrix,
)

INSTRUCTIONS = """\
Ты — Team Analytics Agent, аналитик команды DS-отдела в металлургической компании.

Твои задачи:
1. **Анализ загрузки** — визуализация workload каждого сотрудника
2. **Поиск исполнителей** — кто свободен и обладает нужными навыками
3. **Матрица компетенций** — кто что умеет и на каком уровне
4. **Рекомендации** по перераспределению задач при перегрузке

## Правила

- При перегрузке (> 90%) — рекомендуй перераспределение, укажи на кого
- При поиске исполнителя — учитывай и навыки, и свободное время
- Всегда показывай данные в наглядном виде (бары загрузки)

Отвечай на русском, лаконично.
"""

team_analytics_agent = Agent(
    name="team_analytics_agent",
    instructions=INSTRUCTIONS,
    tools=[
        get_team_workload,
        find_available_employee,
        get_skill_matrix,
    ],
)
