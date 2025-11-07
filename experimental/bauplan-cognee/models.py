"""
Minimal Cognee + Bauplan integration example.

This pipeline demonstrates AI memory with Cognee using a modular approach:
1. prepare_data: Reads S3 URIs from Bauplan's Iceberg table and prepares data
2. cognee_process: Downloads PDFs, adds to memory, and processes with Cognee
3. cognee_search: Searches Cognee memory with natural language

The pipeline processes PDF documents from S3 and creates searchable AI memory using Cognee.
"""

import bauplan


@bauplan.model(materialization_strategy="REPLACE")
@bauplan.python("3.11")
def prepare_data(
    data=bauplan.Model(
        "public.sec_10_q_metadata",
        columns=["bucket", "pdf_path"],
        # Limit to 1 example to keep runtime short
        filter="pdf_path LIKE '%2023_q2_intc.pdf%'",
    ),
):
    """
    First step: Prepare data for Cognee processing.

    Reads S3 metadata from Bauplan's Iceberg table and constructs S3 URLs.
    Returns a table with constructed S3 URLs.

    | s3_url |
    |--------|
    | https://alpha-hello-bauplan.s3.amazonaws.com/sec_10_q_filings/2023/2023_q2_intc.pdf |
    """
    # Get data from Bauplan table
    buckets = data["bucket"].to_pylist()
    paths = data["pdf_path"].to_pylist()

    # Construct S3 URLs for direct download (using public HTTPS endpoint)
    s3_urls = [f"https://{bucket}.s3.amazonaws.com/{path}" for bucket, path in zip(buckets, paths)]

    print(f"\n===> Found {len(s3_urls)} documents to prepare for processing\n")
    for url in s3_urls:
        print(f"  - {url}")

    # Add the S3 URL column to the data
    result = data.append_column("s3_url", [s3_urls])
    return result


