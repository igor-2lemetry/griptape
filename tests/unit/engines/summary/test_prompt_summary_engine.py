import pytest
from griptape.artifacts import TextArtifact, ListArtifact
from griptape.engines import PromptSummaryEngine
from griptape.utils import PromptStack
from tests.mocks.mock_prompt_driver import MockPromptDriver
import os


class TestPromptSummaryEngine:
    @pytest.fixture
    def engine(self):
        return PromptSummaryEngine(prompt_driver=MockPromptDriver())

    def test_summarize_text(self, engine):
        assert engine.summarize_text("foobar") == "mock output"

    def test_summarize_artifacts(self, engine):
        assert (
            engine.summarize_artifacts(ListArtifact([TextArtifact("foo"), TextArtifact("bar")])).value == "mock output"
        )

    def test_max_token_multiplier_invalid(self, engine):
        with pytest.raises(ValueError):
            PromptSummaryEngine(prompt_driver=MockPromptDriver(), max_token_multiplier=0)

        with pytest.raises(ValueError):
            PromptSummaryEngine(prompt_driver=MockPromptDriver(), max_token_multiplier=10000)

    def test_chunked_summary(self, engine):
        def smaller_input(prompt_stack: PromptStack):
            return prompt_stack.inputs[0].content[: (len(prompt_stack.inputs[0].content) // 2)]

        engine = PromptSummaryEngine(prompt_driver=MockPromptDriver(mock_output="smaller_input"))

        def copy_test_resource(resource_path: str):
            file_dir = os.path.dirname(__file__)
            full_path = os.path.join(file_dir, "../../../resources", resource_path)
            full_path = os.path.normpath(full_path)
            with open(full_path) as f:
                return f.read()

        assert engine.summarize_text(copy_test_resource("test.txt") * 50)
