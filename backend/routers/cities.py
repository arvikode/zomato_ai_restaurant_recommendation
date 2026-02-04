"""
GET /cities - distinct sorted city list.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models import Restaurant

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("", response_model=list[str])
def list_cities(db: Session = Depends(get_db)):
    """Return distinct sorted list of cities."""
    stmt = select(Restaurant.city).distinct().order_by(Restaurant.city)
    result = db.execute(stmt)
    return [row[0] for row in result.fetchall()]
