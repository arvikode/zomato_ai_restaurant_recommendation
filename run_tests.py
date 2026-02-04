#!/usr/bin/env python3
"""
Simple test runner when pytest is not available.
Run: python run_tests.py
"""
import sys
sys.path.insert(0, ".")

def run_transform_tests():
    from scripts.transform import (
        normalize_city,
        normalize_rating,
        normalize_cost,
        derive_price_category,
        normalize_online_order,
        normalize_cuisines,
        normalize_location,
        normalize_name,
    )
    errors = []

    # normalize_city
    assert normalize_city("  Bangalore  ") == "Bangalore"
    assert normalize_city("Bengaluru") == "Bangalore"
    assert normalize_city(None) is None
    assert normalize_city("") is None

    # normalize_rating
    assert normalize_rating("4.1/5") == 4.1
    assert normalize_rating(None) is None
    assert normalize_rating("invalid") is None

    # normalize_cost
    assert normalize_cost("800") == 800
    assert normalize_cost("800, 900") == 800
    assert normalize_cost(None) is None
    assert normalize_cost("0") is None

    # derive_price_category
    assert derive_price_category(100) == "$"
    assert derive_price_category(800) == "$$"
    assert derive_price_category(2000) == "$$$"
    assert derive_price_category(None) is None

    # normalize_online_order
    assert normalize_online_order("Yes") is True
    assert normalize_online_order("No") is False
    assert normalize_online_order(None) is False

    # normalize_cuisines, location, name
    assert normalize_cuisines("  North Indian  ") == "North Indian"
    assert normalize_location("Banashankari") == "Banashankari"
    assert normalize_name("Jalsa") == "Jalsa"
    assert normalize_name("") is None

    print("transform.py: all tests passed")


def run_ingest_tests():
    from scripts.transform import transform_row

    COL_NAME = "name"
    COL_LISTED_IN_CITY = "listed_in(city)"
    COL_APPROX_COST = "approx_cost(for two people)"

    row = {
        COL_NAME: "Jalsa",
        COL_LISTED_IN_CITY: "Banashankari",
        "location": "Banashankari",
        "rate": "4.1/5",
        COL_APPROX_COST: "800",
        "online_order": "Yes",
        "cuisines": "North Indian",
    }
    result = transform_row(row)
    assert result is not None
    assert result["name"] == "Jalsa"
    assert result["city"] == "Banashankari"
    assert result["price_category"] == "$$"

    assert transform_row({COL_NAME: "", COL_LISTED_IN_CITY: "B", COL_APPROX_COST: "500"}) is None
    assert transform_row({COL_NAME: "X", COL_LISTED_IN_CITY: None, COL_APPROX_COST: "500"}) is None
    assert transform_row({COL_NAME: "X", COL_LISTED_IN_CITY: "B", COL_APPROX_COST: None}) is None

    print("ingest transform_row: all tests passed")


def run_backend_tests():
    from unittest.mock import MagicMock
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.database import get_db
    from backend.models import Restaurant

    client = TestClient(app)

    def override_get_db(mock_session):
        def _override():
            yield mock_session
        return _override

    # Root
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # Cities
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [("Bangalore",), ("Mumbai",)]
    mock_session = MagicMock()
    mock_session.execute.return_value = mock_result
    app.dependency_overrides[get_db] = override_get_db(mock_session)
    try:
        r = client.get("/cities")
        assert r.status_code == 200
        assert r.json() == ["Bangalore", "Mumbai"]
    finally:
        app.dependency_overrides.clear()

    # Restaurants - valid
    mock_rest = Restaurant(
        id=1, name="Jalsa", city="Bangalore", location="Banashankari",
        rating=4.1, cost_for_two=800, price_category="$$",
        has_online_delivery=True, cuisines="North Indian", raw_data=None,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_rest]
    mock_session = MagicMock()
    mock_session.execute.return_value = mock_result
    app.dependency_overrides[get_db] = override_get_db(mock_session)
    try:
        r = client.get("/restaurants?city=Bangalore&price_category=$$")
        assert r.status_code == 200
        assert r.json()[0]["name"] == "Jalsa"
    finally:
        app.dependency_overrides.clear()

    # Restaurants - invalid price_category (override needed since get_db runs first)
    mock_session = MagicMock()
    app.dependency_overrides[get_db] = override_get_db(mock_session)
    try:
        r = client.get("/restaurants?city=Bangalore&price_category=invalid")
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()

    print("backend API: all tests passed")


def run_recommendations_tests():
    from unittest.mock import MagicMock, patch
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.database import get_db
    from backend.models import Restaurant

    client = TestClient(app)

    def override_get_db(mock_session):
        def _override():
            yield mock_session
        return _override

    # Success case
    mock_rest = Restaurant(
        id=1, name="Jalsa", city="Bangalore", location="Banashankari",
        rating=4.1, cost_for_two=800, price_category="$$",
        has_online_delivery=True, cuisines="North Indian", raw_data=None,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_rest]
    mock_session = MagicMock()
    mock_session.execute.return_value = mock_result
    llm_response = {
        "recommendations": [
            {"rank": 1, "name": "Jalsa", "location": "Banashankari", "rating": 4.1,
             "cost_for_two": 800, "online_order": True, "reason": "Great food."},
        ]
    }
    app.dependency_overrides[get_db] = override_get_db(mock_session)
    with patch("backend.routers.recommendations.rank_restaurants", return_value=llm_response):
        try:
            r = client.post("/recommendations", json={"city": "Bangalore", "price_category": "$$", "limit": 3})
            assert r.status_code == 200
            assert r.json()["recommendations"][0]["name"] == "Jalsa"
        finally:
            app.dependency_overrides.clear()

    # No restaurants -> 404
    mock_result.scalars.return_value.all.return_value = []
    app.dependency_overrides[get_db] = override_get_db(mock_session)
    try:
        r = client.post("/recommendations", json={"city": "Unknown", "price_category": "$$", "limit": 3})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()

    # LLM error -> 503
    mock_result.scalars.return_value.all.return_value = [mock_rest]
    app.dependency_overrides[get_db] = override_get_db(mock_session)
    with patch("backend.routers.recommendations.rank_restaurants", return_value={"error": "API error"}):
        try:
            r = client.post("/recommendations", json={"city": "Bangalore", "price_category": "$$", "limit": 3})
            assert r.status_code == 503
        finally:
            app.dependency_overrides.clear()

    print("recommendations API: all tests passed")


if __name__ == "__main__":
    try:
        run_transform_tests()
        run_ingest_tests()
        run_backend_tests()
        run_recommendations_tests()
        print("\nAll tests passed.")
    except AssertionError as e:
        print(f"FAILED: {e}")
        sys.exit(1)
