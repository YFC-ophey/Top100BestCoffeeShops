from dataclasses import dataclass, asdict


@dataclass(slots=True)
class CoffeeShop:
    name: str
    city: str
    country: str
    rank: int
    category: str
    source_url: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    place_id: str | None = None
    formatted_address: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
