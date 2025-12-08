## Cognee Community Tasks

This directory features custom community tasks, where anyone can define new tasks if they wish.
Please check our [main repository](https://github.com/topoteretes/cognee) before adding new tasks,
make sure that no task can do what this new one is supposed to do.

## Instructions

Tasks should be **grouped** in a meaningful way, such as the codify example, where all tasks related
to the codify pipeline are grouped in a package. When adding new tasks, one should follow these steps:

1) In the `task` directory, create a new directory with the name of the new task group
    (such as `codify_tasks`), and inside it, add the directory (which will be the package
    for this group of tasks), such as `cognee_community_tasks_codify`.
2) Add a `pyproject.toml` file, with all the necessary dependencies defined.
3) Add at least one example and/or test, if necessary, to make sure the tasks works as intended.