from fastapi import APIRouter, Query, Depends, Path, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db import SessionLocal
from app.models import Pharmacy, OpeningHour, PharmacyMask, Mask

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# List all pharmacies open at a specific time and on a day of the week
@router.get("/open")
def get_open_pharmacies(
    weekday: str = Query(..., example="Mon"),
    time_str: str = Query(..., example="08:30"),
    db: Session = Depends(get_db)
):
    try:
        query_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM.")

    pharmacies = db.query(Pharmacy).join(OpeningHour).filter(
        OpeningHour.day_of_week == weekday,
        ((OpeningHour.start_time <= OpeningHour.end_time) &
         (OpeningHour.start_time <= query_time) &
         (OpeningHour.end_time > query_time))
        |
        ((OpeningHour.start_time > OpeningHour.end_time) &
         ((query_time >= OpeningHour.start_time) | (query_time < OpeningHour.end_time)))
    ).all()

    return [
        {"pharmacy_id": pharmacy.id, "pharmacy_name": pharmacy.name, "cash_balance": pharmacy.cash_balance} for pharmacy in pharmacies
    ]

# List all masks sold by a given pharmacy, sorted by mask name or price
@router.get("/{pharmacy_name}/masks")
def get_pharmacy_masks_by_pharmacy_name(
    pharmacy_name: str = Path(..., description="Pharymacy Name"),
    sort_by: str = Query("name", enum=["name", "price"]),
    db: Session = Depends(get_db)
):
    # Look up the pharmacy by name
    pharmacy = db.query(Pharmacy).filter_by(name=pharmacy_name).first()
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    # Query masks for that pharmacy
    pharmacy_masks = db.query(PharmacyMask).join(Mask).filter(
        PharmacyMask.pharmacy == pharmacy
    )

    if sort_by == "name":
        pharmacy_masks = pharmacy_masks.order_by(Mask.name)
    elif sort_by == "price":
        pharmacy_masks = pharmacy_masks.order_by(PharmacyMask.price)
    
    results = pharmacy_masks.all()

    return [
        {
            "mask_id": pharmacyMask.id,
            "mask_name": pharmacyMask.mask.name,
            "price": pharmacyMask.price
        }
        for pharmacyMask in results
    ]

# List all pharmacies with more or fewer than x mask products within a specific price range
@router.get("/filter_by_mask_count")
def filter_pharmacies_by_mask_count(
    min_price: float = Query(..., ge=0),
    max_price: float = Query(..., ge=0),
    count: int = Query(..., ge=0),
    comparison: str = Query(..., enum=["more", "fewer"]),
    db: Session = Depends(get_db)
):
    # Handle unexcepted error
    if min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price must be less than or equal to max_price")
    if comparison not in ["more", "fewer"]:
        raise HTTPException(status_code=400, detail="comparison must be 'more' or 'fewer'")
    if count < 0:
        raise HTTPException(status_code=400, detail="count must be >= 0")
    
    # Build a subquery that counts qualifying masks per pharmacy
    mask_count_subquery = (
        db.query(
            PharmacyMask.pharmacy_id,
            func.count(PharmacyMask.id).label("mask_count")
        )
        .filter(PharmacyMask.price >= min_price, PharmacyMask.price <= max_price)
        .group_by(PharmacyMask.pharmacy_id)
        .subquery()
    )

    # Apply comparison to filter pharmacy IDs
    if comparison == "more":
        filter_condition = mask_count_subquery.c.mask_count >= count
    else:
        filter_condition = mask_count_subquery.c.mask_count <= count

    # Get pharmacies matching condition
    matched_pharmacies = (
        db.query(Pharmacy)
        .join(mask_count_subquery, Pharmacy.id == mask_count_subquery.c.pharmacy_id)
        .filter(filter_condition)
        .all()
    )

    # For each matched pharmacy, get its masks in the price range
    result = []
    for pharmacy in matched_pharmacies:
        masks = [
            {
                "mask_id": pharmacy_mask.id,
                "mask_name": pharmacy_mask.mask.name,
                "price": pharmacy_mask.price
            }
            for pharmacy_mask in pharmacy.masks
            if min_price <= pharmacy_mask.price <= max_price
        ]
        result.append({
            "pharmacy_id": pharmacy.id,
            "pharmacy_name": pharmacy.name,
            "Mask": masks
        })

    if not result:
        return {
            "message": "No pharmacies matched the condition.",
            "data": []
        }
    else:
        return {
            "message": "Filtered pharmacies retrieved successfully.",
            "data": result
        }
