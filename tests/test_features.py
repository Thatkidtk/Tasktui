import json
from datetime import date
from uuid import uuid4

import pytest
from textual.app import App

from tasktui.app import DEFAULT_STATUS_LABELS, CalendarView, TaskBoardApp, TaskTable
from tasktui.config import AppConfig
from tasktui.models import ChecklistItem, Task


def _task(title: str, **kwargs) -> Task:
    """Helper to build tasks quickly."""
    return Task(id=str(uuid4()), title=title, **kwargs)


def test_checklist_and_timer_roundtrip() -> None:
    task = _task(
        "with checklist",
        checklist=[ChecklistItem("a", done=True), ChecklistItem("b", done=False)],
        countdown_seconds=120,
        remaining_seconds=45,
        timer_running=True,
    )
    data = task.to_dict()
    restored = Task.from_dict(data)
    assert restored.checklist[0].done is True
    assert restored.checklist[1].done is False
    assert restored.remaining_seconds == 45
    assert restored.timer_running is True


@pytest.mark.asyncio
async def test_task_table_respects_tag_filter() -> None:
    class TableApp(App):
        def compose(self):
            yield TaskTable(id="task-table")

    tasks = [
        _task("work item", tags=["work"], status="backlog"),
        _task("home item", tags=["home"], status="backlog"),
    ]

    async with TableApp().run_test() as pilot:
        table = pilot.app.query_one(TaskTable)
        table.update_rows(
            tasks=tasks,
            selected=None,
            tag_filter="work",
            status_labels=DEFAULT_STATUS_LABELS,
        )
        assert table.table.row_count == 1
        assert table.table.get_row_at(0)[0] == "work item"


def test_calendar_marks_due_tasks() -> None:
    cal = CalendarView()
    reference = date(2024, 5, 1)
    tasks = [
        _task("due soon", due=reference.replace(day=15)),
        _task("other month", due=reference.replace(month=6, day=2)),
    ]
    cal.update_calendar(tasks, reference=reference)
    assert "15●" in cal.last_render
    assert "02 other month" not in cal.last_render


def test_tick_timers_pauses_at_zero_and_saves_once(tmp_path) -> None:
    config = AppConfig(data_path=tmp_path / "tasks.json")
    task = _task("timed", countdown_seconds=1, remaining_seconds=1, timer_running=True)
    app = TaskBoardApp(config, [task])
    app._last_timer_save = 0
    app.refresh_views = lambda: None  # type: ignore[method-assign]
    # Avoid needing a mounted DOM.
    app.tick_timers()
    assert task.remaining_seconds == 0
    assert task.timer_running is False
    assert config.data_path.exists()
    saved = json.loads(config.data_path.read_text())
    assert saved[0]["remaining_seconds"] == 0
