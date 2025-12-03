from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


@dataclass
class ChecklistItem:
    label: str
    done: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChecklistItem":
        return cls(label=data.get("label", ""), done=bool(data.get("done", False)))

    def to_dict(self) -> Dict[str, Any]:
        return {"label": self.label, "done": self.done}


@dataclass
class Task:
    id: str
    title: str
    status: str = "backlog"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    due: Optional[date] = None
    checklist: List[ChecklistItem] = field(default_factory=list)
    countdown_seconds: int = 25 * 60
    remaining_seconds: int = 25 * 60
    timer_running: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        due_raw = data.get("due")
        due_value = date.fromisoformat(due_raw) if due_raw else None
        checklist_items = [
            ChecklistItem.from_dict(item) for item in data.get("checklist", [])
        ]
        tags = [str(tag) for tag in data.get("tags", []) if isinstance(tag, str)]
        return cls(
            id=str(data.get("id")),
            title=str(data.get("title", "")),
            status=str(data.get("status", "backlog")),
            description=str(data.get("description", "")),
            tags=tags,
            due=due_value,
            checklist=checklist_items,
            countdown_seconds=int(data.get("countdown_seconds", 25 * 60)),
            remaining_seconds=int(
                data.get(
                    "remaining_seconds",
                    data.get("countdown_seconds", 25 * 60),
                )
            ),
            timer_running=bool(data.get("timer_running", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "description": self.description,
            "tags": self.tags,
            "due": self.due.isoformat() if self.due else None,
            "checklist": [item.to_dict() for item in self.checklist],
            "countdown_seconds": self.countdown_seconds,
            "remaining_seconds": self.remaining_seconds,
            "timer_running": self.timer_running,
        }
