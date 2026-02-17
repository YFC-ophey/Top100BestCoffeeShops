import json
from pathlib import Path

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
    assert "Total shops: 2" in response.text
    assert "Top 100: 1" in response.text
    assert "South: 1" in response.text
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
    assert "Top 100 Map Links" in response.text
    assert "South Map Links" in response.text
    assert "Shop+A%2C+USA" in response.text
    assert "query_place_id=pid1" in response.text
    assert "Shop+S%2C+Australia" in response.text
    assert response.text.index("Shop A") < response.text.index("Shop B")
