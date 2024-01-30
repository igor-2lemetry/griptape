from attr import define, field, Factory
from typing import Optional
from griptape.artifacts import TextArtifact
from griptape.engines import BaseQueryEngine
from griptape.loaders import TextLoader
from griptape.tasks import PromptTask
from griptape.utils import PromptStack


@define
class TextQueryTask(PromptTask):
    query_engine: BaseQueryEngine = field(kw_only=True)
    loader: TextLoader = field(default=Factory(lambda: TextLoader()), kw_only=True)
    namespace: Optional[str] = field(default=None, kw_only=True)
    top_n: Optional[int] = field(default=None, kw_only=True)
    preamble: Optional[str] = field(default=None, kw_only=True)
    assistant_appendix: Optional[str] = field(default=None, kw_only=True)

    @property
    def prompt_stack(self) -> PromptStack:
        stack = PromptStack()
        memory = self.structure.conversation_memory

        stack.add_system_input(self.generate_system_template(self))

#         stack.add_user_input(self.input.to_text())

        if self.output:
            stack.add_assistant_input(self.output.to_text())

        if memory:
            # inserting at index 1 to place memory right after system prompt
            stack.add_conversation_memory(memory, 1)

        return stack

    def run(self) -> TextArtifact:
        return self.query_engine.query(
            self.input.to_text(),
            namespace=self.namespace,
            rulesets=self.all_rulesets,
            top_n=self.top_n,
            preamble=self.preamble,
            assistant_appendix=self.assistant_appendix,
            prompt_stack=self.prompt_stack
        )
