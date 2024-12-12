from __future__ import annotations
from typing import Optional, Tuple, TYPE_CHECKING
from griptape import utils
import logging
from griptape.artifacts import TextArtifact
from griptape.utils import import_optional_dependency
from griptape.drivers import BaseVectorStoreDriver
from attr import define, field, Factory

# TODO add extras for it
if TYPE_CHECKING:
    import boto3


@define
class BedrockKnowledgeBaseVectorStoreDriver(BaseVectorStoreDriver):
    bedrock_agent_client: Any = field(
        default=Factory(lambda: import_optional_dependency("boto3").client("bedrock-agent-runtime")), kw_only=True
    )

    knowledge_base_id: str = field(kw_only=True)
    use_hybrid_search: bool = field(default=False, kw_only=True)

    def query(
        self,
        query: str,
        count: Optional[int] = None,
        namespace: Optional[str] = None,
        include_vectors: bool = False,
        **kwargs,
    ) -> list[BaseVectorStoreDriver.QueryResult]:
        count = count if count else BaseVectorStoreDriver.DEFAULT_QUERY_COUNT
        search_type = 'HYBRID' if self.use_hybrid_search else 'SEMANTIC'
        print(">>>>> QUERY for SEARCH")
        print(query)
        print(count)
        print(search_type)

        query_body = {'text': query}
        query_params = {
            'vectorSearchConfiguration': {'numberOfResults': count, 'overrideSearchType': search_type}
        }

        response = self.bedrock_agent_client.retrieve(
            retrievalQuery=query_body,
            knowledgeBaseId=self.knowledge_base_id,
            retrievalConfiguration=query_params
        )

        print(">>>>> BedrockKnowledgeBase Response")
        print(response["retrievalResults"])

        return [
            BaseVectorStoreDriver.QueryResult(
                id=None,
                score=res["score"],
                vector=None,
                meta={"artifact": TextArtifact(res["content"].get("text")).to_json()}
            )
            for res in response["retrievalResults"]
        ]

    def upsert_vector(
        self,
        vector: list[float],
        vector_id: Optional[str] = None,
        namespace: Optional[str] = None,
        meta: Optional[dict] = None,
        **kwargs,
    ) -> str:
        raise NotImplementedError(f"{self.__class__.__name__} does not support upsert.")

    def load_entry(self, vector_id: str, namespace: Optional[str] = None) -> Optional[BaseVectorStoreDriver.Entry]:
        raise NotImplementedError(f"{self.__class__.__name__} does not support loading entry.")

    def load_entries(self, namespace: Optional[str] = None) -> list[BaseVectorStoreDriver.Entry]:
        raise NotImplementedError(f"{self.__class__.__name__} does not support loading entries.")

    def delete_vector(self, vector_id: str):
        raise NotImplementedError(f"{self.__class__.__name__} does not support deletion.")