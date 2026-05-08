from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    patient_code: str = Field(min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    patient_code: str | None = Field(default=None, min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class PatientRead(PatientBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
