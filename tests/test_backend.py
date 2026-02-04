"""
Unit tests for Phase 2 Backend API.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import get_db
from backend.models import Restaurant

client = TestClient(app)


def override_get_db(mock_session):
    """Yield mock session for dependency override."""

    def _override():
        yield mock_session

    return _override


class TestRootEndpoint:
    def test_root_returns_ok(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "docs" in data


class TestCitiesEndpoint:
    def test_cities_returns_sorted_list(self):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("Bangalore",), ("Mumbai",)]
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.get("/cities")
            assert response.status_code == 200
            assert response.json() == ["Bangalore", "Mumbai"]
        finally:
            app.dependency_overrides.clear()

    def test_cities_returns_empty_list_when_no_data(self):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.get("/cities")
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.clear()


class TestRestaurantsEndpoint:
    def test_restaurants_returns_filtered_list(self):
        mock_restaurant = Restaurant(
            id=1,
            name="Jalsa",
            city="Bangalore",
            location="Banashankari",
            rating=4.1,
            cost_for_two=800,
            price_category="$$",
            has_online_delivery=True,
            cuisines="North Indian, Mughlai",
            raw_data=None,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_restaurant]
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.get(
                "/restaurants?city=Bangalore&price_category=$$"
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Jalsa"
            assert data[0]["city"] == "Bangalore"
            assert data[0]["price_category"] == "$$"
            assert data[0]["rating"] == 4.1
        finally:
            app.dependency_overrides.clear()

    def test_restaurants_invalid_price_category_returns_422(self):
        mock_session = MagicMock()
        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.get(
                "/restaurants?city=Bangalore&price_category=invalid"
            )
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_restaurants_missing_city_returns_422(self):
        mock_session = MagicMock()
        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.get("/restaurants?price_category=$$")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_restaurants_missing_price_category_returns_422(self):
        mock_session = MagicMock()
        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.get("/restaurants?city=Bangalore")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_restaurants_accepts_limit_param(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.get(
                "/restaurants?city=Bangalore&price_category=$$&limit=5"
            )
            assert response.status_code == 200
            mock_session.execute.assert_called_once()
        finally:
            app.dependency_overrides.clear()
