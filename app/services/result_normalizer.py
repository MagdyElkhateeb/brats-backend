from pathlib import Path
from typing import Any

from app.services.storage_service import path_to_storage_url


def empty_normalized_result() -> dict[str, Any]:
    return {
        "mask_url": None,
        "slices": [],
        "overlays": [],
        "total_tumor_volume": None,
        "edema_volume": None,
        "enhancing_volume": None,
        "non_enhancing_volume": None,
    }


def normalize_binary_result(saved_file_path: str | Path) -> dict[str, Any]:
    normalized = empty_normalized_result()
    normalized["mask_url"] = path_to_storage_url(saved_file_path)
    return normalized
