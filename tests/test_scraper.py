"""Tests for scraper parsing logic (no network calls)."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scraper import (
    _group_links_by_url,
    _extract_shop_from_links,
    _find_city,
    _find_address,
    _find_contact_header,
    _pick_city_from_candidates,
    parse_list_page,
)
from tests.conftest import (
    make_soup,
    MOCK_LIST_HTML,
    MOCK_SOUTH_LIST_HTML,
    MOCK_DETAIL_HTML,
    MOCK_DETAIL_CONTACTO_HTML,
    MOCK_DETAIL_NO_CONTACT_HTML,
    MOCK_DETAIL_URL_IN_TEXT,
)


# ---------------------------------------------------------------------------
# _group_links_by_url
# ---------------------------------------------------------------------------

class TestGroupLinksByUrl:
    def test_groups_links_by_detail_url(self):
        soup = make_soup(MOCK_LIST_HTML)
        links = soup.find_all("a", href=True)
        grouped = _group_links_by_url(links)
        assert len(grouped) == 3
        urls = list(grouped.keys())
        assert urls[0].endswith("/locales/tobbys-estate/")
        assert urls[1].endswith("/locales/onyx-coffee-lab/")
        assert urls[2].endswith("/locales/gota-coffee-experts/")

    def test_each_shop_has_four_links(self):
        soup = make_soup(MOCK_LIST_HTML)
        grouped = _group_links_by_url(soup.find_all("a", href=True))
        for url, elements in grouped.items():
            assert len(elements) == 4

    def test_ignores_non_locale_links(self):
        soup = make_soup(MOCK_LIST_HTML)
        grouped = _group_links_by_url(soup.find_all("a", href=True))
        for url in grouped:
            assert "/locales/" in url or "/locales-south/" in url

    def test_handles_south_urls(self):
        soup = make_soup(MOCK_SOUTH_LIST_HTML)
        grouped = _group_links_by_url(soup.find_all("a", href=True))
        assert len(grouped) == 1
        assert "/locales-south/" in list(grouped.keys())[0]

    def test_normalizes_relative_urls(self):
        soup = make_soup(MOCK_LIST_HTML)
        grouped = _group_links_by_url(soup.find_all("a", href=True))
        for url in grouped:
            assert url.startswith("https://")


# ---------------------------------------------------------------------------
# _extract_shop_from_links
# ---------------------------------------------------------------------------

class TestExtractShopFromLinks:
    def _get_shop_links(self, index=0):
        soup = make_soup(MOCK_LIST_HTML)
        grouped = _group_links_by_url(soup.find_all("a", href=True))
        url, elements = list(grouped.items())[index]
        return url, elements

    def test_extracts_name(self):
        url, el = self._get_shop_links(0)
        name, _, _ = _extract_shop_from_links(url, el)
        assert name == "Toby's Estate Coffee Roasters"

    def test_extracts_rank(self):
        url, el = self._get_shop_links(0)
        _, rank, _ = _extract_shop_from_links(url, el)
        assert rank == 1

    def test_extracts_country(self):
        url, el = self._get_shop_links(0)
        _, _, country = _extract_shop_from_links(url, el)
        assert country == "Australia"

    def test_second_shop(self):
        url, el = self._get_shop_links(1)
        name, rank, country = _extract_shop_from_links(url, el)
        assert name == "Onyx Coffee LAB"
        assert rank == 2
        assert country == "USA"

    def test_missing_elements_return_none(self):
        html = '<a href="/locales/test/"><img src="x.jpg"/></a>'
        soup = make_soup(html)
        grouped = _group_links_by_url(soup.find_all("a", href=True))
        url, el = list(grouped.items())[0]
        name, rank, country = _extract_shop_from_links(url, el)
        assert name is None
        assert rank is None
        assert country is None


# ---------------------------------------------------------------------------
# _find_city
# ---------------------------------------------------------------------------

class TestFindCity:
    def test_standard_detail(self):
        assert _find_city(make_soup(MOCK_DETAIL_HTML)) == "Sydney"

    def test_contacto_detail(self):
        assert _find_city(make_soup(MOCK_DETAIL_CONTACTO_HTML)) == "Bogota"

    def test_no_contact_section(self):
        assert _find_city(make_soup(MOCK_DETAIL_NO_CONTACT_HTML)) == "Berlin"

    def test_empty_page(self):
        assert _find_city(make_soup("<html><body></body></html>")) is None


# ---------------------------------------------------------------------------
# _find_address
# ---------------------------------------------------------------------------

class TestFindAddress:
    def test_contact_section(self):
        addr = _find_address(make_soup(MOCK_DETAIL_HTML))
        assert addr == "32-36 City Rd, Chippendale NSW 2008, Australia"

    def test_contacto_section(self):
        addr = _find_address(make_soup(MOCK_DETAIL_CONTACTO_HTML))
        assert addr == "Cl. 81a #8-23, Bogota, Colombia"

    def test_no_contact_returns_none(self):
        assert _find_address(make_soup(MOCK_DETAIL_NO_CONTACT_HTML)) is None

    def test_stops_before_url_text(self):
        addr = _find_address(make_soup(MOCK_DETAIL_URL_IN_TEXT))
        assert addr == "1-2-3 Shibuya, Tokyo, Japan"
        assert "http" not in addr

    def test_stops_before_link_element(self):
        addr = _find_address(make_soup(MOCK_DETAIL_HTML))
        assert "tobysestate" not in addr
        assert "instagram" not in addr


# ---------------------------------------------------------------------------
# _find_contact_header
# ---------------------------------------------------------------------------

class TestFindContactHeader:
    def test_finds_contact(self):
        h = _find_contact_header(make_soup(MOCK_DETAIL_HTML))
        assert h is not None and h.get_text(strip=True) == "Contact"

    def test_finds_contacto(self):
        h = _find_contact_header(make_soup(MOCK_DETAIL_CONTACTO_HTML))
        assert h is not None and h.get_text(strip=True) == "Contacto"

    def test_returns_none_when_missing(self):
        assert _find_contact_header(
            make_soup(MOCK_DETAIL_NO_CONTACT_HTML)
        ) is None


# ---------------------------------------------------------------------------
# _pick_city_from_candidates
# ---------------------------------------------------------------------------

class TestPickCityFromCandidates:
    def test_picks_city_after_title(self):
        candidates = [("h1", "Shop Name"), ("p", "Sydney"), ("p", "AU")]
        assert _pick_city_from_candidates(candidates) == "Sydney"

    def test_skips_long_text(self):
        candidates = [
            ("h1", "Shop Name"),
            ("p", "A very long description that cannot be a city name "
                  "because it exceeds forty characters for sure"),
            ("p", "Melbourne"),
        ]
        assert _pick_city_from_candidates(candidates) == "Melbourne"

    def test_skips_urls(self):
        candidates = [
            ("h2", "Shop"), ("p", "http://example.com"), ("p", "Tokyo"),
        ]
        assert _pick_city_from_candidates(candidates) == "Tokyo"

    def test_no_title_returns_none(self):
        assert _pick_city_from_candidates([("p", "Sydney")]) is None

    def test_empty_returns_none(self):
        assert _pick_city_from_candidates([]) is None


# ---------------------------------------------------------------------------
# parse_list_page
# ---------------------------------------------------------------------------

class TestParseListPage:
    def test_parses_three_shops(self):
        shops = parse_list_page(make_soup(MOCK_LIST_HTML), "Main")
        assert len(shops) == 3

    def test_shop_structure(self):
        shops = parse_list_page(make_soup(MOCK_LIST_HTML), "Main")
        s = shops[0]
        assert s["name"] == "Toby's Estate Coffee Roasters"
        assert s["rank"] == 1
        assert s["country"] == "Australia"
        assert s["category"] == "Main"
        assert s["detail_url"].endswith("/locales/tobbys-estate/")

    def test_all_ranks_and_countries(self):
        shops = parse_list_page(make_soup(MOCK_LIST_HTML), "Main")
        assert [(s["rank"], s["country"]) for s in shops] == [
            (1, "Australia"), (2, "USA"), (3, "Austria"),
        ]

    def test_south_category(self):
        shops = parse_list_page(make_soup(MOCK_SOUTH_LIST_HTML), "South")
        assert len(shops) == 1
        assert shops[0]["category"] == "South"
        assert shops[0]["name"] == "Tropicalia Coffee"
        assert shops[0]["country"] == "Colombia"

    def test_none_soup_returns_empty(self):
        assert parse_list_page(None, "Main") == []

    def test_no_shops_returns_empty(self):
        html = "<html><body><a href='/about/'>About</a></body></html>"
        assert parse_list_page(make_soup(html), "Main") == []
