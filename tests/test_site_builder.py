import json
from pathlib import Path

from src.site_builder import build_static_site


def test_build_static_site_generates_index_and_styles(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    output_csv = tmp_path / "output" / "coffee_shops.csv"
    output_kml = tmp_path / "output" / "coffee_shops.kml"
    site_dir = tmp_path / "site"
    payload = [
        {"name": "A", "city": "Copenhagen", "country": "Denmark", "rank": 1, "category": "Top 100"},
        {"name": "B", "city": "Lima", "country": "Peru", "rank": 1, "category": "South"},
    ]
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(payload), encoding="utf-8")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_csv.write_text("rank,name\n1,A\n", encoding="utf-8")
    output_kml.write_text("<kml></kml>", encoding="utf-8")

    build_static_site(data_file=data_file, site_dir=site_dir, csv_file=output_csv, kml_file=output_kml)

    index = (site_dir / "index.html").read_text(encoding="utf-8")
    style = (site_dir / "assets" / "style.css").read_text(encoding="utf-8")
    assert 'id="overview-map"' in index
    assert "Main Top 100" in index
    assert "South America" in index
    assert "Chat conversation history" not in index
    assert "Project canvas and components" not in index
    assert "Live preview" not in index
    assert "Menu Highlights" not in index
    assert "Open Today" not in index
    assert "WiFi Speed" not in index
    assert "Recent Review" not in index
    assert "Book a Table" not in index
    assert "Open in Google Maps" in index
    assert "Download CSV" in index
    assert "--api-key $GOOGLE_MAPS_JS_API_KEY" in index
    assert '"$GOOGLE_MAPS_JS_API_KEY"' not in index
    assert 'const googleMapsKey = "";' in index
    assert index.index("markerState.map = new google.maps.Map") < index.index("if (!mapShops.length)")
    assert "top10" in style


def test_build_static_site_does_not_embed_env_api_key(tmp_path: Path, monkeypatch) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    output_csv = tmp_path / "output" / "coffee_shops.csv"
    output_kml = tmp_path / "output" / "coffee_shops.kml"
    site_dir = tmp_path / "site"
    payload = [{"name": "A", "city": "Copenhagen", "country": "Denmark", "rank": 1, "category": "Top 100"}]
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(payload), encoding="utf-8")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_csv.write_text("rank,name\n1,A\n", encoding="utf-8")
    output_kml.write_text("<kml></kml>", encoding="utf-8")

    monkeypatch.setenv("GOOGLE_MAPS_JS_API_KEY", "TEST_MAPS_KEY_PLACEHOLDER_DO_NOT_USE")

    build_static_site(data_file=data_file, site_dir=site_dir, csv_file=output_csv, kml_file=output_kml)

    index = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "TEST_MAPS_KEY_PLACEHOLDER_DO_NOT_USE" not in index
    assert 'const googleMapsKey = "";' in index
