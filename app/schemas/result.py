from pydantic import BaseModel

from app.models.case import CaseStatus


class ResultRead(BaseModel):
    case_id: int
    status: CaseStatus
    total_tumor_volume: float | None
    edema_volume: float | None
    enhancing_volume: float | None
    non_enhancing_volume: float | None
    mask_url: str | None
    slices: list[str]
    overlays: list[str]
