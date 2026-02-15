"""Integration tests for scraper (mocked network calls)."""

import sys
import os
from unittest.mock import patch, MagicMock

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scraper import (
    fetch_page,
    extract_detail_info,
    scrape_list,
    scrape_all,
)
from tests.conftest import (
    make_soup,
    MOCK_LIST_HTML,
    MOCK_SOUTH_LIST_HTML,
    MOCK_DETAIL_HTML,
    MOCK_DETAIL_CONTACTO_HTML,
    MOCK_DETAIL_ONYX,
    MOCK_DETAIL_GOTA,
)


# ---------------------------------------------------------------------------
# fetch_page (retry logic)
# ---------------------------------------------------------------------------

class TestFetchPage:
    @patch("src.scraper.requests.get")
    def test_returns_soup_on_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello</body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_page("http://example.com")
        assert result is not None
        assert result.find("body").text == "Hello"

    @patch("src.scraper.time.sleep")
    @patch("src.scraper.requests.get")
    def test_retries_on_failure(self, mock_get, mock_sleep):
        mock_get.side_effect = [
            requests.ConnectionError("fail"),
            requests.ConnectionError("fail"),
            MagicMock(
                text="<html><body>OK</body></html>",
                raise_for_status=MagicMock(),
            ),
        ]
        result = fetch_page("http://example.com", retries=3)
        assert result is not None
        assert mock_get.call_count == 3

    @patch("src.scraper.time.sleep")
    @patch("src.scraper.requests.get")
    def test_returns_none_after_all_retries(self, mock_get, mock_sleep):
        mock_get.side_effect = requests.ConnectionError("fail")
        result = fetch_page("http://example.com", retries=3)
        assert result is None
        assert mock_get.call_count == 3

    @patch("src.scraper.time.sleep")
    @patch("src.scraper.requests.get")
    def test_backoff_timing(self, mock_get, mock_sleep):
        mock_get.side_effect = requests.ConnectionError("fail")
        fetch_page("http://example.com", retries=3)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(2)
        mock_sleep.assert_any_call(4)


# ---------------------------------------------------------------------------
# extract_detail_info
# ---------------------------------------------------------------------------

class TestExtractDetailInfo:
    @patch("src.scraper.fetch_page")
    def test_returns_city_and_address(self, mock_fetch):
        mock_fetch.return_value = make_soup(MOCK_DETAIL_HTML)
        result = extract_detail_info("http://example.com/locales/test/")
        assert result["city"] == "Sydney"
        assert "Chippendale" in result["address"]

    @patch("src.scraper.fetch_page")
    def test_returns_none_on_fetch_failure(self, mock_fetch):
        mock_fetch.return_value = None
        result = extract_detail_info("http://example.com/locales/test/")
        assert result["city"] is None
        assert result["address"] is None


# ---------------------------------------------------------------------------
# scrape_list (full integration)
# ---------------------------------------------------------------------------

class TestScrapeList:
    @patch("src.scraper.time.sleep")
    @patch("src.scraper.fetch_page")
    def test_integrates_list_and_detail_data(self, mock_fetch, mock_sleep):
        mock_fetch.side_effect = [
            make_soup(MOCK_LIST_HTML),
            make_soup(MOCK_DETAIL_HTML),
            make_soup(MOCK_DETAIL_ONYX),
            make_soup(MOCK_DETAIL_GOTA),
        ]
        shops = scrape_list("http://example.com/list", "Main", delay=0)

        assert len(shops) == 3
        assert shops[0]["name"] == "Toby's Estate Coffee Roasters"
        assert shops[0]["city"] == "Sydney"
        assert shops[0]["country"] == "Australia"
        assert shops[0]["rank"] == 1
        assert shops[0]["category"] == "Main"
        assert "Chippendale" in shops[0]["address"]
        assert shops[1]["city"] == "Rogers"
        assert shops[2]["city"] == "Vienna"

    @patch("src.scraper.fetch_page")
    def test_returns_empty_on_list_failure(self, mock_fetch):
        mock_fetch.return_value = None
        assert scrape_list("http://x.com/list", "Main", delay=0) == []

    @patch("src.scraper.time.sleep")
    @patch("src.scraper.fetch_page")
    def test_handles_detail_failure(self, mock_fetch, mock_sleep):
        mock_fetch.side_effect = [
            make_soup(MOCK_SOUTH_LIST_HTML),
            None,
        ]
        shops = scrape_list("http://x.com/south", "South", delay=0)
        assert len(shops) == 1
        assert shops[0]["city"] is None
        assert shops[0]["address"] == "Address not found"


# ---------------------------------------------------------------------------
# scrape_all
# ---------------------------------------------------------------------------

class TestScrapeAll:
    @patch("src.scraper.scrape_list")
    def test_combines_main_and_south(self, mock_scrape):
        mock_scrape.side_effect = [
            [{"name": "A", "category": "Main"}],
            [{"name": "B", "category": "South"}],
        ]
        result = scrape_all()
        assert len(result) == 2
        assert result[0]["category"] == "Main"
        assert result[1]["category"] == "South"

    @patch("src.scraper.scrape_list")
    def test_handles_empty(self, mock_scrape):
        mock_scrape.side_effect = [[], []]
        assert scrape_all() == []


# ---------------------------------------------------------------------------
# Output format (Phase 2 compatibility)
# ---------------------------------------------------------------------------

class TestOutputFormat:
    @patch("src.scraper.time.sleep")
    @patch("src.scraper.fetch_page")
    def test_all_required_keys_present(self, mock_fetch, mock_sleep):
        mock_fetch.side_effect = [
            make_soup(MOCK_SOUTH_LIST_HTML),
            make_soup(MOCK_DETAIL_CONTACTO_HTML),
        ]
        shops = scrape_list("http://x.com/south", "South", delay=0)
        required = {
            "name", "city", "country", "rank",
            "category", "detail_url", "address",
        }
        assert set(shops[0].keys()) == required
