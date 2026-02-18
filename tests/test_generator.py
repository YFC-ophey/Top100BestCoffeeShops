from pathlib import Path
import xml.etree.ElementTree as ET

from src.generator import generate_kml
from src.models import CoffeeShop


def test_generate_kml_groups_by_category_and_writes_valid_xml(tmp_path: Path) -> None:
    shops = [
        CoffeeShop(
            name="Coffee Collective",
            city="Copenhagen",
            country="Denmark",
            rank=1,
            category="Top 100",
            lat=55.6761,
            lng=12.5683,
        ),
        CoffeeShop(
            name="Proud Mary",
            city="Melbourne",
            country="Australia",
            rank=2,
            category="South America",
            lat=-37.8136,
            lng=144.9631,
        ),
    ]
    output_path = tmp_path / "coffee_shops.kml"

    generate_kml(shops, output_path)

    root = ET.parse(output_path).getroot()
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    folder_names = [
        node.text
        for node in root.findall(".//kml:Folder/kml:name", ns)
        if node.text is not None
    ]

    assert output_path.exists()
    assert "Top 100" in folder_names
    assert "South America" in folder_names
