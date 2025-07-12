"""Example usage of the Memgraph community adapter for Cognee."""

import asyncio
import os
import cognee
from cognee_community_graph_adapter_memgraph import register


async def main():
    # Register the Memgraph community adapter
    register()
    
    # Configure cognee to use Memgraph
    cognee.config.set_graph_database_provider("memgraph")
    
    # Set up your Memgraph connection
    # Make sure you have Memgraph running on localhost:7687
    cognee.config.set_graph_database_url("bolt://localhost:7687")
    cognee.config.set_graph_database_username("memgraph")
    cognee.config.set_graph_database_password("memgraph")
    
    # Optional: Set custom data and system directories
    cognee.config.data_root_directory("./data")
    cognee.config.system_root_directory("./system")
    
    # Sample data to add to the knowledge graph
    sample_data = [
        "Artificial intelligence is a branch of computer science that aims to create intelligent machines.",
        "Machine learning is a subset of AI that focuses on algorithms that can learn from data.",
        "Deep learning is a subset of machine learning that uses neural networks with many layers.",
        "Natural language processing enables computers to understand and process human language.",
        "Computer vision allows machines to interpret and make decisions based on visual information."
    ]
    
    try:
        print("Adding data to Cognee...")
        await cognee.add(sample_data, "ai_knowledge")
        
        print("Processing data with Cognee...")
        await cognee.cognify(["ai_knowledge"])
        
        print("Searching for insights...")
        search_results = await cognee.search(
            query_type=cognee.SearchType.INSIGHTS,
            query_text="artificial intelligence"
        )
        
        print(f"Found {len(search_results)} insights:")
        for i, result in enumerate(search_results, 1):
            print(f"{i}. {result}")
            
        print("\nSearching for chunks...")
        chunk_results = await cognee.search(
            query_type=cognee.SearchType.CHUNKS,
            query_text="machine learning"
        )
        
        print(f"Found {len(chunk_results)} chunks:")
        for i, result in enumerate(chunk_results, 1):
            print(f"{i}. {result}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Memgraph is running and accessible at bolt://localhost:7687")


if __name__ == "__main__":
    asyncio.run(main()) 