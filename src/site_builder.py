import json
from pathlib import Path
from urllib.parse import urlencode

from src.models import CoffeeShop


def build_static_site(
    data_file: Path,
    site_dir: Path,
    csv_file: Path,
    kml_file: Path,
) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = site_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    shops = _load_shops(data_file)
    top_100 = sorted((shop for shop in shops if shop.category == "Top 100"), key=lambda value: value.rank)
    south = sorted((shop for shop in shops if shop.category == "South"), key=lambda value: value.rank)

    (assets_dir / "style.css").write_text(_style_css(), encoding="utf-8")
    (site_dir / "index.html").write_text(
        _index_html(top_100=top_100, south=south, csv_exists=csv_file.exists(), kml_exists=kml_file.exists()),
        encoding="utf-8",
    )


def _load_shops(data_file: Path) -> list[CoffeeShop]:
    if not data_file.exists():
        return []
    payload = json.loads(data_file.read_text(encoding="utf-8"))
    return [CoffeeShop(**item) for item in payload]


def _maps_link(shop: CoffeeShop) -> str:
    query_parts = [shop.name]
    if shop.city:
        query_parts.append(shop.city)
    if shop.country:
        query_parts.append(shop.country)
    query = ", ".join(query_parts)
    params: dict[str, str] = {"api": "1", "query": query}
    if shop.place_id:
        params["query_place_id"] = shop.place_id
    return f"https://www.google.com/maps/search/?{urlencode(params)}"


def _section_html(title: str, shops: list[CoffeeShop], map_query: str) -> str:
    rows = []
    for shop in shops:
        top10_class = "top10" if shop.rank <= 10 else ""
        rows.append(
            f"""
            <li class="shop-row {top10_class}">
              <span class="rank">#{shop.rank}</span>
              <div class="meta">
                <strong>{shop.name}</strong>
                <small>{shop.city + ", " if shop.city else ""}{shop.country}</small>
              </div>
              <a href="{_maps_link(shop)}" target="_blank" rel="noopener">Open in Google Maps</a>
            </li>
            """
        )
    return f"""
    <section class="section">
      <h2>{title}</h2>
      <div class="embed-wrap">
        <iframe
          title="{title} map preview"
          loading="lazy"
          src="https://www.google.com/maps?q={map_query}&output=embed"
        ></iframe>
      </div>
      <ol class="shop-list">
        {''.join(rows)}
      </ol>
    </section>
    """


def _index_html(top_100: list[CoffeeShop], south: list[CoffeeShop], csv_exists: bool, kml_exists: bool) -> str:
    download_links = []
    if csv_exists:
        download_links.append('<a href="../output/coffee_shops.csv">Download CSV</a>')
    if kml_exists:
        download_links.append('<a href="../output/coffee_shops.kml">Download KML</a>')

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Top 100 Best Coffee Shops 2026</title>
    <link rel="stylesheet" href="./assets/style.css" />
  </head>
  <body>
    <header>
      <h1>Top 100 Best Coffee Shops 2026</h1>
      <p>Static map companion built for zero-cost GitHub Pages hosting.</p>
      <nav class="downloads">{' | '.join(download_links)}</nav>
    </header>
    {_section_html("Main Top 100", top_100, "Top+100+coffee+shops")}
    {_section_html("South America", south, "Top+South+America+coffee+shops")}
  </body>
</html>
"""


def _style_css() -> str:
    return """
:root {
  --bg: #f4eee4;
  --surface: #fffdf8;
  --ink: #2b1f18;
  --muted: #6f6257;
  --accent: #8a5a2b;
}
* { box-sizing: border-box; }
body {
  margin: 0 auto;
  max-width: 1100px;
  padding: 24px;
  background: linear-gradient(150deg, #f4eee4, #f8f5ef);
  color: var(--ink);
  font-family: "Avenir Next", "Segoe UI", sans-serif;
}
header { margin-bottom: 24px; }
h1 { margin: 0 0 8px 0; }
.downloads a { color: var(--accent); text-decoration: none; font-weight: 600; }
.section { background: var(--surface); border: 1px solid #dfd1bf; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
.embed-wrap iframe { width: 100%; min-height: 280px; border: 0; border-radius: 10px; margin-bottom: 14px; }
.shop-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }
.shop-row { display: grid; grid-template-columns: 56px 1fr auto; gap: 12px; align-items: center; padding: 10px; border-bottom: 1px solid #eee4d7; }
.shop-row .rank { font-weight: 800; color: var(--accent); }
.shop-row .meta small { color: var(--muted); display: block; margin-top: 2px; }
.shop-row a { color: var(--accent); font-weight: 600; text-decoration: none; }
.shop-row.top10 { background: #fff2df; border-radius: 8px; }
@media (max-width: 720px) {
  body { padding: 14px; }
  .shop-row { grid-template-columns: 48px 1fr; }
  .shop-row a { grid-column: 2; }
}
"""
