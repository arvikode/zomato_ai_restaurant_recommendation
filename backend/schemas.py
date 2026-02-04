"""
Pydantic request/response models for API.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class RestaurantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    city: str
    location: Optional[str] = None
    rating: Optional[float] = None
    cost_for_two: Optional[int] = None
    price_category: Optional[str] = None
    has_online_delivery: Optional[bool] = None
    cuisines: Optional[str] = None


class RecommendationRequest(BaseModel):
    city: str
    price_category: str
    limit: int = 3  # 3-10, validated in router


class RecommendationItem(BaseModel):
    rank: int
    name: str
    location: str
    rating: float
    cost_for_two: int
    online_order: bool
    reason: str


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationItem]
