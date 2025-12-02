from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import List
from uuid import uuid4

from .config import CONFIG_DIR, DEFAULT_TASK_PATH
from .models import Task, ChecklistItem


DEFAULT_TASKS: List[Task] = [
    Task(
        id=str(uuid4()),
        title="Sketch board layout",
        status="backlog",
        description="Rough out how the kanban and list views should look.",
        tags=["design", "kanban"],
        checklist=[
            ChecklistItem(label="List view columns"),
            ChecklistItem(label="Board column titles"),
            ChecklistItem(label="Calendar cells"),
        ],
        countdown_seconds=15 * 60,
        remaining_seconds=15 * 60,
    ),
    Task(
        id=str(uuid4()),
        title="Wire up time tracking",
        status="in_progress",
        description="Make sure timers can be started and paused from the TUI.",
        tags=["timer", "tui"],
        checklist=[
            ChecklistItem(label="Start/pause control", done=True),
            ChecklistItem(label="Countdown per task"),
            ChecklistItem(label="Reset to default duration"),
        ],
        countdown_seconds=25 * 60,
        remaining_seconds=22 * 60,
    ),
    Task(
        id=str(uuid4()),
        title="Ship a first demo",
        status="done",
        description="Create a default config and sample data so new users can explore.",
        tags=["docs", "demo"],
        checklist=[
            ChecklistItem(label="Default config file", done=True),
            ChecklistItem(label="Sample tasks", done=True),
            ChecklistItem(label="Update README", done=True),
        ],
        due=date.today(),
        countdown_seconds=5 * 60,
        remaining_seconds=0,
    ),
]


def ensure_data_file(data_path: Path = DEFAULT_TASK_PATH) -> None:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if data_path.exists():
        return
    save_tasks(DEFAULT_TASKS, data_path=data_path)


def load_tasks(data_path: Path = DEFAULT_TASK_PATH) -> List[Task]:
    ensure_data_file(data_path)
    try:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Corrupt data; back it up and re-seed with defaults.
        backup = data_path.with_suffix(".bak")
        data_path.rename(backup)
        save_tasks(DEFAULT_TASKS, data_path=data_path)
        raw = [task.to_dict() for task in DEFAULT_TASKS]
    return [Task.from_dict(item) for item in raw]


def save_tasks(tasks: List[Task], data_path: Path = DEFAULT_TASK_PATH) -> None:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    serialised = [task.to_dict() for task in tasks]
    data_path.write_text(json.dumps(serialised, indent=2), encoding="utf-8")
