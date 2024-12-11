This example shows how to use one `Agent` to load content into `TaskMemory` and get that content from another `Agent` using `TaskMemoryClient`.

The first `Agent` uses a remote vector store (`MongoDbAtlasVectorStoreDriver` in this example) to handle memory operations. The second `Agent` uses the same instance of `TaskMemory` and the `TaskMemoryClient` with the same `MongoDbAtlasVectorStoreDriver` to get the data.

The `MongoDbAtlasVectorStoreDriver` assumes that you have a vector index configured where the path to the content is called `vector`, and the number of dimensions set on the index is `1536` (this is a commonly used number of dimensions for embedding models).

`asker` uses the same instance of `TaskMemory` as `loader` so that `asker` has access to the `namespace_storages` that `loader` has set.

```python
import os
from griptape.tools import WebScraper, VectorStoreClient, TaskMemoryClient
from griptape.structures import Agent
from griptape.drivers import AzureOpenAiEmbeddingDriver, AzureMongoDbVectorStoreDriver
from griptape.engines import VectorQueryEngine, PromptSummaryEngine, CsvExtractionEngine, JsonExtractionEngine
from griptape.memory import TaskMemory 
from griptape.artifacts import TextArtifact
from griptape.memory.task.storage import TextArtifactStorage
from griptape.config import AzureOpenAiStructureConfig


AZURE_OPENAI_ENDPOINT_1 = os.environ["AZURE_OPENAI_ENDPOINT_1"]
AZURE_OPENAI_API_KEY_1 = os.environ["AZURE_OPENAI_API_KEY_1"]

MONGODB_HOST = os.environ["MONGODB_HOST"]
MONGODB_USERNAME = os.environ["MONGODB_USERNAME"]
MONGODB_PASSWORD = os.environ["MONGODB_PASSWORD"]
MONGODB_DATABASE_NAME = os.environ["MONGODB_DATABASE_NAME"]
MONGODB_COLLECTION_NAME = os.environ["MONGODB_COLLECTION_NAME"]
MONGODB_INDEX_NAME = os.environ["MONGODB_INDEX_NAME"]
MONGODB_VECTOR_PATH = os.environ["MONGODB_VECTOR_PATH"]
MONGODB_CONNECTION_STRING = f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}/{MONGODB_DATABASE_NAME}?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"


embedding_driver = AzureOpenAiEmbeddingDriver(
    model='text-embedding-ada-002',
    azure_endpoint=AZURE_OPENAI_ENDPOINT_1,
    api_key=AZURE_OPENAI_API_KEY_1,
)

mongo_driver = AzureMongoDbVectorStoreDriver(
    connection_string=MONGODB_CONNECTION_STRING,
    database_name=MONGODB_DATABASE_NAME,
    collection_name=MONGODB_COLLECTION_NAME,
    embedding_driver=embedding_driver,
    index_name=MONGODB_INDEX_NAME,
    vector_path=MONGODB_VECTOR_PATH,
)

config = AzureOpenAiStructureConfig(
    azure_endpoint=AZURE_OPENAI_ENDPOINT_1,
    vector_store_driver=mongo_driver,
    embedding_driver=embedding_driver,
)

loader = Agent(
    tools=[
        WebScraper(off_prompt=True),
    ],
    config=config,
)
asker = Agent(
    tools=[
        TaskMemoryClient(off_prompt=False),
    ],
    meta_memory=loader.meta_memory,
    task_memory=loader.task_memory,
    config=config,
)

if __name__ == "__main__":
    loader.run("Load https://medium.com/enterprise-rag/a-first-intro-to-complex-rag-retrieval-augmented-generation-a8624d70090f")
    asker.run("why is retrieval augmented generation useful?")
```
