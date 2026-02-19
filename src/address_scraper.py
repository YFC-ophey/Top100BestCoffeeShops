from __future__ import annotations

from argparse import ArgumentParser
import csv
from dataclasses import dataclass
import html
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

from src.category_utils import normalize_category
from src.models import CoffeeShop
from src.state import load_previous_state

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = BASE_DIR / "data" / "current_list.json"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"

_CONTACT_SECTION_PATTERN = re.compile(
    r"<h2[^>]*>\s*Contact\s*</h2>(?P<section>.*?)(?:<h2[^>]*>|<div data-elementor-type=\"footer\"|</body>|$)",
    re.IGNORECASE | re.DOTALL,
)
_CONTACT_TEXT_PATTERN = re.compile(
    r'<p[^>]*class="[^"]*elementor-heading-title[^"]*"[^>]*>\s*(?P<text>.*?)\s*</p>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_PATTERN = re.compile(r"<[^>]+>")
_SPACE_PATTERN = re.compile(r"\s+")
_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


@dataclass(slots=True)
class AddressResult:
    rank: int
    coffee_shop: str
    country: str
    category: str
    address: str
    source_url: str
    status: str
    error: str

    def to_csv_row(self) -> dict[str, str]:
        return {
            "Rank": str(self.rank),
            "Coffee Shop": self.coffee_shop,
            "Country": self.country,
            "Address": self.address,
        }

    def to_missing_row(self) -> dict[str, str]:
        return {
            "Rank": str(self.rank),
            "Coffee Shop": self.coffee_shop,
            "Country": self.country,
            "Source URL": self.source_url,
            "Reason": self.status,
            "Error": self.error,
        }


def extract_contact_address(html_content: str) -> str:
    match = _CONTACT_SECTION_PATTERN.search(html_content)
    if not match:
        return ""

    section = match.group("section")
    for entry in _CONTACT_TEXT_PATTERN.finditer(section):
        raw_text = entry.group("text")
        text = html.unescape(_TAG_PATTERN.sub(" ", raw_text))
        text = _SPACE_PATTERN.sub(" ", text).strip(" \t\r\n,")
        if text and not _URL_PATTERN.match(text):
            return text
    return ""


def fetch_html(url: str, timeout_seconds: int = 30) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; CodexAddressScraper/1.0)"})
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="ignore")


def scrape_addresses(
    shops: list[CoffeeShop],
    category: str,
    timeout_seconds: int = 30,
    limit: int | None = None,
) -> list[AddressResult]:
    normalized_filter = category.casefold().strip()
    results: list[AddressResult] = []
    processed = 0

    for shop in sorted(shops, key=lambda value: (value.rank, value.name)):
        normalized_shop_category = normalize_category(shop.category)
        include = normalized_filter == "all" or normalize_category(category) == normalized_shop_category
        if not include:
            continue
        if limit is not None and processed >= limit:
            break

        source_url = (shop.source_url or "").strip()
        status = "ok"
        error = ""
        address = ""
        if not source_url:
            status = "missing_source_url"
        else:
            try:
                html_content = fetch_html(source_url, timeout_seconds=timeout_seconds)
                address = extract_contact_address(html_content)
                if not address:
                    status = "missing_contact_address"
            except Exception as exc:  # pragma: no cover - exercised by CLI in networked runs
                status = "fetch_error"
                error = str(exc)

        results.append(
            AddressResult(
                rank=shop.rank,
                coffee_shop=shop.name,
                country=shop.country,
                category=normalized_shop_category,
                address=address,
                source_url=source_url,
                status=status,
                error=error,
            )
        )
        processed += 1

    return results


def write_address_csv(results: list[AddressResult], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Rank", "Coffee Shop", "Country", "Address"])
        writer.writeheader()
        writer.writerows(result.to_csv_row() for result in results)


def write_missing_csv(results: list[AddressResult], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    missing = [result for result in results if result.status != "ok"]
    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Rank", "Coffee Shop", "Country", "Source URL", "Reason", "Error"],
        )
        writer.writeheader()
        writer.writerows(result.to_missing_row() for result in missing)


def apply_addresses_to_state(data_file: Path, results: list[AddressResult]) -> int:
    payload = json.loads(data_file.read_text(encoding="utf-8"))
    address_by_key = {
        _shop_key(result.rank, result.coffee_shop, result.category): result.address
        for result in results
        if result.status == "ok" and result.address
    }

    updated_count = 0
    for item in payload:
        key = _shop_key(int(item.get("rank", 0)), str(item.get("name", "")), normalize_category(item.get("category")))
        address = address_by_key.get(key)
        if not address:
            continue
        current = str(item.get("formatted_address") or "").strip()
        if current == address:
            continue
        item["formatted_address"] = address
        updated_count += 1

    data_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return updated_count


def _shop_key(rank: int, name: str, category: str) -> str:
    normalized_name = re.sub(r"\W+", "", name.casefold())
    return f"{normalize_category(category)}::{rank}::{normalized_name}"


def _default_output_filename(category: str) -> str:
    if category.casefold().strip() == "all":
        return "all coffee shops address.csv"
    normalized = normalize_category(category)
    return f"{normalized.lower()} coffee shops address.csv"


def main() -> int:
    parser = ArgumentParser(description="Scrape contact addresses for coffee shops")
    parser.add_argument("--category", default="South America", help='Category to scrape: "Top 100", "South America", or "all"')
    parser.add_argument("--data-file", type=Path, default=DEFAULT_DATA_FILE, help="Path to current_list.json")
    parser.add_argument("--output-file", type=Path, default=None, help="Output CSV path")
    parser.add_argument("--missing-output-file", type=Path, default=None, help="Missing-data CSV path")
    parser.add_argument("--timeout", type=int, default=30, help="Per-request timeout seconds")
    parser.add_argument("--limit", type=int, default=None, help="Optional item limit for quick checks")
    parser.add_argument(
        "--update-state",
        action="store_true",
        help="Write scraped addresses into formatted_address fields in current_list.json",
    )
    args = parser.parse_args()

    shops = load_previous_state(args.data_file)
    if not shops:
        print(f"No shops found in {args.data_file}")
        return 1

    output_file = args.output_file or (DEFAULT_OUTPUT_DIR / _default_output_filename(args.category))
    missing_output_file = args.missing_output_file or output_file.with_name(output_file.stem + " missing.csv")

    results = scrape_addresses(
        shops=shops,
        category=args.category,
        timeout_seconds=args.timeout,
        limit=args.limit,
    )
    write_address_csv(results, output_file)
    write_missing_csv(results, missing_output_file)

    updated_count = 0
    if args.update_state:
        updated_count = apply_addresses_to_state(args.data_file, results)

    total = len(results)
    with_address = sum(1 for result in results if result.address)
    missing = sum(1 for result in results if result.status != "ok")
    print(f"Scraped category: {args.category}")
    print(f"Rows processed: {total}")
    print(f"Rows with address: {with_address}")
    print(f"Rows missing/failing: {missing}")
    print(f"Address CSV: {output_file}")
    print(f"Missing CSV: {missing_output_file}")
    if args.update_state:
        print(f"State rows updated with formatted_address: {updated_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
