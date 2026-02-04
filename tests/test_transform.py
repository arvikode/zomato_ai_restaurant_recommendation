"""
Unit tests for Zomato dataset transformation/normalization functions.
"""

import pytest

from scripts.transform import (
    derive_price_category,
    normalize_city,
    normalize_cost,
    normalize_cuisines,
    normalize_location,
    normalize_name,
    normalize_online_order,
    normalize_rating,
)


class TestNormalizeCity:
    def test_trim_whitespace(self):
        assert normalize_city("  Bangalore  ") == "Bangalore"

    def test_title_case(self):
        assert normalize_city("bangalore") == "Bangalore"
        assert normalize_city("BANGALORE") == "Bangalore"

    def test_bengaluru_to_bangalore(self):
        assert normalize_city("Bengaluru") == "Bangalore"
        assert normalize_city("bengaluru") == "Bangalore"

    def test_none_returns_none(self):
        assert normalize_city(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_city("") is None
        assert normalize_city("   ") is None

    def test_preserves_other_cities(self):
        assert normalize_city("Mumbai") == "Mumbai"
        assert normalize_city("Delhi") == "Delhi"


class TestNormalizeRating:
    def test_parse_fraction_format(self):
        assert normalize_rating("4.1/5") == 4.1
        assert normalize_rating("3.8/5") == 3.8

    def test_parse_plain_float(self):
        assert normalize_rating("4.5") == 4.5
        assert normalize_rating("5.0") == 5.0

    def test_none_returns_none(self):
        assert normalize_rating(None) is None

    def test_empty_returns_none(self):
        assert normalize_rating("") is None
        assert normalize_rating("   ") is None

    def test_invalid_returns_none(self):
        assert normalize_rating("N/A") is None
        assert normalize_rating("invalid") is None
        assert normalize_rating("-") is None


class TestNormalizeCost:
    def test_parse_simple_int(self):
        assert normalize_cost("800") == 800
        assert normalize_cost("300") == 300

    def test_parse_comma_separated_takes_first(self):
        assert normalize_cost("800, 900") == 800
        assert normalize_cost("500,1000") == 500

    def test_none_returns_none(self):
        assert normalize_cost(None) is None

    def test_empty_returns_none(self):
        assert normalize_cost("") is None
        assert normalize_cost("   ") is None

    def test_zero_returns_none(self):
        assert normalize_cost("0") is None

    def test_strips_non_digits(self):
        assert normalize_cost("₹800") == 800
        assert normalize_cost("800 Rs") == 800


class TestDerivePriceCategory:
    def test_under_500(self):
        assert derive_price_category(100) == "$"
        assert derive_price_category(499) == "$"

    def test_500_to_1500(self):
        assert derive_price_category(500) == "$$"
        assert derive_price_category(1000) == "$$"
        assert derive_price_category(1500) == "$$"

    def test_over_1500(self):
        assert derive_price_category(1501) == "$$$"
        assert derive_price_category(3000) == "$$$"

    def test_none_returns_none(self):
        assert derive_price_category(None) is None


class TestNormalizeOnlineOrder:
    def test_yes(self):
        assert normalize_online_order("Yes") is True
        assert normalize_online_order("yes") is True
        assert normalize_online_order("YES") is True

    def test_no(self):
        assert normalize_online_order("No") is False
        assert normalize_online_order("no") is False

    def test_invalid_defaults_false(self):
        assert normalize_online_order(None) is False
        assert normalize_online_order("") is False
        assert normalize_online_order("maybe") is False


class TestNormalizeCuisines:
    def test_trim(self):
        assert normalize_cuisines("  North Indian, Chinese  ") == "North Indian, Chinese"

    def test_empty_returns_none(self):
        assert normalize_cuisines(None) is None
        assert normalize_cuisines("") is None
        assert normalize_cuisines("   ") is None

    def test_preserves_content(self):
        assert normalize_cuisines("North Indian, Mughlai, Chinese") == "North Indian, Mughlai, Chinese"


class TestNormalizeLocation:
    def test_trim(self):
        assert normalize_location("  Banashankari  ") == "Banashankari"

    def test_empty_returns_none(self):
        assert normalize_location(None) is None
        assert normalize_location("") is None


class TestNormalizeName:
    def test_trim(self):
        assert normalize_name("  Jalsa  ") == "Jalsa"

    def test_empty_returns_none(self):
        assert normalize_name(None) is None
        assert normalize_name("") is None
        assert normalize_name("   ") is None
