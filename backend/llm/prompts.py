"""
Prompt templates for restaurant recommendation.
"""


def build_system_prompt() -> str:
    """System role for the LLM."""
    return """You are a restaurant recommendation assistant. Your task is to rank restaurants from a provided list and explain why each is a good choice.

RULES (strict):
1. You MUST rank ONLY from the restaurants in the list provided. Do NOT invent or add any restaurant not in the list.
2. Return your response as valid JSON only. No markdown, no explanation outside the JSON.
3. Use the exact restaurant names from the list.
4. Provide a brief, helpful reason for each recommendation."""


def build_user_prompt(restaurants: list[dict], city: str, price_category: str, limit: int) -> str:
    """Build user prompt with restaurant list."""
    lines = [
        f"City: {city}",
        f"Price category: {price_category}",
        f"Rank exactly the top {limit} restaurants from the list below.",
        "",
        "Restaurant list (name, location, rating, cost_for_two, online_order, cuisines):",
    ]
    for i, r in enumerate(restaurants, 1):
        name = r.get("name", "?")
        location = r.get("location") or "N/A"
        rating = r.get("rating") or "N/A"
        cost = r.get("cost_for_two") or "N/A"
        online = "Yes" if r.get("has_online_delivery") else "No"
        cuisines = r.get("cuisines") or "N/A"
        lines.append(f"{i}. {name} | {location} | {rating} | {cost} | Online: {online} | {cuisines}")

    lines.append("")
    lines.append(
        "Respond with JSON in this exact format (no other text): "
        '{"recommendations": [{"rank": 1, "name": "...", "location": "...", "rating": 4.1, '
        '"cost_for_two": 800, "online_order": true, "reason": "..."}]}'
    )
    return "\n".join(lines)
