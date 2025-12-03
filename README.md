# Tasktui

Textual-based TUI with list, kanban, calendar, and detail views plus tags, checklists, due dates, and per-task countdown timers. Python 3.11+.

## Features
- List, kanban, calendar, and detail tabs with quick switching via `Tab`
- Tags, checklists, due dates, and configurable status columns/labels
- Countdown timers with presets and auto-pause at zero (state is saved every few seconds)
- Themeable colors and layout defaults via a small `config.toml`
- Safe storage: JSON backed up on corruption; override data dir with `TASKTUI_HOME`

## Install
```bash
pipx install git+https://github.com/Thatkidtk/Tasktui.git@v0.1.4  # tagged release
# or the latest main branch
pipx install git+https://github.com/Thatkidtk/Tasktui.git
# or with uv
uv tool install .
# or editable dev install
pip install -e ".[dev]"
```

## Run
```bash
tasktui
# or
python -m tasktui
# or
python main.py
```

## Controls
- `Tab` switch views (List, Board, Calendar, Details)
- `a` add a new task
- `s` move the selected task to the next column
- `c` mark the selected task as done (last column)
- `p` apply a timer preset
- `t` start/pause the timer
- `r` reset the timer to its default countdown
- `f` filter by tag (blank to clear)
- `d` jump to Details
- `?` open the in-app help overlay
- `q` quit

Checklist items are toggled directly in the Details tab.

## Config and data
The app writes to `~/.tasktui/` on first run:
- `config.toml` — appearance and layout defaults
- `tasks.json` — your data store

Set `TASKTUI_HOME=/tmp/tasktui-demo` (or any path) to isolate config/data for demos or tests. The old `OVER_SSH_HOME` still works as a legacy fallback.

Example defaults:
```toml
[app]
default_view = "board"          # list, board, calendar, or details
data_path = "/home/you/.tasktui/tasks.json"
board_columns = ["backlog", "in_progress", "done"]
status_labels = {backlog = "Backlog", in_progress = "In Progress", done = "Done"}
timer_presets = [5, 15, 25, 50]  # minutes
default_timer_minutes = 25

[appearance]
theme = "midnight"
background = "#0d1117"
primary = "#58a6ff"
accent = "#ff7b72"
muted = "#30363d"
text = "#c9d1d9"
```

Adjust colors, default view, and board columns to match your workflow.

## Development
```bash
pip install -e ".[dev]"
pre-commit install
pytest
```
