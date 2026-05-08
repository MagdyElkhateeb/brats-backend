from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CaseResult(Base):
    __tablename__ = "case_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    mask_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    slices_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    overlays_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    total_tumor_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    edema_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    enhancing_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    non_enhancing_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    case = relationship("Case", back_populates="result")
