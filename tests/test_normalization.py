from src.category_utils import SOUTH_AMERICA_CATEGORY, TOP_100_CATEGORY, normalize_category
from src.country_centroids import UNKNOWN_COUNTRY, normalize_country


def test_normalize_category_supports_legacy_south() -> None:
    assert normalize_category("South") == SOUTH_AMERICA_CATEGORY
    assert normalize_category("South America") == SOUTH_AMERICA_CATEGORY
    assert normalize_category("Top 100") == TOP_100_CATEGORY


def test_normalize_country_handles_aliases_and_invalid_values() -> None:
    assert normalize_country("EEUU") == ("USA", False)
    assert normalize_country("México") == ("Mexico", False)
    assert normalize_country("69") == (UNKNOWN_COUNTRY, True)
