from griptape.artifacts.list_artifact import ListArtifact
from griptape.engines import InpaintingImageGenerationEngine
from unittest.mock import Mock

import pytest
from griptape.tasks import BaseTask, InpaintingImageGenerationTask
from griptape.artifacts import TextArtifact, ImageArtifact
from griptape.structures import Agent
from tests.mocks.mock_image_generation_driver import MockImageGenerationDriver
from tests.mocks.mock_structure_config import MockStructureConfig


class TestInpaintingImageGenerationTask:
    @pytest.fixture
    def text_artifact(self):
        return TextArtifact(value="some text")

    @pytest.fixture
    def image_artifact(self):
        return ImageArtifact(value=b"some image data", format="png", width=512, height=512)

    def test_artifact_inputs(self, text_artifact: TextArtifact, image_artifact: ImageArtifact):
        input_tuple = (text_artifact, image_artifact, image_artifact)
        task = InpaintingImageGenerationTask(input_tuple, image_generation_engine=Mock())

        assert task.input.value == list(input_tuple)

    def test_callable_input(self, text_artifact: TextArtifact, image_artifact: ImageArtifact):
        input = [text_artifact, image_artifact, image_artifact]

        def callable(task: BaseTask) -> ListArtifact:
            return ListArtifact(value=list(input))

        task = InpaintingImageGenerationTask(callable, image_generation_engine=Mock())

        assert task.input.value == input

    def test_list_input(self, text_artifact: TextArtifact, image_artifact: ImageArtifact):
        input = [text_artifact, image_artifact]
        task = InpaintingImageGenerationTask(ListArtifact(input), image_generation_engine=Mock())

        assert task.input.value == input

    def test_bad_input(self, image_artifact):
        with pytest.raises(ValueError):
            InpaintingImageGenerationTask(("foo", "bar", image_artifact)).run()  # pyright: ignore[reportArgumentType]

        with pytest.raises(ValueError):
            InpaintingImageGenerationTask(("foo", image_artifact, "baz")).run()  # pyright: ignore[reportArgumentType]

    def test_config_image_generation_engine(self, text_artifact, image_artifact):
        task = InpaintingImageGenerationTask((text_artifact, image_artifact, image_artifact))
        Agent(config=MockStructureConfig()).add_task(task)

        assert isinstance(task.image_generation_engine, InpaintingImageGenerationEngine)
        assert isinstance(task.image_generation_engine.image_generation_driver, MockImageGenerationDriver)

    def test_missing_image_generation_engine(self, text_artifact, image_artifact):
        task = InpaintingImageGenerationTask((text_artifact, image_artifact, image_artifact))

        with pytest.raises(ValueError):
            task.image_generation_engine
