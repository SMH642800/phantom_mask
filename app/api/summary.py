from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime

from app.db import SessionLocal
from app.models import Transaction, PharmacyMask

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================================
# GET /summary
# Purpose: Calculate the total number of masks and the total transaction value within a date range.
# =========================================
@router.get("")
def get_mask_summary(
    start_date: str = Query(..., description="Format: YYYY-MM-DD"),
    end_date: str = Query(..., description="Format: YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    # Parse date range
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Count transactions
    total_transactions = db.query(func.count(Transaction.id)).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).scalar()

    # Calculate total revenue and total masks sold
    total_result =(
        db.query(
            func.sum(Transaction.transaction_amount).label("total_value"),
            func.sum(Transaction.transaction_amount / PharmacyMask.price).label("total_quantity")
        )
        .join(PharmacyMask,
              (Transaction.pharmacy_id == PharmacyMask.pharmacy_id) &
              (Transaction.mask_id == PharmacyMask.mask_id))
        .filter(and_(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ))
        .first()
    )

    return {
        "total_transactions": total_transactions,
        "total_masks_sold": int(total_result.total_quantity or 0),
        "total_value": round(total_result.total_value or 0.0, 2)
    }