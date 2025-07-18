from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime

from app.db import SessionLocal
from app.models import User, Transaction

router = APIRouter()

def get_db():
    """
    Dependency for getting a SQLAlchemy session. Used by FastAPI Depends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================================
# GET /users/top
# Purpose: Retrieve the top X users by total transaction amount of masks within a date range.
# ============================================================================================
@router.get("/top")
def get_top_users(
    limit: int = Query(5, ge=1, le=100),
    start_date: str = Query(..., description="Format: YYYY-MM-DD"),
    end_date: str = Query(..., description="Format: YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    Query the top N users by transaction amount within a date range.
    - limit: Number of users to return
    - start_date, end_date: Date range
    Returns: Users and their total transaction amount
    """
    # Parse date range
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get top users by total mask transaction amounts within date range
    result = (
        db.query(
            User.id,
            User.name,
            func.sum(Transaction.transaction_amount).label("total_amount")
        )
        .join(Transaction)
        .filter(and_(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ))
        .group_by(User.id)
        .order_by(func.sum(Transaction.transaction_amount).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "user_id": top_user.id,
            "user_name": top_user.name,
            "total_amount": round(top_user.total_amount, 2)
        } 
        for top_user in result
    ]
