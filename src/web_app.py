from __future__ import annotations

from collections import Counter, defaultdict
import os
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from src.category_utils import SOUTH_AMERICA_CATEGORY, TOP_100_CATEGORY, normalize_category
from src.country_centroids import (
    UNKNOWN_COUNTRY,
    country_base_color,
    country_centroid,
    normalize_country,
)
from src.env_utils import load_env_file
from src.models import CoffeeShop
from src.state import load_previous_state

BASE_DIR = Path(__file__).resolve().parent.parent
load_env_file(BASE_DIR)
DEFAULT_DATA_FILE = BASE_DIR / "data" / "current_list.json"
DEFAULT_CSV_FILE = BASE_DIR / "output" / "coffee_shops.csv"
DEFAULT_KML_FILE = BASE_DIR / "output" / "coffee_shops.kml"
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app(data_file: Path, csv_file: Path, kml_file: Path) -> FastAPI:
    app = FastAPI(title="Top100BestCoffeeShops Preview")
    app.state.data_file = data_file
    app.state.csv_file = csv_file
    app.state.kml_file = kml_file

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def home(request: Request):
        shops = _load_shops(app.state.data_file)
        category_counts = Counter(shop.category for shop in shops)
        top_100_links = _build_ordered_links(shops, TOP_100_CATEGORY)
        south_america_links = _build_ordered_links(shops, SOUTH_AMERICA_CATEGORY)
        map_shops, missing_coords_count = _build_map_shops(shops)
        sidebar_shops = _build_sidebar_shops(shops)
        map_country_aggregates = _build_country_aggregates(sidebar_shops)
        overview_filters = _build_overview_filters(sidebar_shops)
        data_quality = _build_data_quality(shops, sidebar_shops, missing_coords_count)
        context = {
            "request": request,
            "shops": sorted(shops, key=lambda value: (value.rank, value.category, value.name)),
            "total_shops": len(shops),
            "category_counts": dict(sorted(category_counts.items())),
            "csv_available": app.state.csv_file.exists(),
            "kml_available": app.state.kml_file.exists(),
            "csv_url": "/artifacts/csv",
            "kml_url": "/artifacts/kml",
            "top_100_links": top_100_links,
            "south_america_links": south_america_links,
            "south_links": south_america_links,
            "google_maps_js_api_key": _google_maps_js_key(),
            "map_shops": map_shops,
            "sidebar_shops": sidebar_shops,
            "map_country_aggregates": map_country_aggregates,
            "map_missing_coords_count": missing_coords_count,
            "overview_countries": map_country_aggregates,
            "overview_shops": sidebar_shops,
            "overview_filters": overview_filters,
            "data_quality": data_quality,
        }
        return TEMPLATES.TemplateResponse(request=request, name="index.html", context=context)

    @app.get("/artifacts/{artifact_name}")
    def artifact(artifact_name: str):
        paths = {"csv": app.state.csv_file, "kml": app.state.kml_file}
        target = paths.get(artifact_name)
        if target is None or not target.exists():
            raise HTTPException(status_code=404, detail="Artifact not found")
        media_type = "text/csv" if artifact_name == "csv" else "application/vnd.google-earth.kml+xml"
        return FileResponse(path=target, media_type=media_type, filename=target.name)

    return app


def _google_maps_js_key() -> str:
    for env_key in ("GOOGLE_MAPS_JS_API_KEY", "GOOGLE_MAPS_API_KEY"):
        value = os.getenv(env_key, "").strip()
        if value:
            return value
    return ""


def _load_shops(data_file: Path) -> list[CoffeeShop]:
    if not data_file.exists():
        return []

    shops = load_previous_state(data_file)
    for shop in shops:
        shop.category = normalize_category(shop.category)
    return shops


def _build_ordered_links(shops: list[CoffeeShop], category: str) -> list[dict[str, str]]:
    filtered = [shop for shop in shops if normalize_category(shop.category) == category]
    ordered = sorted(filtered, key=lambda value: (value.rank, value.name))
    return [{"label": f"{shop.rank}. {shop.name}", "url": _google_maps_link(shop)} for shop in ordered]


def _google_maps_link(shop: CoffeeShop) -> str:
    query_parts = [shop.name]
    city = shop.city.strip() if shop.city else ""
    if city:
        query_parts.append(city)

    country_value, _ = normalize_country(shop.country)
    if country_value != UNKNOWN_COUNTRY:
        query_parts.append(country_value)
    elif shop.country:
        query_parts.append(shop.country)

    query = ", ".join(query_parts)
    params: dict[str, str] = {"api": "1", "query": query}
    if shop.place_id:
        params["query_place_id"] = shop.place_id
    return f"https://www.google.com/maps/search/?{urlencode(params)}"


