from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
import textwrap
import tomllib


def _config_dir() -> Path:
    env_dir = os.environ.get("TASKTUI_HOME") or os.environ.get("OVER_SSH_HOME")
    if env_dir:
        return Path(env_dir).expanduser()
    new_default = Path.home() / ".tasktui"
    legacy_default = Path.home() / ".over-ssh"
    # Prefer the new location, but if a legacy directory exists and the new one
    # does not, keep using the legacy path for backward compatibility.
    if not new_default.exists() and legacy_default.exists():
        return legacy_default
    return new_default


CONFIG_DIR = _config_dir()
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.toml"
DEFAULT_TASK_PATH = CONFIG_DIR / "tasks.json"


@dataclass
class ThemeConfig:
    name: str = "midnight"
    background: str = "#0d1117"
    primary: str = "#58a6ff"
    accent: str = "#ff7b72"
    muted: str = "#30363d"
    text: str = "#c9d1d9"


@dataclass
class AppConfig:
    data_path: Path = DEFAULT_TASK_PATH
    default_view: str = "board"
    board_columns: list[str] = field(
        default_factory=lambda: ["backlog", "in_progress", "done"]
    )
    status_labels: dict[str, str] = field(
        default_factory=lambda: {
            "backlog": "Backlog",
            "in_progress": "In Progress",
            "done": "Done",
        }
    )
    timer_presets: list[int] = field(default_factory=lambda: [5, 15, 25, 50])
    default_timer_minutes: int = 25
    theme: ThemeConfig = field(default_factory=ThemeConfig)


def ensure_config_file(path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Create a starter config file if one does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    starter = textwrap.dedent(
        f"""
        # Tasktui configuration
        [app]
        default_view = "board"  # options: board, list, calendar, details
        data_path = "{DEFAULT_TASK_PATH.as_posix()}"
        board_columns = ["backlog", "in_progress", "done"]
        status_labels = {{backlog = "Backlog", in_progress = "In Progress", done = "Done"}}
        timer_presets = [5, 15, 25, 50]  # minutes
        default_timer_minutes = 25

        [appearance]
        theme = "midnight"
        background = "#0d1117"
        primary = "#58a6ff"
        accent = "#ff7b72"
        muted = "#30363d"
        text = "#c9d1d9"
        """
    ).strip()
    path.write_text(starter + "\n", encoding="utf-8")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load configuration and apply defaults."""
    ensure_config_file(path)
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    app_cfg = data.get("app", {})
    appearance_cfg = data.get("appearance", {})

    config = AppConfig()

    data_path_value = app_cfg.get("data_path")
    if isinstance(data_path_value, str):
        config.data_path = Path(data_path_value).expanduser()

    view = app_cfg.get("default_view")
    if isinstance(view, str):
        config.default_view = view

    columns = app_cfg.get("board_columns")
    if isinstance(columns, list) and all(isinstance(c, str) for c in columns):
        config.board_columns = columns

    status_labels = app_cfg.get("status_labels")
    if isinstance(status_labels, dict):
        filtered = {
            str(key): str(value)
            for key, value in status_labels.items()
            if isinstance(key, str) and isinstance(value, str)
        }
        if filtered:
            config.status_labels = filtered

    timer_presets = app_cfg.get("timer_presets")
    if isinstance(timer_presets, list):
        parsed_presets: list[int] = []
        for item in timer_presets:
            try:
                parsed = int(item)
            except (TypeError, ValueError):
                continue
            if parsed > 0:
                parsed_presets.append(parsed)
        if parsed_presets:
            config.timer_presets = parsed_presets

    default_timer_minutes = app_cfg.get("default_timer_minutes")
    if isinstance(default_timer_minutes, int) and default_timer_minutes > 0:
        config.default_timer_minutes = default_timer_minutes

    theme = ThemeConfig()
    if isinstance(appearance_cfg.get("background"), str):
        theme.background = appearance_cfg["background"]
    if isinstance(appearance_cfg.get("primary"), str):
        theme.primary = appearance_cfg["primary"]
    if isinstance(appearance_cfg.get("accent"), str):
        theme.accent = appearance_cfg["accent"]
    if isinstance(appearance_cfg.get("muted"), str):
        theme.muted = appearance_cfg["muted"]
    if isinstance(appearance_cfg.get("text"), str):
        theme.text = appearance_cfg["text"]
    theme_name = appearance_cfg.get("theme")
    if isinstance(theme_name, str):
        theme.name = theme_name

    config.theme = theme
    return config
