from __future__ import annotations

from typing import Final

UNKNOWN_COUNTRY: Final[str] = "Unknown"

COUNTRY_ALIASES: Final[dict[str, str]] = {
    "eeuu": "USA",
    "méxico": "Mexico",
    "mexico": "Mexico",
    "united states": "USA",
    "united states of america": "USA",
}

COUNTRY_CENTROIDS: Final[dict[str, tuple[float, float]]] = {
    "Argentina": (-38.4161, -63.6167),
    "Australia": (-25.2744, 133.7751),
    "Austria": (47.5162, 14.5501),
    "Belgium": (50.5039, 4.4699),
    "Bolivia": (-16.2902, -63.5887),
    "Brazil": (-14.2350, -51.9253),
    "Bulgaria": (42.7339, 25.4858),
    "Canada": (56.1304, -106.3468),
    "Chile": (-35.6751, -71.5430),
    "China": (35.8617, 104.1954),
    "Colombia": (4.5709, -74.2973),
    "Costa Rica": (9.7489, -83.7534),
    "Czech Republic": (49.8175, 15.4730),
    "Denmark": (56.2639, 9.5018),
    "Dominican Republic": (18.7357, -70.1627),
    "Ecuador": (-1.8312, -78.1834),
    "Egypt": (26.8206, 30.8025),
    "El Salvador": (13.7942, -88.8965),
    "England": (52.3555, -1.1743),
    "Ethiopia": (9.1450, 40.4897),
    "France": (46.2276, 2.2137),
    "Greece": (39.0742, 21.8243),
    "Guatemala": (15.7835, -90.2308),
    "Honduras": (15.2000, -86.2419),
    "Ireland": (53.4129, -8.2439),
    "Italy": (41.8719, 12.5674),
    "Japan": (36.2048, 138.2529),
    "Macedonia": (41.6086, 21.7453),
    "Malaysia": (4.2105, 101.9758),
    "Mexico": (23.6345, -102.5528),
    "Netherlands": (52.1326, 5.2913),
    "Nicaragua": (12.8654, -85.2072),
    "Norway": (60.4720, 8.4689),
    "Paraguay": (-23.4425, -58.4438),
    "Peru": (-9.1900, -75.0152),
    "Portugal": (39.3999, -8.2245),
    "Qatar": (25.3548, 51.1839),
    "Republic of Korea": (35.9078, 127.7669),
    "Romania": (45.9432, 24.9668),
    "Rwanda": (-1.9403, 29.8739),
    "Scotland": (56.4907, -4.2026),
    "Singapore": (1.3521, 103.8198),
    "South Africa": (-30.5595, 22.9375),
    "Spain": (40.4637, -3.7492),
    "Switzerland": (46.8182, 8.2275),
    "Taiwan": (23.6978, 120.9605),
    "Thailand": (15.8700, 100.9925),
    "The Philippines": (12.8797, 121.7740),
    "Turkey": (38.9637, 35.2433),
    "UAE": (23.4241, 53.8478),
    "USA": (37.0902, -95.7129),
    "Uruguay": (-32.5228, -55.7658),
    "Venezuela": (6.4238, -66.5897),
    UNKNOWN_COUNTRY: (8.0, 0.0),
}

COUNTRY_BASE_COLORS: Final[dict[str, str]] = {
    "Argentina": "#6EC1FF",
    "Australia": "#2F4B9C",
    "Brazil": "#45B649",
    "Colombia": "#FFD030",
    "Japan": "#E24B5B",
    "Peru": "#FF7600",
    "USA": "#E2ACB7",
    "Mexico": "#3B8C4A",
    "Venezuela": "#F5D547",
    "Chile": "#D64545",
}


def normalize_country(value: str | None) -> tuple[str, bool]:
    if value is None:
        return UNKNOWN_COUNTRY, True

    cleaned = value.strip()
    if not cleaned:
        return UNKNOWN_COUNTRY, True

    lowered = cleaned.casefold()
    if lowered in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[lowered], False

    if any(char.isdigit() for char in cleaned):
        return UNKNOWN_COUNTRY, True

    return cleaned, False


def country_centroid(country: str) -> tuple[float, float]:
    return COUNTRY_CENTROIDS.get(country, COUNTRY_CENTROIDS[UNKNOWN_COUNTRY])


def country_base_color(country: str) -> str:
    return COUNTRY_BASE_COLORS.get(country, "#888899")
