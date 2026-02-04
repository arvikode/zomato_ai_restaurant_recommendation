#!/usr/bin/env python3
"""
Interactive terminal test for the recommendation API.
Start the server first (uvicorn backend.main:app --reload), then run:
  python scripts/terminal_test.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

# Use 127.0.0.1 to avoid IPv6 localhost timeout on macOS; override via API_URL env
BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")


def main():
    print("\n--- Restaurant Recommendation (Terminal Test) ---\n")

    # 1. Fetch cities
    try:
        r = httpx.get(f"{BASE_URL}/cities", timeout=10.0)
        r.raise_for_status()
        cities = r.json()
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        print("Cannot connect to server (connection refused or timed out).")
        print("  -> Start the server first:  uvicorn backend.main:app --reload")
        print("  -> If the server is loading data, wait 1–2 min and try again.")
        print(f"  -> URL used: {BASE_URL}")
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching cities: {e}")
        sys.exit(1)

    if not cities:
        print("No cities in database. Start the server and wait for auto-load (~1-2 min), or run:")
        print("  python scripts/ingest_zomato_data.py")
        sys.exit(1)

    # 2. Select city
    cities_sorted = sorted(cities)
    print("Select city (number or name):")
    for i, c in enumerate(cities_sorted, 1):
        print(f"  {i}. {c}")
    print("  0. Enter city name manually")
    choice = input("\nYour choice: ").strip()

    if choice == "0":
        city = input("Enter city name: ").strip()
        if not city:
            print("No city entered.")
            sys.exit(1)
    elif choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(cities_sorted):
            city = cities_sorted[idx - 1]
        else:
            print("Invalid number.")
            sys.exit(1)
    else:
        city = choice
        if city not in cities_sorted:
            print(f"'{city}' not in list; using it anyway.")

    # 3. Select price
    print("\nSelect price category:")
    print("  1. $  (budget)")
    print("  2. $$ (mid)")
    print("  3. $$$ (premium)")
    price_choice = input("Your choice (1/2/3): ").strip()
    price_map = {"1": "$", "2": "$$", "3": "$$$"}
    price_category = price_map.get(price_choice, "$$")
    print(f"  Using: {price_category}")

    # 4. Limit (optional)
    limit_input = input("How many recommendations? (3-10, default 3): ").strip()
    if limit_input.isdigit() and 3 <= int(limit_input) <= 10:
        limit = int(limit_input)
    else:
        limit = 3

    # 5. Call recommendations
    print(f"\nFetching top {limit} recommendations for {city} ({price_category})...\n")
    try:
        r = httpx.post(
            f"{BASE_URL}/recommendations",
            json={"city": city, "price_category": price_category, "limit": limit},
            timeout=60.0,
        )
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPStatusError as e:
        print(f"API error: {e.response.status_code}")
        print(e.response.text[:500])
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    recs = data.get("recommendations", [])
    if not recs:
        print("No recommendations returned.")
        sys.exit(0)

    # 6. Print results
    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    for rec in recs:
        print(f"\n  #{rec.get('rank', '?')}  {rec.get('name', '?')}")
        print(f"      Location: {rec.get('location', 'N/A')}")
        print(f"      Rating: {rec.get('rating', 'N/A')}  |  Cost for two: ₹{rec.get('cost_for_two', 'N/A')}")
        print(f"      Online order: {'Yes' if rec.get('online_order') else 'No'}")
        print(f"      Why: {rec.get('reason', 'N/A')}")
    print("\n" + "=" * 60)
    print("Done.\n")


if __name__ == "__main__":
    main()
