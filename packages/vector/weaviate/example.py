import os
import sys
import asyncio
import pathlib

######### Needed only for this example, not to be used in production code.
packages_module_path = os.path.join(pathlib.Path(__file__).parent.parent.parent.parent)
sys.path.append(packages_module_path)
#########

# NOTE: Importing the register module we let cognee know it can use the Weaviate vector adapter
import packages.vector.weaviate.cognee_community_vector_adapter_weaviate.register

async def main():
    from cognee import config, prune, add, cognify, search, SearchType

    system_path = pathlib.Path(__file__).parent
    config.system_root_directory(os.path.join(system_path, ".cognee-system"))
    config.data_root_directory(os.path.join(system_path, ".cognee-data"))

    config.set_relational_db_config({
        "db_provider": "sqlite",
    })
    config.set_vector_db_config({
        "vector_db_provider": "weaviate",
        "vector_db_url": os.getenv("VECTOR_DB_URL"),
        "vector_db_key": os.getenv("VECTOR_DB_KEY"),
    })
    config.set_graph_db_config({
        "graph_database_provider": "networkx",
    })

    await prune.prune_data()
    await prune.prune_system()

    text = """
    Weaviate is an open-source vector database that stores both objects and vectors.
    It allows for combining vector search with structured filtering.
    Weaviate can be deployed in the cloud, on-premise, or embedded in your application.
    """

    await add(text)

    await cognify()

    query_text = "Tell me about Weaviate vector database"

    search_results = await search(query_type=SearchType.GRAPH_COMPLETION, query_text=query_text)

    for result_text in search_results:
        print(result_text)


if __name__ == "__main__":
    asyncio.run(main()) 