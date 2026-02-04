"""
Unit tests for Phase 3 - POST /recommendations endpoint.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import get_db
from backend.models import Restaurant


def override_get_db(mock_session):
    def _override():
        yield mock_session
    return _override


client = TestClient(app)


class TestRecommendationsEndpoint:
    def test_recommendations_returns_ranked_list(self):
        mock_restaurants = [
            Restaurant(
                id=1, name="Jalsa", city="Bangalore", location="Banashankari",
                rating=4.1, cost_for_two=800, price_category="$$",
                has_online_delivery=True, cuisines="North Indian", raw_data=None,
            ),
            Restaurant(
                id=2, name="Onesta", city="Bangalore", location="Banashankari",
                rating=4.6, cost_for_two=600, price_category="$$",
                has_online_delivery=True, cuisines="Pizza", raw_data=None,
            ),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_restaurants
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        llm_response = {
            "recommendations": [
                {"rank": 1, "name": "Onesta", "location": "Banashankari", "rating": 4.6,
                 "cost_for_two": 600, "online_order": True, "reason": "Best pizza in town."},
                {"rank": 2, "name": "Jalsa", "location": "Banashankari", "rating": 4.1,
                 "cost_for_two": 800, "online_order": True, "reason": "Great North Indian."},
            ]
        }

        app.dependency_overrides[get_db] = override_get_db(mock_session)
        with patch("backend.routers.recommendations.rank_restaurants", return_value=llm_response):
            try:
                response = client.post(
                    "/recommendations",
                    json={"city": "Bangalore", "price_category": "$$", "limit": 3},
                )
                assert response.status_code == 200
                data = response.json()
                assert "recommendations" in data
                assert len(data["recommendations"]) == 2  # LLM returned 2, limit was 3
                assert data["recommendations"][0]["name"] == "Onesta"
                assert data["recommendations"][0]["reason"] == "Best pizza in town."
            finally:
                app.dependency_overrides.clear()

    def test_recommendations_no_restaurants_returns_404(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.post(
                "/recommendations",
                json={"city": "UnknownCity", "price_category": "$$", "limit": 3},
            )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_recommendations_invalid_price_category_returns_422(self):
        mock_session = MagicMock()
        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.post(
                "/recommendations",
                json={"city": "Bangalore", "price_category": "invalid", "limit": 3},
            )
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_recommendations_limit_out_of_range_returns_422(self):
        mock_session = MagicMock()
        app.dependency_overrides[get_db] = override_get_db(mock_session)
        try:
            response = client.post(
                "/recommendations",
                json={"city": "Bangalore", "price_category": "$$", "limit": 99},
            )
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_recommendations_llm_error_returns_503(self):
        mock_restaurants = [
            Restaurant(
                id=1, name="Jalsa", city="Bangalore", location="Banashankari",
                rating=4.1, cost_for_two=800, price_category="$$",
                has_online_delivery=True, cuisines="North Indian", raw_data=None,
            ),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_restaurants
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        app.dependency_overrides[get_db] = override_get_db(mock_session)
        with patch("backend.routers.recommendations.rank_restaurants", return_value={"error": "API key invalid"}):
            try:
                response = client.post(
                    "/recommendations",
                    json={"city": "Bangalore", "price_category": "$$", "limit": 3},
                )
                assert response.status_code == 503
            finally:
                app.dependency_overrides.clear()

    def test_recommendations_accepts_limit_in_range(self):
        mock_restaurants = [
            Restaurant(
                id=1, name="Jalsa", city="Bangalore", location="Banashankari",
                rating=4.1, cost_for_two=800, price_category="$$",
                has_online_delivery=True, cuisines="North Indian", raw_data=None,
            ),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_restaurants
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        llm_response = {
            "recommendations": [
                {"rank": 1, "name": "Jalsa", "location": "Banashankari", "rating": 4.1,
                 "cost_for_two": 800, "online_order": True, "reason": "Good food."},
            ]
        }

        app.dependency_overrides[get_db] = override_get_db(mock_session)
        with patch("backend.routers.recommendations.rank_restaurants", return_value=llm_response):
            try:
                response = client.post(
                    "/recommendations",
                    json={"city": "Bangalore", "price_category": "$$", "limit": 5},
                )
                assert response.status_code == 200
                assert len(response.json()["recommendations"]) == 1
            finally:
                app.dependency_overrides.clear()


class TestLlmClient:
    """Unit tests for LLM client helpers."""

    def test_extract_json_plain(self):
        from backend.llm.client import _extract_json
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_extract_json_markdown_block(self):
        from backend.llm.client import _extract_json
        text = '```json\n{"recommendations": []}\n```'
        assert _extract_json(text) == {"recommendations": []}

    def test_extract_json_invalid_returns_none(self):
        from backend.llm.client import _extract_json
        assert _extract_json("not json") is None

    def test_rank_restaurants_no_api_key(self):
        from backend.llm.client import rank_restaurants
        # Default provider is Gemini; empty key triggers Gemini error message
        with patch.dict("os.environ", {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": ""}, clear=False):
            result = rank_restaurants(
                [{"name": "X", "location": "Y", "rating": 4, "cost_for_two": 500}],
                "Bangalore", "$$", 3,
            )
        assert "error" in result
        assert "GEMINI_API_KEY" in result["error"]

    def test_rank_restaurants_empty_list(self):
        from backend.llm.client import rank_restaurants
        # Empty list is checked before API key
        result = rank_restaurants([], "Bangalore", "$$", 3)
        assert "error" in result
        assert "No restaurants" in result["error"]