def _build_map_shops(shops: list[CoffeeShop]) -> tuple[list[dict[str, object]], int]:
    missing = 0
    items: list[dict[str, object]] = []
    for shop in shops:
        country_normalized, invalid_country = normalize_country(shop.country)
        if invalid_country:
            country_normalized = UNKNOWN_COUNTRY

        has_coords = shop.lat is not None and shop.lng is not None
        if not has_coords:
            missing += 1

        items.append(
            {
                "id": _shop_id(shop),
                "name": shop.name,
                "city": shop.city,
                "country_normalized": country_normalized,
                "country": country_normalized,
                "country_raw": shop.country,
                "rank": shop.rank,
                "category": normalize_category(shop.category),
                "lat": shop.lat,
                "lng": shop.lng,
                "place_id": shop.place_id or "",
                "address": shop.formatted_address or shop.address or "",
                "source_url": shop.source_url or "",
                "google_maps_url": _google_maps_link(shop),
            }
        )
    return items, missing


def _build_sidebar_shops(shops: list[CoffeeShop]) -> list[dict[str, object]]:
    ordered = sorted(shops, key=lambda value: (value.rank, value.category, value.name))
    rows: list[dict[str, object]] = []
    for shop in ordered:
        country_normalized, invalid_country = normalize_country(shop.country)
        if invalid_country:
            country_normalized = UNKNOWN_COUNTRY
        rows.append(
            {
                "id": _shop_id(shop),
                "name": shop.name,
                "city": shop.city,
                "country_normalized": country_normalized,
                "country": country_normalized,
                "country_raw": shop.country,
                "rank": shop.rank,
                "category": normalize_category(shop.category),
                "lat": shop.lat,
                "lng": shop.lng,
                "place_id": shop.place_id or "",
                "address": shop.formatted_address or shop.address or "",
                "source_url": shop.source_url or "",
                "google_maps_url": _google_maps_link(shop),
            }
        )
    return rows


def _build_country_aggregates(shops: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "country": UNKNOWN_COUNTRY,
            "count": 0,
            "top_count": 0,
            "south_count": 0,
            "lat_values": [],
            "lng_values": [],
        }
    )

    for item in shops:
        country = str(item.get("country") or UNKNOWN_COUNTRY)
        bucket = grouped[country]
        bucket["country"] = country
        bucket["count"] = int(bucket["count"]) + 1
        if item.get("category") == TOP_100_CATEGORY:
            bucket["top_count"] = int(bucket["top_count"]) + 1
        if item.get("category") == SOUTH_AMERICA_CATEGORY:
            bucket["south_count"] = int(bucket["south_count"]) + 1

        lat = item.get("lat")
        lng = item.get("lng")
        if lat is not None and lng is not None:
            bucket["lat_values"].append(float(lat))
            bucket["lng_values"].append(float(lng))

    result: list[dict[str, object]] = []
    for country, bucket in grouped.items():
        lat_values: list[float] = bucket["lat_values"]  # type: ignore[assignment]
        lng_values: list[float] = bucket["lng_values"]  # type: ignore[assignment]
        if lat_values and lng_values:
            lat = sum(lat_values) / len(lat_values)
            lng = sum(lng_values) / len(lng_values)
        else:
            lat, lng = country_centroid(country)
        result.append(
            {
                "country": country,
                "count": int(bucket["count"]),
                "top_count": int(bucket["top_count"]),
                "south_count": int(bucket["south_count"]),
                "lat": lat,
                "lng": lng,
                "color": country_base_color(country),
            }
        )

    return sorted(result, key=lambda row: (-int(row["count"]), str(row["country"])))


def _shop_id(shop: CoffeeShop) -> str:
    raw = f"{normalize_category(shop.category)}-{shop.rank}-{shop.name}".strip().lower()
    return "".join(char if char.isalnum() else "-" for char in raw).strip("-")


def _build_overview_filters(sidebar_shops: list[dict[str, object]]) -> dict[str, object]:
    countries = sorted({str(item.get("country") or UNKNOWN_COUNTRY) for item in sidebar_shops})
    return {
        "categories": [TOP_100_CATEGORY, SOUTH_AMERICA_CATEGORY],
        "countries": countries,
        "rank_bands": ["All", "1-10", "11-25", "26-50", "51-100"],
        "defaults": {
            "categories": [TOP_100_CATEGORY, SOUTH_AMERICA_CATEGORY],
            "country": "All Countries",
            "rank_band": "All",
        },
    }


def _build_data_quality(
    shops: list[CoffeeShop],
    sidebar_shops: list[dict[str, object]],
    missing_coords_count: int,
) -> dict[str, int]:
    invalid_country_values = 0
    rows_without_city = 0
    missing_place_id = 0
    for shop in shops:
        _, invalid_country = normalize_country(shop.country)
        if invalid_country:
            invalid_country_values += 1
        if not (shop.city or "").strip():
            rows_without_city += 1
        if not (shop.place_id or "").strip():
            missing_place_id += 1

    unknown_country_markers = sum(1 for item in sidebar_shops if item.get("country") == UNKNOWN_COUNTRY)
    return {
        "invalid_country_values": invalid_country_values,
        "unknown_country_markers": unknown_country_markers,
        "rows_without_city": rows_without_city,
        "missing_lat_lng": missing_coords_count,
        "missing_place_id": missing_place_id,
    }


app = create_app(data_file=DEFAULT_DATA_FILE, csv_file=DEFAULT_CSV_FILE, kml_file=DEFAULT_KML_FILE)
