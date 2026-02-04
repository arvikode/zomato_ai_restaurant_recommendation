"""
Unit tests for ingest script - transform_row and row processing logic.
"""

import pytest

from scripts.transform import transform_row

# Dataset column names
COL_NAME = "name"
COL_LISTED_IN_CITY = "listed_in(city)"
COL_LOCATION = "location"
COL_RATE = "rate"
COL_APPROX_COST = "approx_cost(for two people)"
COL_ONLINE_ORDER = "online_order"
COL_CUISINES = "cuisines"


class TestTransformRow:
    def test_valid_row_produces_record(self):
        row = {
            COL_NAME: "Jalsa",
            COL_LISTED_IN_CITY: "Banashankari",
            COL_LOCATION: "Banashankari",
            COL_RATE: "4.1/5",
            COL_APPROX_COST: "800",
            COL_ONLINE_ORDER: "Yes",
            COL_CUISINES: "North Indian, Mughlai, Chinese",
        }
        result = transform_row(row)
        assert result is not None
        assert result["name"] == "Jalsa"
        assert result["city"] == "Banashankari"
        assert result["location"] == "Banashankari"
        assert result["rating"] == 4.1
        assert result["cost_for_two"] == 800
        assert result["price_category"] == "$$"
        assert result["has_online_delivery"] is True
        assert result["cuisines"] == "North Indian, Mughlai, Chinese"
        assert "raw_data" in result
        assert result["raw_data"] == row  # raw_data holds original row

    def test_skips_row_when_city_null(self):
        row = {
            COL_NAME: "Test",
            COL_LISTED_IN_CITY: None,
            COL_APPROX_COST: "500",
        }
        assert transform_row(row) is None

    def test_skips_row_when_city_empty(self):
        row = {
            COL_NAME: "Test",
            COL_LISTED_IN_CITY: "   ",
            COL_APPROX_COST: "500",
        }
        assert transform_row(row) is None

    def test_skips_row_when_name_empty(self):
        row = {
            COL_NAME: "",
            COL_LISTED_IN_CITY: "Bangalore",
            COL_APPROX_COST: "500",
        }
        assert transform_row(row) is None

    def test_skips_row_when_cost_null(self):
        row = {
            COL_NAME: "Test",
            COL_LISTED_IN_CITY: "Bangalore",
            COL_APPROX_COST: None,
        }
        assert transform_row(row) is None

    def test_skips_row_when_cost_zero(self):
        row = {
            COL_NAME: "Test",
            COL_LISTED_IN_CITY: "Bangalore",
            COL_APPROX_COST: "0",
        }
        assert transform_row(row) is None

    def test_bengaluru_normalized_to_bangalore(self):
        row = {
            COL_NAME: "Test",
            COL_LISTED_IN_CITY: "Bengaluru",
            COL_APPROX_COST: "600",
        }
        result = transform_row(row)
        assert result is not None
        assert result["city"] == "Bangalore"

    def test_price_category_buckets(self):
        # $ : < 500
        row_low = {
            COL_NAME: "Low",
            COL_LISTED_IN_CITY: "Mumbai",
            COL_APPROX_COST: "300",
        }
        assert transform_row(row_low)["price_category"] == "$"

        # $$ : 500-1500
        row_mid = {
            COL_NAME: "Mid",
            COL_LISTED_IN_CITY: "Mumbai",
            COL_APPROX_COST: "800",
        }
        assert transform_row(row_mid)["price_category"] == "$$"

        # $$$ : > 1500
        row_high = {
            COL_NAME: "High",
            COL_LISTED_IN_CITY: "Mumbai",
            COL_APPROX_COST: "2000",
        }
        assert transform_row(row_high)["price_category"] == "$$$"
