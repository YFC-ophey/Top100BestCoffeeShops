from __future__ import annotations

from collections import Counter, defaultdict
import os
from pathlib import Path
import re
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from src.category_utils import SOUTH_AMERICA_CATEGORY, TOP_100_CATEGORY, normalize_category
from src.country_centroids import (
    COUNTRY_CENTROIDS,
    UNKNOWN_COUNTRY,
    country_base_color,
    country_centroid,
    normalize_country,
)
from src.models import CoffeeShop
from src.state import load_previous_state

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = BASE_DIR / "data" / "current_list.json"
DEFAULT_CSV_FILE = BASE_DIR / "output" / "coffee_shops.csv"
DEFAULT_KML_FILE = BASE_DIR / "output" / "coffee_shops.kml"
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

RANK_BANDS = [
    {"key": "1-10", "label": "1-10", "min": 1, "max": 10},
    {"key": "11-25", "label": "11-25", "min": 11, "max": 25},
    {"key": "26-50", "label": "26-50", "min": 26, "max": 50},
    {"key": "51-100", "label": "51-100", "min": 51, "max": 100},
]


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
        normalized_shops = sorted(shops, key=lambda value: (value.rank, value.category, value.name))

        category_counts = Counter(shop.category for shop in normalized_shops)
        top_100_links = _build_ordered_links(normalized_shops, TOP_100_CATEGORY)
        south_america_links = _build_ordered_links(normalized_shops, SOUTH_AMERICA_CATEGORY)

        overview_shops, data_quality = _build_overview_shops(normalized_shops)
        overview_countries = _build_overview_countries(overview_shops)
        overview_filters = _build_overview_filters(overview_shops, overview_countries)

        context = {
            "request": request,
            "shops": normalized_shops,
            "total_shops": len(normalized_shops),
            "category_counts": dict(sorted(category_counts.items())),
            "csv_available": app.state.csv_file.exists(),
            "kml_available": app.state.kml_file.exists(),
            "csv_url": "/artifacts/csv",
            "kml_url": "/artifacts/kml",
            "top_100_links": top_100_links,
            "south_america_links": south_america_links,
            "south_links": south_america_links,
            "overview_shops": overview_shops,
            "overview_countries": overview_countries,
            "overview_filters": overview_filters,
            "data_quality": data_quality,
            "google_maps_js_api_key": _google_maps_js_key(),
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
        env_value = os.getenv(env_key, "").strip()
        if env_value:
            return env_value

    env_candidates = [BASE_DIR / ".env"]
    if BASE_DIR.parent.name == ".worktrees":
        env_candidates.append(BASE_DIR.parent.parent / ".env")

    for env_path in env_candidates:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#") or "=" not in cleaned:
                continue
            key, value = cleaned.split("=", 1)
            if key.strip() in {"GOOGLE_MAPS_JS_API_KEY", "GOOGLE_MAPS_API_KEY"}:
                return value.strip().strip('"').strip("'")
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
    return [
        {
            "label": f"{shop.rank}. {shop.name}",
            "url": _google_maps_link(shop),
        }
        for shop in ordered
    ]


def _google_maps_link(shop: CoffeeShop) -> str:
    query_parts = [shop.name]
    city = shop.city.strip() if shop.city else ""
    if city:
        query_parts.append(city)

    country_value, _ = normalize_country(shop.country)
    if country_value and country_value != UNKNOWN_COUNTRY:
        query_parts.append(country_value)
    elif shop.country:
        query_parts.append(shop.country)

    query = ", ".join(query_parts)
    params: dict[str, str] = {"api": "1", "query": query}
    if shop.place_id:
        params["query_place_id"] = shop.place_id
    return f"https://www.google.com/maps/search/?{urlencode(params)}"


def _build_overview_shops(shops: list[CoffeeShop]) -> tuple[list[dict[str, object]], dict[str, object]]:
    payload: list[dict[str, object]] = []
    invalid_country_count = 0
    unknown_country_count = 0
    missing_city_count = 0
    flagged_shop_ids: list[str] = []

    for shop in shops:
        country_normalized, invalid_country = normalize_country(shop.country)
        if country_normalized not in COUNTRY_CENTROIDS:
            country_normalized = UNKNOWN_COUNTRY
            invalid_country = True

        if invalid_country:
            invalid_country_count += 1

        if country_normalized == UNKNOWN_COUNTRY:
            unknown_country_count += 1

        city = (shop.city or "").strip()
        if not city:
            missing_city_count += 1

        item = {
            "id": _shop_id(shop),
            "name": shop.name,
            "rank": shop.rank,
            "category": normalize_category(shop.category),
            "country_raw": shop.country,
            "country_normalized": country_normalized,
            "city": city,
            "source_url": shop.source_url or "",
            "google_maps_url": _google_maps_link(shop),
            "rank_band": _rank_band(shop.rank),
            "formatted_address": shop.formatted_address or "",
            "lat": shop.lat,
            "lng": shop.lng,
        }
        payload.append(item)

        if invalid_country:
            flagged_shop_ids.append(str(item["id"]))

    data_quality = {
        "invalid_country_count": invalid_country_count,
        "unknown_country_count": unknown_country_count,
        "missing_city_count": missing_city_count,
        "flagged_shop_ids": flagged_shop_ids,
    }
    return payload, data_quality


def _build_overview_countries(overview_shops: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "shop_count": 0,
            "top_100_count": 0,
            "south_america_count": 0,
            "primary_shop": None,
        }
    )

    for shop in overview_shops:
        country = str(shop["country_normalized"])
        bucket = grouped[country]
        bucket["shop_count"] = int(bucket["shop_count"]) + 1
        if shop["category"] == TOP_100_CATEGORY:
            bucket["top_100_count"] = int(bucket["top_100_count"]) + 1
        if shop["category"] == SOUTH_AMERICA_CATEGORY:
            bucket["south_america_count"] = int(bucket["south_america_count"]) + 1

        current = bucket["primary_shop"]
        if current is None or int(shop["rank"]) < int(current["rank"]):
            bucket["primary_shop"] = shop

    max_count = max((int(item["shop_count"]) for item in grouped.values()), default=1)

    overview_countries: list[dict[str, object]] = []
    for country, bucket in grouped.items():
        lat, lng = country_centroid(country)
        ratio = int(bucket["shop_count"]) / max_count
        size = round(16 + ratio * 40, 2)
        overview_countries.append(
            {
                "country": country,
                "lat": lat,
                "lng": lng,
                "shop_count": int(bucket["shop_count"]),
                "top_100_count": int(bucket["top_100_count"]),
                "south_america_count": int(bucket["south_america_count"]),
                "marker_color": country_base_color(country),
                "marker_size_px": size,
                "primary_shop": bucket["primary_shop"],
            }
        )

    return sorted(overview_countries, key=lambda value: (-int(value["shop_count"]), str(value["country"])))


