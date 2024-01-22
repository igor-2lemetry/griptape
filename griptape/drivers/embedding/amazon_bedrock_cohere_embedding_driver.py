from __future__ import annotations
import json
from typing import Any, TYPE_CHECKING
from attr import define, field, Factory
from griptape.drivers import BaseEmbeddingDriver
from griptape.utils import import_optional_dependency

if TYPE_CHECKING:
    import boto3


@define
class AmazonBedrockCohereEmbeddingDriver(BaseEmbeddingDriver):
    """
    Attributes:
        model: Embedding model name. Defaults to DEFAULT_MODEL.
        session: Optionally provide custom `boto3.Session`.
        bedrock_client: Optionally provide custom `bedrock-runtime` client.
    """

    DEFAULT_MODEL = "cohere.embed-english-v3"

    model: str = field(default=DEFAULT_MODEL, kw_only=True)
    session: boto3.Session = field(default=Factory(lambda: import_optional_dependency("boto3").Session()), kw_only=True)
    bedrock_client: Any = field(
        default=Factory(lambda self: self.session.client("bedrock-runtime"), takes_self=True), kw_only=True
    )

    def try_embed_chunk(self, chunk: str) -> list[float]:
        print(">>>>> HERE 3")

        payload = {
            "input_type": "search_document",
            "texts": [chunk]
        }

        response = self.bedrock_client.invoke_model(
            body=json.dumps(payload), modelId=self.model, accept="*/*", contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())

        print(">>>>> RESPONSE")
        print(response_body.get("embeddings"))
        print("=====")
        print(response_body.get("embeddings")[0])
        print("=====")

        return response_body.get("embeddings")[0]
