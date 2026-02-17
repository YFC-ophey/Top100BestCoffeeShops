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
        _index_html(
            top_100=top_100,
            south=south,
            csv_exists=csv_file.exists(),
            kml_exists=kml_file.exists(),
            total_count=len(shops),
        ),
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


def _rows_html(shops: list[CoffeeShop]) -> str:
    rows = []
    for shop in shops:
        rows.append(
            f"""
            <tr>
              <td>{shop.rank}</td>
              <td>{shop.name}</td>
              <td>{shop.city}</td>
              <td>{shop.country}</td>
              <td>{shop.category}</td>
            </tr>
            """
        )
    return "".join(rows)


def _section_html(panel_id: str, title: str, shops: list[CoffeeShop], map_query: str, active: bool = False) -> str:
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

    active_class = " active" if active else ""
    return f"""
    <section id="{panel_id}" class="tab-panel panel{active_class}">
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


def _index_html(top_100: list[CoffeeShop], south: list[CoffeeShop], csv_exists: bool, kml_exists: bool, total_count: int) -> str:
    download_links = []
    if csv_exists:
        download_links.append('<a href="../output/coffee_shops.csv">CSV</a>')
    if kml_exists:
        download_links.append('<a href="../output/coffee_shops.kml">KML</a>')

    all_rows = top_100 + south

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Top 100 Best Coffee Shops 2026</title>
    <link rel="stylesheet" href="./assets/style.css" />
  </head>
  <body>
    <div class="app-shell">
      <header class="shell-topbar">
        <div class="brand-wrap">
          <span class="brand-dot" aria-hidden="true"></span>
          <div>
            <div class="brand-title">ROAST. | Global Coffee Explorer</div>
            <div class="brand-sub">Top100BestCoffeeShops Preview</div>
          </div>
        </div>
        <div class="topbar-actions">
          <span class="status-pill">Public Static Site</span>
          {' '.join(download_links)}
        </div>
      </header>

      <main class="shell-body">
        <section class="workspace-main">
          <div class="workspace-head">
            <div>
              <h1>Top 100 Best Coffee Shops 2026</h1>
              <p>Data-driven map workspace with ranked shops and shareable Google Maps links.</p>
            </div>
            <div class="meta-chips">
              <span class="chip">Total shops: {total_count}</span>
              <span class="chip">Top 100: {len(top_100)}</span>
              <span class="chip">South: {len(south)}</span>
            </div>
          </div>

          <div class="tabs" role="tablist" aria-label="Coffee shop views">
            <button class="tab-btn active" data-tab="overview" role="tab" aria-selected="true">Overview</button>
            <button class="tab-btn" data-tab="top100-links" role="tab" aria-selected="false">Main Top 100</button>
            <button class="tab-btn" data-tab="south-links" role="tab" aria-selected="false">South America</button>
          </div>

          <section id="overview" class="tab-panel panel active" role="tabpanel">
            <div class="layout-3">
              <article class="tile">
                <h3>Chat conversation history</h3>
                <p>Track sync decisions and yearly update notes for rankings.</p>
              </article>
              <article class="tile">
                <h3>Project canvas and components</h3>
                <p>Map previews, ordered map links, and export artifacts in one shell.</p>
              </article>
              <article class="tile">
                <h3>Live preview</h3>
                <p>Dark-first layout ready for GitHub Pages public hosting.</p>
              </article>
            </div>

            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Name</th>
                  <th>City</th>
                  <th>Country</th>
                  <th>Category</th>
                </tr>
              </thead>
              <tbody>
                {_rows_html(all_rows)}
              </tbody>
            </table>
          </section>

          {_section_html("top100-links", "Main Top 100", top_100, "Top+100+coffee+shops")}
          {_section_html("south-links", "South America", south, "Top+South+America+coffee+shops")}
        </section>

        <aside class="utility-panel" aria-label="Session and map helper panel">
          <div class="utility-head">
            <h2>Initial Session</h2>
            <span>History</span>
          </div>
          <div class="utility-scroll">
            <article class="util-card">
              <h3>Session / History</h3>
              <p>This static shell mirrors the live workspace style used in app preview mode.</p>
              <div class="chat-row">
                <span class="chat-badge you">You</span>
                <p>Need global and South America coffee lists in one dashboard.</p>
              </div>
              <div class="chat-row">
                <span class="chat-badge ai">AI</span>
                <p>Built with map previews, rank ordering, and direct map links.</p>
              </div>
            </article>

            <article class="util-card">
              <h3>Artifacts</h3>
              <p>Export data for Google Maps and external tools.</p>
              <div class="artifact-links">
                {'<a href="../output/coffee_shops.csv">Download CSV</a>' if csv_exists else ''}
                {'<a href="../output/coffee_shops.kml">Download KML</a>' if kml_exists else ''}
              </div>
            </article>

            <article class="util-card">
              <h3>Map Usage Notes</h3>
              <ul class="util-list">
                <li>Open each ranked entry in Google Maps and save to your own map lists.</li>
                <li>The Top 100 and South tabs preserve rank order.</li>
                <li>Where available, place IDs are embedded for direct match quality.</li>
              </ul>
            </article>
          </div>
          <div class="footer-note">Data source: theworlds100bestcoffeeshops.com</div>
        </aside>
      </main>
    </div>

    <script>
      const tabButtons = document.querySelectorAll('.tab-btn');
      const tabPanels = document.querySelectorAll('.tab-panel');
      tabButtons.forEach((button) => {{
        button.addEventListener('click', () => {{
          const target = button.dataset.tab;
          tabButtons.forEach((item) => {{
            const active = item === button;
            item.classList.toggle('active', active);
            item.setAttribute('aria-selected', String(active));
          }});
          tabPanels.forEach((panel) => panel.classList.toggle('active', panel.id === target));
        }});
      }});
    </script>
  </body>
</html>
"""


