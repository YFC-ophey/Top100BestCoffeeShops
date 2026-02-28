import json
from pathlib import Path

from src.country_centroids import UNKNOWN_COUNTRY, normalize_country


def test_no_place_id_shared_across_different_countries() -> None:
    data_path = Path(__file__).resolve().parent.parent / "data" / "current_list.json"
    rows = json.loads(data_path.read_text(encoding="utf-8"))

    place_to_countries: dict[str, set[str]] = {}
    for row in rows:
        place_id = str(row.get("place_id") or "").strip()
        if not place_id:
            continue
        normalized_country, unknown = normalize_country(str(row.get("country") or ""))
        country = normalized_country if not unknown else UNKNOWN_COUNTRY
        place_to_countries.setdefault(place_id, set()).add(country)

    offenders = {
        place_id: sorted(countries)
        for place_id, countries in place_to_countries.items()
        if len(countries) > 1
    }

    assert not offenders, f"place_id mapped to multiple countries: {offenders}"
