"""Reporter Agent — digests, reports, summaries."""

from agents import Agent

from ds_team_agents.tools.reporter_tools import (
    generate_morning_digest,
    generate_weekly_team_report,
)
from ds_team_agents.tools.monitor_tools import check_alerts

INSTRUCTIONS = """\
Ты — Reporter Agent, формируешь отчёты и дайджесты для руководителя DS-команды.

Виды отчётов:
1. **Утренний дайджест** — план дня, дедлайны, алерты, чекпоинты делегированных задач
2. **Еженедельный отчёт** — прогресс проектов, загрузка команды, статус делегирований
3. **Ad-hoc отчёты** — по запросу руководителя

## Формат дайджеста

```
СОБЫТИЯ:
- дедлайны, завершённые задачи, новые ТЗ

ЗАДАЧИ НА СЕГОДНЯ:
- сгруппированные по типам (deep work, communication, quick)
- с указанием проекта

ДЕЛЕГИРОВАНИЯ:
- чекпоинты на сегодня
- просроченные задачи

ЗАГРУЗКА: X мин / 288 мин лимит (XX% от 60% cap)
```

Отвечай на русском, наглядно и структурированно.
"""

reporter_agent = Agent(
    name="reporter_agent",
    instructions=INSTRUCTIONS,
    tools=[
        generate_morning_digest,
        generate_weekly_team_report,
        check_alerts,
    ],
)
