from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import httpx

from app.core.config import settings


class ModelClientError(Exception):
    """Raised when the external model endpoint cannot produce a usable response."""


MASK_FILENAME = "segmentation_mask.nii.gz"


@dataclass
class ModelClientResponse:
    response_type: Literal["binary"]
    file_path: str | None = None


def call_model_endpoint(
    t1_path: str | Path,
    t1ce_path: str | Path,
    t2_path: str | Path,
    flair_path: str | Path,
    output_dir: str | Path,
) -> ModelClientResponse:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    opened_files = []
    try:
        files = {}
        for field_name, file_path in {
            "t1": t1_path,
            "t1ce": t1ce_path,
            "t2": t2_path,
            "flair": flair_path,
        }.items():
            path = Path(file_path)
            handle = path.open("rb")
            opened_files.append(handle)
            files[field_name] = (path.name, handle, "application/gzip")

        timeout = httpx.Timeout(float(settings.MODEL_REQUEST_TIMEOUT_SECONDS))
        with httpx.Client(timeout=timeout) as client:
            response = client.post(settings.MODEL_ENDPOINT_URL, files=files)

        if not 200 <= response.status_code < 300:
            raise ModelClientError(_model_error_message(response))

        if not response.content:
            raise ModelClientError("Model service returned an empty segmentation mask.")

        content_type = response.headers.get("content-type", "").lower()
        if "gzip" not in content_type and not response.content.startswith(b"\x1f\x8b"):
            raise ModelClientError(
                "Model service returned an unexpected response type; "
                "expected application/gzip .nii.gz mask."
            )

        saved_path = output_path / MASK_FILENAME
        saved_path.write_bytes(response.content)
        return ModelClientResponse(response_type="binary", file_path=str(saved_path))

    except httpx.TimeoutException as exc:
        raise ModelClientError(
            "Model service timed out while generating the segmentation mask."
        ) from exc
    except httpx.RequestError as exc:
        raise ModelClientError(
            "Model service is unavailable; could not reach the prediction endpoint."
        ) from exc
    finally:
        for handle in opened_files:
            handle.close()


def _model_error_message(response: httpx.Response) -> str:
    if response.status_code == 422:
        return (
            "Model service returned HTTP 422; one or more required MRI files may be missing."
        )
    if response.status_code == 500:
        return (
            "Model service returned HTTP 500; MRI files may be invalid or dimension-mismatched."
        )

    body = response.text.strip()
    if not body:
        body = "No response body."
    return f"Model service returned HTTP {response.status_code}: {body[:500]}"
