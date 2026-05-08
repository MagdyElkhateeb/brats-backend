from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.case import CaseStatus


class CaseCreate(BaseModel):
    patient_id: int
    title: str = Field(min_length=1, max_length=255)
    scan_date: date | None = None


class CaseRead(BaseModel):
    id: int
    user_id: int
    patient_id: int
    title: str
    scan_date: date | None
    status: CaseStatus
    task_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseStatusRead(BaseModel):
    case_id: int
    status: CaseStatus
    task_id: str | None
    error_message: str | None