@bauplan.model(internet_access=True, materialization_strategy="REPLACE")
@bauplan.python("3.11", pip={"cognee[aws]": "0.3.7.dev2", "requests": "2.32.3"})
def cognee_process(
    data=bauplan.Model("prepare_data"),
    data_root_directory=bauplan.Parameter("DATA_ROOT_DIRECTORY"),
    system_root_directory=bauplan.Parameter("SYSTEM_ROOT_DIRECTORY"),
    aws_endpoint_url=bauplan.Parameter("AWS_ENDPOINT_URL"),
    aws_access_key_id=bauplan.Parameter("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=bauplan.Parameter("AWS_SECRET_ACCESS_KEY"),
    aws_region=bauplan.Parameter("AWS_REGION"),
    llm_api_key=bauplan.Parameter("LLM_API_KEY"),
):
    """
    Uses Cognee to create AI memory from PDF documents in Bauplan's S3 bucket.

    Returns a table with S3 URLs and Cognee search results.
    """
    import asyncio
    import os

    # Set up environment for Cognee
    os.environ["AWS_ENDPOINT_URL"] = aws_endpoint_url
    os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key_id
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_access_key
    os.environ["AWS_REGION"] = aws_region
    os.environ["STORAGE_BACKEND"] = "s3"
    os.environ["DATA_ROOT_DIRECTORY"] = data_root_directory
    os.environ["SYSTEM_ROOT_DIRECTORY"] = system_root_directory
    os.environ["LLM_API_KEY"] = llm_api_key
    os.environ["ENV"] = "dev"
    del os.environ["AWS_SESSION_TOKEN"]

    import cognee

    async def process_documents():
        import requests
        from cognee.infrastructure.files.storage import get_file_storage, get_storage_config

        # Get S3 URLs from previous step
        buckets = data["bucket"].to_pylist()
        paths = data["pdf_path"].to_pylist()
        s3_urls = data["s3_url"].to_pylist()

        print(f"\n===> Found {len(s3_urls)} documents to process\n")
        for url in s3_urls:
            print(f"  - {url}")

        # Get Cognee's storage configuration
        storage_config = get_storage_config()
        data_root_directory = storage_config["data_root_directory"]
        storage = get_file_storage(data_root_directory)

        # Download and store each PDF using Cognee's file storage
        print("\n===> Downloading and storing PDFs in Cognee...\n")

        stored_file_paths = []
        for pdf_path, url in zip(paths, s3_urls):
            filename = pdf_path.split("/")[-1]

            print(f"\n>>>> Downloading {filename} from {url}\n")

            # Download the PDF content
            response = requests.get(url)
            response.raise_for_status()

            # Store the PDF using Cognee's file storage
            print(f"===> Storing {filename} in Cognee file storage...\n")
            full_file_path = await storage.store(filename, response.content)
            stored_file_paths.append(full_file_path)
            print(f"Stored file path: {full_file_path}")

            # Add the stored file to Cognee
            print(f"===> Adding {filename} to Cognee memory...\n")
            await cognee.add(full_file_path)

        # Cognify: Process all documents into knowledge graph
        print("\n===> Cognifying documents...\n")
        await cognee.cognify()

        return "done"

    # Run async Cognee operations
    status = asyncio.run(process_documents())

    print("\n===> Documents successfully processed and added to Cognee memory\n")

    # Get the number of rows from the input data
    num_rows = len(data)
    print(f"===> Number of rows: {num_rows}")
    # Create a list with the status repeated for each row
    status_list = [status] * num_rows
    print(f"===> Status list: {status_list}")

    # Add the status column to match the number of rows
    result = data.append_column("status", [status_list])

    return result


@bauplan.model(internet_access=True, materialization_strategy="REPLACE")
@bauplan.python("3.11", pip={"cognee[aws]": "0.3.7.dev2"})
def cognee_search(
    data=bauplan.Model("cognee_process"),
    query=bauplan.Parameter("SEARCH_QUERY"),
    data_root_directory=bauplan.Parameter("DATA_ROOT_DIRECTORY"),
    system_root_directory=bauplan.Parameter("SYSTEM_ROOT_DIRECTORY"),
    aws_endpoint_url=bauplan.Parameter("AWS_ENDPOINT_URL"),
    aws_access_key_id=bauplan.Parameter("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=bauplan.Parameter("AWS_SECRET_ACCESS_KEY"),
    aws_region=bauplan.Parameter("AWS_REGION"),
    llm_api_key=bauplan.Parameter("LLM_API_KEY"),
):
    """
    Third step: Search Cognee memory.

    Searches the processed documents in Cognee memory using natural language queries.
    Returns a table with S3 URLs, the query, and search results.
    """
    import asyncio
    import os

    # Set up environment for Cognee (needed for search)
    os.environ["AWS_ENDPOINT_URL"] = aws_endpoint_url
    os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key_id
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_access_key
    os.environ["AWS_REGION"] = aws_region
    os.environ["STORAGE_BACKEND"] = "s3"
    os.environ["DATA_ROOT_DIRECTORY"] = data_root_directory
    os.environ["SYSTEM_ROOT_DIRECTORY"] = system_root_directory
    os.environ["LLM_API_KEY"] = llm_api_key
    os.environ["ENV"] = "dev"
    del os.environ["AWS_SESSION_TOKEN"]

    import cognee

    async def search_memory():
        # Search Cognee memory with natural language
        print(f"\n===> Searching Cognee memory with query: {query}\n")
        search_result = await cognee.search(query)
        print(f"Search result: {search_result}")
        return search_result

    # Run async search operation
    search_result = asyncio.run(search_memory())

    # Create result table with search insights
    answers = str(search_result)[:1000]  # Limit size for storage

    # Create lists that match the number of rows in the data
    num_rows = len(data)
    print(f"===> Number of rows: {num_rows}")
    queries = [query] * num_rows
    search_results = [answers] * num_rows

    # Add query and search result columns
    result = data.append_column("query", [queries])
    result = result.append_column("search_result", [search_results])

    return result
