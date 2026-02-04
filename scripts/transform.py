"""
Pure transformation functions for Zomato dataset normalization.
Designed for testability without DB or external API calls.
"""

from typing import Optional


def normalize_city(raw: Optional[str]) -> Optional[str]:
    """
    Normalize city: trim, title-case, Bengaluru -> Bangalore.
    Returns None if city is null or empty (row should be skipped).
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    s = s.title()
    if s == "Bengaluru":
        return "Bangalore"
    return s


def normalize_rating(raw: Optional[str]) -> Optional[float]:
    """
    Parse rating from formats like '4.1/5' or '4.1'.
    Returns None if missing or invalid.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        # Handle "4.1/5" format
        if "/" in s:
            s = s.split("/")[0].strip()
        return float(s)
    except (ValueError, TypeError):
        return None


def normalize_cost(raw: Optional[str]) -> Optional[int]:
    """
    Parse cost from formats like '800' or '800, 900'.
    Returns None if missing or zero.
    Takes first value when comma-separated.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # Handle "800, 900" - take first value
    if "," in s:
        s = s.split(",")[0].strip()
    # Remove any non-digit chars (e.g. currency symbols)
    s = "".join(c for c in s if c.isdigit())
    if not s:
        return None
    try:
        val = int(s)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None


def derive_price_category(cost: Optional[int]) -> Optional[str]:
    """
    Derive price category from cost_for_two.
    < 500 -> $, 500-1500 -> $$, > 1500 -> $$$.
    Returns None if cost is None (row should be skipped).
    """
    if cost is None:
        return None
    if cost < 500:
        return "$"
    if cost <= 1500:
        return "$$"
    return "$$$"


def normalize_online_order(raw: Optional[str]) -> bool:
    """
    Convert Yes/No to boolean. Default False if invalid.
    """
    if raw is None:
        return False
    s = str(raw).strip().lower()
    return s == "yes"


def normalize_cuisines(raw: Optional[str]) -> Optional[str]:
    """
    Trim cuisines. Return None if empty.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def normalize_location(raw: Optional[str]) -> Optional[str]:
    """
    Trim location (area/locality).
    """
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def normalize_name(raw: Optional[str]) -> Optional[str]:
    """
    Trim restaurant name. Required field - return None if empty.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


# HuggingFace dataset column names
COL_NAME = "name"
COL_LISTED_IN_CITY = "listed_in(city)"
COL_LOCATION = "location"
COL_RATE = "rate"
COL_APPROX_COST = "approx_cost(for two people)"
COL_ONLINE_ORDER = "online_order"
COL_CUISINES = "cuisines"


def transform_row(row: dict) -> dict | None:
    """
    Transform a single dataset row into DB record.
    Returns None if row should be skipped.
    """
    city = normalize_city(row.get(COL_LISTED_IN_CITY))
    if city is None:
        return None

    name = normalize_name(row.get(COL_NAME))
    if name is None:
        return None

    cost = normalize_cost(row.get(COL_APPROX_COST))
    price_category = derive_price_category(cost)
    if price_category is None:
        return None

    return {
        "name": name,
        "city": city,
        "location": normalize_location(row.get(COL_LOCATION)),
        "rating": normalize_rating(row.get(COL_RATE)),
        "cost_for_two": cost,
        "price_category": price_category,
        "has_online_delivery": normalize_online_order(row.get(COL_ONLINE_ORDER)),
        "cuisines": normalize_cuisines(row.get(COL_CUISINES)),
        "raw_data": row,  # Caller will serialize to JSON
    }
