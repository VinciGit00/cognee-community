## Cognee Community Tasks

This directory features custom community tasks, where anyone can define new, custom tasks.
Please check our [main repository](https://github.com/topoteretes/cognee) before adding new tasks, and make sure that the functionality
you want to implement isn't already present in an existing task.

## Instructions

Detailed information about creating custom tasks and pipelines can be found on our [docs](https://docs.cognee.ai/guides/custom-tasks-pipelines) page.
There we explain how to define tasks and pipelines, how to run them successfully, and we break down
what happens in a pipeline run.

Tasks should be **grouped** so that mutually relevant tasks are in one package. Take the codify pipeline as an example,
where all tasks related to that pipeline are grouped in a package. When adding new tasks, one should follow these steps:

1) In the `task` directory, create a new directory with the name of the new task group
    (such as `codify_tasks`), and inside it, add the directory (which will be the package
    for this group of tasks), named `cognee_community_tasks_<your_task_group_name>`, e.g. `cognee_community_tasks_codify`.
2) Add a `pyproject.toml` file, with all the necessary dependencies defined.
3) Add at least one example and/or test, if necessary, to make sure the tasks works as intended.