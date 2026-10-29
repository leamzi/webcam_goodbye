"""Trusted metadata for the local MediaPipe model files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_DIR / "models"
PENDING_SHA256 = None


@dataclass(frozen=True)
class ModelMetadata:
    filename: str
    local_path: Path
    official_url: str | None
    expected_sha256: str | None
    expected_size: int | None


SELFIE_SEGMENTER = ModelMetadata(
    filename="selfie_segmenter_landscape.tflite",
    local_path=MODELS_DIR / "selfie_segmenter_landscape.tflite",
    official_url=(
        "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
        "selfie_segmenter_landscape/float16/latest/"
        "selfie_segmenter_landscape.tflite"
    ),
    expected_sha256=(
        "490E9EA734313E0DE10FA0CD9E3C6133E36EA4DB2B7A49BDE9EF019F72796B8E"
    ),
    expected_size=250_177,
)

GESTURE_RECOGNIZER = ModelMetadata(
    filename="gesture_recognizer.task",
    local_path=MODELS_DIR / "gesture_recognizer.task",
    official_url=(
        "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
        "gesture_recognizer/float16/1/gesture_recognizer.task"
    ),
    expected_sha256=(
        "97952348CF6A6A4915C2EA1496B4B37EBABC50CBBF80571435643C455F2B0482"
    ),
    expected_size=8_373_440,
)

HAND_LANDMARKER = ModelMetadata(
    filename="hand_landmarker.task",
    local_path=PROJECT_DIR / "hand_landmarker.task",
    official_url=None,
    expected_sha256=(
        "FBC2A30080C3C557093B5DDFC334698132EB341044CCEE322CCF8BCF3607CDE1"
    ),
    expected_size=7_819_105,
)

MODEL_MANIFEST = {
    model.filename: model
    for model in (SELFIE_SEGMENTER, GESTURE_RECOGNIZER, HAND_LANDMARKER)
}
