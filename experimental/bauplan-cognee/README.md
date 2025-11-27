# Bauplan + Cognee Integration

This is a 3-step pipeline that turns PDFs from Bauplan's public S3 bucket into searchable AI memory with cognee via chained Bauplan.model's.

It can be extended to any data type that cognee supports since there's no manual transformation step. 

```
 =>  ----------------
 => |  prepare_data  |
 =>  ----------------
 =>   |
 =>   |
 =>   v
 =>  ----------------
 => | cognee_process |
 =>  ----------------
 =>   |
 =>   |
 =>   v
 =>  ----------------
 => | cognee_search  |
 =>  ----------------
```

## What It Does

The pipeline transforms PDF documents from an S3 bucket into a semantic memory with cognee, stored in S3. You can then query this memory with natural language questions.

## How It Works

The pipeline consists of three sequential steps:

1. **`prepare_data`** - Reads document metadata from Bauplan's Iceberg table and constructs S3 URLs from bucket and file paths
2. **`cognee_process`** - Downloads PDFs from constructured S3 URLs, stores them in Cognee storage, and builds semantic memory
3. **`cognee_search`** - Enables natural language search over the processed documents

Each step is a separate Bauplan model that chains its output to the next, creating a clean data flow from raw documents to searchable knowledge.

## Requirements

### Infrastructure
- **Bauplan account** and api key
- **AWS S3** for document storage (configured via parameters) - see [docs for cognee configs](https://docs.cognee.ai/guides/s3-storage)
- **LLM API key** (e.g., OpenAI) for AI processing 

### Dependencies
- Python 3.11
- `cognee[aws]` 0.3.7.dev2
- `requests` 2.32.3
- Internet access enabled for models

### Configuration
All parameters are managed through `bauplan_project.yml`:
- AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- AWS configuration (`AWS_ENDPOINT_URL`, `AWS_REGION`)
- Cognee storage paths (`DATA_ROOT_DIRECTORY`, `SYSTEM_ROOT_DIRECTORY`)
- LLM API key (`LLM_API_KEY`)
- Search query (`SEARCH_QUERY` - customizable, default: "What's in the document?")

## Limitations

- **Document scope**: Currently processes only Intel Q2 2023 filing (hardcoded filter for demo purposes)
- **Memory persistence**: Cognee memory persists across runs - delete to be added
- **Search results**: Limited to 1000 characters for storage efficiency during demo
- **AWS session tokens**: Removed from environment (incompatible with configured S3 storage backend)

## Usage Example

Follow installation, quick start guides from [bauplan docs](https://docs.bauplanlabs.com/tutorial/installation) to complete successful setup.

```bash
# navigate to the project folder
cd bauplan-cognee
# Run the entire pipeline
bauplan run 
```

The pipeline will:
1. Fetch document metadata from Bauplan's public dataset
2. Download and process the PDF into Cognee's AI memory
3. Return search results based on your configured query

