from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SequenceType(str, enum.Enum):
    T1 = "T1"
    T1CE = "T1CE"
    T2 = "T2"
    FLAIR = "FLAIR"


class CaseFile(Base):
    __tablename__ = "case_files"
    __table_args__ = (
        UniqueConstraint("case_id", "sequence_type", name="uq_case_file_sequence"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sequence_type: Mapped[SequenceType] = mapped_column(
        Enum(SequenceType, name="sequence_type"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    case = relationship("Case", back_populates="files")
