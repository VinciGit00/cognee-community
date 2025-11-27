import asyncio
import os

import cognee
from cognee import SearchType
from cognee_community_pipelines.code_graph_pipeline import run_code_graph_pipeline
from cognee_community_retrievers.code_retriever import CodeRetriever, CodeSearchType
from cognee_community_retrievers.register import register


async def main():
    # Disable permissions feature for this example
    os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
    repo_path = "/Users/milicevi/cognee_project/cognee"
    include_docs = False

    register(SearchType[CodeSearchType.name], CodeRetriever)

    run_status = False
    async for run_status in run_code_graph_pipeline(repo_path=repo_path, include_docs=include_docs):
        run_status = run_status

    # Test CODE search
    search_results = await cognee.search(
        query_type=SearchType[CodeSearchType.name],
        query_text="Find dependencies and relationships between components",
    )
    assert len(search_results) != 0, "The search results list is empty."
    print("\n\nSearch results are:\n")
    for result in search_results:
        print(f"{result}\n")

    return run_status


if __name__ == "__main__":
    asyncio.run(main())
