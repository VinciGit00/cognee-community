import asyncio

import cognee
from cognee import SearchType
from cognee_community_pipelines.custom_pipelines.code_graph_pipeline import CodeGraphPipeline


async def main():
    repo_path = "/path/to/repo"
    include_docs = False

    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)

    code_graph_pipeline = CodeGraphPipeline(
        repo_path=repo_path,
        include_docs=include_docs,
    )

    run_status = False
    async for run_status in code_graph_pipeline.run_pipeline():
        run_status = run_status

    # Test CODE search
    search_results = await cognee.search(
        query_type=SearchType.CODE,
        query_text="Find dependencies and relationships between components",
    )
    assert len(search_results) != 0, "The search results list is empty."
    print("\n\nSearch results are:\n")
    for result in search_results:
        print(f"{result}\n")

    return run_status


if __name__ == "__main__":
    asyncio.run(main())
