import json
from pathlib import Path

from src.address_scraper import AddressResult, apply_addresses_to_state, extract_contact_address


def test_extract_contact_address_returns_first_non_url_contact_line() -> None:
    html = """
    <div>
      <h2 class="elementor-heading-title">Contact</h2>
      <p class="elementor-heading-title elementor-size-default">Cl. 81a #8-23, Bogotá, Colombia</p>
      <p class="elementor-heading-title elementor-size-default"><a href="https://example.com">https://example.com</a></p>
    </div>
    """

    assert extract_contact_address(html) == "Cl. 81a #8-23, Bogotá, Colombia"


def test_extract_contact_address_returns_empty_when_no_contact_section() -> None:
    html = "<html><body><h2>About</h2><p>No address here</p></body></html>"

    assert extract_contact_address(html) == ""


def test_apply_addresses_to_state_updates_formatted_address_with_legacy_south_alias(tmp_path: Path) -> None:
    data_file = tmp_path / "current_list.json"
    payload = [
        {
            "name": "Tropicalia Coffee",
            "city": "",
            "country": "Colombia",
            "rank": 1,
            "category": "South",
            "source_url": "https://example.com",
            "lat": None,
            "lng": None,
            "place_id": None,
            "formatted_address": None,
        },
        {
            "name": "Onyx Coffee LAB",
            "city": "",
            "country": "USA",
            "rank": 1,
            "category": "Top 100",
            "source_url": "https://example.com",
            "lat": None,
            "lng": None,
            "place_id": None,
            "formatted_address": None,
        },
    ]
    data_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    results = [
        AddressResult(
            rank=1,
            coffee_shop="Tropicalia Coffee",
            country="Colombia",
            category="South America",
            address="Cl. 81a #8-23, Bogotá, Colombia",
            source_url="https://example.com",
            status="ok",
            error="",
        ),
        AddressResult(
            rank=1,
            coffee_shop="Onyx Coffee LAB",
            country="USA",
            category="Top 100",
            address="101 E Walnut Ave Rogers, AR 72756, USA",
            source_url="https://example.com",
            status="ok",
            error="",
        ),
    ]

    updated_count = apply_addresses_to_state(data_file, results)
    updated_payload = json.loads(data_file.read_text(encoding="utf-8"))

    assert updated_count == 2
    assert updated_payload[0]["formatted_address"] == "Cl. 81a #8-23, Bogotá, Colombia"
    assert updated_payload[1]["formatted_address"] == "101 E Walnut Ave Rogers, AR 72756, USA"
