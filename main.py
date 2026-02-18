from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Iterable

from src.geocoder import GooglePlacesGeocoder
from src.generator import generate_csv, generate_kml
from src.models import CoffeeShop
from src.scraper import SOURCE_URLS, fetch_html, parse_coffee_shops
from src.state import has_shop_changes, load_previous_state

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "current_list.json"
KML_FILE = BASE_DIR / "output" / "coffee_shops.kml"
CSV_FILE = BASE_DIR / "output" / "coffee_shops.csv"


def _save_state(shops: Iterable[CoffeeShop]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps([shop.to_dict() for shop in shops], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def run(api_key: str | None = None) -> tuple[list[CoffeeShop], bool]:
    previous_shops = load_previous_state(DATA_FILE)

    all_shops: list[CoffeeShop] = []
    for category, url in SOURCE_URLS.items():
        html = fetch_html(url)
        all_shops.extend(parse_coffee_shops(html, category=category))

    if api_key:
        geocoder = GooglePlacesGeocoder(api_key)
        geocoded: list[CoffeeShop] = []
        for shop in all_shops:
            result = geocoder.geocode_shop(shop)
            if result:
                shop.lat = result.lat
                shop.lng = result.lng
                shop.place_id = result.place_id
                shop.formatted_address = result.formatted_address
            geocoded.append(shop)
        all_shops = geocoded

    changed = has_shop_changes(previous_shops, all_shops)
    _save_state(all_shops)
    generate_kml(all_shops, KML_FILE)
    generate_csv(all_shops, CSV_FILE)
    return all_shops, changed


def main() -> int:
    parser = ArgumentParser(description="Coffee map auto-sync")
    parser.add_argument(
        "--api-key",
        default=None,
        help="Google Maps Places API key (optional for geocoding)",
    )
    args = parser.parse_args()

    _shops, changed = run(api_key=args.api_key)
    print(f"Detected changes: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
