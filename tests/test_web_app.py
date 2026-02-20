import json
from pathlib import Path
import re

from fastapi.testclient import TestClient

from src.web_app import create_app


def _write_state(path: Path) -> None:
    payload = [
        {
            "name": "Coffee Collective",
            "city": "Copenhagen",
            "country": "Denmark",
            "rank": 1,
            "category": "Top 100",
            "lat": 55.6761,
            "lng": 12.5683,
            "place_id": "abc123",
            "formatted_address": "Copenhagen, Denmark",
        },
        {
            "name": "Proud Mary",
            "city": "Melbourne",
            "country": "Australia",
            "rank": 2,
            "category": "South",
            "lat": -37.8136,
            "lng": 144.9631,
            "place_id": "def456",
            "formatted_address": "Melbourne, Australia",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_home_page_renders_summary_and_rows(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    csv_file = tmp_path / "output" / "coffee_shops.csv"
    kml_file = tmp_path / "output" / "coffee_shops.kml"
    _write_state(data_file)
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    csv_file.write_text("rank,name\n1,Coffee Collective\n", encoding="utf-8")
    kml_file.write_text("<kml></kml>", encoding="utf-8")

    app = create_app(data_file=data_file, csv_file=csv_file, kml_file=kml_file)
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Top100BestCoffeeShops Preview" in response.text
    assert '<p class="banner-title">Top 100 Best Coffee Shops 2026</p>' in response.text
    assert response.text.index('class="banner-title"') < response.text.index('class="workspace-head"')
    assert 'data-category="Top 100"' in response.text
    assert 'data-category="South America"' in response.text
    assert 'data-category="South"' not in response.text
    assert 'class="profile-badge"' not in response.text
    assert "Total shops: 2" in response.text
    assert "Top 100: 1" in response.text
    assert "South America: 1" in response.text
    assert 'id="overview-map"' in response.text
    assert "Chat conversation history" not in response.text
    assert "Project canvas and components" not in response.text
    assert "Live preview" not in response.text
    assert "Menu Highlights" not in response.text
    assert "Open Today" not in response.text
    assert "WiFi Speed" not in response.text
    assert "Recent Review" not in response.text
    assert "Book a Table" not in response.text
    assert response.text.index("markerState.map = new google.maps.Map") < response.text.index("if (!sidebarShops.length)")
    assert "Coffee Collective" in response.text
    assert "Proud Mary" in response.text


def test_health_endpoint_reports_ok(tmp_path: Path) -> None:
    app = create_app(
        data_file=tmp_path / "data" / "current_list.json",
        csv_file=tmp_path / "output" / "coffee_shops.csv",
        kml_file=tmp_path / "output" / "coffee_shops.kml",
    )
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_artifact_endpoint_serves_csv(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    csv_file = tmp_path / "output" / "coffee_shops.csv"
    kml_file = tmp_path / "output" / "coffee_shops.kml"
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    csv_file.write_text("rank,name\n1,Coffee Collective\n", encoding="utf-8")

    app = create_app(data_file=data_file, csv_file=csv_file, kml_file=kml_file)
    client = TestClient(app)

    response = client.get("/artifacts/csv")

    assert response.status_code == 200
    assert "Coffee Collective" in response.text


def test_home_page_renders_ordered_google_maps_links_tabs(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    payload = [
        {
            "name": "Shop B",
            "city": "",
            "country": "USA",
            "rank": 2,
            "category": "Top 100",
            "place_id": "pid2",
        },
        {
            "name": "Shop A",
            "city": "",
            "country": "USA",
            "rank": 1,
            "category": "Top 100",
            "place_id": "pid1",
        },
        {
            "name": "Shop S",
            "city": "",
            "country": "Australia",
            "rank": 1,
            "category": "South",
            "place_id": None,
        },
    ]
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(payload), encoding="utf-8")

    app = create_app(
        data_file=data_file,
        csv_file=tmp_path / "output" / "coffee_shops.csv",
        kml_file=tmp_path / "output" / "coffee_shops.kml",
    )
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Top 100 Links" in response.text
    assert "South America Links" in response.text
    assert "<h2>South America</h2>" in response.text
    assert "Shop+A%2C+USA" in response.text
    assert "query_place_id=pid1" in response.text
    assert "Shop+S%2C+Australia" in response.text
    assert response.text.index("Shop A") < response.text.index("Shop B")


def test_map_payload_renders_when_all_coordinates_missing(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    payload = [
        {
            "name": "No Lat 1",
            "city": "Lima",
            "country": "Peru",
            "rank": 1,
            "category": "Top 100",
            "lat": None,
            "lng": None,
        },
        {
            "name": "No Lat 2",
            "city": "Bogota",
            "country": "Colombia",
            "rank": 2,
            "category": "South",
            "lat": None,
            "lng": None,
        },
    ]
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(payload), encoding="utf-8")
    app = create_app(
        data_file=data_file,
        csv_file=tmp_path / "output" / "coffee_shops.csv",
        kml_file=tmp_path / "output" / "coffee_shops.kml",
    )
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert "const mapShops = " in response.text
    assert "No mapped coordinates are available yet" not in response.text
    assert "const mapMissingCoordsCount = 2;" in response.text
    assert "shops are using centroid fallback until lat/lng is available" in response.text


def test_country_normalization_handles_aliases_and_invalid_values(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    payload = [
        {"name": "Shop USA", "city": "", "country": "EEUU", "rank": 1, "category": "Top 100"},
        {"name": "Shop MX", "city": "", "country": "México", "rank": 2, "category": "Top 100"},
        {"name": "Shop Unknown", "city": "", "country": "69", "rank": 3, "category": "South"},
    ]
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(payload), encoding="utf-8")
    app = create_app(
        data_file=data_file,
        csv_file=tmp_path / "output" / "coffee_shops.csv",
        kml_file=tmp_path / "output" / "coffee_shops.kml",
    )
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    countries_match = re.search(r"const mapCountries = (.*?);", response.text, re.DOTALL)
    assert countries_match is not None
    countries_payload = json.loads(countries_match.group(1))
    country_names = {row["country"] for row in countries_payload}
    assert "USA" in country_names
    assert "Mexico" in country_names
    assert "Unknown" in country_names
