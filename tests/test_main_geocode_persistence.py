from src.main import _carry_forward_geocode
from src.models import CoffeeShop


def test_carry_forward_geocode_reuses_previous_fields() -> None:
    previous = [
        CoffeeShop(
            name="Onyx Coffee LAB",
            city="Rogers",
            country="USA",
            rank=1,
            category="Top 100",
            source_url="https://theworlds100bestcoffeeshops.com/locales/onyx-coffee-lab/",
            lat=36.332,
            lng=-94.118,
            place_id="abc123",
            formatted_address="101 E Walnut Ave Rogers, AR 72756, USA",
        )
    ]
    current = [
        CoffeeShop(
            name="Onyx Coffee LAB",
            city="Rogers",
            country="USA",
            rank=1,
            category="Top 100",
            source_url="https://theworlds100bestcoffeeshops.com/locales/onyx-coffee-lab/",
            lat=None,
            lng=None,
            place_id=None,
            formatted_address=None,
        )
    ]

    updated = _carry_forward_geocode(previous, current)

    assert updated[0].place_id == "abc123"
    assert updated[0].lat == 36.332
    assert updated[0].lng == -94.118
    assert updated[0].formatted_address == "101 E Walnut Ave Rogers, AR 72756, USA"
