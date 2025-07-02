from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone

from app.db import SessionLocal
from app.models import User, Pharmacy, Mask, PharmacyMask, Transaction

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Pydantic input model
# ---------------------------
class PurchaseItem(BaseModel):
    pharmacy_name: str
    mask_name: str
    quantity: int

class PurchaseRequest(BaseModel):
    user_name: str
    items: List[PurchaseItem]

# ---------------------------
# POST /purchase
# ---------------------------
@router.post("")
def purchase_masks(
    data: PurchaseRequest,
    db: Session = Depends(get_db)
):
    # Step 1: Validate user
    user = db.query(User).filter_by(name=data.user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_cost = 0.0
    transactions = []

    try:
        # Step 2: Validate each item and calculate cost
        for item in data.items:
            pharmacy = db.query(Pharmacy).filter_by(name=item.pharmacy_name).first()
            if not pharmacy:
                raise HTTPException(status_code=404, detail=f"Pharmacy '{item.pharmacy_name}' not found")
            
            mask = db.query(Mask).filter_by(name=item.mask_name).first()
            if not mask:
                raise HTTPException(status_code=404, detail=f"Mask '{item.mask_name}' not found")
            
            pharmacy_mask = db.query(PharmacyMask).filter_by(pharmacy_id=pharmacy.id, mask_id=mask.id).first()
            if not pharmacy_mask:
                raise HTTPException(status_code=404, detail=f"Mask '{mask.name}' not sold by '{pharmacy.name}'")
            
            cost = item.quantity * pharmacy_mask.price
            total_cost += cost

            transactions.append({
                "user_id": user.id,
                "pharmacy_id": pharmacy.id,
                "mask_id": mask.id,
                "transaction_amount": cost
            })
        
        # Step 3: Check user balance
        if total_cost > user.cash_balance:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Step 4: Process purchase (atomic)
        user.cash_balance -= total_cost
        for transaction in transactions:
            # Add money to the pharmacy
            pharmacy = db.query(Pharmacy).get(transaction["pharmacy_id"])
            pharmacy.cash_balance += transaction["transaction_amount"]

            # Record the transaction
            transaction_data = Transaction(
                user_id=transaction["user_id"],
                pharmacy_id=transaction["pharmacy_id"],
                mask_id=transaction["mask_id"],
                transaction_amount=transaction["transaction_amount"],
                transaction_date=datetime.now(timezone.utc)
            )
            db.add(transaction_data)
        
        db.commit()

        return {
            "user_id": user.id,
            "user_name": user.name,
            "total_amount": round(total_cost, 2),
            "message": "Purchase completed susccessfully"
        }
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")
