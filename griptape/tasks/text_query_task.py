from attr import define, field, Factory
from typing import Optional
from griptape.artifacts import TextArtifact
from griptape.engines import BaseQueryEngine
from griptape.loaders import TextLoader
from griptape.tasks import BaseTextInputTask


@define
class TextQueryTask(BaseTextInputTask):
    query_engine: BaseQueryEngine = field(kw_only=True)
    loader: TextLoader = field(default=Factory(lambda: TextLoader()), kw_only=True)
    namespace: Optional[str] = field(default=None, kw_only=True)
    top_n: Optional[int] = field(default=None, kw_only=True)
    preamble: Optional[str] = field(default=None, kw_only=True)

    def run(self) -> TextArtifact:
        print(">>>>> Passing structure memory")
        print(self.query_engine.vector_store_driver.use_rag_api)
#         if self.query_engine.vector_store_driver.use_rag_api == True:
        self.query_engine.prompt_driver.structure = self.structure

        return self.query_engine.query(
            self.input.to_text(),
            namespace=self.namespace,
            rulesets=self.all_rulesets,
            top_n=self.top_n,
            preamble=self.preamble
        )
