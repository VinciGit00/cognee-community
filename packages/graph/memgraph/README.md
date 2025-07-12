# Cognee Community Graph Adapter - Memgraph

This package provides a Memgraph graph database adapter for the Cognee framework.

## Installation

```bash
pip install cognee-community-graph-adapter-memgraph
```

## Usage

```python
import cognee
from cognee_community_graph_adapter_memgraph import register

# Register the Memgraph adapter
register()

# Configure cognee to use Memgraph
cognee.config.set_graph_database_provider("memgraph")

# Set up your Memgraph connection
cognee.config.set_graph_database_url("bolt://localhost:7687")
cognee.config.set_graph_database_username("your_username")
cognee.config.set_graph_database_password("your_password")

# Now you can use cognee with Memgraph
await cognee.add(["your_data"])
await cognee.cognify()
```

## Requirements

- Python >= 3.9
- Memgraph database instance
- neo4j driver (for Bolt protocol support)

## Configuration

The adapter requires the following configuration:

- `GRAPH_DATABASE_URL`: The Memgraph database URL (e.g., `bolt://localhost:7687`)
- `GRAPH_DATABASE_USERNAME`: Username for authentication
- `GRAPH_DATABASE_PASSWORD`: Password for authentication

## Features

- Full support for Memgraph's property graph model
- Optimized queries for graph operations
- Async/await support
- Transaction support
- Comprehensive error handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. 