"""Download and verify the model files used by VanishCam."""

from __future__ import annotations

import argparse
import hashlib
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from models_manifest import MODEL_MANIFEST, ModelMetadata


ALLOWED_MODEL_HOST = "storage.googleapis.com"
DOWNLOAD_CHUNK_SIZE = 256 * 1024
PREPARATION_USER_AGENT = "VanishCam-Model-Preparation/1.0"


class ModelPreparationError(RuntimeError):
    pass


def _validate_download_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_MODEL_HOST
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        raise ModelPreparationError(
            f"URL modello non autorizzato; e' consentito solo HTTPS su "
            f"{ALLOWED_MODEL_HOST}: {url}"
        )


class RestrictedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        try:
            _validate_download_url(new_url)
        except ModelPreparationError as error:
            raise urllib.error.HTTPError(
                request.full_url, code, str(error), headers, file_pointer
            ) from error
        return super().redirect_request(
            request, file_pointer, code, message, headers, new_url
        )


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(DOWNLOAD_CHUNK_SIZE):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest().upper(), size


def verify_existing_model(model: ModelMetadata) -> tuple[bool, str]:
    if not model.local_path.is_file():
        return False, f"file mancante: {model.local_path}"
    if model.expected_sha256 is None:
        return False, "SHA-256 atteso ancora da stabilire"

    actual_hash, actual_size = _hash_file(model.local_path)
    if model.expected_size is not None and actual_size != model.expected_size:
        return False, (
            f"dimensione non valida: {actual_size} byte; "
            f"attesi {model.expected_size}"
        )
    if actual_hash != model.expected_sha256.upper():
        return False, (
            f"SHA-256 non valido: {actual_hash}; "
            f"atteso {model.expected_sha256.upper()}"
        )
    return True, f"SHA-256 verificato: {actual_hash}"


def download_and_verify_model(model: ModelMetadata) -> None:
    if model.expected_sha256 is None:
        raise ModelPreparationError(
            f"{model.filename}: SHA-256 atteso non ancora stabilito; download vietato"
        )
    if model.official_url is None:
        raise ModelPreparationError(
            f"{model.filename}: nessuna URL di download autorizzata"
        )

    _validate_download_url(model.official_url)
    destination = model.local_path
    temporary = destination.with_suffix(destination.suffix + ".part")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary.unlink(missing_ok=True)

    print(f"[Modelli] Scarico {model.filename} da {model.official_url}")
    digest = hashlib.sha256()
    received = 0
    declared_size = None
    try:
        request = urllib.request.Request(
            model.official_url, headers={"User-Agent": PREPARATION_USER_AGENT}
        )
        opener = urllib.request.build_opener(RestrictedRedirectHandler())
        with opener.open(request, timeout=60) as response:
            _validate_download_url(response.geturl())
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                declared_size = int(content_length)
            with temporary.open("wb") as output:
                while chunk := response.read(DOWNLOAD_CHUNK_SIZE):
                    output.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)

        if declared_size is not None and received != declared_size:
            raise ModelPreparationError(
                f"{model.filename}: ricevuti {received} byte; "
                f"Content-Length dichiarava {declared_size}"
            )
        if model.expected_size is not None and received != model.expected_size:
            raise ModelPreparationError(
                f"{model.filename}: ricevuti {received} byte; "
                f"attesi {model.expected_size}"
            )
        actual_hash = digest.hexdigest().upper()
        if actual_hash != model.expected_sha256.upper():
            raise ModelPreparationError(
                f"{model.filename}: SHA-256 {actual_hash}; "
                f"atteso {model.expected_sha256.upper()}"
            )
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    print(f"[Modelli] Verificato {model.filename}: {actual_hash}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepara e verifica i modelli locali di VanishCam."
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verifica i file esistenti senza effettuare download.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failed = False
    for model in MODEL_MANIFEST.values():
        valid, detail = verify_existing_model(model)
        if valid:
            print(f"[Modelli] OK {model.filename}: {detail}")
            continue

        print(f"[Modelli] NON VERIFICATO {model.filename}: {detail}")
        if args.verify_only:
            failed = True
            continue
        try:
            download_and_verify_model(model)
        except (
            ModelPreparationError, OSError, ValueError, urllib.error.URLError
        ) as error:
            print(f"[Modelli] ERRORE {error}")
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
