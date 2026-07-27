"""Keep only India-based jobs."""
from __future__ import annotations

# Major Indian hubs + the country itself. A job's location must contain one of
# these for it to be kept.
INDIA_TERMS = [
    "india", "bharat", "ncr", "remote india",
    "mumbai", "navi mumbai", "thane", "pune", "nagpur", "nashik",
    "delhi", "new delhi", "gurgaon", "gurugram", "noida", "faridabad", "ghaziabad",
    "bengaluru", "bangalore", "hyderabad", "chennai", "kolkata",
    "ahmedabad", "surat", "vadodara", "jaipur", "chandigarh", "lucknow",
    "kochi", "cochin", "trivandrum", "coimbatore", "indore", "bhopal",
    "nagpur", "visakhapatnam", "vizag", "bhubaneswar", "goa", "mysuru", "mysore",
    "maharashtra", "karnataka", "telangana", "tamil nadu", "gujarat", "haryana",
    "uttar pradesh", "west bengal", "kerala", "rajasthan", "punjab",
]


def is_india(location: str) -> bool:
    loc = (location or "").strip().lower()
    if not loc:
        # Empty location on India-scoped searches — keep rather than lose it.
        return True
    return any(term in loc for term in INDIA_TERMS)
