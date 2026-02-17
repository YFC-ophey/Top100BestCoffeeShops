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
    <main class="page">
      <header class="hero">
        <h1>Top 100 Best Coffee Shops 2026</h1>
        <p>Frontend Design V1 for zero-cost GitHub Pages hosting with map-ready link lists.</p>
        <nav class="downloads">{' | '.join(download_links)}</nav>
      </header>

      <section class="overview">
        <article class="tile">
          <h3>Chat conversation history</h3>
          <p>Decisions and sync notes for ranking refreshes and publishing flow.</p>
        </article>
        <article class="tile">
          <h3>Project canvas and components</h3>
          <p>Data table, category splits, and route-level artifacts for map export.</p>
        </article>
        <article class="tile">
          <h3>Live preview</h3>
          <p>Public page ready for quick validation before deeper UI/UX polish.</p>
        </article>
      </section>

      {_section_html("Main Top 100", top_100, "Top+100+coffee+shops")}
      {_section_html("South America", south, "Top+South+America+coffee+shops")}
    </main>
  </body>
</html>
"""


def _style_css() -> str:
    return """
:root {
  --bg: #efe8de;
  --surface: #fffdf8;
  --ink: #221812;
  --muted: #6f6257;
  --accent: #9a5f28;
  --line: #dfd1bf;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background:
    radial-gradient(circle at 84% 4%, #f7e8d6 0, transparent 22%),
    radial-gradient(circle at 6% 10%, #f3dbc2 0, transparent 26%),
    linear-gradient(150deg, #efe8de, #f8f5ef);
  color: var(--ink);
  font-family: "Avenir Next", "Segoe UI", sans-serif;
}
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 24px 16px 40px;
}
.hero {
  background: linear-gradient(130deg, #fff8ef, #fffefb);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 14px 38px rgba(53, 35, 19, 0.08);
}
h1 { margin: 0 0 8px; }
.hero p { margin: 0; color: var(--muted); }
.downloads a { color: var(--accent); text-decoration: none; font-weight: 600; }
.downloads { margin-top: 10px; }
.overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0;
}
.tile {
  background: #fff;
  border: 1px solid #e8dbc9;
  border-radius: 12px;
  padding: 12px;
}
.tile h3 { margin: 0 0 6px; font-size: 1rem; }
.tile p { margin: 0; color: var(--muted); font-size: 0.93rem; line-height: 1.45; }
.section { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 16px; margin-bottom: 20px; }
.embed-wrap iframe { width: 100%; min-height: 280px; border: 0; border-radius: 10px; margin-bottom: 14px; }
.shop-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }
.shop-row { display: grid; grid-template-columns: 56px 1fr auto; gap: 12px; align-items: center; padding: 10px; border-bottom: 1px solid #eee4d7; }
.shop-row .rank { font-weight: 800; color: var(--accent); }
.shop-row .meta small { color: var(--muted); display: block; margin-top: 2px; }
.shop-row a { color: var(--accent); font-weight: 600; text-decoration: none; }
.shop-row.top10 { background: #fff2df; border-radius: 8px; }
@media (max-width: 720px) {
  .overview { grid-template-columns: 1fr; }
  .page { padding: 14px; }
  .shop-row { grid-template-columns: 48px 1fr; }
  .shop-row a { grid-column: 2; }
}
"""
