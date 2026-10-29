import hashlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from models_manifest import ModelMetadata
import prepare_models as preparation


OFFICIAL_URL = (
    "https://storage.googleapis.com/mediapipe-models/test/model.task"
)


class FakeResponse(io.BytesIO):
    def __init__(self, content: bytes, final_url: str = OFFICIAL_URL):
        super().__init__(content)
        self.headers = {"Content-Length": str(len(content))}
        self.final_url = final_url

    def geturl(self):
        return self.final_url

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.close()


class ModelPreparationTests(unittest.TestCase):
    def test_only_approved_https_host_is_allowed(self):
        preparation._validate_download_url(OFFICIAL_URL)
        for url in (
            "http://storage.googleapis.com/model.task",
            "https://example.com/model.task",
            "https://storage.googleapis.com.evil.example/model.task",
            "https://user@storage.googleapis.com/model.task",
            "https://storage.googleapis.com:444/model.task",
        ):
            with self.subTest(url=url):
                with self.assertRaises(preparation.ModelPreparationError):
                    preparation._validate_download_url(url)

    def test_existing_model_requires_matching_hash_and_size(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "model.task"
            content = b"trusted model"
            path.write_bytes(content)
            model = ModelMetadata(
                filename=path.name,
                local_path=path,
                official_url=OFFICIAL_URL,
                expected_sha256=hashlib.sha256(content).hexdigest().upper(),
                expected_size=len(content),
            )
            self.assertTrue(preparation.verify_existing_model(model)[0])
            path.write_bytes(b"altered model")
            valid, detail = preparation.verify_existing_model(model)
            self.assertFalse(valid)
            self.assertIn("SHA-256", detail)

    def test_pending_hash_blocks_download_before_network_access(self):
        with TemporaryDirectory() as directory:
            model = ModelMetadata(
                filename="model.task",
                local_path=Path(directory) / "model.task",
                official_url=OFFICIAL_URL,
                expected_sha256=None,
                expected_size=None,
            )
            with patch.object(preparation.urllib.request, "build_opener") as opener:
                with self.assertRaisesRegex(
                    preparation.ModelPreparationError, "download vietato"
                ):
                    preparation.download_and_verify_model(model)
            opener.assert_not_called()

    def test_hash_failure_removes_partial_download(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "model.task"
            content = b"downloaded model"
            model = ModelMetadata(
                filename=path.name,
                local_path=path,
                official_url=OFFICIAL_URL,
                expected_sha256="0" * 64,
                expected_size=len(content),
            )
            opener = Mock()
            opener.open.return_value = FakeResponse(content)
            with patch.object(
                preparation.urllib.request, "build_opener", return_value=opener
            ):
                with self.assertRaisesRegex(
                    preparation.ModelPreparationError, "SHA-256"
                ):
                    preparation.download_and_verify_model(model)
            self.assertFalse(path.exists())
            self.assertFalse(path.with_suffix(".task.part").exists())


if __name__ == "__main__":
    unittest.main()
