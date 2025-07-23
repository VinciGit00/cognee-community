# Cognee Community Weaviate Vector Adapter

This is a community-maintained adapter that enables Cognee to work with Weaviate as a vector database.

## Installation

```bash
pip install cognee-community-vector-adapter-weaviate
```

## Usage

```python
import asyncio
from cognee import config, add, cognify, search, SearchType

# Import the register module to enable Weaviate support
import cognee_community_vector_adapter_weaviate.register

async def main():
    # Configure Weaviate
    config.set_vector_db_config({
        "vector_db_provider": "weaviate",
        "vector_db_url": "https://your-weaviate-instance.weaviate.network",
        "vector_db_key": "your-api-key"
    })
    
    # Use cognee as normal
    text = "Your text content here"
    await add(text)
    await cognify()
    
    search_results = await search(
        query_type=SearchType.GRAPH_COMPLETION,
        query_text="Your search query"
    )
    
    for result in search_results:
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The Weaviate adapter requires the following configuration parameters:

- `vector_db_url`: Your Weaviate cluster endpoint URL
- `vector_db_key`: Your Weaviate API key
- `vector_db_provider`: Set to "weaviate"

## Requirements

- Python >= 3.11
- weaviate-client >= 4.9.6, < 5.0.0
- cognee >= 0.1.41

## Features

- Full vector search capabilities
- Batch operations support
- Async/await support
- Retry logic for better reliability
- Collection management
- Data point indexing and retrieval 