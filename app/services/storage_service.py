import re
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


def get_storage_root() -> Path:
    return Path(settings.STORAGE_ROOT)


def get_case_input_dir(case_id: int) -> Path:
    return get_storage_root() / "cases" / str(case_id) / "input"


def get_case_results_dir(case_id: int) -> Path:
    return get_storage_root() / "cases" / str(case_id) / "results"


def ensure_results_dir(case_id: int) -> Path:
    output_dir = get_case_results_dir(case_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def is_nii_gz_filename(filename: str) -> bool:
    return filename.lower().endswith(".nii.gz")


def sanitize_filename(filename: str) -> str:
    name = filename.replace("\\", "/").split("/")[-1].strip()
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name or "file.bin"


async def save_upload_file(case_id: int, sequence_field: str, upload_file: UploadFile) -> Path:
    input_dir = get_case_input_dir(case_id)
    input_dir.mkdir(parents=True, exist_ok=True)

    target_path = input_dir / f"{sequence_field.lower()}.nii.gz"
    with target_path.open("wb") as buffer:
        while chunk := await upload_file.read(1024 * 1024):
            buffer.write(chunk)
    await upload_file.close()
    return target_path


def path_to_storage_url(path: str | Path) -> str:
    storage_root = get_storage_root().resolve()
    file_path = Path(path).resolve()
    relative_path = file_path.relative_to(storage_root)
    return "/storage/" + relative_path.as_posix()
