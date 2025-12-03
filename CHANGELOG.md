# Changelog

## v0.1.1 — 2025-02-19
**Fixes**
- Adjust Textual CSS to use valid border syntax (fixes startup error after pipx install).
- Set CSS variables via stylesheet API for compatibility with Textual 6.x.

## v0.1.0 — 2024-12-XX
**Highlights**
- First tagged release of Tasktui (Textual-based TUI) with list, kanban board, calendar, and detail tabs.
- Task features: tags, checklists, due dates, and per-task countdown timers with presets and auto-pause.
- Configurable via `~/.tasktui/config.toml` (or `TASKTUI_HOME`); legacy `.over-ssh` supported for migration.
- Storage resilience: corrupt JSON is backed up and auto-regenerated; default sample tasks included.
- Timer persistence debounced to reduce disk churn; in-app help overlay on `?`.
- Tooling: console script `tasktui`, CI (ruff/mypy/pytest), dev extras, and pre-commit hooks.

**Install**
- `pipx install git+https://github.com/Thatkidtk/Tasktui.git@v0.1.0`
- `pip install git+https://github.com/Thatkidtk/Tasktui.git@v0.1.0` (venv)
- `python -m tasktui` or `tasktui`
