from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        Index("ix_complaints_phone_reference", "phone", "reference_number"),
        Index("ix_complaints_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    reference_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, default=lambda: f"CAP-{uuid4().hex[:10].upper()}"
    )
    language: Mapped[str] = mapped_column(String(2), default="ar")
    full_name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(40), index=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    district: Mapped[str] = mapped_column(String(180))
    address: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    onset: Mapped[str] = mapped_column(String(30))
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="received", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
