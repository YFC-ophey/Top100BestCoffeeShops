from argparse import ArgumentParser
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.generator import generate_csv, generate_kml
from src.geocoder import GooglePlacesGeocoder
from src.models import CoffeeShop
from src.scraper import SOURCE_URLS, enrich_shops_with_details, fetch_html, parse_coffee_shops
from src.site_builder import build_static_site
from src.state import has_shop_changes, load_previous_state

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "current_list.json"
KML_FILE = BASE_DIR / "output" / "coffee_shops.kml"
CSV_FILE = BASE_DIR / "output" / "coffee_shops.csv"
SITE_DIR = BASE_DIR / "site"


def scrape_only(sleep_seconds: float = 1.0) -> tuple[list[CoffeeShop], bool]:
    previous = load_previous_state(DATA_FILE)
    all_shops: list[CoffeeShop] = []
    for category, url in SOURCE_URLS.items():
        html = fetch_html(url)
        all_shops.extend(parse_coffee_shops(html, category=category))

    all_shops = enrich_shops_with_details(all_shops, sleep_seconds=sleep_seconds)
    changed = has_shop_changes(previous, all_shops)
    _save_state(all_shops)
    generate_csv(all_shops, CSV_FILE)
    generate_kml(all_shops, KML_FILE)
    return all_shops, changed


def owner_geocode(api_key: str) -> None:
    shops = load_previous_state(DATA_FILE)
    geocoder = GooglePlacesGeocoder(api_key)
    for shop in shops:
        result = geocoder.geocode_shop(shop)
        if result:
            shop.lat = result.lat
            shop.lng = result.lng
            shop.place_id = result.place_id
            shop.formatted_address = result.formatted_address
    _save_state(shops)
    generate_csv(shops, CSV_FILE)
    generate_kml(shops, KML_FILE)


def build_site() -> None:
    build_static_site(DATA_FILE, SITE_DIR, CSV_FILE, KML_FILE)


def _save_state(shops: list[CoffeeShop]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps([shop.to_dict() for shop in shops], indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = ArgumentParser(description="Top 100 coffee shops utility CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    scrape = sub.add_parser("scrape-only", help="Scrape and enrich source data without requiring API keys")
    scrape.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Delay between detail-page requests (default: 1.0)",
    )
    sub.add_parser("build-site", help="Build static site from current_list.json")
    geocode = sub.add_parser("owner-geocode", help="Optional owner-only geocoding refresh")
    geocode.add_argument("--api-key", required=True, help="Owner Google Places API key")
    args = parser.parse_args()

    if args.command == "scrape-only":
        shops, changed = scrape_only(sleep_seconds=args.sleep_seconds)
        print(f"Scraped {len(shops)} shops. Detected changes: {changed}")
        return 0
    if args.command == "build-site":
        build_site()
        print("Site built at site/index.html")
        return 0
    if args.command == "owner-geocode":
        owner_geocode(args.api_key)
        print("Owner geocode refresh complete.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
