from src.country_centroids import UNKNOWN_COUNTRY, normalize_country


def test_normalize_country_maps_united_kingdom_aliases() -> None:
    assert normalize_country("United Kingdom") == ("United Kingdom", False)
    assert normalize_country("UK") == ("United Kingdom", False)
    assert normalize_country("Scotland") == ("United Kingdom", False)


def test_normalize_country_maps_parenthesized_us_states() -> None:
    assert normalize_country("Texas (USA)") == ("USA", False)
    assert normalize_country("Illinois (USA)") == ("USA", False)


def test_normalize_country_marks_numeric_noise_as_unknown() -> None:
    assert normalize_country("Region 7") == (UNKNOWN_COUNTRY, True)
