"""
GET /restaurants - filter by city and price_category.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models import Restaurant
from backend.schemas import RestaurantResponse

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

VALID_PRICE_CATEGORIES = ("$", "$$", "$$$")


@router.get("", response_model=list[RestaurantResponse])
def list_restaurants(
    city: str = Query(..., description="City name"),
    price_category: str = Query(..., description="Price category: $, $$, or $$$"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: Session = Depends(get_db),
):
    """Return restaurants filtered by city and price_category, ordered by rating DESC."""
    if price_category not in VALID_PRICE_CATEGORIES:
        from fastapi import HTTPException
        raise HTTPException(422, "price_category must be $, $$, or $$$")

    stmt = (
        select(Restaurant)
        .where(Restaurant.city == city, Restaurant.price_category == price_category)
        .order_by(Restaurant.rating.desc().nullslast())
        .limit(limit)
    )
    result = db.execute(stmt)
    restaurants = result.scalars().all()
    return [RestaurantResponse.model_validate(r) for r in restaurants]
