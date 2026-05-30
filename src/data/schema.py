"""
Column mapping for the Zomato Hugging Face dataset.

Source: ManikaSaini/zomato-restaurant-recommendation (and equivalent forks such as
dhavalpm/zomato-restaurant-recommendation) — classic Zomato India export (~51.7k rows).

Raw columns (train split):
  url, address, name, online_order, book_table, rate, votes, phone,
  location, rest_type, dish_liked, cuisines,
  approx_cost(for two people), reviews_list, menu_item,
  listed_in(type), listed_in(city)
"""

from __future__ import annotations

# Logical field -> ordered list of possible raw column names (first match wins)
SCHEMA_MAP: dict[str, list[str]] = {
    "url": ["url"],
    "name": ["name", "restaurant_name", "Restaurant Name"],
    "city": ["listed_in(city)", "city", "City", "listed_in_city"],
    "locality": ["location", "locality", "Locality", "Locality Verbose"],
    "address": ["address", "Address"],
    "cuisines": ["cuisines", "Cuisines"],
    "rate": ["rate", "aggregate_rating", "Aggregate rating", "rating"],
    "votes": ["votes", "Votes"],
    "approx_cost": [
        "approx_cost(for two people)",
        "average_cost_for_two",
        "Average Cost for two",
        "approx_cost",
    ],
    "rest_type": ["rest_type", "restaurant_type"],
    "online_order": ["online_order", "has_online_delivery"],
    "book_table": ["book_table", "has_table_booking"],
    "listed_in_type": ["listed_in(type)", "listed_in_type"],
}

# City name normalization (edge case D-14)
LOCATION_ALIASES: dict[str, str] = {
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "blr": "Bangalore",
    "delhi ncr": "Delhi",
    "new delhi": "Delhi",
    "gurugram": "Gurgaon",
    "gurgaon": "Gurgaon",
}


def resolve_column(raw_row: dict[str, object], logical_key: str) -> object | None:
    """Return the first present raw value for a logical schema key."""
    for column in SCHEMA_MAP.get(logical_key, []):
        if column in raw_row and raw_row[column] not in (None, ""):
            return raw_row[column]
    return None
