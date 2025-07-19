#!/usr/bin/env python3
"""
Example script demonstrating how to use Cognee with Milvus community adapter

This example shows:
1. How to install and use the Milvus community adapter
2. Configures Cognee to use Milvus as vector database
3. Adds data and performs cognification
4. Searches for insights and chunks
5. Cleans up data

Prerequisites:
- Install Milvus adapter: pip install ./community/adapters/vector/milvus/
- Or install dependencies: pip install pymilvus milvus-lite (Linux/Mac only)
- Set LLM_API_KEY environment variable
- Set EMBEDDING_API_KEY environment variable (if using external embeddings)

Usage:
    python community/examples/milvus_example.py
"""

import os
import sys
import asyncio

# Add the cognee directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import cognee
from cognee.modules.search.SearchType import SearchType
from community.adapters.vector.milvus import MilvusAdapter


async def main():
    # Set up paths for this example
    cognee_directory_path = os.path.join(os.path.dirname(__file__), ".cognee_system", "milvus_example")
    data_directory_path = os.path.join(os.path.dirname(__file__), ".data_storage", "milvus_example")

    # Configure Cognee system directories
    cognee.config.system_root_directory(cognee_directory_path)
    cognee.config.data_root_directory(data_directory_path)

    # Set up Milvus database path
    local_milvus_db_path = os.path.join(cognee_directory_path, "databases", "milvus.db")

    # Register the Milvus community adapter
    cognee.use_vector_adapter("milvus", MilvusAdapter)

    # Configure Milvus as the vector database provider
    cognee.config.vector_db_provider("milvus")
    cognee.config.vector_db_url(local_milvus_db_path)  # Enter Milvus Endpoint if exist
    cognee.config.vector_db_key("")  # Enter Milvus API Key if exist

    # Set dataset name
    dataset_name = "milvus_example"

    print("🚀 Starting Milvus Community Adapter Example")
    print("=" * 50)

    # Sample text about Milvus
    sample_text = """Milvus is an open-source vector database built to power AI applications.
    It provides high-performance similarity search and supports various index types.
    Milvus implements efficient approximate nearest neighbor search algorithms.
    The database supports hybrid searches combining vector similarity with scalar filtering.
    Milvus supports horizontal scaling and can handle billions of vectors."""

    print(f"📝 Adding sample text to dataset: {dataset_name}")
    await cognee.add(sample_text, dataset_name)

    print("🧠 Starting cognification process...")
    await cognee.cognify([dataset_name])

    print("\n🔍 Performing searches...")
    print("-" * 30)

    # 1. Search for insights related to "Milvus"
    insights_results = await cognee.search(query_type=SearchType.INSIGHTS, query_text="Milvus")
    print("\nInsights about Milvus:")
    for i, result in enumerate(insights_results, 1):
        print(f"{i}. {result}")

    # 2. Search for chunks related to "vector database"
    chunks_results = await cognee.search(query_type=SearchType.CHUNKS, query_text="vector database")
    print(f"\nChunks about 'vector database' (found {len(chunks_results)} results):")
    for i, result in enumerate(chunks_results, 1):
        print(f"{i}. {result}")

    # 3. Search for summaries related to "AI applications"
    summaries_results = await cognee.search(query_type=SearchType.SUMMARIES, query_text="AI applications")
    print(f"\nSummaries about 'AI applications' (found {len(summaries_results)} results):")
    for i, result in enumerate(summaries_results, 1):
        print(f"{i}. {result}")

    print("\n📊 Getting search history...")
    search_history = await cognee.get_search_history()
    print(f"Total searches performed: {len(search_history)}")
    for i, search in enumerate(search_history, 1):
        print(f"{i}. Query: '{search.query_text}' | Type: {search.search_type}")

    print("\n🧹 Cleaning up data...")
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)

    print("\n✅ Milvus community adapter example completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main()) 