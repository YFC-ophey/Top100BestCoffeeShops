import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from src.models import CoffeeShop
from src.web_app import _best_map_query_text, _city_from_address, _google_maps_link, create_app


def _write_state(path: Path) -> None:
    payload = [
        {
            "name": "Coffee Collective",
            "city": "Copenhagen",
            "country": "Denmark",
            "rank": 1,
            "category": "Top 100",
            "lat": None,
            "lng": None,
            "place_id": "abc123",
            "formatted_address": "Copenhagen, Denmark",
        },
        {
            "name": "Proud Mary",
            "city": "Melbourne",
            "country": "Australia",
            "rank": 2,
            "category": "South",
            "lat": None,
            "lng": None,
            "place_id": "def456",
            "formatted_address": "Melbourne, Australia",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_home_page_renders_roast_overview_with_south_america_label(tmp_path: Path) -> None:
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
    assert "ROAST." in response.text
    assert "World's 100 Best Coffee Shops" in response.text
    assert "Interactive map with country-level shop density and source-backed shop details." in response.text
    assert 'class="banner-subtitle"' in response.text
    assert 'id="overview-map"' in response.text
    assert "South America" in response.text
    assert "Data Quality" not in response.text
    assert "Total shops" not in response.text
    assert ">CSV<" not in response.text
    assert ">KML<" not in response.text
    assert "<th>City</th>" in response.text
    assert ">Map</a>" in response.text
    assert "color: var(--brand-gold);" in response.text
    assert "Pins use national flag colors. Zoom out for country density, zoom in for individual shops." in response.text
    assert 'const PIN_PATH = "M 0,-24 C -6.6,-24 -12,-18.6 -12,-12 C -12,-4.8 0,0 0,0 C 0,0 12,-4.8 12,-12 C 12,-18.6 6.6,-24 0,-24 Z";' in response.text
    assert 'gestureHandling: "greedy"' in response.text
    assert "zoomControl: true" in response.text
    assert "#f6d57c" in response.text
    assert "focusCountry: null" in response.text
    assert "World's Best Coffee Shops Complete Map" in response.text
    assert "https://buymeacoffee.com/opheliachen" in response.text


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


def test_home_page_renders_map_links_and_legacy_south_normalization(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    payload = [
        {
            "name": "Shop B",
            "city": "",
            "country": "USA",
            "rank": 2,
            "category": "Top 100",
            "formatted_address": "Bleecker St, New York, NY 10014, USA",
        },
        {
            "name": "Shop A",
            "city": "",
            "country": "USA",
            "rank": 1,
            "category": "Top 100",
            "place_id": "pid1",
            "formatted_address": "R. dos Sapateiros 111, 1100-619 Lisbon, Portugal",
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
    assert "Top 100 Links" not in response.text
    assert "South America Links" not in response.text
    assert "Shop+A%2C+USA" not in response.text
    assert "R.+dos+Sapateiros+111%2C+1100-619+Lisbon%2C+Portugal" in response.text
    assert "query_place_id=pid1" in response.text
    assert "Shop+S%2C+Australia" in response.text
    assert response.text.index("Shop A") < response.text.index("Shop B")
    assert "South America" in response.text
    assert ">Map</a>" in response.text
    assert "shopPosition(" not in response.text
    assert "hashString(" not in response.text


def test_overview_table_map_links_are_per_row_direct_google_maps_targets(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    payload = [
        {
            "name": "Shop A",
            "city": "Lisbon",
            "country": "Portugal",
            "rank": 1,
            "category": "Top 100",
            "place_id": "pid1",
            "formatted_address": "R. dos Sapateiros 111, 1100-619 Lisbon, Portugal",
        },
        {
            "name": "Shop B",
            "city": "Miraflores",
            "country": "Peru",
            "rank": 2,
            "category": "South America",
            "place_id": None,
            "formatted_address": "Entre Pardos Chicken y Wong, Mal. de la Reserva 610, Miraflores 15074, Peru",
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
    html = response.text

    match_a = re.search(
        r"<tr>\s*<td>1</td>\s*<td>Shop A</td>.*?<a href=\"([^\"]+)\" target=\"_blank\" rel=\"noopener\">Map</a>",
        html,
        flags=re.DOTALL,
    )
    assert match_a, "Shop A row should include a map link in the map column."
    assert "query_place_id=pid1" in match_a.group(1)
    assert "R.+dos+Sapateiros+111%2C+1100-619+Lisbon%2C+Portugal" in match_a.group(1)

    match_b = re.search(
        r"<tr>\s*<td>2</td>\s*<td>Shop B</td>.*?<a href=\"([^\"]+)\" target=\"_blank\" rel=\"noopener\">Map</a>",
        html,
        flags=re.DOTALL,
    )
    assert match_b, "Shop B row should include a map link in the map column."
    assert "query_place_id=" not in match_b.group(1)
    assert "Entre+Pardos+Chicken+y+Wong%2C+Mal.+de+la+Reserva+610%2C+Miraflores+15074%2C+Peru" in match_b.group(1)


def test_overview_payload_uses_country_markers_without_shop_coordinates(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    payload = [
        {
            "name": "Metric",
            "city": "",
            "country": "EEUU",
            "rank": 95,
            "category": "Top 100",
            "place_id": None,
            "lat": None,
            "lng": None,
            "formatted_address": None,
        },
        {
            "name": "El Terrible Juan Café",
            "city": "",
            "country": "México",
            "rank": 96,
            "category": "Top 100",
            "place_id": None,
            "lat": None,
            "lng": None,
            "formatted_address": None,
        },
        {
            "name": "Azura",
            "city": "",
            "country": "69",
            "rank": 68,
            "category": "Top 100",
            "place_id": None,
            "lat": None,
            "lng": None,
            "formatted_address": None,
        },
        {
            "name": "Malformed Country Shop",
            "city": "",
            "country": "1234",
            "rank": 67,
            "category": "Top 100",
            "place_id": None,
            "lat": None,
            "lng": None,
            "formatted_address": None,
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
    assert '"country_normalized": "USA"' in response.text
    assert '"country_normalized": "Mexico"' in response.text
    assert '"country_normalized": "Oman"' in response.text
    assert '"country_normalized": "Unknown"' in response.text


def test_google_maps_link_uses_required_precedence_rules() -> None:
    with_place_id = CoffeeShop(
        name="The Folks",
        city="Lisbon",
        country="Portugal",
        rank=88,
        category="Top 100",
        place_id="abc123",
        formatted_address="R. dos Sapateiros 111, 1100-619 Lisbon, Portugal",
    )
    with_address_only = CoffeeShop(
        name="Puku Puku",
        city="Miraflores",
        country="Peru",
        rank=69,
        category="South America",
        address="Entre Pardos Chicken y Wong, Mal. de la Reserva 610, Miraflores 15074, Peru",
        source_url="https://example.com",
        formatted_address=None,
    )

    with_name_city_country = CoffeeShop(
        name="Onyx Coffee LAB",
        city="Rogers, Arkansas",
        country="USA",
        rank=1,
        category="Top 100",
        formatted_address=None,
    )
    with_name_country = CoffeeShop(
        name="Shop No City",
        city="",
        country="Japan",
        rank=50,
        category="Top 100",
        formatted_address=None,
    )

    place_link = _google_maps_link(with_place_id)
    place_query = parse_qs(urlparse(place_link).query)
    assert place_query["query"] == ["R. dos Sapateiros 111, 1100-619 Lisbon, Portugal"]
    assert place_query["query_place_id"] == ["abc123"]

    address_link = _google_maps_link(with_address_only)
    address_query = parse_qs(urlparse(address_link).query)
    assert address_query["query"] == [
        "Entre Pardos Chicken y Wong, Mal. de la Reserva 610, Miraflores 15074, Peru"
    ]
    assert "query_place_id" not in address_query

    city_link = _google_maps_link(with_name_city_country)
    city_query = parse_qs(urlparse(city_link).query)
    assert city_query["query"] == ["Onyx Coffee LAB, Rogers, Arkansas, USA"]

    country_link = _google_maps_link(with_name_country)
    country_query = parse_qs(urlparse(country_link).query)
    assert country_query["query"] == ["Shop No City, Japan"]


def test_best_map_query_text_sanitizes_entities_and_duplicate_country_suffix() -> None:
    noisy = CoffeeShop(
        name="Azura &#8211; The Coffee Company",
        city="Muscat",
        country="Oman",
        rank=68,
        category="Top 100",
        formatted_address="Way Number: 9203 Building Number: 790, Muscat, Oman, Oman, Unknown",
    )
    query = _best_map_query_text(noisy)
    assert "&#8211;" not in query
    assert "Unknown" not in query
    assert "Oman, Oman" not in query
    assert "Muscat, Oman" in query

    duplicate_tokens = CoffeeShop(
        name="Repeat City Cafe",
        city="",
        country="Peru",
        rank=2,
        category="Top 100",
        formatted_address="Miraflores, Peru, Miraflores, Peru",
    )
    deduped_query = _best_map_query_text(duplicate_tokens)
    assert deduped_query == "Miraflores, Peru"


def test_rank_68_top_100_is_corrected_to_azure_muscat_oman(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    payload = [
        {
            "name": "Azura &#8211; The Coffee Company",
            "city": "",
            "country": "69",
            "rank": 68,
            "category": "Top 100",
            "formatted_address": "Way Number: 9203 Building Number: 790, Muscat, Oman",
        }
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
    assert "Azure The Coffee Company" in response.text
    assert '"country_normalized": "Oman"' in response.text
    assert '"city": "Muscat"' in response.text
    assert "Multiple locations, Muscat, Oman" in response.text


def test_city_extraction_derives_city_from_address_patterns() -> None:
    assert _city_from_address("R. dos Sapateiros 111, 1100-619 Lisbon, Portugal", "Portugal") == "Lisbon"
    assert _city_from_address("101 E Walnut Ave Rogers, AR 72756, USA", "USA") == "Rogers"
    assert _city_from_address("Shop 2/118 Willoughby Rd, Crows Nest NSW 2065, Australia", "Australia") == "Crows Nest"
    assert _city_from_address("Calle, Calle Pte. Bolognesi 216, Arequipa, Perú", "Peru") == "Arequipa"
    assert _city_from_address("73 Berkeley St., Glasgow G3 7DX, United Kingdom", "United Kingdom") == "Glasgow"
    assert _city_from_address("Bayfield Rd, Portree IV51 9EL, United Kingdom", "United Kingdom") == "Portree"
    assert _city_from_address("205B Emmet Rd, Inchicore, Dublin 8, D08 EN29, Ireland", "Ireland") == "Dublin"
    assert (
        _city_from_address("403, Taiwan, Taichung City, West District, Fulong St, 7號1樓", "Taiwan")
        == "Taichung City"
    )
    assert (
        _city_from_address("Conesa 3705, C1429 C1429ALQ, Cdad. Autónoma de Buenos Aires, Argentina", "Argentina")
        == "Buenos Aires"
    )
    assert (
        _city_from_address("Carlos Bories 385, 6160000 Natales, Magallanes y la Antártica Chilena, Chile", "Chile")
        == "Natales"
    )


def test_home_page_uses_address_city_when_explicit_city_is_noisy(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    payload = [
        {
            "name": "Kafi Wasi Café Tostaduría",
            "city": "a white sillar (ashlar [volcanic stone]) district",
            "country": "Peru",
            "rank": 17,
            "category": "South America",
            "formatted_address": "Calle Pte. Bolognesi 216, Arequipa 04001, Peru",
        }
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
    assert '"city": "Arequipa"' in response.text
    assert "a white sillar (ashlar [volcanic stone]) district" not in response.text
