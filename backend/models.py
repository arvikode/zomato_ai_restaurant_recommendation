"""
SQLAlchemy models matching Phase 1 schema.
Uses JSON (not JSONB) for SQLite compatibility.
"""

from sqlalchemy import Column, Integer, Float, Boolean, Text, CheckConstraint, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    city = Column(Text, nullable=False)
    location = Column(Text)
    rating = Column(Float)
    cost_for_two = Column(Integer)
    price_category = Column(Text, CheckConstraint("price_category IN ('$', '$$', '$$$')"))
    has_online_delivery = Column(Boolean)
    cuisines = Column(Text)
    raw_data = Column(JSON)
