from __future__ import annotations

TOP_100_CATEGORY = "Top 100"
SOUTH_AMERICA_CATEGORY = "South America"


def normalize_category(category: str | None) -> str:
    if category is None:
        return ""
    cleaned = category.strip()
    lowered = cleaned.casefold()
    if lowered in {"south", "south america"}:
        return SOUTH_AMERICA_CATEGORY
    if lowered == "top 100":
        return TOP_100_CATEGORY
    return cleaned
