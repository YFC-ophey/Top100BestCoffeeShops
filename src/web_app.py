import os
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

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
        top_100_links = _build_ordered_links(shops, "Top 100")
        south_links = _build_ordered_links(shops, "South")
        map_shops, missing_coords_count = _build_map_shops(shops)
        sidebar_shops = _build_sidebar_shops(shops)
        map_country_aggregates = _build_country_aggregates(map_shops)
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
            "south_links": south_links,
            "google_maps_js_api_key": os.getenv("GOOGLE_MAPS_JS_API_KEY", "").strip(),
            "map_shops": map_shops,
            "sidebar_shops": sidebar_shops,
            "map_country_aggregates": map_country_aggregates,
            "map_missing_coords_count": missing_coords_count,
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


def _load_shops(data_file: Path) -> list[CoffeeShop]:
    if not data_file.exists():
        return []
    return load_previous_state(data_file)


def _build_ordered_links(shops: list[CoffeeShop], category: str) -> list[dict[str, str]]:
    filtered = [shop for shop in shops if shop.category == category]
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
    if shop.city:
        query_parts.append(shop.city)
    if shop.country:
        query_parts.append(shop.country)
    query = ", ".join(query_parts)
    params: dict[str, str] = {"api": "1", "query": query}
    if shop.place_id:
        params["query_place_id"] = shop.place_id
    return f"https://www.google.com/maps/search/?{urlencode(params)}"


def _build_map_shops(shops: list[CoffeeShop]) -> tuple[list[dict[str, object]], int]:
    map_shops: list[dict[str, object]] = []
    missing = 0
    for shop in shops:
        if shop.lat is None or shop.lng is None:
            missing += 1
            continue
        map_shops.append(
            {
                "name": shop.name,
                "city": shop.city,
                "country": shop.country,
                "rank": shop.rank,
                "category": shop.category,
                "lat": shop.lat,
                "lng": shop.lng,
                "place_id": shop.place_id or "",
                "address": shop.formatted_address or shop.address or "",
                "source_url": shop.source_url or "",
                "google_maps_url": _google_maps_link(shop),
            }
        )
    return map_shops, missing


def _build_sidebar_shops(shops: list[CoffeeShop]) -> list[dict[str, object]]:
    ordered = sorted(shops, key=lambda value: (value.rank, value.category, value.name))
    return [
        {
            "name": shop.name,
            "city": shop.city,
            "country": shop.country,
            "rank": shop.rank,
            "category": shop.category,
            "lat": shop.lat,
            "lng": shop.lng,
            "place_id": shop.place_id or "",
            "address": shop.formatted_address or shop.address or "",
            "source_url": shop.source_url or "",
            "google_maps_url": _google_maps_link(shop),
        }
        for shop in ordered
    ]


COUNTRY_COLOR_MAP: dict[str, str] = {
    "Argentina": "#74ACDF",
    "Australia": "#00008B",
    "Austria": "#ED2939",
    "Belgium": "#FDDA24",
    "Bolivia": "#007934",
    "Brazil": "#009C3B",
    "Bulgaria": "#00966E",
    "Canada": "#FF0000",
    "Chile": "#D52B1E",
    "China": "#DE2910",
    "Colombia": "#FCD116",
    "Costa Rica": "#002B7F",
    "Czech Republic": "#D7141A",
    "Denmark": "#C60C30",
    "Dominican Republic": "#002D62",
    "EEUU": "#3C3B6E",
    "Ecuador": "#FFD100",
    "Egypt": "#CE1126",
    "El Salvador": "#0F47AF",
    "England": "#CF081F",
    "Ethiopia": "#009A44",
    "France": "#002395",
    "Greece": "#004C98",
    "Guatemala": "#4997D0",
    "Honduras": "#0073CF",
    "Ireland": "#169B62",
    "Italy": "#008C45",
    "Japan": "#BC002D",
    "Macedonia": "#D20000",
    "Malaysia": "#010066",
    "Mexico": "#006847",
    "México": "#006847",
    "Netherlands": "#AE1C28",
    "Nicaragua": "#0067C6",
    "Norway": "#EF2B2D",
    "Paraguay": "#D52B1E",
    "Peru": "#D91023",
    "Portugal": "#006600",
    "Qatar": "#8D1B3D",
    "Republic of Korea": "#CD2E3A",
    "Romania": "#002B7F",
    "Rwanda": "#20603D",
    "Scotland": "#005EB8",
    "Singapore": "#EF3340",
    "South Africa": "#007749",
    "Spain": "#AA151B",
    "Switzerland": "#D52B1E",
    "Taiwan": "#000095",
    "Thailand": "#A51931",
    "The Philippines": "#0038A8",
    "Turkey": "#E30A17",
    "UAE": "#00732F",
    "United States": "#3C3B6E",
    "Uruguay": "#001489",
    "USA": "#3C3B6E",
    "Venezuela": "#FFCC00",
}


def _build_country_aggregates(map_shops: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for item in map_shops:
        country = str(item.get("country") or "Unknown")
        bucket = grouped.setdefault(
            country,
            {
                "country": country,
                "count": 0,
                "top_count": 0,
                "south_count": 0,
                "lat_sum": 0.0,
                "lng_sum": 0.0,
            },
        )
        bucket["count"] = int(bucket["count"]) + 1
        if item.get("category") == "Top 100":
            bucket["top_count"] = int(bucket["top_count"]) + 1
        if item.get("category") == "South":
            bucket["south_count"] = int(bucket["south_count"]) + 1
        bucket["lat_sum"] = float(bucket["lat_sum"]) + float(item["lat"])
        bucket["lng_sum"] = float(bucket["lng_sum"]) + float(item["lng"])

    aggregates: list[dict[str, object]] = []
    for country, bucket in grouped.items():
        count = int(bucket["count"])
        aggregates.append(
            {
                "country": country,
                "count": count,
                "top_count": int(bucket["top_count"]),
                "south_count": int(bucket["south_count"]),
                "lat": float(bucket["lat_sum"]) / count,
                "lng": float(bucket["lng_sum"]) / count,
                "color": COUNTRY_COLOR_MAP.get(country, "#888899"),
            }
        )

    return sorted(aggregates, key=lambda row: (-int(row["count"]), str(row["country"])))


app = create_app(
    data_file=DEFAULT_DATA_FILE,
    csv_file=DEFAULT_CSV_FILE,
    kml_file=DEFAULT_KML_FILE,
)
