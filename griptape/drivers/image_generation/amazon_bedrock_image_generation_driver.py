import base64
import json
from typing import Optional, TYPE_CHECKING, Any
from attr import define, field, Factory
from griptape.artifacts import ImageArtifact
from .base_multi_model_image_generation_driver import BaseMultiModelImageGenerationDriver
from griptape.utils import import_optional_dependency

if TYPE_CHECKING:
    import boto3


@define
class AmazonBedrockImageGenerationDriver(BaseMultiModelImageGenerationDriver):
    session: boto3.Session = field(default=Factory(lambda: import_optional_dependency("boto3").Session()), kw_only=True)
    bedrock_client: Any = field(
        default=Factory(lambda self: self.session.client(service_name="bedrock-runtime"), takes_self=True)
    )
    image_width: int = field(default=512, kw_only=True)
    image_height: int = field(default=512, kw_only=True)
    seed: Optional[int] = field(default=None, kw_only=True)

    def try_generate_image(self, prompts: list[str], negative_prompts: Optional[list[str]] = None) -> ImageArtifact:
        request = self.image_generation_model_driver.text_to_image_request_parameters(
            prompts, self.image_width, self.image_height, negative_prompts=negative_prompts, seed=self.seed
        )

        response = self.bedrock_client.invoke_model(
            body=json.dumps(request), modelId=self.model, accept="application/json", contentType="application/json"
        )

        response_body = json.loads(response.get("body").read())
        image_response = response_body["artifacts"][0]
        if image_response.get("finishReason") != "SUCCESS":
            raise ValueError(f"Image generation failed: {image_response.get('finishReason')}")

        image_bytes = base64.decodebytes(bytes(image_response.get("base64"), "utf-8"))

        return ImageArtifact(
            prompt=", ".join(prompts),
            value=image_bytes,
            mime_type="image/png",
            width=self.image_width,
            height=self.image_height,
            model=self.model,
        )