def _style_css() -> str:
    return """
:root {
  --bg: #0e1117;
  --surface-1: #141a24;
  --surface-2: #1a2230;
  --surface-3: #212b3c;
  --line: #2f3b50;
  --text-1: #eef3ff;
  --text-2: #aebad2;
  --accent: #0f83fd;
  --accent-soft: rgba(15, 131, 253, 0.18);
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background:
    radial-gradient(1200px 500px at 20% -10%, #1d2940 0%, transparent 60%),
    radial-gradient(900px 450px at 95% 5%, #19243a 0%, transparent 60%),
    var(--bg);
  color: var(--text-1);
}
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 10px;
}
.shell-topbar {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid var(--line);
  background: rgba(20, 26, 36, 0.88);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 0 12px;
}
.brand-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 6px rgba(15, 131, 253, 0.12);
}
.brand-title {
  font-size: 0.92rem;
  font-weight: 700;
}
.brand-sub {
  font-size: 0.78rem;
  color: var(--text-2);
}
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-pill {
  border: 1px solid #33557a;
  background: #132033;
  color: #9bc7ff;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 600;
}
.topbar-actions a {
  color: var(--text-2);
  text-decoration: none;
  border: 1px solid var(--line);
  background: var(--surface-2);
  border-radius: 8px;
  padding: 6px 9px;
  font-size: 0.76rem;
}
.topbar-actions a:hover,
.topbar-actions a:focus-visible {
  border-color: #3f5f86;
  color: var(--text-1);
  outline: none;
}
.shell-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 10px;
}
.workspace-main {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(26, 34, 48, 0.94), rgba(20, 26, 36, 0.94));
  min-height: 0;
  padding: 12px;
  display: flex;
  flex-direction: column;
}
.workspace-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.workspace-head h1 {
  margin: 0;
  font-size: clamp(1.1rem, 2vw, 1.45rem);
  letter-spacing: -0.01em;
}
.workspace-head p {
  margin: 3px 0 0;
  color: var(--text-2);
  font-size: 0.86rem;
}
.meta-chips {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
}
.chip {
  border: 1px solid var(--line);
  background: var(--surface-3);
  border-radius: 999px;
  padding: 5px 10px;
  color: #dbe6fb;
  font-size: 0.77rem;
}
.tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 0 0 10px;
}
.tab-btn {
  border: 1px solid var(--line);
  background: var(--surface-2);
  color: var(--text-2);
  border-radius: 9px;
  padding: 7px 11px;
  font-size: 0.8rem;
  cursor: pointer;
}
.tab-btn:hover,
.tab-btn:focus-visible {
  border-color: #3f5f86;
  color: var(--text-1);
  outline: none;
}
.tab-btn.active {
  border-color: #3f5f86;
  background: var(--accent-soft);
  color: var(--text-1);
}
.tab-panel {
  display: none;
  animation: panelIn 150ms ease;
}
.tab-panel.active { display: block; }
@keyframes panelIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.panel {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(20, 26, 36, 0.82);
  padding: 10px;
}
.layout-3 {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}
.tile {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface-2);
  padding: 10px;
}
.tile h3 {
  margin: 0 0 5px;
  font-size: 0.83rem;
}
.tile p {
  margin: 0;
  color: var(--text-2);
  font-size: 0.76rem;
  line-height: 1.45;
}
table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid var(--line);
  border-radius: 10px;
  overflow: hidden;
  background: #111723;
}
th,
td {
  padding: 8px 7px;
  text-align: left;
  border-bottom: 1px solid #263349;
  font-size: 0.78rem;
}
th {
  color: #a5b6d6;
  background: #182131;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: 0.7rem;
}
td { color: #e6efff; }
.embed-wrap iframe {
  width: 100%;
  min-height: 260px;
  border: 0;
  border-radius: 10px;
  margin-bottom: 10px;
}
.shop-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}
.shop-row {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 10px;
  border: 1px solid #263349;
  border-radius: 9px;
  background: #111723;
}
.shop-row .rank {
  font-weight: 800;
  color: #8bc1ff;
}
.shop-row .meta small {
  color: var(--text-2);
  display: block;
  margin-top: 2px;
}
.shop-row a {
  color: #8cc1ff;
  font-weight: 600;
  text-decoration: none;
}
.shop-row a:hover,
.shop-row a:focus-visible {
  color: #d1e6ff;
  outline: none;
}
.shop-row.top10 {
  border-color: #3f5f86;
  background: #15243a;
}
.utility-panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: rgba(20, 26, 36, 0.92);
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.utility-head {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.utility-head h2 {
  margin: 0;
  font-size: 0.82rem;
}
.utility-head span {
  color: var(--text-2);
  font-size: 0.74rem;
}
.utility-scroll {
  min-height: 0;
  overflow: auto;
  padding: 10px;
  display: grid;
  gap: 9px;
}
.util-card {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface-2);
  padding: 10px;
}
.util-card h3 {
  margin: 0 0 5px;
  font-size: 0.8rem;
}
.util-card p,
.util-card li {
  margin: 0;
  color: var(--text-2);
  font-size: 0.76rem;
  line-height: 1.5;
}
.util-list {
  margin: 6px 0 0;
  padding-left: 18px;
}
.artifact-links {
  margin-top: 8px;
  display: grid;
  gap: 6px;
}
.artifact-links a {
  display: inline-block;
  color: #9dcbff;
  text-decoration: none;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 6px 8px;
  background: #162133;
  width: fit-content;
  font-size: 0.76rem;
}
.artifact-links a:hover,
.artifact-links a:focus-visible {
  border-color: #3f5f86;
  color: #d1e6ff;
  outline: none;
}
.chat-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.chat-badge {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  display: grid;
  place-items: center;
  font-size: 0.64rem;
  font-weight: 700;
}
.chat-badge.you { background: #294870; color: #cbe4ff; }
.chat-badge.ai { background: #28354c; color: #d6e4ff; }
.footer-note {
  padding: 8px 12px 10px;
  border-top: 1px solid var(--line);
  color: #93a4c3;
  font-size: 0.7rem;
}
@media (max-width: 1060px) {
  .shell-body { grid-template-columns: 1fr; }
  .utility-panel { min-height: 300px; }
}
@media (max-width: 760px) {
  .layout-3 { grid-template-columns: 1fr; }
  th,
  td { font-size: 0.72rem; }
  .topbar-actions { display: none; }
  .shop-row { grid-template-columns: 48px 1fr; }
  .shop-row a { grid-column: 2; }
}
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}
"""
