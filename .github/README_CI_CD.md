# Cognee Community CI/CD Setup

This document explains the Continuous Integration and Continuous Deployment (CI/CD) setup for the Cognee Community repository, which hosts community-maintained database adapters and plugins.

## Overview

The CI/CD system is designed to automatically test all community database adapters whenever changes are made. It uses GitHub Actions workflows to ensure that each database adapter works correctly with the core Cognee framework.

## Workflow Structure

### Main Workflows

#### 1. Community Test Suite (`community_test_suite.yml`)
- **Trigger**: Push to `main`/`dev` branches, Pull Requests, Manual dispatch
- **Purpose**: Orchestrates all community database tests
- **Components**:
  - Runs vector database tests
  - Runs graph database tests  
  - Provides a consolidated test summary

#### 2. Vector Database Tests (`vector_db_community_tests.yml`)
- **Purpose**: Tests all vector database community adapters
- **Supported Databases**:
  - Weaviate
  - Qdrant  
  - OpenSearch
  - Redis
  - Milvus
  - Azure AI Search

#### 3. Graph Database Tests (`graph_db_community_tests.yml`)
- **Purpose**: Tests all graph database community adapters
- **Supported Databases**:
  - NetworkX
  - Memgraph

### Individual Database Workflows  

Each database adapter has its own dedicated workflow:
- `test_weaviate.yml` - Tests Weaviate adapter
- `test_qdrant.yml` - Tests Qdrant adapter
- `test_opensearch.yml` - Tests OpenSearch adapter (already exists)
- `test_redis.yml` - Tests Redis adapter
- `test_milvus.yml` - Tests Milvus adapter
- `test_networkx.yml` - Tests NetworkX adapter
- `test_memgraph.yml` - Tests Memgraph adapter

**Individual Workflow Features**:
- Trigger on changes to specific package paths
- Run only when relevant code changes
- Include necessary service containers (Redis, Memgraph, etc.)

## Setup Action

### Community Setup Action (`community_setup`)
Located at `.github/actions/community_setup/action.yml`

**Purpose**: Standardized setup for community package testing
**Features**:
- Sets up Python environment
- Installs Poetry
- Installs package dependencies
- Verifies Cognee imports work correctly

**Usage**:
```yaml
- name: Community Setup
  uses: ./.github/actions/community_setup
  with:
    python-version: '3.11.x'
    package-path: packages/vector/qdrant
```

## Environment Variables & Secrets

### Required Secrets
All workflows require these secrets for LLM and embedding functionality:
- `LLM_MODEL` - Language model identifier
- `LLM_ENDPOINT` - LLM API endpoint
- `LLM_API_KEY` - LLM API key
- `LLM_API_VERSION` - LLM API version
- `EMBEDDING_MODEL` - Embedding model identifier  
- `EMBEDDING_ENDPOINT` - Embedding API endpoint
- `EMBEDDING_API_KEY` - Embedding API key
- `EMBEDDING_API_VERSION` - Embedding API version

### Database-Specific Secrets
- `QDRANT_API_URL` & `QDRANT_API_KEY` - For Qdrant cloud instances
- `WEAVIATE_API_URL` & `WEAVIATE_API_KEY` - For Weaviate cloud instances

### Local Services
Some databases run as Docker services in the workflows:
- **Redis**: `redis/redis-stack-server:7.4.0-v1`
- **OpenSearch**: `opensearchproject/opensearch:2.17.1`
- **Memgraph**: `memgraph/memgraph:2.20.1`
- **Milvus**: `milvusdb/milvus:v2.4.15`

## Workflow Triggers

### Automatic Triggers
1. **Push Events**: When code is pushed to `main` or `dev` branches
2. **Pull Request Events**: When PRs are opened against `main` or `dev`
3. **Path-Based Triggers**: Individual workflows trigger only on relevant path changes

### Manual Triggers  
All workflows support `workflow_dispatch` for manual execution with optional parameters:
- `databases`: Specify which databases to test (comma-separated or "all")
- `python-version`: Specify Python version (default: "3.11.x")

## Test Execution

### Test Flow
1. **Checkout**: Get the latest code
2. **Setup**: Install Python, Poetry, and dependencies
3. **Service Start**: Start required database services (if applicable)
4. **Wait**: Wait for services to be ready
5. **Test**: Run the package example/test scripts
6. **Report**: Report success/failure

### Test Scripts
Each package should have:
- `example.py` - Demonstrates basic functionality
- Optional: `tests/` directory with more comprehensive tests
- Optional: `examples/` directory with additional examples

### Working Directory
Tests run from the specific package directory:
```yaml
working-directory: ./packages/vector/qdrant
run: poetry run python example.py
```

## Concurrency Control

All workflows use concurrency groups to:
- Cancel running workflows when new commits are pushed
- Prevent resource conflicts
- Optimize CI/CD resource usage

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

## Adding New Database Adapters

To add a new database adapter to the CI/CD system:

1. **Create Package Structure**:
   ```
   packages/vector/newdb/
   ├── pyproject.toml
   ├── README.md
   ├── example.py
   └── newdb_adapter/
       ├── __init__.py
       ├── adapter.py
       └── register.py
   ```

2. **Add to Main Workflows**:
   - Add a new job in `vector_db_community_tests.yml` or `graph_db_community_tests.yml`
   - Include necessary environment variables and services

3. **Create Individual Workflow**:
   - Copy an existing workflow (e.g., `test_qdrant.yml`)
   - Update database-specific configuration
   - Set appropriate path triggers

4. **Test Configuration**:
   - Ensure `example.py` works with required environment variables
   - Add any necessary Docker services
   - Test locally before committing

## Monitoring and Debugging

### Workflow Status
- View workflow runs in the "Actions" tab of the GitHub repository
- Each workflow shows individual job status and logs
- The summary job provides an overview of all test results

### Common Issues
1. **Service Startup**: Database services may need time to start
2. **Dependencies**: Ensure all required packages are in `pyproject.toml`
3. **Environment Variables**: Verify all required secrets are configured
4. **Path Triggers**: Individual workflows only run on relevant path changes

### Debugging Tips
- Use `workflow_dispatch` to run tests manually
- Check individual job logs for detailed error messages
- Verify service health checks are working
- Ensure working directory paths are correct

## Maintenance

### Regular Updates
- Update Docker image versions periodically
- Keep Python and Poetry versions current
- Update database client library versions in packages
- Review and update secret rotation policies

### Performance Optimization
- Use concurrency controls to prevent resource waste
- Implement effective caching strategies
- Optimize service startup times
- Consider matrix builds for multiple Python versions if needed 