import os
from pathlib import Path
import tempfile
import pytest
from griptape.artifacts import ErrorArtifact, ListArtifact, InfoArtifact, TextArtifact
from griptape.drivers import LocalFileManagerDriver
from griptape.loaders.text_loader import TextLoader


class TestLocalFileManagerDriver:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:

            def write_file(path: str, content: bytes):
                full_path = os.path.join(temp_dir, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "wb") as f:
                    f.write(content)

            def mkdir(path: str):
                full_path = os.path.join(temp_dir, path)
                os.makedirs(full_path, exist_ok=True)

            def copy_test_resources(resource_path: str):
                file_dir = os.path.dirname(__file__)
                full_path = os.path.join(file_dir, "../../../resources", resource_path)
                full_path = os.path.normpath(full_path)
                with open(full_path, "rb") as source:
                    content = source.read()
                dest_path = os.path.join(temp_dir, "resources", resource_path)
                write_file(dest_path, content)

            # Add some files
            write_file("foo.txt", b"foo")
            write_file("foo/bar.txt", b"bar")
            write_file("foo/bar/baz.txt", b"baz")
            copy_test_resources("bitcoin.pdf")
            copy_test_resources("small.png")
            copy_test_resources("test.txt")

            # Add some empty directories
            mkdir("foo-empty")
            mkdir("foo/bar-empty")
            mkdir("foo/bar/baz-empty")

            yield temp_dir

    @pytest.fixture
    def driver(self, temp_dir):
        return LocalFileManagerDriver(workdir=temp_dir)

    def test_validate_workdir(self):
        with pytest.raises(ValueError):
            LocalFileManagerDriver(workdir="foo")

    @pytest.mark.parametrize(
        "workdir,path,expected",
        [
            # Valid non-empty directories (witout trailing slash)
            ("/", "", ["foo", "foo.txt", "foo-empty", "resources"]),
            ("/", "foo", ["bar", "bar.txt", "bar-empty"]),
            ("/", "foo/bar", ["baz.txt", "baz-empty"]),
            ("/", "resources", ["bitcoin.pdf", "small.png", "test.txt"]),
            ("/foo", "", ["bar", "bar.txt", "bar-empty"]),
            ("/foo", "bar", ["baz.txt", "baz-empty"]),
            ("/foo/bar", "", ["baz.txt", "baz-empty"]),
            ("/resources", "", ["bitcoin.pdf", "small.png", "test.txt"]),
            # Valid non-empty directories (with trailing slash)
            ("/", "/", ["foo", "foo.txt", "foo-empty", "resources"]),
            ("/", "foo/", ["bar", "bar.txt", "bar-empty"]),
            ("/", "foo/bar/", ["baz.txt", "baz-empty"]),
            ("/foo", "/", ["bar", "bar.txt", "bar-empty"]),
            ("/foo", "bar/", ["baz.txt", "baz-empty"]),
            ("/foo/bar", "/", ["baz.txt", "baz-empty"]),
            # relative paths
            ("/", ".", ["foo", "foo.txt", "foo-empty", "resources"]),
            ("/", "foo/..", ["foo", "foo.txt", "foo-empty", "resources"]),
            ("/", "bar/..", ["foo", "foo.txt", "foo-empty", "resources"]),
            ("/", "foo/.", ["bar", "bar.txt", "bar-empty"]),
            ("/", "foo/bar/.", ["baz.txt", "baz-empty"]),
            ("/./..", ".", ["foo", "foo.txt", "foo-empty", "resources"]),
            ("/./..", "foo/..", ["foo", "foo.txt", "foo-empty", "resources"]),
            ("/./..", "bar/..", ["foo", "foo.txt", "foo-empty", "resources"]),
            ("/./..", "foo/.", ["bar", "bar.txt", "bar-empty"]),
            ("/./..", "foo/bar/.", ["baz.txt", "baz-empty"]),
            # Empty folders (witout trailing slash)
            ("/", "foo-empty", []),
            ("/", "foo/bar-empty", []),
            ("/", "foo/bar/baz-empty", []),
            # Empty folders (with trailing slash)
            ("/", "foo-empty/", []),
            ("/", "foo/bar-empty/", []),
            ("/", "foo/bar/baz-empty/", []),
        ],
    )
    def test_list_files(self, workdir, path, expected, temp_dir, driver):
        # Treat the workdir as an absolute path, but modify it to be relative to the temp_dir.
        driver.workdir = os.path.join(temp_dir, os.path.abspath(workdir).lstrip("/"))

        artifact = driver.list_files(path)

        assert isinstance(artifact, TextArtifact)
        assert set(filter(None, artifact.value.split("\n"))) == set(expected)

    @pytest.mark.parametrize(
        "workdir,path,expected",
        [
            # non-existent paths
            ("/", "bar", "Path not found"),
            ("/", "bar/", "Path not found"),
            ("/", "bitcoin.pdf", "Path not found"),
            # # paths to files (not directories)
            ("/", "foo.txt", "Path is not a directory"),
            ("/", "/foo.txt", "Path is not a directory"),
            ("/resources", "bitcoin.pdf", "Path is not a directory"),
            ("/resources", "/bitcoin.pdf", "Path is not a directory"),
        ],
    )
    def test_list_files_failure(self, workdir, path, expected, temp_dir, driver):
        # Treat the workdir as an absolute path, but modify it to be relative to the temp_dir.
        driver.workdir = os.path.join(temp_dir, os.path.abspath(workdir).lstrip("/"))

        artifact = driver.list_files(path)

        assert isinstance(artifact, ErrorArtifact)
        assert artifact.value == expected

    def test_load_file(self, driver: LocalFileManagerDriver):
        artifact = driver.load_file("resources/bitcoin.pdf")

        assert isinstance(artifact, ListArtifact)
        assert len(artifact.value) == 4

    @pytest.mark.parametrize(
        "workdir,path,expected",
        [
            # # non-existent files or directories
            ("/", "bitcoin.pdf", "Path not found"),
            ("/resources", "foo.txt", "Path not found"),
            ("/", "bar/", "Path is a directory"),
            # existing files with trailing slash
            ("/", "resources/bitcoin.pdf/", "Path is a directory"),
            ("/resources", "bitcoin.pdf/", "Path is a directory"),
            # directories (not files)
            ("/", "", "Path is a directory"),
            ("/", "/", "Path is a directory"),
            ("/", "resources", "Path is a directory"),
            ("/", "resources/", "Path is a directory"),
            ("/resources", "", "Path is a directory"),
            ("/resources", "/", "Path is a directory"),
        ],
    )
    def test_load_file_failure(self, workdir, path, expected, temp_dir, driver):
        # Treat the workdir as an absolute path, but modify it to be relative to the temp_dir.
        driver.workdir = os.path.join(temp_dir, os.path.abspath(workdir).lstrip("/"))

        artifact = driver.load_file(path)

        assert isinstance(artifact, ErrorArtifact)
        assert artifact.value == expected

    def test_load_file_with_encoding(self, driver: LocalFileManagerDriver):
        artifact = driver.load_file("resources/test.txt")

        assert isinstance(artifact, ListArtifact)
        assert len(artifact.value) == 1
        assert isinstance(artifact.value[0], TextArtifact)

    def test_load_file_with_encoding_failure(self):
        driver = LocalFileManagerDriver(
            default_loader=TextLoader(encoding="utf-8"), loaders={}, workdir=os.path.abspath(os.path.dirname(__file__))
        )

        artifact = driver.load_file("resources/bitcoin.pdf")

        assert isinstance(artifact, ErrorArtifact)

    @pytest.mark.parametrize(
        "workdir,path,content",
        [
            # non-existent files
            ("/", "resources/foo.txt", "one"),
            ("/resources", "foo.txt", "two"),
            # existing files
            ("/", "foo.txt", "three"),
            ("/resources", "test.txt", "four"),
            ("/", "resources/test.txt", "five"),
            # binary content
            ("/", "bone.fooz", b"bone"),
        ],
    )
    def test_save_file(self, workdir, path, content, temp_dir, driver):
        # Treat the workdir as an absolute path, but modify it to be relative to the temp_dir.
        driver.workdir = os.path.join(temp_dir, os.path.abspath(workdir).lstrip("/"))

        result = driver.save_file(path, content)

        assert isinstance(result, InfoArtifact)
        assert result.value == "Successfully saved file"
        content_bytes = content if isinstance(content, str) else content.decode()
        assert Path(driver.workdir, path).read_text() == content_bytes

    @pytest.mark.parametrize(
        "workdir,path,expected",
        [
            # non-existent directories
            ("/", "bar/", "Path is a directory"),
            ("/", "/bar/", "Path is a directory"),
            # existing directories
            ("/", "", "Path is a directory"),
            ("/", "/", "Path is a directory"),
            ("/", "resources", "Path is a directory"),
            ("/", "resources/", "Path is a directory"),
            ("/resources", "", "Path is a directory"),
            ("/resources", "/", "Path is a directory"),
            # existing files with trailing slash
            ("/", "resources/bitcoin.pdf/", "Path is a directory"),
            ("/resources", "bitcoin.pdf/", "Path is a directory"),
        ],
    )
    def test_save_file_failure(self, workdir, path, expected, temp_dir, driver):
        # Treat the workdir as an absolute path, but modify it to be relative to the temp_dir.
        driver.workdir = os.path.join(temp_dir, os.path.abspath(workdir).lstrip("/"))

        artifact = driver.save_file(path, "foobar")

        assert isinstance(artifact, ErrorArtifact)
        assert artifact.value == expected

    def test_save_file_with_encoding(self, temp_dir):
        driver = LocalFileManagerDriver(default_loader=TextLoader(encoding="utf-8"), loaders={}, workdir=temp_dir)
        result = driver.save_file(os.path.join("test", "foobar.txt"), "foobar")

        assert Path(os.path.join(temp_dir, "test", "foobar.txt")).read_text() == "foobar"
        assert result.value == "Successfully saved file"

    def test_save_and_load_file_with_encoding(self, temp_dir):
        driver = LocalFileManagerDriver(loaders={"txt": TextLoader(encoding="ascii")}, workdir=temp_dir)
        result = driver.save_file(os.path.join("test", "foobar.txt"), "foobar")

        assert Path(os.path.join(temp_dir, "test", "foobar.txt")).read_text() == "foobar"
        assert result.value == "Successfully saved file"

        driver = LocalFileManagerDriver(default_loader=TextLoader(encoding="ascii"), loaders={}, workdir=temp_dir)
        result = driver.load_file(os.path.join("test", "foobar.txt"))

        assert isinstance(result, ListArtifact)
        assert len(result.value) == 1
        assert isinstance(result.value[0], TextArtifact)

    def test_chrdir_getcwd(self, temp_dir):
        os.chdir(temp_dir)
        file_manager_1 = LocalFileManagerDriver()
        assert file_manager_1.workdir.endswith(temp_dir)
        os.chdir("/tmp")
        file_manager_2 = LocalFileManagerDriver()
        assert file_manager_2.workdir.endswith("/tmp")
