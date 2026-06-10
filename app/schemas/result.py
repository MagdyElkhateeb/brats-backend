from pydantic import BaseModel

from app.models.case import CaseStatus


class ResultModalities(BaseModel):
    t1: str | None
    t1ce: str | None
    t2: str | None
    flair: str | None


class ResultRead(BaseModel):
    case_id: int
    status: CaseStatus
    total_tumor_volume: float | None
    edema_volume: float | None
    enhancing_volume: float | None
    non_enhancing_volume: float | None
    mask_url: str | None
    modalities: ResultModalities
    slices: list[str]
    overlays: list[str]
