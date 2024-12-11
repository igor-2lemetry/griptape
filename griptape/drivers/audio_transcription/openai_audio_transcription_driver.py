from __future__ import annotations

import io
from typing import Optional

import openai
from attrs import field, Factory, define

from griptape.artifacts import AudioArtifact, TextArtifact
from griptape.drivers import BaseAudioTranscriptionDriver


@define
class OpenAiAudioTranscriptionDriver(BaseAudioTranscriptionDriver):
    api_type: str = field(default=openai.api_type, kw_only=True)
    api_version: Optional[str] = field(default=openai.api_version, kw_only=True, metadata={"serializable": True})
    base_url: Optional[str] = field(default=None, kw_only=True, metadata={"serializable": True})
    api_key: Optional[str] = field(default=None, kw_only=True, metadata={"serializable": False})
    organization: Optional[str] = field(default=openai.organization, kw_only=True, metadata={"serializable": True})
    client: openai.OpenAI = field(
        default=Factory(
            lambda self: openai.OpenAI(api_key=self.api_key, base_url=self.base_url, organization=self.organization),
            takes_self=True,
        )
    )

    def try_run(self, audio: AudioArtifact, prompts: Optional[list[str]] = None) -> TextArtifact:
        additional_params = {}

        if prompts is not None:
            additional_params["prompt"] = ", ".join(prompts)

        transcription = self.client.audio.transcriptions.create(
            # Even though we're not actually providing a file to the client, the API still requires that we send a file
            # name. We set the file name to use the same format as the audio file so that the API can reject
            # it if the format is unsupported.
            model=self.model,
            file=(f"a.{audio.format}", io.BytesIO(audio.value)),
            response_format="json",
            **additional_params,
        )

        return TextArtifact(value=transcription.text)
