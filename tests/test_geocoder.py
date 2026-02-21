import io
import json
from urllib.error import URLError
from unittest.mock import patch

from src.geocoder import GooglePlacesGeocoder
from src.models import CoffeeShop


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_geocode_shop_returns_first_candidate() -> None:
    payload = {
        "status": "OK",
        "candidates": [
            {
                "place_id": "abc123",
                "formatted_address": "Godthabsvej 34B, 2000 Frederiksberg, Denmark",
                "geometry": {"location": {"lat": 55.686, "lng": 12.532}},
            }
        ],
    }

    with patch("urllib.request.urlopen", return_value=_FakeResponse(json.dumps(payload).encode())):
        geocoder = GooglePlacesGeocoder(api_key="test-key")
        shop = CoffeeShop(
            name="Coffee Collective",
            city="Copenhagen",
            country="Denmark",
            rank=1,
            category="Top 100",
        )

        result = geocoder.geocode_shop(shop)

    assert result is not None
    assert result.place_id == "abc123"
    assert result.lat == 55.686
    assert result.lng == 12.532


def test_geocode_shop_returns_none_when_no_candidates() -> None:
    payload = {"status": "ZERO_RESULTS", "candidates": []}

    with patch(
        "urllib.request.urlopen",
        side_effect=[
            _FakeResponse(json.dumps(payload).encode()),
            _FakeResponse(json.dumps({"status": "ZERO_RESULTS", "results": []}).encode()),
        ],
    ):
        geocoder = GooglePlacesGeocoder(api_key="test-key")
        shop = CoffeeShop(
            name="Unknown",
            city="Nowhere",
            country="Noland",
            rank=1,
            category="Top 100",
        )

        result = geocoder.geocode_shop(shop)

    assert result is None
    assert geocoder.last_status == "ZERO_RESULTS"


def test_geocode_shop_falls_back_to_geocoding_api_when_places_has_zero_results() -> None:
    places_payload = {"status": "ZERO_RESULTS", "candidates": []}
    geocode_payload = {
        "status": "OK",
        "results": [
            {
                "place_id": "geo123",
                "formatted_address": "R. dos Sapateiros 111, 1100-619 Lisboa, Portugal",
                "geometry": {"location": {"lat": 38.71066, "lng": -9.13922}},
            }
        ],
    }

    with patch(
        "urllib.request.urlopen",
        side_effect=[
            _FakeResponse(json.dumps(places_payload).encode()),
            _FakeResponse(json.dumps(geocode_payload).encode()),
        ],
    ):
        geocoder = GooglePlacesGeocoder(api_key="test-key")
        shop = CoffeeShop(
            name="The Folks",
            city="Lisbon",
            country="Portugal",
            rank=88,
            category="Top 100",
        )

        result = geocoder.geocode_shop(shop)

    assert result is not None
    assert result.place_id == "geo123"
    assert result.lat == 38.71066
    assert result.lng == -9.13922
    assert geocoder.last_status == "OK"


def test_geocode_shop_retries_and_recovers_on_transient_error() -> None:
    payload = {
        "status": "OK",
        "candidates": [
            {
                "place_id": "abc123",
                "formatted_address": "Godthabsvej 34B, 2000 Frederiksberg, Denmark",
                "geometry": {"location": {"lat": 55.686, "lng": 12.532}},
            }
        ],
    }
    sleeper_calls: list[float] = []

    with patch(
        "urllib.request.urlopen",
        side_effect=[URLError("temporary"), _FakeResponse(json.dumps(payload).encode())],
    ):
        geocoder = GooglePlacesGeocoder(
            api_key="test-key",
            max_retries=2,
            retry_delay_seconds=0.5,
            sleeper=sleeper_calls.append,
        )
        shop = CoffeeShop(
            name="Coffee Collective",
            city="Copenhagen",
            country="Denmark",
            rank=1,
            category="Top 100",
        )

        result = geocoder.geocode_shop(shop)

    assert result is not None
    assert result.place_id == "abc123"
    assert sleeper_calls == [0.5]


def test_geocode_shop_returns_none_after_retry_exhaustion() -> None:
    sleeper_calls: list[float] = []

    with patch("urllib.request.urlopen", side_effect=URLError("always down")):
        geocoder = GooglePlacesGeocoder(
            api_key="test-key",
            max_retries=2,
            retry_delay_seconds=0.25,
            sleeper=sleeper_calls.append,
        )
        shop = CoffeeShop(
            name="Coffee Collective",
            city="Copenhagen",
            country="Denmark",
            rank=1,
            category="Top 100",
        )

        result = geocoder.geocode_shop(shop)

    assert result is None
    assert sleeper_calls == [0.25]
    assert geocoder.last_status == "NETWORK_ERROR"
    assert "always down" in geocoder.last_error_message
