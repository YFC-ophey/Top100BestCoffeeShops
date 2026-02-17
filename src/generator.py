import csv
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

from src.models import CoffeeShop

KML_NS = "http://www.opengis.net/kml/2.2"
ET.register_namespace("", KML_NS)


CSV_HEADERS = [
    "rank",
    "name",
    "city",
    "country",
    "address",
    "category",
    "lat",
    "lng",
    "place_id",
    "formatted_address",
]


def _style_url(rank: int) -> str:
    return "#top10" if rank <= 10 else "#default"


def generate_kml(shops: list[CoffeeShop], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[CoffeeShop]] = defaultdict(list)
    for shop in shops:
        grouped[shop.category].append(shop)

    kml = ET.Element(f"{{{KML_NS}}}kml")
    doc = ET.SubElement(kml, f"{{{KML_NS}}}Document")
    ET.SubElement(doc, f"{{{KML_NS}}}name").text = "Top 100 Best Coffee Shops"

    top10_style = ET.SubElement(doc, f"{{{KML_NS}}}Style", id="top10")
    top10_icon_style = ET.SubElement(top10_style, f"{{{KML_NS}}}IconStyle")
    ET.SubElement(top10_icon_style, f"{{{KML_NS}}}scale").text = "1.2"

    default_style = ET.SubElement(doc, f"{{{KML_NS}}}Style", id="default")
    default_icon_style = ET.SubElement(default_style, f"{{{KML_NS}}}IconStyle")
    ET.SubElement(default_icon_style, f"{{{KML_NS}}}scale").text = "1.0"

    for category, category_shops in grouped.items():
        folder = ET.SubElement(doc, f"{{{KML_NS}}}Folder")
        ET.SubElement(folder, f"{{{KML_NS}}}name").text = category

        for shop in sorted(category_shops, key=lambda value: value.rank):
            placemark = ET.SubElement(folder, f"{{{KML_NS}}}Placemark")
            ET.SubElement(placemark, f"{{{KML_NS}}}name").text = f"{shop.rank}. {shop.name}"
            ET.SubElement(placemark, f"{{{KML_NS}}}description").text = f"{shop.city}, {shop.country}"
            ET.SubElement(placemark, f"{{{KML_NS}}}styleUrl").text = _style_url(shop.rank)
            if shop.lat is not None and shop.lng is not None:
                point = ET.SubElement(placemark, f"{{{KML_NS}}}Point")
                ET.SubElement(point, f"{{{KML_NS}}}coordinates").text = f"{shop.lng},{shop.lat},0"

    tree = ET.ElementTree(kml)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def generate_csv(shops: list[CoffeeShop], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for shop in sorted(shops, key=lambda value: (value.rank, value.category, value.name)):
            row = {header: shop.to_dict().get(header) for header in CSV_HEADERS}
            writer.writerow(row)
