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
    generate_response: bool = field(default=False, kw_only=True)
#     sessionId: str = field(kw_only=True)

    def query(
        self,
        query: str,
        count: Optional[int] = None,
        namespace: Optional[str] = None,
        include_vectors: bool = False,
        **kwargs,
    ) -> list[BaseVectorStoreDriver.QueryResult]:
        print("Retrieve API")
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

        print(">>>>> BedrockKnowledgeBase Query")
        print(query_body)
        print(query_params)

        response = self.bedrock_agent_client.retrieve(
            retrievalQuery=query_body,
            knowledgeBaseId=self.knowledge_base_id,
            retrievalConfiguration=query_params
        )

        print(">>>>> BedrockKnowledgeBase Response")
        print(response["retrievalResults"])

#         {
#            "nextToken": "string",
#            "retrievalResults": [
#               {
#                  "content": {
#                     "text": "string"
#                  },
#                  "location": {
#                     "s3Location": {
#                        "uri": "string"
#                     },
#                     "type": "string"
#                  },
#                  "score": number
#               }
#            ]
#         }

        return [
            BaseVectorStoreDriver.QueryResult(
                id=None,
                score=res["score"],
                vector=None,
                meta={"artifact": TextArtifact(res["content"].get("text")).to_json()}
            )
            for res in response["retrievalResults"]
        ]

    def retrieve_and_generate(
        self,
        query: str,
        count: Optional[int] = None,
        namespace: Optional[str] = None,
        include_vectors: bool = False,
        prompt: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> TextArtifact:
        print("Retrieve and Generate API")
        count = count if count else BaseVectorStoreDriver.DEFAULT_QUERY_COUNT
        search_type = 'HYBRID' if self.use_hybrid_search else 'SEMANTIC'
        print(">>>>> QUERY for SEARCH")
        print(query)
        print(count)
        print(search_type)
        print(prompt)

        query_body = {'text': query}
        query_params = {
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': self.knowledge_base_id,
                'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': count,
                        'overrideSearchType': search_type
                    }
                },
                'generationConfiguration': {
                    'promptTemplate': {
                        'textPromptTemplate': prompt
                    }
                }
            }
        }

        print(">>>>> BedrockKnowledgeBase Query")
        print(query_body)
        print(query_params)
        print(session_id)

        if session_id:
            response = self.bedrock_agent_client.retrieve_and_generate(
                input=query_body,
                sessionId=session_id,
                retrieveAndGenerateConfiguration=query_params
            )
        else:
            response = self.bedrock_agent_client.retrieve_and_generate(
                input=query_body,
                retrieveAndGenerateConfiguration=query_params
            )

        print(">>>>> BedrockKnowledgeBase Response")
        print(response)

        return TextArtifact(response["output"]["text"] + '<SID>' + response["sessionId"])

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