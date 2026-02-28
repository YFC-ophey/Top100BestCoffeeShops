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


def test_rank_71_little_victories_has_ottawa_coordinates() -> None:
    data_path = Path(__file__).resolve().parent.parent / "data" / "current_list.json"
    rows = json.loads(data_path.read_text(encoding="utf-8"))

    target = next(
        (
            row
            for row in rows
            if str(row.get("rank")) == "71"
            and str(row.get("category")) == "Top 100"
            and str(row.get("name")) == "Little Victories Coffee"
        ),
        None,
    )
    assert target is not None, "Expected rank 71 Little Victories Coffee row in dataset"

    lat = target.get("lat")
    lng = target.get("lng")
    assert lat is not None and lng is not None, "Rank 71 must not use centroid fallback coordinates"

    # Ottawa city bounds (approx): avoid regressions to western Canada fallback pins.
    assert 45.30 <= float(lat) <= 45.50
    assert -75.80 <= float(lng) <= -75.55
