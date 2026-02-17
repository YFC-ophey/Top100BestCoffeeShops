from src.models import CoffeeShop
from src.state import has_shop_changes


def test_has_shop_changes_false_when_same_shops_different_order() -> None:
    previous = [
        CoffeeShop(name="A", city="X", country="Y", rank=1, category="Top 100"),
        CoffeeShop(name="B", city="X", country="Y", rank=2, category="Top 100"),
    ]
    current = [
        CoffeeShop(name="B", city="X", country="Y", rank=2, category="Top 100"),
        CoffeeShop(name="A", city="X", country="Y", rank=1, category="Top 100"),
    ]

    assert has_shop_changes(previous, current) is False


def test_has_shop_changes_true_when_rank_changes() -> None:
    previous = [CoffeeShop(name="A", city="X", country="Y", rank=1, category="Top 100")]
    current = [CoffeeShop(name="A", city="X", country="Y", rank=2, category="Top 100")]

    assert has_shop_changes(previous, current) is True
from pathlib import Path

from src.state import load_previous_state


def test_load_previous_state_returns_empty_when_file_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"

    loaded = load_previous_state(missing_path)

    assert loaded == []
