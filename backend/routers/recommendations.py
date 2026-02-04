"""
POST /recommendations - AI-ranked restaurant recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models import Restaurant
from backend.schemas import RecommendationRequest, RecommendationItem, RecommendationResponse
from backend.llm.client import rank_restaurants

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

VALID_PRICE_CATEGORIES = ("$", "$$", "$$$")
LIMIT_MIN, LIMIT_MAX = 3, 10


def _restaurant_to_dict(r: Restaurant) -> dict:
    """Convert Restaurant model to dict for LLM prompt."""
    return {
        "name": r.name,
        "city": r.city,
        "location": r.location,
        "rating": r.rating,
        "cost_for_two": r.cost_for_two,
        "has_online_delivery": r.has_online_delivery or False,
        "cuisines": r.cuisines,
    }


@router.post("", response_model=RecommendationResponse)
def get_recommendations(
    body: RecommendationRequest,
    db: Session = Depends(get_db),
):
    """
    Get AI-ranked restaurant recommendations.
    Queries top 20 by rating, passes to Grok for ranking and explanation.
    """
    if body.price_category not in VALID_PRICE_CATEGORIES:
        raise HTTPException(422, "price_category must be $, $$, or $$$")
    if not (LIMIT_MIN <= body.limit <= LIMIT_MAX):
        raise HTTPException(422, f"limit must be between {LIMIT_MIN} and {LIMIT_MAX}")

    stmt = (
        select(Restaurant)
        .where(
            Restaurant.city == body.city,
            Restaurant.price_category == body.price_category,
        )
        .order_by(Restaurant.rating.desc().nullslast())
        .limit(20)
    )
    result = db.execute(stmt)
    restaurants = result.scalars().all()

    if not restaurants:
        raise HTTPException(404, "No restaurants found for the given city and price category")

    restaurant_dicts = [_restaurant_to_dict(r) for r in restaurants]
    llm_result = rank_restaurants(
        restaurant_dicts,
        body.city,
        body.price_category,
        body.limit,
    )

    if "error" in llm_result:
        raise HTTPException(503, llm_result["error"])

    raw_recs = llm_result.get("recommendations", [])[: body.limit]
    valid_names = {r["name"] for r in restaurant_dicts}

    recommendations = []
    for rec in raw_recs:
        if not isinstance(rec, dict):
            continue
        name = rec.get("name")
        if name and name not in valid_names:
            continue  # LLM invented a restaurant - skip
        try:
            item = RecommendationItem(
                rank=rec.get("rank", 0),
                name=rec.get("name", ""),
                location=rec.get("location", ""),
                rating=float(rec.get("rating", 0)),
                cost_for_two=int(rec.get("cost_for_two", 0)),
                online_order=bool(rec.get("online_order", False)),
                reason=rec.get("reason", ""),
            )
            recommendations.append(item)
        except (TypeError, ValueError):
            continue

    if not recommendations:
        raise HTTPException(503, "Could not parse valid recommendations from LLM response")

    return RecommendationResponse(recommendations=recommendations)
