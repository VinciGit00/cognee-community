from cognee.infrastructure.databases.relational import get_relational_engine
from cognee.infrastructure.llm import get_max_chunk_tokens
from cognee.modules.cognify.config import get_cognify_config
from cognee.modules.data.methods import create_dataset
from cognee.modules.observability.get_observe import get_observe
from cognee.modules.pipelines import CustomPipelineInterface, run_tasks
from cognee.modules.pipelines.tasks.task import Task
from cognee.modules.users.methods import get_default_user
from cognee.modules.users.models import User
from cognee.shared.data_models import KnowledgeGraph
from cognee.shared.logging_utils import get_logger
from cognee.tasks.documents import classify_documents, extract_chunks_from_documents
from cognee.tasks.graph import extract_graph_from_data
from cognee.tasks.ingestion import ingest_data
from cognee.tasks.storage import add_data_points
from cognee.tasks.summarization import summarize_text

from ..custom_tasks.repo_processor import get_non_py_files, get_repo_file_dependencies

observe = get_observe()

logger = get_logger("code_graph_pipeline")


class CodeGraphPipeline(CustomPipelineInterface):
    def __init__(
        self,
        repo_path,
        include_docs: bool = False,
        excluded_paths: list[str] | None = None,
        supported_languages: list[str] | None = None,
        user: User = None,
        detailed_extraction: bool = True,
    ):
        self.repo_path = repo_path
        self.include_docs = include_docs
        self.excluded_paths = excluded_paths
        self.supported_languages = supported_languages
        self.user = user
        self.detailed_extraction = detailed_extraction

    @observe
    async def run_pipeline(self):
        cognee_config = get_cognify_config()
        if not self.user:
            from cognee.low_level import setup

            await setup()

            self.user = await get_default_user()

        tasks = [
            Task(
                get_repo_file_dependencies,
                detailed_extraction=self.detailed_extraction,
                supported_languages=self.supported_languages,
                excluded_paths=self.excluded_paths,
            ),
            # This task takes a long time to complete
            # Task(summarize_code, task_config={"batch_size": 500}),
            Task(add_data_points, task_config={"batch_size": 30}),
        ]

        if self.include_docs:
            # These tasks take a long time to complete
            non_code_tasks = [
                Task(get_non_py_files, task_config={"batch_size": 50}),
                Task(ingest_data, dataset_name="repo_docs", user=self.user),
                Task(classify_documents),
                Task(extract_chunks_from_documents, max_chunk_size=get_max_chunk_tokens()),
                Task(
                    extract_graph_from_data,
                    graph_model=KnowledgeGraph,
                    task_config={"batch_size": 50},
                ),
                Task(
                    summarize_text,
                    summarization_model=cognee_config.summarization_model,
                    task_config={"batch_size": 50},
                ),
            ]

        dataset_name = "codebase"

        # Save dataset to database
        db_engine = get_relational_engine()
        async with db_engine.get_async_session() as session:
            dataset = await create_dataset(dataset_name, self.user, session)

        if self.include_docs:
            non_code_pipeline_run = run_tasks(
                non_code_tasks, dataset.id, self.repo_path, self.user, "cognify_pipeline"
            )
            async for run_status in non_code_pipeline_run:
                yield run_status

        async for run_status in run_tasks(
            tasks,
            dataset.id,
            self.repo_path,
            self.user,
            "cognify_code_pipeline",
            incremental_loading=False,
        ):
            yield run_status
