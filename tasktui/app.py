from __future__ import annotations

import calendar
from datetime import date
from time import monotonic
from uuid import uuid4
from typing import Iterable, List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)

from .config import AppConfig
from .models import Task
from .storage import save_tasks


DEFAULT_STATUS_LABELS: dict[str, str] = {
    "backlog": "Backlog",
    "in_progress": "In Progress",
    "done": "Done",
}


def pretty_status(status: str, labels: dict[str, str]) -> str:
    return labels.get(status, status.replace("_", " ").title())


def next_status(current: str, columns: list[str]) -> str:
    if not columns:
        return current
    if current not in columns:
        return columns[0]
    index = columns.index(current)
    return columns[(index + 1) % len(columns)]


class TaskSelected(Message):
    """Message emitted when a task selection changes."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__()


class TagFilterChanged(Message):
    """Message emitted when a tag filter is updated."""

    def __init__(self, tag: Optional[str]) -> None:
        self.tag = tag
        super().__init__()


class TaskTable(Static):
    """Table view of tasks."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.table: DataTable = DataTable(zebra_stripes=True)

    def compose(self) -> ComposeResult:
        self.table.add_columns("Title", "Status", "Tags", "Due")
        yield self.table

    def update_rows(
        self,
        tasks: Iterable[Task],
        selected: Optional[str],
        tag_filter: Optional[str],
        status_labels: dict[str, str],
    ) -> None:
        self.table.clear()
        for task in tasks:
            if tag_filter and tag_filter not in task.tags:
                continue
            due = task.due.isoformat() if task.due else "—"
            tags = ", ".join(task.tags) if task.tags else "—"
            self.table.add_row(
                task.title,
                pretty_status(task.status, status_labels),
                tags,
                due,
                key=task.id,
            )
        if selected:
            try:
                self.table.focus()
                self.table.cursor_type = "row"
                row = self.table.get_row_index(selected)
                self.table.move_cursor(row=row)
            except Exception:
                pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.post_message(TaskSelected(str(event.row_key)))


class TaskCard(ListItem):
    """Compact card used in the kanban board."""

    def __init__(self, task: Task) -> None:
        subtitle_parts = []
        if task.tags:
            subtitle_parts.append(", ".join(task.tags))
        if task.due:
            subtitle_parts.append(f"Due {task.due.isoformat()}")
        subtitle = " • ".join(subtitle_parts) if subtitle_parts else "No tags or due date"
        body = Static(f"[b]{task.title}[/b]\n[dim]{subtitle}[/dim]", markup=True)
        super().__init__(body)
        self.task_id = task.id


class KanbanBoard(VerticalScroll):
    """Simple kanban board layout."""

    def __init__(self, columns: List[str], status_labels: dict[str, str]) -> None:
        super().__init__()
        self.columns = columns
        self.status_labels = status_labels
        self.column_views: list[ListView] = []
        self.headings: list[Label] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="board"):
            for column in self.columns:
                with Vertical(classes="board-column"):
                    heading = Label(
                        pretty_status(column, self.status_labels),
                        classes="board-heading",
                        id=f"heading-{column}",
                    )
                    self.headings.append(heading)
                    yield heading
                    list_view = ListView(id=f"column-{column}")
                    self.column_views.append(list_view)
                    yield list_view

    def refresh_board(
        self,
        tasks: Iterable[Task],
        selected: Optional[str],
        tag_filter: Optional[str],
        status_labels: dict[str, str],
    ) -> None:
        for list_view in self.column_views:
            list_view.clear()
        by_status: dict[str, list[Task]] = {column: [] for column in self.columns}
        for task in tasks:
            if task.status not in by_status:
                continue
            if tag_filter and tag_filter not in task.tags:
                continue
            by_status[task.status].append(task)
        for heading, list_view in zip(self.headings, self.column_views):
            if not list_view.id:
                continue
            column = list_view.id.replace("column-", "")
            for task in by_status.get(column, []):
                card = TaskCard(task)
                list_view.append(card)
                if selected and selected == task.id:
                    list_view.index = len(list_view) - 1
            heading.update(
                f"{pretty_status(column, self.status_labels)} ({len(by_status.get(column, []))})"
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, TaskCard):
            self.post_message(TaskSelected(item.task_id))


