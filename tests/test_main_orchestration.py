from pathlib import Path
from unittest.mock import patch

import main
from src.models import CoffeeShop


def test_run_returns_changed_true_when_no_previous_state(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    kml_file = tmp_path / "output" / "coffee_shops.kml"
    csv_file = tmp_path / "output" / "coffee_shops.csv"

    with patch.object(main, "DATA_FILE", data_file), \
         patch.object(main, "KML_FILE", kml_file), \
         patch.object(main, "CSV_FILE", csv_file), \
         patch.object(main, "SOURCE_URLS", {"Top 100": "https://example.com"}), \
         patch.object(main, "fetch_html", return_value="<li>1. A - X, Y</li>"):
        shops, changed = main.run(api_key=None)

    assert len(shops) == 1
    assert changed is True
    assert data_file.exists()
    assert kml_file.exists()
    assert csv_file.exists()


def test_run_returns_changed_false_when_state_is_same(tmp_path: Path) -> None:
    data_file = tmp_path / "data" / "current_list.json"
    kml_file = tmp_path / "output" / "coffee_shops.kml"
    csv_file = tmp_path / "output" / "coffee_shops.csv"

    previous = [CoffeeShop(name="A", city="X", country="Y", rank=1, category="Top 100")]
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text("""[
  {
    "name": "A",
    "city": "X",
    "country": "Y",
    "rank": 1,
    "category": "Top 100",
    "lat": null,
    "lng": null,
    "place_id": null,
    "formatted_address": null
  }
]""", encoding="utf-8")

    with patch.object(main, "DATA_FILE", data_file), \
         patch.object(main, "KML_FILE", kml_file), \
         patch.object(main, "CSV_FILE", csv_file), \
         patch.object(main, "SOURCE_URLS", {"Top 100": "https://example.com"}), \
         patch.object(main, "fetch_html", return_value="<li>1. A - X, Y</li>"):
        _shops, changed = main.run(api_key=None)

    assert changed is False
