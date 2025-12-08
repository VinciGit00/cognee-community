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
3) As you can see in the `code_retriever`, one must also define a new `SearchType` to go along
    with the new retriever. The way this is done now (as of December 8th 2025), is that one should
    add new values to the `SearchType` Enum imported from Cognee. More specifically, this is the part
    of the code responsible:
```python
from aenum import extend_enum
# We define the search type as a class here to avoid hardcoding it in
# other modules and files. This will also help in reducing warnings from the compiler.
class CodeSearchType:
    name = "CODE"
    value = "CODE"


extend_enum(SearchType, CodeSearchType.name, CodeSearchType.value)
```
After defining the retriever and the search type, you must also create a `register.py` file, which calls the
registration function. This enables cognee to use the new retriever. How one should do this can be found in the
`register.py` file of the `cognee_community_retriever_code` package.
An example of how to use this register function can be seen in the `codify_example.py` in the `pipeline/codify_pipeline` 
directory. It is enough to simply do something like this before using the retriever and search type:
```python
from cognee_community_retriever_code import register  # noqa: F401
```
4) Add at least one example and/or test, if necessary, to make sure the retriever works as intended.