class CalendarView(Static):
    """Compact month calendar with due tasks."""

    def __init__(self) -> None:
        super().__init__()
        self.last_render: str = ""

    def update_calendar(
        self, tasks: Iterable[Task], reference: Optional[date] = None
    ) -> None:
        today = reference or date.today()
        cal = calendar.Calendar()
        month_matrix = cal.monthdayscalendar(today.year, today.month)
        tasks_by_day: dict[int, list[Task]] = {}
        for task in tasks:
            if task.due and task.due.month == today.month and task.due.year == today.year:
                tasks_by_day.setdefault(task.due.day, []).append(task)

        lines = [f"{today:%B %Y}".center(26), "Mo Tu We Th Fr Sa Su"]
        for week in month_matrix:
            week_cells = []
            for day in week:
                if day == 0:
                    week_cells.append("  ")
                else:
                    marker = "●" if day in tasks_by_day else " "
                    week_cells.append(f"{day:2d}{marker}")
            lines.append(" ".join(week_cells))

        lines.append("")
        lines.append("Due this month:")
        for day in sorted(tasks_by_day):
            for task in tasks_by_day[day]:
                tags = ", ".join(task.tags) if task.tags else "no tags"
                lines.append(f"{day:02d} {task.title} [{tags}]")

        calendar_text = "\n".join(lines)
        self.last_render = calendar_text
        self.update(calendar_text)


class DetailPanel(Static):
    """Shows task detail, checklist, and timer state."""

    def __init__(self) -> None:
        super().__init__()
        self.checklist_container = Vertical()
        self.meta_log = RichLog(
            highlight=False,
            markup=True,
            wrap=True,
            auto_scroll=False,
        )
        self.meta_log.border_title = "Details"

    def compose(self) -> ComposeResult:
        yield self.meta_log
        yield Label("Checklist", classes="section-heading")
        yield self.checklist_container

    def update_task(self, task: Optional[Task], status_labels: dict[str, str]) -> None:
        self.checklist_container.remove_children()
        if not task:
            self.meta_log.clear()
            self.meta_log.write("Select a task to see details.")
            return

        self.meta_log.clear()
        tags = ", ".join(task.tags) if task.tags else "No tags"
        due = task.due.isoformat() if task.due else "No due date"
        timer = f"{task.remaining_seconds // 60:02d}:{task.remaining_seconds % 60:02d}"
        status = pretty_status(task.status, status_labels)
        self.meta_log.write(f"[b]{task.title}[/b]")
        if task.description:
            self.meta_log.write(task.description)
        self.meta_log.write(f"Status: [bold]{status}[/bold]")
        self.meta_log.write(f"Tags: {tags}")
        self.meta_log.write(f"Due: {due}")
        timer_state = "running" if task.timer_running else "paused"
        self.meta_log.write(f"Countdown: {timer} ({timer_state})")

        for index, item in enumerate(task.checklist):
            checkbox = Checkbox(
                item.label,
                value=item.done,
                id=f"check-{task.id}-{index}",
            )
            self.checklist_container.mount(checkbox)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        # Bubble up with a message that carries the checkbox id.
        self.post_message(event)


