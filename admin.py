from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date, datetime, time

from database import SessionLocal
from models import Complaints, Users
from auth import get_current_user


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


class StatusUpdate(BaseModel):
    status: str


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def get_admin_user(
    current_user: Users = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


@router.get("/complaints")
def get_all_complaints(
    search: str = None,
    category: str = None,
    status: str = None,
    start_date: date = None,
    end_date: date = None,
    sort: str = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    admin_user: Users = Depends(get_admin_user)
):

    query = db.query(Complaints)

    if search:
        query = query.filter(
            Complaints.title.contains(search)
        )

    if category:
        query = query.filter(
            Complaints.category == category
        )

    if status:
        query = query.filter(
            Complaints.status == status
        )

    if start_date:
        start_datetime = datetime.combine(
            start_date,
            time.min
        )

        query = query.filter(
            Complaints.created_at >= start_datetime
        )

    if end_date:
        end_datetime = datetime.combine(
            end_date,
            time.max
        )

        query = query.filter(
            Complaints.created_at <= end_datetime
        )

    if sort == "alphabetical":
        query = query.order_by(
            Complaints.title.asc()
        )
    else:
        query = query.order_by(
            Complaints.created_at.desc()
        )

    total = query.count()

    complaints = query.offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": complaints
    }


@router.put("/complaints/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    status_data: StatusUpdate,
    db: Session = Depends(get_db),
    admin_user: Users = Depends(get_admin_user)
):

    complaint = db.query(Complaints).filter(
        Complaints.id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    complaint.status = status_data.status

    db.commit()
    db.refresh(complaint)

    return {
        "message": "Complaint status updated successfully"
    }