import os

from project_stories import check_project_stories, list_resources


def run_scheduled_task():
    task = os.getenv("SCHEDULED_TASK", "project_stories")
    print(f'RUN TASK: {task.upper()}')

    if task == "project_stories":
        check_project_stories()

    elif task == "list_resources":
        list_resources()

    else:
        print(f'UNKNOWN TASK {task}')


if __name__ == "__main__":
    run_scheduled_task()
