## Cognee Community Pipelines

This directory features custom community pipelines, where anyone can define new, custom pipelines.
Here is where most of the pipelines available in cognee should go, except a few main ones which are on our
[main repository](https://github.com/topoteretes/cognee).

## Instructions

Detailed information about creating custom tasks and pipelines can be found on our [docs](https://docs.cognee.ai/guides/custom-tasks-pipelines) page.
There we explain how to define tasks and pipelines, how to run them successfully, and we break down
what happens in a pipeline run.

When adding a new pipeline to this repo, one should follow these steps:

1) In the `pipeline` directory, create a new directory with the name of the new pipeline
    (such as `codify_pipeline`), and inside it, add the directory (which will be the package
    for the pipeline), named `cognee_community_pipeline_<your_pipeline_name>`, e.g. `cognee_community_pipeline_codify`.
2) Add a `pyproject.toml` file, with all the necessary dependencies defined.
3) Add at least one example and/or test, to make sure the pipeline works as intended.