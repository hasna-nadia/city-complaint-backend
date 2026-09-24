from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Complaints, Users
from auth import get_current_user


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"]
)


class ComplaintCreate(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=5)
    category: str = Field(min_length=2)
    location: str = Field(min_length=2)
    urgency: str = Field(min_length=2)


class ComplaintUpdate(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=5)
    category: str = Field(min_length=2)
    location: str = Field(min_length=2)
    urgency: str = Field(min_length=2)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post("/")
def create_complaint(
    complaint: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):

    new_complaint = Complaints(
        title=complaint.title,
        description=complaint.description,
        category=complaint.category,
        location=complaint.location,
        urgency=complaint.urgency,
        status="Pending",
        user_id=current_user.id
    )

    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    return {
        "message": "Complaint created successfully",
        "complaint_id": new_complaint.id
    }


@router.get("/my")
def get_my_complaints(
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):

    complaints = db.query(Complaints).filter(
        Complaints.user_id == current_user.id
    ).all()

    return complaints


@router.get("/{complaint_id}")
def get_complaint_by_id(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):

    complaint = db.query(Complaints).filter(
        Complaints.id == complaint_id,
        Complaints.user_id == current_user.id
    ).first()

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return complaint


@router.put("/{complaint_id}")
def update_complaint(
    complaint_id: int,
    complaint_data: ComplaintUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):

    complaint = db.query(Complaints).filter(
        Complaints.id == complaint_id,
        Complaints.user_id == current_user.id
    ).first()

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    complaint.title = complaint_data.title
    complaint.description = complaint_data.description
    complaint.category = complaint_data.category
    complaint.location = complaint_data.location
    complaint.urgency = complaint_data.urgency

    db.commit()
    db.refresh(complaint)

    return {
        "message": "Complaint updated successfully"
    }


@router.delete("/{complaint_id}")
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):

    complaint = db.query(Complaints).filter(
        Complaints.id == complaint_id,
        Complaints.user_id == current_user.id
    ).first()

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    db.delete(complaint)
    db.commit()

    return {
        "message": "Complaint deleted successfully"
    }