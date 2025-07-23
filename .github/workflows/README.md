# Cognee Community Workflows

This directory contains GitHub Actions workflows for testing community database adapters.

## Workflow Files

### Main Orchestration
- `community_test_suite.yml` - Main workflow that runs all community tests
- `vector_db_community_tests.yml` - Reusable workflow for vector database tests
- `graph_db_community_tests.yml` - Reusable workflow for graph database tests

### Individual Database Tests  
- `test_weaviate.yml` - Weaviate vector database adapter
- `test_qdrant.yml` - Qdrant vector database adapter
- `test_opensearch.yml` - OpenSearch vector database adapter
- `test_redis.yml` - Redis vector database adapter
- `test_milvus.yml` - Milvus vector database adapter
- `test_networkx.yml` - NetworkX graph database adapter
- `test_memgraph.yml` - Memgraph graph database adapter

## Usage

### Running All Tests
Tests run automatically on push/PR to `main` or `dev` branches.

To manually trigger all tests:
1. Go to Actions tab in GitHub
2. Select "Community Test Suite"
3. Click "Run workflow"
4. Choose options (databases: "all", python-version: "3.11.x")

### Running Individual Database Tests
Individual tests trigger automatically when files in the relevant package directory change.

To manually trigger a specific database test:
1. Go to Actions tab in GitHub
2. Select the specific test workflow (e.g., "Test Weaviate Community Adapter")
3. Click "Run workflow"

## Requirements

See `README_CI_CD.md` for detailed setup requirements, secrets configuration, and troubleshooting information. 