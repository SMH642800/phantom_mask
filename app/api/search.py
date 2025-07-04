from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from difflib import SequenceMatcher

from app.db import SessionLocal
from app.models import Pharmacy, Mask, PharmacyMask

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

def calculate_relevance_score(search_term: str, target_text: str) -> float:
    """
    Calculate the relevance score between the search term and target text (exact match, startswith, contains, fuzzy match).
    """
    if not search_term or not target_text:
        return 0.0
    
    search_lower = search_term.lower()
    target_lower = target_text.lower()

    # Exact math gets highest score
    if search_lower == target_lower:
        return 1.0
    
    # Starts with search term gets high score
    if target_lower.startswith(search_lower):
        return 0.9
    
    # Contains search term gets medium score
    if search_lower in target_lower:
        return 0.7
    
    # Use sequence matcher for fuzzy matching
    similarity = SequenceMatcher(None, search_lower, target_lower).ratio()

    return max(0.0, similarity) if similarity > 0.3 else 0.0

# ============================================================================================
# GET /search?query_name=...&search_type=pharmacy|mask
# Purpose: Search for pharmacies or masks by name and rank the results by relevance to the search term
# ============================================================================================
@router.get("")
def search_items(
    query_name: str = Query(..., min_length=1),
    search_type: str = Query(..., enum=["pharmacy", "mask"]),
    db: Session = Depends(get_db)
):
    """
    Search for pharmacies or masks by name and rank by relevance.
    - query_name: Search keyword
    - search_type: 'pharmacy' or 'mask'
    Returns: List of relevant results
    """
    keyword = query_name.lower()
    results = []

    if search_type == "pharmacy":
        pharmacies = db.query(Pharmacy).all()

        for pharmacy in pharmacies:
            pharmacy_name = pharmacy.name.lower()
            pharmacy_name_score = calculate_relevance_score(keyword, pharmacy_name)

            if pharmacy_name_score > 0:
                # Opening hours
                opening_hours = [
                    f"{hour.day_of_week} {hour.start_time.strftime('%H:%M')} - {hour.end_time.strftime('%H:%M')}"
                    for hour in pharmacy.opening_hours
                ]

                # Masks
                masks = [
                    {
                        "mask_id": pharmacy_mask.mask.id,
                        "mask_name": pharmacy_mask.mask.name,
                        "price": pharmacy_mask.price
                    }
                    for pharmacy_mask in pharmacy.masks
                ]

                results.append({
                    "pharmacy_id": pharmacy.id,
                    "pharmacy_name": pharmacy.name,
                    "cashBalance": pharmacy.cash_balance,
                    "openingHours": opening_hours,
                    "masks": masks,
                    "relevanceScore": pharmacy_name_score
                })

    elif search_type == "mask":
        pharmacy_masks = db.query(PharmacyMask).join(Mask).join(Pharmacy).all()

        for pharmacy_mask in pharmacy_masks:
            mask_name = pharmacy_mask.mask.name.lower()
            mask_name_score = calculate_relevance_score(keyword, mask_name)

            if mask_name_score > 0:
                # Pharmacy info
                pharmacy = pharmacy_mask.pharmacy
                opening_hours = [
                    f"{hour.day_of_week} {hour.start_time.strftime('%H:%M')} - {hour.end_time.strftime('%H:%M')}"
                    for hour in pharmacy.opening_hours
                ]

                results.append({
                    "mask_id": pharmacy_mask.mask.id,
                    "mask_name": pharmacy_mask.mask.name,
                    "mask_price": pharmacy_mask.price,
                    "pharmacy": {
                        "pharmacy_id": pharmacy.id,
                        "pharmacy_name": pharmacy.name,
                        "cashBalance": pharmacy.cash_balance,
                        "openingHours": opening_hours
                    },
                    "relevanceScore": mask_name_score
                })
        
    # Sort by relevance descending
    results.sort(key=lambda result: result["relevanceScore"], reverse=True)

    if not results:
        return {
            "message": "No results found.",
            "data": []
        }
    else:
        return {
            "message": "Search successfully.",
            "data": results
        }
