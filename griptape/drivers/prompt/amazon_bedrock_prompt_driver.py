import json

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Optional

from attrs import Factory, define, field

from griptape.artifacts import TextArtifact
from griptape.drivers import BasePromptDriver
from griptape.tokenizers import AmazonBedrockTokenizer, BaseTokenizer
from griptape.utils import import_optional_dependency

if TYPE_CHECKING:
    import boto3

    from griptape.utils import PromptStack


@define
class AmazonBedrockPromptDriver(BasePromptDriver):
    session: boto3.Session = field(default=Factory(lambda: import_optional_dependency("boto3").Session()), kw_only=True)
    bedrock_client: Any = field(
        default=Factory(lambda self: self.session.client("bedrock-runtime"), takes_self=True), kw_only=True
    )
    additional_model_request_fields: dict = field(default=Factory(dict), kw_only=True)
    tokenizer: BaseTokenizer = field(
        default=Factory(lambda self: AmazonBedrockTokenizer(model=self.model), takes_self=True), kw_only=True
    )
    assistant_appendix: Optional[str] = field(default=None, kw_only=True)

    def try_run(self, prompt_stack: PromptStack) -> TextArtifact:
        response = self.bedrock_client.converse(**self._base_params(prompt_stack))

        output_message = response["output"]["message"]
        output_content = output_message["content"][0]["text"]

        print(">>>>> RESPONSE FROM BEDROCK")
        print(output_content)

        return TextArtifact(output_content)

    def try_stream(self, prompt_stack: PromptStack) -> Iterator[TextArtifact]:
        response = self.bedrock_client.converse_stream(**self._base_params(prompt_stack))

        stream = response.get("stream")
        if stream is not None:
            for event in stream:
                if "contentBlockDelta" in event:
                    yield TextArtifact(event["contentBlockDelta"]["delta"]["text"])
        else:
            raise Exception("model response is empty")

    def _prompt_stack_input_to_message(self, prompt_input: PromptStack.Input) -> dict:
        content = [{"text": prompt_input.content}]

        if prompt_input.is_system():
            return {"text": prompt_input.content}
        elif prompt_input.is_assistant():
            return {"role": "assistant", "content": content}
        else:
            return {"role": "user", "content": content}

    def _base_params(self, prompt_stack: PromptStack) -> dict:
        system_messages = [
            self._prompt_stack_input_to_message(input)
            for input in prompt_stack.inputs
            if input.is_system() and input.content
        ]
        messages = [
            self._prompt_stack_input_to_message(input) for input in prompt_stack.inputs if not input.is_system()
        ]

        if self.assistant_appendix != None:
            messages.append({"role": "assistant", "content": self.assistant_appendix})

        print(">>>>> PAYLOAD TO BEDROCK")
        print(json.dumps({
            "modelId": self.model,
            "messages": messages,
            "system": system_messages,
            "inferenceConfig": {
                # https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InferenceConfiguration.html
                "temperature": self.temperature,
                "topP": self.top_p,
                "maxTokens": self.max_tokens if self.max_tokens else self.tokenizer._default_max_output_tokens()
            },
            "additionalModelRequestFields": self.additional_model_request_fields,
        }))

        return {
            "modelId": self.model,
            "messages": messages,
            "system": system_messages,
            "inferenceConfig": {
                # https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InferenceConfiguration.html
                "temperature": self.temperature,
                "topP": self.top_p,
                "maxTokens": self.max_tokens if self.max_tokens else self.tokenizer._default_max_output_tokens()
            },
            "additionalModelRequestFields": self.additional_model_request_fields,
        }
