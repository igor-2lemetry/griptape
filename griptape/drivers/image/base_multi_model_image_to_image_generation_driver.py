from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Optional, TYPE_CHECKING

from attr import field, define

from griptape.artifacts import ImageArtifact

if TYPE_CHECKING:
    from griptape.drivers import BaseImageToImageGenerationModelDriver, BaseImageToImageGenerationDriver


@define
class BaseMultiModelImageToImageGenerationDriver(BaseImageToImageGenerationDriver, ABC):
    """Image Modification Driver for platforms like Amazon Bedrock that host many LLM models.

    Instances of this Image Generation Driver require a Image Generation Model Driver which is used to structure the
    image generation request in the format required by the model and to process the output.

    Attributes:
        model: Name of the model to use.
        image_modification_model_driver: Image Modification Model Driver to use.
    """

    image_modification_model_driver: BaseImageToImageGenerationModelDriver = field(kw_only=True)

    @abstractmethod
    def try_generate_image(self, prompts: list[str], negative_prompts: Optional[list[str]] = None) -> ImageArtifact:
        ...
