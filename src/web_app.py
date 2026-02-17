from collections import Counter
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from src.models import CoffeeShop
from src.state import load_previous_state

BASE_DIR = Path(__file__).resolve().parent.parent
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
        context = {
            "request": request,
            "shops": sorted(shops, key=lambda value: (value.rank, value.category, value.name)),
            "total_shops": len(shops),
            "category_counts": dict(sorted(category_counts.items())),
            "csv_available": app.state.csv_file.exists(),
            "kml_available": app.state.kml_file.exists(),
            "top_100_links": top_100_links,
            "south_links": south_links,
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


app = create_app(
    data_file=DEFAULT_DATA_FILE,
    csv_file=DEFAULT_CSV_FILE,
    kml_file=DEFAULT_KML_FILE,
)
