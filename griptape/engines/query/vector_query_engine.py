from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from attr import define, field, Factory
from griptape.artifacts import TextArtifact, BaseArtifact, ListArtifact
from griptape.utils import PromptStack
from griptape.drivers import OpenAiChatPromptDriver
from griptape.engines import BaseQueryEngine
from griptape.utils.j2 import J2
from griptape.tokenizers import OpenAiTokenizer
from griptape.rules import Ruleset

if TYPE_CHECKING:
    from griptape.drivers import BaseVectorStoreDriver, BasePromptDriver


@define
class VectorQueryEngine(BaseQueryEngine):
    answer_token_offset: int = field(default=400, kw_only=True)
    vector_store_driver: BaseVectorStoreDriver = field(kw_only=True)
    prompt_driver: BasePromptDriver = field(
        default=Factory(lambda: OpenAiChatPromptDriver(model=OpenAiTokenizer.DEFAULT_OPENAI_GPT_3_CHAT_MODEL)),
        kw_only=True,
    )
    template_generator: J2 = field(default=Factory(lambda: J2("engines/query/vector_query.j2")), kw_only=True)
    system_generator: J2 = field(default=Factory(lambda: J2("engines/query/vector_system.j2")), kw_only=True)
    retrieve_generator: J2 = field(default=Factory(lambda: J2("engines/query/vector_generate.j2")), kw_only=True)

    DEFAULT_QUERY_PREAMBLE = "You can answer questions by searching through text segments. Always be truthful. Don't make up facts. Use the below list of text segments to respond to the subsequent query. If the answer cannot be found in the segments, say 'I could not find an answer'."

    def query(
        self,
        query: str,
        namespace: Optional[str] = None,
        rulesets: Optional[list[Ruleset]] = None,
        metadata: Optional[str] = None,
        top_n: Optional[int] = None,
        preamble: Optional[str] = None,
    ) -> TextArtifact:
        preamble = preamble if preamble else self.DEFAULT_QUERY_PREAMBLE

        if self.vector_store_driver.use_rag_api == True:
            print(">>>>> RetrieveAndGenerateAPI")

            retrieve_message = ""

            retrieve_message = self.retrieve_generator.render(
                preamble=preamble,
                rulesets=J2("rulesets/rulesets.j2").render(rulesets=rulesets),
                appendix=self.prompt_driver.prompt_model_driver.assistant_appendix
            )

            session_id = ""

            if len(self.prompt_driver.structure.conversation_memory.runs) > 0:
                session_id = self.prompt_driver.structure.conversation_memory.runs[-1].output.split('<SID>')[-1]
            else:
                print(">>>>> No session stored")

            return self.vector_store_driver.retrieve_and_generate(query, top_n, namespace, prompt=retrieve_message, model=self.prompt_driver.model, session_id=session_id)

        tokenizer = self.prompt_driver.tokenizer
        result = self.vector_store_driver.query(query, top_n, namespace)

        artifacts = [
            artifact
            for artifact in [BaseArtifact.from_json(r.meta["artifact"]) for r in result if r.meta]
            if isinstance(artifact, TextArtifact)
        ]
        text_segments = []
        message = ""
        system_message = ""

        system_message = self.system_generator.render(
            preamble=preamble,
#             rulesets=J2("rulesets/rulesets.j2").render(rulesets=rulesets),
        )

        for artifact in artifacts:
            text_segments.append(artifact.value)

            message = self.template_generator.render(
#                 preamble=preamble,
                metadata=metadata,
                query=query,
                text_segments=text_segments,
                rulesets=J2("rulesets/rulesets.j2").render(rulesets=rulesets),
            )
            message_token_count = self.prompt_driver.token_count(
                PromptStack(inputs=[PromptStack.Input(message, role=PromptStack.USER_ROLE)])
            )

            if message_token_count + self.answer_token_offset >= tokenizer.max_tokens:
                text_segments.pop()

                message = self.template_generator.render(
#                     preamble=preamble,
                    metadata=metadata,
                    query=query,
                    text_segments=text_segments,
                    rulesets=J2("rulesets/rulesets.j2").render(rulesets=rulesets),
                )

                break

        return self.prompt_driver.run(PromptStack(inputs=[PromptStack.Input(system_message, role=PromptStack.SYSTEM_ROLE), PromptStack.Input(message, role=PromptStack.USER_ROLE)]))

    def upsert_text_artifact(self, artifact: TextArtifact, namespace: Optional[str] = None) -> str:
        result = self.vector_store_driver.upsert_text_artifact(artifact, namespace=namespace)

        return result

    def upsert_text_artifacts(self, artifacts: list[TextArtifact], namespace: str) -> None:
        self.vector_store_driver.upsert_text_artifacts({namespace: artifacts})

    def load_artifacts(self, namespace: str) -> ListArtifact:
        result = self.vector_store_driver.load_entries(namespace)
        artifacts = [BaseArtifact.from_json(r.meta["artifact"]) for r in result if r.meta and r.meta.get("artifact")]

        return ListArtifact([a for a in artifacts if isinstance(a, TextArtifact)])