def _build_overview_filters(
    overview_shops: list[dict[str, object]], overview_countries: list[dict[str, object]]
) -> dict[str, object]:
    category_counts = Counter(str(shop["category"]) for shop in overview_shops)
    categories = [
        {
            "key": TOP_100_CATEGORY,
            "label": "Top 100 World",
            "count": int(category_counts.get(TOP_100_CATEGORY, 0)),
            "active": True,
        },
        {
            "key": SOUTH_AMERICA_CATEGORY,
            "label": SOUTH_AMERICA_CATEGORY,
            "count": int(category_counts.get(SOUTH_AMERICA_CATEGORY, 0)),
            "active": True,
        },
    ]

    countries = [
        {
            "key": str(country["country"]),
            "label": str(country["country"]),
            "count": int(country["shop_count"]),
        }
        for country in overview_countries
    ]

    return {
        "categories": categories,
        "countries": countries,
        "rank_bands": RANK_BANDS,
        "defaults": {
            "active_categories": [TOP_100_CATEGORY, SOUTH_AMERICA_CATEGORY],
            "country": "All",
            "rank_band": "All",
        },
    }


def _rank_band(rank: int) -> str:
    for item in RANK_BANDS:
        if int(item["min"]) <= rank <= int(item["max"]):
            return str(item["key"])
    return "Other"


def _shop_id(shop: CoffeeShop) -> str:
    base = f"{normalize_category(shop.category)}-{shop.rank}-{shop.name}".casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return normalized or f"shop-{shop.rank}"

app = create_app(
    data_file=DEFAULT_DATA_FILE,
    csv_file=DEFAULT_CSV_FILE,
    kml_file=DEFAULT_KML_FILE,
)
