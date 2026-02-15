"""
Scraper for theworlds100bestcoffeeshops.com.

Extracts shop data (name, rank, country, city, address) from the
Main and South America Top 100 lists, including detail page visits.
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import logging
import os
from urllib.parse import urljoin
from collections import OrderedDict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://theworlds100bestcoffeeshops.com"
MAIN_LIST_URL = f"{BASE_URL}/top-100-coffee-shops/"
SOUTH_LIST_URL = f"{BASE_URL}/top-100-coffee-shops-south/"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubles each retry
REQUEST_DELAY = 1.0  # seconds between detail page requests


def fetch_page(url, retries=MAX_RETRIES):
    """Fetch a URL and return a BeautifulSoup object. Retries with backoff."""
    for attempt in range(retries):
        try:
            response = requests.get(
                url, headers=REQUEST_HEADERS, timeout=15
            )
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as e:
            wait = RETRY_BACKOFF * (2 ** attempt)
            logger.warning(
                f"Attempt {attempt + 1}/{retries} failed for {url}: {e}"
            )
            if attempt < retries - 1:
                logger.info(f"Retrying in {wait}s...")
                time.sleep(wait)
    logger.error(f"All {retries} attempts failed for {url}")
    return None


def _group_links_by_url(links):
    """Group list-page <a> tags by their normalized href.

    Returns an OrderedDict of {url: [link_elements]} preserving
    first-seen order.
    """
    grouped = OrderedDict()
    for link in links:
        href = link.get("href", "")
        full_url = urljoin(BASE_URL, href)
        if "/locales/" not in full_url and "/locales-south/" not in full_url:
            continue
        if full_url in (MAIN_LIST_URL, SOUTH_LIST_URL):
            continue
        grouped.setdefault(full_url, []).append(link)
    return grouped


def _extract_shop_from_links(detail_url, link_elements):
    """Extract name, rank, and country from grouped link elements.

    Each shop on the list page has ~4 links sharing the same href:
      - <a><img ...></a>       (image)
      - <a><h3>rank</h3></a>   (rank number)
      - <a><h2>name</h2></a>   (shop name)
      - <a><p>country</p></a>  (country)
    """
    name = None
    rank = None
    country = None

    for link in link_elements:
        h2 = link.find("h2")
        if h2:
            name = h2.get_text(strip=True)
            continue
        h3 = link.find("h3")
        if h3:
            text = h3.get_text(strip=True)
            if text.isdigit():
                rank = int(text)
            continue
        p_tag = link.find("p")
        if p_tag:
            country = p_tag.get_text(strip=True)
            continue

    return name, rank, country


def _find_city(soup):
    """Find the city name on a detail page.

    The city appears as a short text element near the top of the
    page, typically after the shop name heading and before the
    country. We look for the pattern: h1/h2 (name), then a short
    text element (city), then another short text element (country).
    """
    # Strategy: look for all headings, find the shop name (longest),
    # then look at the elements near it for short text (city name).
    contact_header = _find_contact_header(soup)

    # Collect all text-bearing elements before Contact
    candidates = []
    for el in soup.find_all(["h1", "h2", "h3", "p"]):
        if contact_header and el == contact_header:
            break
        text = el.get_text(strip=True)
        if text:
            candidates.append((el.name, text))

    # Filter for short text elements that look like city names
    # (not the shop name, not navigation text)
    return _pick_city_from_candidates(candidates)


def _pick_city_from_candidates(candidates):
    """Pick the city name from a list of (tag_name, text) candidates.

    The city is typically a short string (< 40 chars) appearing
    after the shop name heading. We skip the first h1/h2 (shop name)
    and look for the next short text element.
    """
    found_title = False
    for tag_name, text in candidates:
        # Skip until we find the first h1/h2 (the shop name)
        if not found_title and tag_name in ("h1", "h2"):
            found_title = True
            continue
        if not found_title:
            continue
        # After the title, the next short text is likely the city
        if len(text) < 40 and not text.startswith("http"):
            return text
    return None


def _find_contact_header(soup):
    """Find the Contact/Contacto section header on a detail page."""
    return soup.find(
        lambda tag: tag.name in ["h2", "h3", "h4"]
        and "ontac" in tag.get_text().lower()
    )


def _find_address(soup):
    """Extract the full address from the Contact section.

    The address is the first text element after the "Contact" h2,
    before any links (website/social URLs).
    """
    contact_header = _find_contact_header(soup)
    if not contact_header:
        return None

    address_parts = []
    current = contact_header.next_sibling
    while current:
        tag_name = getattr(current, "name", None)
        if tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            break
        text = getattr(current, "get_text", lambda **kw: "")
        text_content = text(strip=True)
        if text_content:
            # Stop at URLs (website/social links come after address)
            if text_content.startswith("http"):
                break
            # Skip if the element is an <a> tag with an href
            if tag_name == "a" and current.get("href", ""):
                break
            address_parts.append(text_content)
        current = current.next_sibling

    if address_parts:
        return " ".join(address_parts).strip()
    return None


def extract_detail_info(detail_url):
    """Fetch a detail page and extract city and address.

    Returns a dict with 'city' and 'address' keys.
    """
    soup = fetch_page(detail_url)
    if not soup:
        return {"city": None, "address": None}

    city = _find_city(soup)
    address = _find_address(soup)
    return {"city": city, "address": address}


def parse_list_page(soup, category):
    """Parse a list page and return shop entries without detail info.

    Returns a list of dicts with name, rank, country, category,
    and detail_url. Does NOT fetch detail pages.
    """
    if not soup:
        return []

    links = soup.find_all("a", href=True)
    grouped = _group_links_by_url(links)

    shops = []
    for detail_url, link_elements in grouped.items():
        name, rank, country = _extract_shop_from_links(
            detail_url, link_elements
        )
        if not name:
            logger.warning(f"No name found for {detail_url}, skipping")
            continue

        shops.append({
            "name": name,
            "rank": rank if rank else len(shops) + 1,
            "country": country or "Unknown",
            "category": category,
            "detail_url": detail_url,
        })

    return shops


def scrape_list(list_url, category, delay=REQUEST_DELAY):
    """Scrape a list page and enrich with detail page data.

    Fetches the list page, parses entries, then visits each detail
    page to extract city and address. Applies rate limiting.
    """
    logger.info(f"Scraping list: {category} - {list_url}")
    soup = fetch_page(list_url)
    if not soup:
        return []

    shops = parse_list_page(soup, category)
    logger.info(f"Found {len(shops)} shops in {category} list")

    for shop in shops:
        time.sleep(delay)
        detail = extract_detail_info(shop["detail_url"])
        shop["city"] = detail["city"]
        shop["address"] = detail["address"] or "Address not found"
        logger.info(
            f"#{shop['rank']} {shop['name']} - {shop['city']}, "
            f"{shop['country']}"
        )

    return shops


def scrape_all():
    """Scrape both Main and South lists. Returns combined results."""
    all_shops = []

    main_shops = scrape_list(MAIN_LIST_URL, "Main")
    all_shops.extend(main_shops)

    south_shops = scrape_list(SOUTH_LIST_URL, "South")
    all_shops.extend(south_shops)

    return all_shops


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    logger.info("Starting scrape...")
    results = scrape_all()

    output_file = "data/raw_coffee_shops.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Scraping complete. Saved {len(results)} shops to {output_file}")
