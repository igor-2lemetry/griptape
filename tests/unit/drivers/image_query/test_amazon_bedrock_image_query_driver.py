import pytest
import io
from unittest.mock import Mock
from griptape.drivers import AmazonBedrockImageQueryDriver
from griptape.artifacts import ImageArtifact, TextArtifact


class TestAmazonBedrockImageQueryDriver:
    @pytest.fixture
    def bedrock_client(self, mocker):
        return Mock()

    @pytest.fixture
    def session(self, bedrock_client):
        session = Mock()
        session.client.return_value = bedrock_client

        return session

    @pytest.fixture
    def model_driver(self):
        model_driver = Mock()
        model_driver.image_query_request_parameters.return_value = {}
        model_driver.process_output.return_value = TextArtifact("content")

        return model_driver

    @pytest.fixture
    def image_query_driver(self, session, model_driver):
        return AmazonBedrockImageQueryDriver(session=session, model="model", image_query_model_driver=model_driver)

    def test_init(self, image_query_driver):
        assert image_query_driver

    def test_try_query(self, image_query_driver):
        image_query_driver.bedrock_client.invoke_model.return_value = {"body": io.BytesIO(b"""{"content": []}""")}

        text_artifact = image_query_driver.try_query(
            "Prompt String", [ImageArtifact(value=b"test-data", width=100, height=100)]
        )

        assert text_artifact.value == "content"

    def test_try_query_no_body(self, image_query_driver):
        image_query_driver.bedrock_client.invoke_model.return_value = {"body": io.BytesIO(b"")}

        with pytest.raises(ValueError):
            image_query_driver.try_query("Prompt String", [ImageArtifact(value=b"test-data", width=100, height=100)])
