from dataclasses import dataclass
import json
import time
from typing import Callable
from urllib.error import URLError
from urllib.parse import urlencode
import urllib.request

from src.models import CoffeeShop


@dataclass(slots=True)
class GeocodeResult:
    lat: float
    lng: float
    place_id: str
    formatted_address: str


class GooglePlacesGeocoder:
    def __init__(
        self,
        api_key: str,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        rate_limit_seconds: float = 0.0,
        timeout_seconds: float = 30.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.rate_limit_seconds = rate_limit_seconds
        self.timeout_seconds = timeout_seconds
        self.sleeper = sleeper
        self.last_status = ""
        self.last_error_message = ""

    def geocode_text(self, query: str) -> GeocodeResult | None:
        self.last_status = ""
        self.last_error_message = ""
        place_result = self._find_place_from_text(query)
        if place_result:
            return place_result

        # Fallback to Geocoding API when Places text search does not return a candidate.
        if self.last_status in {"ZERO_RESULTS", "NOT_FOUND", "MISSING_GEOMETRY", "UNKNOWN"}:
            geocode_result = self._geocode_address(query)
            if geocode_result:
                return geocode_result

        return None

    def _find_place_from_text(self, query: str) -> GeocodeResult | None:
        params = urlencode(
            {
                "input": query,
                "inputtype": "textquery",
                "fields": "place_id,formatted_address,geometry",
                "key": self.api_key,
            }
        )
        url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?{params}"
        payload = self._request_json(url)
        if payload is None:
            return None
        return self._extract_result(payload, "candidates")

    def _geocode_address(self, query: str) -> GeocodeResult | None:
        params = urlencode({"address": query, "key": self.api_key})
        url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
        payload = self._request_json(url)
        if payload is None:
            return None
        return self._extract_result(payload, "results")

    def _request_json(self, url: str) -> dict[str, object] | None:
        payload: dict[str, object] | None = None
        for attempt in range(self.max_retries):
            try:
                if self.rate_limit_seconds > 0:
                    self.sleeper(self.rate_limit_seconds)
                with urllib.request.urlopen(url, timeout=self.timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except URLError as error:
                self.last_status = "NETWORK_ERROR"
                self.last_error_message = str(error.reason or error)
                if attempt == (self.max_retries - 1):
                    return None
                self.sleeper(self.retry_delay_seconds)
            except TimeoutError as error:
                self.last_status = "TIMEOUT"
                self.last_error_message = str(error)
                if attempt == (self.max_retries - 1):
                    return None
                self.sleeper(self.retry_delay_seconds)
            except json.JSONDecodeError as error:
                self.last_status = "INVALID_JSON"
                self.last_error_message = str(error)
                if attempt == (self.max_retries - 1):
                    return None
                self.sleeper(self.retry_delay_seconds)
        return payload

    def _extract_result(self, payload: dict[str, object], collection_key: str) -> GeocodeResult | None:
        payload_status = str(payload.get("status", "")).strip().upper()
        payload_error = str(payload.get("error_message", "")).strip()
        self.last_status = payload_status or self.last_status or "UNKNOWN"
        self.last_error_message = payload_error or self.last_error_message

        candidates = payload.get(collection_key, [])
        if not candidates:
            return None

        candidate = candidates[0]
        location = candidate.get("geometry", {}).get("location", {})
        if "lat" not in location or "lng" not in location:
            self.last_status = "MISSING_GEOMETRY"
            return None

        return GeocodeResult(
            lat=float(location["lat"]),
            lng=float(location["lng"]),
            place_id=str(candidate.get("place_id", "")),
            formatted_address=str(candidate.get("formatted_address", "")),
        )

    def geocode_shop(self, shop: CoffeeShop) -> GeocodeResult | None:
        query = f"{shop.name}, {shop.city}, {shop.country}"
        return self.geocode_text(query)
