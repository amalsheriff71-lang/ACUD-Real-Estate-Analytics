from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

import cohere
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Complaint
from app.districts import DISTRICTS, get_district_label

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

CATEGORY_LABELS = {
    "lighting": "Street lighting",
    "roads": "Roads and pavements",
    "waste": "Waste build-up",
    "water": "Water leak",
    "parking": "Parking violations",
    "noise": "Noise",
    "other": "Other complaint",
}
RESOLVED_STATUSES = {"resolved", "closed", "completed", "complete", "done"}


class AnalyticsFilters(BaseModel):
    from_date: date | None = Field(default=None, alias="from")
    to_date: date | None = Field(default=None, alias="to")
    district: str | None = None
    category: str | None = None
    status: str | None = None

    model_config = {"populate_by_name": True}


class AnalyticsQuestion(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    language: Literal["ar", "en"] = "en"
    filters: AnalyticsFilters = Field(default_factory=AnalyticsFilters)


def _filtered_complaints(db: Session, filters: AnalyticsFilters):
    stmt = select(
        Complaint.category,
        Complaint.district,
        Complaint.status,
        Complaint.created_at,
        Complaint.updated_at,
        Complaint.onset,
    )
    if filters.from_date:
        start = datetime.combine(filters.from_date, time.min, tzinfo=timezone.utc)
        stmt = stmt.where(Complaint.created_at >= start)
    if filters.to_date:
        end = datetime.combine(filters.to_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        stmt = stmt.where(Complaint.created_at < end)
    if filters.district and filters.district.strip():
        district_value = filters.district.strip()

        # Match the stable ID and known labels from older database records.
        district_values = [district_value]
        district = DISTRICTS.get(district_value)

        if district:
            district_values.extend(
                label
                for label in district.values()
                if label and label not in district_values
            )

        stmt = stmt.where(Complaint.district.in_(district_values))
    if filters.category and filters.category.strip():
        category_value = filters.category.strip()
        reverse = {label.lower(): key for key, label in CATEGORY_LABELS.items()}
        category_value = reverse.get(category_value.lower(), category_value)
        stmt = stmt.where(Complaint.category == category_value)
    if filters.status and filters.status.strip():
        stmt = stmt.where(Complaint.status == filters.status.strip())
    stmt = stmt.order_by(Complaint.created_at.asc())
    return db.execute(stmt).all()


def _summary(rows):
    total = len(rows)
    statuses = Counter((r.status or "unknown").lower() for r in rows)
    categories = Counter(r.category or "unknown" for r in rows)
    districts = Counter((r.district or "Unknown") for r in rows)
    weekly = Counter()
    for row in rows:
        created = row.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        week_start = (created.date() - timedelta(days=created.weekday())).isoformat()
        weekly[week_start] += 1
    resolved_count = sum(n for status, n in statuses.items() if status in RESOLVED_STATUSES)
    open_count = total - resolved_count
    return {
        "total_complaints": total,
        "open_complaints": open_count,
        "resolved_complaints": resolved_count,
        "by_status": [{"status": k, "count": v} for k, v in statuses.most_common()],
        "by_category": [
            {"category": CATEGORY_LABELS.get(k, k), "category_code": k, "count": v}
            for k, v in categories.most_common()
        ],
        "by_district": [{"district": k, "count": v} for k, v in districts.most_common()],
        "weekly_counts": [{"week_start": k, "count": v} for k, v in sorted(weekly.items())],
        "data_limitations": [
            "The current database schema does not store a dedicated resolved_at timestamp, so resolution duration and SLA compliance cannot be calculated reliably.",
            "The current database schema does not store satisfaction ratings, so CSAT cannot be calculated.",
        ],
    }


@router.get("/complaints")
def dashboard_complaints(db: Session = Depends(get_db)):
    """Return only non-identifying fields needed by the dashboard; never return name, phone, email, address, or description."""
    rows = _filtered_complaints(db, AnalyticsFilters())
    return {
        "source": "postgresql",
        "count": len(rows),
        "complaints": [
            {
                "category": row.category,
                "district_id": row.district,
                "district": get_district_label(row.district, "en"),
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in rows
        ],
    }


@router.post("/ask")
def ask_about_complaints(payload: AnalyticsQuestion, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.cohere_api_key:
        raise HTTPException(status_code=503, detail="Cohere is not configured. Add COHERE_API_KEY to backend/.env.")

    rows = _filtered_complaints(db, payload.filters)
    summary = _summary(rows)
    filters_applied = payload.filters.model_dump(by_alias=True, mode="json", exclude_none=True)
    system_prompt = (
        "You are an evidence-based operations analyst for the New Administrative Capital complaints dashboard. "
        "Answer in the user's language. Use only the supplied database summary; never invent values. "
        "Lead with a direct answer and cite 2-4 relevant counts or percentages. Clearly label hypotheses. "
        "If there are no rows, say so. Warn that the dataset does not include reliable resolved_at timestamps or satisfaction ratings, "
        "so do not claim to calculate resolution time, SLA compliance, or CSAT. Do not request or reveal personal data. "
        "Keep answers concise unless the user requests a report."
    )
    context = {
        "filters_applied": filters_applied,
        "database_summary": summary,
        "privacy": "Personal identifiers and complaint descriptions were not provided to the model.",
    }
    try:
        client = cohere.ClientV2(api_key=settings.cohere_api_key)
        response = client.chat(
            model=settings.cohere_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Database evidence (JSON):\n" + __import__("json").dumps(context, ensure_ascii=False) + "\n\nQuestion: " + payload.question},
            ],
            temperature=0.2,
            max_tokens=700,
        )
        content = getattr(response.message, "content", None) or []
        answer = "\n".join(part.text for part in content if getattr(part, "text", None)).strip()
        if not answer:
            raise RuntimeError("Cohere returned an empty response")
    except Exception as exc:
        print(f"Cohere analytics error: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail="The analytics assistant is temporarily unavailable.") from exc

    return {"reply": answer, "provider": "cohere", "model": settings.cohere_model, "filters_applied": filters_applied, "evidence": summary}
