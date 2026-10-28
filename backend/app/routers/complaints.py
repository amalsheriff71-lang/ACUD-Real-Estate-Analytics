from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Complaint
from app.schemas import ComplaintCreate, ComplaintCreated, ComplaintLookup, ComplaintStatus

router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintCreated, status_code=status.HTTP_201_CREATED)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    if not payload.consent:
        raise HTTPException(status_code=422, detail="Consent is required to submit a complaint.")

    complaint = Complaint(**payload.model_dump())
    db.add(complaint)
    try:
        db.commit()
        db.refresh(complaint)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save the complaint. Please try again.")

    message = (
        f"تم استلام بيانات الشكوى تجريبياً. رقم المتابعة: {complaint.reference_number}"
        if payload.language == "ar"
        else f"Complaint recorded. Reference number: {complaint.reference_number}"
    )
    return ComplaintCreated(
        reference_number=complaint.reference_number,
        status=complaint.status,
        created_at=complaint.created_at,
        message=message,
    )


@router.post("/lookup", response_model=ComplaintStatus)
def lookup_complaint(payload: ComplaintLookup, db: Session = Depends(get_db)):
    # Require both reference number and phone number; do not expose public listing.
    complaint = db.query(Complaint).filter(
        Complaint.reference_number == payload.reference_number.strip().upper(),
        Complaint.phone == payload.phone.strip(),
    ).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found. Check the reference number and phone number.")

    return ComplaintStatus(
        reference_number=complaint.reference_number,
        category=complaint.category,
        district=complaint.district,
        status=complaint.status,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
    )
