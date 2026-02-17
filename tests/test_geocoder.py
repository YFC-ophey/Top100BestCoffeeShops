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

    with patch("urllib.request.urlopen", return_value=_FakeResponse(json.dumps(payload).encode())):
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
