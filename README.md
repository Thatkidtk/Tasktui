## Terminal task tracker

Textual-based TUI with list, kanban, calendar, and detail views, tags, checklists, and per-task countdown timers. A small config file lets you pick themes and defaults after install.

### Quick start

```bash
pip install -e .
python main.py
```

The app writes two files to `~/.over-ssh/` the first time it runs:
- `config.toml` — appearance and layout defaults you can tweak.
- `tasks.json` — your data store. Edit by hand or through the TUI.

### Controls

- `Tab` switch between views (List, Board, Calendar, Details)
- `a` add a new task
- `s` move the selected task to the next column
- `c` mark selected task as the last column (done)
- `p` apply a timer preset to the selected task
- `t` start/pause the task timer
- `r` reset the task timer to its default countdown
- `f` filter by tag (blank to clear)
- `d` jump to the Details tab
- `q` quit

Checklist items are toggled directly in the Details tab.

### Configuration

`~/.over-ssh/config.toml` is created with sensible defaults:

```toml
[app]
default_view = "board"          # list, board, calendar, or details
data_path = "/home/you/.over-ssh/tasks.json"
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

Adjust colors, default view, and board columns to match your style.
Add more board columns and labels for a custom workflow, and tweak timer presets to fit your cadence (e.g., `[10, 30, 90]`).

Tip: set `OVER_SSH_HOME=/tmp/over-ssh-demo` (or any path) to isolate config/data for experiments or tests.

### Views

- **List**: sortable table with tags and due dates.
- **Board**: kanban-style columns driven by `board_columns`.
- **Calendar**: monthly grid highlighting due tasks.
- **Details**: task summary, tags, checklist toggles, and countdown timer state.

Timers tick once per second; when a countdown hits zero, it pauses automatically. Every change saves back to `tasks.json`.
# Tasktui
