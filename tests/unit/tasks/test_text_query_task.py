import pytest
from griptape.drivers import LocalVectorStoreDriver
from griptape.engines import VectorQueryEngine
from griptape.structures import Agent
from griptape.tasks import TextQueryTask
from tests.mocks.mock_embedding_driver import MockEmbeddingDriver
from tests.mocks.mock_prompt_driver import MockPromptDriver


class TestTextQueryTask:
    @pytest.fixture
    def task(self):
        return TextQueryTask(
            "test",
            query_engine=VectorQueryEngine(
                vector_store_driver=LocalVectorStoreDriver(embedding_driver=MockEmbeddingDriver()),
                prompt_driver=MockPromptDriver(),
            ),
            namespace="test",
        )

    def test_run(self, task):
        agent = Agent()

        agent.add_task(task)

        assert task.run().to_text() == "mock output"

    def test_context_propagation(self, task):
        task.input = "{{ test }}"
        task.context = {"test": "test value"}

        Agent().add_task(task)

        assert task.input.to_text() == "test value"
