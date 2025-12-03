from tasktui.app import TaskBoardApp
from tasktui.config import load_config
from tasktui.storage import load_tasks


def main() -> None:
    config = load_config()
    tasks = load_tasks(config.data_path)
    app = TaskBoardApp(config, tasks)
    app.run()


if __name__ == "__main__":
    main()
