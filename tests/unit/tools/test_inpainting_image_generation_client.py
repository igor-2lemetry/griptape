import os
import tempfile
import uuid
from unittest.mock import Mock

import pytest

from griptape.artifacts import ImageArtifact
from griptape.tools import InpaintingImageGenerationClient


class TestInpaintingImageGenerationClient:
    @pytest.fixture
    def image_generation_engine(self) -> Mock:
        return Mock()

    @pytest.fixture
    def image_loader(self) -> Mock:
        loader = Mock()
        loader.load.return_value = ImageArtifact(value=b"image_data", format="png", width=512, height=512)

        return loader

    @pytest.fixture
    def image_generator(self, image_generation_engine, image_loader) -> InpaintingImageGenerationClient:
        return InpaintingImageGenerationClient(engine=image_generation_engine, image_loader=image_loader)

    def test_validate_output_configs(self, image_generation_engine) -> None:
        with pytest.raises(ValueError):
            InpaintingImageGenerationClient(engine=image_generation_engine, output_dir="test", output_file="test")

    def test_image_inpainting(self, image_generator) -> None:
        image_generator.engine.run.return_value = Mock(
            value=b"image data", format="png", width=512, height=512, model="test model", prompt="test prompt"
        )

        image_artifact = image_generator.image_inpainting_from_file(
            params={
                "values": {
                    "prompts": ["test prompt"],
                    "negative_prompts": ["test negative prompt"],
                    "image_file": "image.png",
                    "mask_file": "mask.png",
                }
            }
        )

        assert image_artifact

    def test_image_inpainting_with_outfile(self, image_generation_engine, image_loader) -> None:
        outfile = f"{tempfile.gettempdir()}/{str(uuid.uuid4())}.png"
        image_generator = InpaintingImageGenerationClient(
            engine=image_generation_engine, output_file=outfile, image_loader=image_loader
        )

        image_generator.engine.run.return_value = Mock(  # pyright: ignore
            value=b"image data", format="png", width=512, height=512, model="test model", prompt="test prompt"
        )

        image_artifact = image_generator.image_inpainting_from_file(
            params={
                "values": {
                    "prompts": ["test prompt"],
                    "negative_prompts": ["test negative prompt"],
                    "image_file": "image.png",
                    "mask_file": "mask.png",
                }
            }
        )

        assert image_artifact
        assert os.path.exists(outfile)
