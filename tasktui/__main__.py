from .app import TaskBoardApp
from .config import load_config
from .storage import load_tasks


def main() -> None:
    """Entry point for the tasktui console script."""
    config = load_config()
    tasks = load_tasks(config.data_path)
    TaskBoardApp(config, tasks).run()


if __name__ == "__main__":
    main()
