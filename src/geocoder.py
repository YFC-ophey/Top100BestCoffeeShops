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
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.rate_limit_seconds = rate_limit_seconds
        self.sleeper = sleeper

    def geocode_text(self, query: str) -> GeocodeResult | None:
        params = urlencode(
            {
                "input": query,
                "inputtype": "textquery",
                "fields": "place_id,formatted_address,geometry",
                "key": self.api_key,
            }
        )
        url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?{params}"

        payload: dict[str, object] | None = None
        for attempt in range(self.max_retries):
            try:
                if self.rate_limit_seconds > 0:
                    self.sleeper(self.rate_limit_seconds)
                with urllib.request.urlopen(url, timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except (URLError, TimeoutError, json.JSONDecodeError):
                is_last_attempt = attempt == (self.max_retries - 1)
                if is_last_attempt:
                    return None
                self.sleeper(self.retry_delay_seconds)

        if payload is None:
            return None

        candidates = payload.get("candidates", [])
        if not candidates:
            return None

        candidate = candidates[0]
        location = candidate.get("geometry", {}).get("location", {})
        if "lat" not in location or "lng" not in location:
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
