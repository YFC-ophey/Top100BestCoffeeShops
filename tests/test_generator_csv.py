from pathlib import Path

from src.generator import generate_csv
from src.models import CoffeeShop


def test_generate_csv_writes_expected_header_and_rows(tmp_path: Path) -> None:
    shops = [
        CoffeeShop(name="Coffee Collective", city="Copenhagen", country="Denmark", rank=1, category="Top 100"),
        CoffeeShop(name="Proud Mary", city="Melbourne", country="Australia", rank=2, category="South"),
    ]
    output_path = tmp_path / "coffee_shops.csv"

    generate_csv(shops, output_path)

    text = output_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]
    assert lines[0] == "rank,name,city,country,address,category,lat,lng,place_id,formatted_address"
    assert "1,Coffee Collective,Copenhagen,Denmark,Top 100,,, ,".replace(" ", "")[:20] not in lines[0]
    assert "1,Coffee Collective,Copenhagen,Denmark,,Top 100" in lines[1]
    assert "2,Proud Mary,Melbourne,Australia,,South" in lines[2]