class AddTaskModal(ModalScreen[Optional[Task]]):
    """Modal form for adding a task."""

    def __init__(self, presets: list[int], default_minutes: int) -> None:
        super().__init__()
        self.presets = presets
        self.default_minutes = default_minutes

    def compose(self) -> ComposeResult:
        presets_text = ", ".join(str(p) for p in self.presets) if self.presets else "—"
        countdown_placeholder = (
            f"Countdown minutes (default {self.default_minutes}, presets: {presets_text})"
        )
        yield Container(
            Label("New Task", classes="dialog-heading"),
            Input(placeholder="Title", id="title"),
            Input(placeholder="Description (optional)", id="description"),
            Input(placeholder="Tags (comma separated)", id="tags"),
            Input(placeholder="Due date (YYYY-MM-DD)", id="due"),
            Input(placeholder=countdown_placeholder, id="countdown"),
            Horizontal(
                *[
                    Button(f"{preset}m", id=f"preset-{preset}", variant="primary")
                    for preset in self.presets
                ],
                classes="preset-row",
            )
            if self.presets
            else Static(),
            Horizontal(
                Button("Save", id="save", variant="success"),
                Button("Cancel", id="cancel", variant="warning"),
                classes="dialog-actions",
            ),
            classes="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("preset-"):
            minutes_str = event.button.id.split("-")[1]
            if minutes_str.isdigit():
                self.query_one("#countdown", Input).value = minutes_str
            return
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        if event.button.id == "save":
            title = self.query_one("#title", Input).value.strip()
            if not title:
                return
            description = self.query_one("#description", Input).value.strip()
            tags_raw = self.query_one("#tags", Input).value
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            due_raw = self.query_one("#due", Input).value.strip()
            due = None
            if due_raw:
                try:
                    due = date.fromisoformat(due_raw)
                except ValueError:
                    pass
            countdown_raw = self.query_one("#countdown", Input).value.strip()
            countdown_seconds = self.default_minutes * 60
            if countdown_raw.isdigit() and int(countdown_raw) > 0:
                countdown_seconds = int(countdown_raw) * 60
            task = Task(
                id=str(uuid4()),
                title=title,
                description=description,
                tags=tags,
                due=due,
                status="backlog",
                countdown_seconds=countdown_seconds,
                remaining_seconds=countdown_seconds,
            )
            self.dismiss(task)


class TagFilterModal(ModalScreen[Optional[str]]):
    """Modal for choosing a tag filter."""

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Filter by tag (leave blank to clear)", classes="dialog-heading"),
            Input(placeholder="tag", id="tag-filter"),
            Horizontal(
                Button("Apply", id="apply", variant="success"),
                Button("Clear", id="clear"),
                Button("Cancel", id="cancel", variant="warning"),
            ),
            classes="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            tag = self.query_one("#tag-filter", Input).value.strip()
            self.dismiss(tag or None)
        elif event.button.id == "clear":
            self.dismiss(None)
        else:
            self.dismiss(None)


class TimerPresetModal(ModalScreen[Optional[int]]):
    """Modal for applying a timer preset to the selected task."""

    def __init__(self, presets: list[int], current_minutes: Optional[int]) -> None:
        super().__init__()
        self.presets = presets
        self.current_minutes = current_minutes

    def compose(self) -> ComposeResult:
        current_text = (
            f"Current countdown: {self.current_minutes}m" if self.current_minutes else ""
        )
        yield Container(
            Label("Set timer preset", classes="dialog-heading"),
            Label(current_text) if current_text else Static(),
            Input(placeholder="Minutes (e.g. 25)", id="minutes"),
            Horizontal(
                *[
                    Button(f"{preset}m", id=f"preset-{preset}", variant="primary")
                    for preset in self.presets
                ],
                classes="preset-row",
            )
            if self.presets
            else Static(),
            Horizontal(
                Button("Apply", id="apply", variant="success"),
                Button("Cancel", id="cancel", variant="warning"),
            ),
            classes="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("preset-"):
            minutes_str = button_id.split("-")[1]
            if minutes_str.isdigit() and int(minutes_str) > 0:
                self.dismiss(int(minutes_str))
            return
        if button_id == "apply":
            minutes_raw = self.query_one("#minutes", Input).value.strip()
            if minutes_raw.isdigit() and int(minutes_raw) > 0:
                self.dismiss(int(minutes_raw))
            else:
                self.dismiss(None)
        else:
            self.dismiss(None)


class HelpModal(ModalScreen[None]):
    """Modal showing available keybindings."""

    def __init__(self, bindings: list[Binding]) -> None:
        super().__init__()
        self._binding_list: list[Binding] = bindings

    def compose(self) -> ComposeResult:
        rows = [("Tab", "Switch views (List, Board, Calendar, Details)")]
        for binding in self._binding_list:
            if binding.show is False:
                continue
            key = binding.key or ""
            desc = binding.description or binding.action.replace("_", " ")
            rows.append((key, desc))
        body = "\n".join(f"{key:<8} {desc}" for key, desc in rows)
        yield Container(
            Label("Help / Keybindings", classes="dialog-heading"),
            Static(body, classes="dialog-body", markup=False),
            Horizontal(
                Button("Close", id="close", variant="primary"),
                classes="dialog-actions",
            ),
            classes="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss(None)


class TaskBoardApp(App):
    """Main task tracker app."""

    CSS = """
    Screen {
        overflow: hidden;
    }
    .board-column {
        width: 1fr;
        min-width: 26;
        border: solid $primary;
        padding: 1 1;
        margin: 0 1;
    }
    .board-heading {
        text-style: bold;
        padding: 0 0 1 0;
    }
    .dialog {
        width: 60%;
        max-width: 80;
        border: solid $accent;
        padding: 1;
        background: $panel;
    }
    .dialog-body {
        padding: 1 0 1 0;
    }
    .dialog-actions {
        width: 100%;
        padding-top: 1;
        content-align: center middle;
    }
    .dialog-heading {
        text-style: bold;
        padding-bottom: 1;
    }
    .section-heading {
        padding-top: 1;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("a", "add_task", "Add task"),
        Binding("s", "cycle_status", "Move status"),
        Binding("c", "mark_done", "Mark done"),
        Binding("t", "toggle_timer", "Start/Pause timer"),
        Binding("r", "reset_timer", "Reset timer"),
        Binding("p", "set_timer_preset", "Timer preset"),
        Binding("f", "filter_tag", "Filter tags"),
        Binding("d", "show_details", "Details tab"),
        Binding("?", "show_help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    TIMER_SAVE_INTERVAL = 5.0

    def __init__(self, config: AppConfig, tasks: List[Task]) -> None:
        self.config = config
        super().__init__()
        self.tasks: List[Task] = tasks
        self.tag_filter: Optional[str] = None
        self.selected_task_id: Optional[str] = tasks[0].id if tasks else None
        self.status_labels: dict[str, str] = {
            **DEFAULT_STATUS_LABELS,
            **(config.status_labels or {}),
        }
        self.timer_presets: list[int] = config.timer_presets
        self.default_timer_minutes: int = (
            config.default_timer_minutes if config.default_timer_minutes > 0 else 25
        )
        self.timer: Timer | None = None
        self._last_timer_save = monotonic()

    def get_css_variables(self) -> dict[str, str]:
        variables = super().get_css_variables()
        variables.update(
            {
                "background": self.config.theme.background,
                "foreground": self.config.theme.text,
                "primary": self.config.theme.primary,
                "accent": self.config.theme.accent,
                "panel": self.config.theme.muted,
                "scrollbar-background": self.config.theme.muted,
                "scrollbar-background-hover": self.config.theme.muted,
                "scrollbar-background-active": self.config.theme.muted,
            }
        )
        return variables

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(id="tabs", initial=self.config.default_view):
            with TabPane("List", id="list"):
                yield TaskTable(id="task-table")
            with TabPane("Board", id="board"):
                yield KanbanBoard(self.config.board_columns, self.status_labels)
            with TabPane("Calendar", id="calendar"):
                yield CalendarView()
            with TabPane("Details", id="details"):
                yield DetailPanel()
        yield Footer()

    def on_mount(self) -> None:
        # Apply appearance settings.
        self.styles.background = self.config.theme.background
        self.styles.color = self.config.theme.text
        self.refresh_views()
        self.timer = self.set_interval(1.0, self.tick_timers)

    def refresh_views(self) -> None:
        table = self.query_one("#task-table", TaskTable)
        board = self.query_one(KanbanBoard)
        calendar_view = self.query_one(CalendarView)
        detail = self.query_one(DetailPanel)

        table.update_rows(
            self.tasks, self.selected_task_id, self.tag_filter, self.status_labels
        )
        board.refresh_board(
            self.tasks, self.selected_task_id, self.tag_filter, self.status_labels
        )
        calendar_view.update_calendar(self.tasks)
        detail.update_task(self.get_selected_task(), self.status_labels)

    def get_selected_task(self) -> Optional[Task]:
        if not self.selected_task_id:
            return None
        for task in self.tasks:
            if task.id == self.selected_task_id:
                return task
        return None

    def handle_task_selected(self, task_id: str) -> None:
        self.selected_task_id = task_id
        self.refresh_views()

    def on_task_selected(self, event: TaskSelected) -> None:
        self.handle_task_selected(event.task_id)

    def action_add_task(self) -> None:
        self.push_screen(
            AddTaskModal(self.timer_presets, self.default_timer_minutes),
            self._add_task_callback,
        )

    def _add_task_callback(self, task: Optional[Task]) -> None:
        if task:
            self.tasks.append(task)
            self.selected_task_id = task.id
            save_tasks(self.tasks, data_path=self.config.data_path)
            self.refresh_views()

    def action_filter_tag(self) -> None:
        self.push_screen(TagFilterModal(), self._tag_filter_callback)

    def _tag_filter_callback(self, tag: Optional[str]) -> None:
        self.tag_filter = tag
        self.refresh_views()

    def action_cycle_status(self) -> None:
        task = self.get_selected_task()
        if not task:
            return
        columns = self.config.board_columns
        if not columns:
            return
        task.status = next_status(task.status, columns)
        save_tasks(self.tasks, data_path=self.config.data_path)
        self.refresh_views()

    def action_mark_done(self) -> None:
        task = self.get_selected_task()
        if not task or not self.config.board_columns:
            return
        task.status = self.config.board_columns[-1]
        save_tasks(self.tasks, data_path=self.config.data_path)
        self.refresh_views()

    def action_toggle_timer(self) -> None:
        task = self.get_selected_task()
        if not task:
            return
        task.timer_running = not task.timer_running
        save_tasks(self.tasks, data_path=self.config.data_path)
        self.refresh_views()

    def action_reset_timer(self) -> None:
        task = self.get_selected_task()
        if not task:
            return
        task.timer_running = False
        task.remaining_seconds = task.countdown_seconds
        save_tasks(self.tasks, data_path=self.config.data_path)
        self.refresh_views()

    def action_set_timer_preset(self) -> None:
        task = self.get_selected_task()
        if not task:
            return
        current_minutes = task.countdown_seconds // 60 if task.countdown_seconds else None
        self.push_screen(
            TimerPresetModal(self.timer_presets, current_minutes),
            self._preset_callback,
        )

    def _preset_callback(self, minutes: Optional[int]) -> None:
        task = self.get_selected_task()
        if not task or not minutes or minutes <= 0:
            return
        task.countdown_seconds = minutes * 60
        task.remaining_seconds = minutes * 60
        task.timer_running = False
        save_tasks(self.tasks, data_path=self.config.data_path)
        self.refresh_views()

    def action_show_details(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "details"

    def action_show_help(self) -> None:
        bindings = [b for b in self.BINDINGS if isinstance(b, Binding)]
        self.push_screen(HelpModal(bindings))

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        checkbox_id = event.checkbox.id or ""
        parts = checkbox_id.split("-")
        if len(parts) < 3:
            return
        task_id = parts[1]
        index = int(parts[2])
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task or index >= len(task.checklist):
            return
        task.checklist[index].done = event.value
        save_tasks(self.tasks, data_path=self.config.data_path)
        self.refresh_views()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, TaskCard):
            self.handle_task_selected(event.item.task_id)

    def tick_timers(self) -> None:
        changed = False
        hit_zero = False
        for task in self.tasks:
            if task.timer_running and task.remaining_seconds > 0:
                task.remaining_seconds -= 1
                changed = True
                if task.remaining_seconds <= 0:
                    task.timer_running = False
                    hit_zero = True
        if changed:
            now = monotonic()
            should_save = hit_zero or (now - self._last_timer_save) >= self.TIMER_SAVE_INTERVAL
            if should_save:
                save_tasks(self.tasks, data_path=self.config.data_path)
                self._last_timer_save = now
            self.refresh_views()
