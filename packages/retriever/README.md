## Cognee Community Retrievers

This directory features custom community retrievers, where anyone can define new retrievers if they wish.
Please check our [main repository](https://github.com/topoteretes/cognee) before adding new retrievers,
make sure that no retriever can do what this new one is supposed to do.

## Instructions

When adding a new retriever, one should follow these steps:

1) In the `retriever` directory, create a new directory with the name of the new retriever
    (such as `code_retriever`), and inside it, add the directory (which will be the package
    for the retriever), such as `cognee_community_retriever_code`.
2) Add a `pyproject.toml` file, with all the necessary dependencies defined.
3) Add at least one example and/or test, if necessary, to make sure the retriever works as intended.