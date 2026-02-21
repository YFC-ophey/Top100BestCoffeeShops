import html
import json
import os
from pathlib import Path
from urllib.parse import urlencode

from src.models import CoffeeShop

COUNTRY_COLOR_MAP: dict[str, str] = {
    "Argentina": "#74ACDF",
    "Australia": "#00008B",
    "Austria": "#ED2939",
    "Belgium": "#FDDA24",
    "Bolivia": "#007934",
    "Brazil": "#009C3B",
    "Bulgaria": "#00966E",
    "Canada": "#FF0000",
    "Chile": "#D52B1E",
    "China": "#DE2910",
    "Colombia": "#FCD116",
    "Costa Rica": "#002B7F",
    "Czech Republic": "#D7141A",
    "Denmark": "#C60C30",
    "Dominican Republic": "#002D62",
    "EEUU": "#3C3B6E",
    "Ecuador": "#FFD100",
    "Egypt": "#CE1126",
    "El Salvador": "#0F47AF",
    "England": "#CF081F",
    "Ethiopia": "#009A44",
    "France": "#002395",
    "Greece": "#004C98",
    "Guatemala": "#4997D0",
    "Honduras": "#0073CF",
    "Ireland": "#169B62",
    "Italy": "#008C45",
    "Japan": "#BC002D",
    "Macedonia": "#D20000",
    "Malaysia": "#010066",
    "Mexico": "#006847",
    "México": "#006847",
    "Netherlands": "#AE1C28",
    "Nicaragua": "#0067C6",
    "Norway": "#EF2B2D",
    "Paraguay": "#D52B1E",
    "Peru": "#D91023",
    "Portugal": "#006600",
    "Qatar": "#8D1B3D",
    "Republic of Korea": "#CD2E3A",
    "Romania": "#002B7F",
    "Rwanda": "#20603D",
    "Scotland": "#005EB8",
    "Singapore": "#EF3340",
    "South Africa": "#007749",
    "Spain": "#AA151B",
    "Switzerland": "#D52B1E",
    "Taiwan": "#000095",
    "Thailand": "#A51931",
    "The Philippines": "#0038A8",
    "Turkey": "#E30A17",
    "UAE": "#00732F",
    "United States": "#3C3B6E",
    "Uruguay": "#001489",
    "USA": "#3C3B6E",
    "Venezuela": "#FFCC00",
}


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
    top_100 = sorted((shop for shop in shops if shop.category == "Top 100"), key=lambda value: (value.rank, value.name))
    south = sorted((shop for shop in shops if shop.category == "South"), key=lambda value: (value.rank, value.name))
    all_shops = sorted(shops, key=lambda value: (value.rank, value.category, value.name))

    map_shops, missing_coords_count = _build_map_shops(all_shops)
    sidebar_shops = _build_sidebar_shops(all_shops)
    map_country_aggregates = _build_country_aggregates(map_shops)

    csv_url = "../output/coffee_shops.csv" if csv_file.exists() else ""
    kml_url = "../output/coffee_shops.kml" if kml_file.exists() else ""

    html_output = _index_html(
        all_shops=all_shops,
        top_100=top_100,
        south=south,
        map_shops=map_shops,
        sidebar_shops=sidebar_shops,
        map_country_aggregates=map_country_aggregates,
        missing_coords_count=missing_coords_count,
        total_count=len(all_shops),
        csv_url=csv_url,
        kml_url=kml_url,
        google_maps_key=os.getenv("GOOGLE_MAPS_JS_API_KEY", "").strip(),
    )

    (assets_dir / "style.css").write_text(_style_css(), encoding="utf-8")
    (site_dir / "index.html").write_text(html_output, encoding="utf-8")


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


def _build_map_shops(shops: list[CoffeeShop]) -> tuple[list[dict[str, object]], int]:
    map_shops: list[dict[str, object]] = []
    missing = 0
    for shop in shops:
        if shop.lat is None or shop.lng is None:
            missing += 1
            continue
        map_shops.append(
            {
                "name": shop.name,
                "city": shop.city,
                "country": shop.country,
                "rank": shop.rank,
                "category": shop.category,
                "lat": shop.lat,
                "lng": shop.lng,
                "place_id": shop.place_id or "",
                "address": shop.formatted_address or shop.address or "",
                "source_url": shop.source_url or "",
                "google_maps_url": _maps_link(shop),
            }
        )
    return map_shops, missing


def _build_sidebar_shops(shops: list[CoffeeShop]) -> list[dict[str, object]]:
    return [
        {
            "name": shop.name,
            "city": shop.city,
            "country": shop.country,
            "rank": shop.rank,
            "category": shop.category,
            "lat": shop.lat,
            "lng": shop.lng,
            "place_id": shop.place_id or "",
            "address": shop.formatted_address or shop.address or "",
            "source_url": shop.source_url or "",
            "google_maps_url": _maps_link(shop),
        }
        for shop in shops
    ]


def _json_script_literal(value: object) -> str:
    return json.dumps(value).replace("</", "<\\/")


def _build_country_aggregates(map_shops: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for item in map_shops:
        country = str(item.get("country") or "Unknown")
        bucket = grouped.setdefault(
            country,
            {
                "country": country,
                "count": 0,
                "top_count": 0,
                "south_count": 0,
                "lat_sum": 0.0,
                "lng_sum": 0.0,
            },
        )
        bucket["count"] = int(bucket["count"]) + 1
        if item.get("category") == "Top 100":
            bucket["top_count"] = int(bucket["top_count"]) + 1
        if item.get("category") == "South":
            bucket["south_count"] = int(bucket["south_count"]) + 1
        bucket["lat_sum"] = float(bucket["lat_sum"]) + float(item["lat"])
        bucket["lng_sum"] = float(bucket["lng_sum"]) + float(item["lng"])

    result: list[dict[str, object]] = []
    for country, bucket in grouped.items():
        count = int(bucket["count"])
        result.append(
            {
                "country": country,
                "count": count,
                "top_count": int(bucket["top_count"]),
                "south_count": int(bucket["south_count"]),
                "lat": float(bucket["lat_sum"]) / count,
                "lng": float(bucket["lng_sum"]) / count,
                "color": COUNTRY_COLOR_MAP.get(country, "#888899"),
            }
        )

    return sorted(result, key=lambda row: (-int(row["count"]), str(row["country"])))


def _table_rows_html(shops: list[CoffeeShop]) -> str:
    rows: list[str] = []
    for shop in shops:
        rows.append(
            "<tr>"
            f"<td>{shop.rank}</td>"
            f"<td>{html.escape(shop.name)}</td>"
            f"<td>{html.escape(shop.city)}</td>"
            f"<td>{html.escape(shop.country)}</td>"
            f"<td>{html.escape(shop.category)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _ordered_links_html(shops: list[CoffeeShop]) -> str:
    items: list[str] = []
    for shop in shops:
        top10_class = " top10" if shop.rank <= 10 else ""
        label = html.escape(f"{shop.rank}. {shop.name}")
        url = html.escape(_maps_link(shop), quote=True)
        subtitle = html.escape((f"{shop.city}, " if shop.city else "") + shop.country)
        items.append(
            "<li class=\"shop-row" + top10_class + "\">"
            f"<span class=\"rank\">#{shop.rank}</span>"
            "<div class=\"meta\">"
            f"<strong>{html.escape(shop.name)}</strong>"
            f"<small>{subtitle}</small>"
            "</div>"
            f"<a href=\"{url}\" target=\"_blank\" rel=\"noopener\">Open in Google Maps</a>"
            "</li>"
        )
    return "".join(items)


def _index_html(
    all_shops: list[CoffeeShop],
    top_100: list[CoffeeShop],
    south: list[CoffeeShop],
    map_shops: list[dict[str, object]],
    sidebar_shops: list[dict[str, object]],
    map_country_aggregates: list[dict[str, object]],
    missing_coords_count: int,
    total_count: int,
    csv_url: str,
    kml_url: str,
    google_maps_key: str,
) -> str:
    html_output = _html_template()
    replacements = {
        "TOTAL_SHOPS": str(total_count),
        "TOP_100_COUNT": str(len(top_100)),
        "SOUTH_COUNT": str(len(south)),
        "MISSING_COORDS_COUNT": str(missing_coords_count),
        "TABLE_ROWS": _table_rows_html(all_shops),
        "TOP100_LINKS": _ordered_links_html(top_100),
        "SOUTH_LINKS": _ordered_links_html(south),
        "MAP_SHOPS_JSON": _json_script_literal(map_shops),
        "SIDEBAR_SHOPS_JSON": _json_script_literal(sidebar_shops),
        "MAP_COUNTRIES_JSON": _json_script_literal(map_country_aggregates),
        "GOOGLE_MAPS_KEY_JSON": _json_script_literal(google_maps_key),
        "CSV_BUTTON": (
            f'<a class="btn-secondary" href="{html.escape(csv_url, quote=True)}">Download CSV</a>' if csv_url else ""
        ),
        "KML_BUTTON": (
            f'<a class="btn-secondary" href="{html.escape(kml_url, quote=True)}">Download KML</a>' if kml_url else ""
        ),
    }

    for key, value in replacements.items():
        html_output = html_output.replace(f"__{key}__", value)

    return html_output


def _html_template() -> str:
    return """<!doctype html>
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
          <div class="brand-icon">☕</div>
          <div>
            <p class="brand-title">ROAST.</p>
            <p class="brand-sub">Top100BestCoffeeShops Preview</p>
          </div>
        </div>

        <div class="collection-toggle" aria-label="Collection toggles">
          <button class="category-chip active" data-category="Top 100">Top 100 World</button>
          <button class="category-chip active" data-category="South">South America</button>
        </div>

        <div class="topbar-actions">
          <div class="view-toggle">
            <button class="view-btn active" data-overview-view="map">Map</button>
            <button class="view-btn" data-overview-view="list">List</button>
          </div>
          <div class="profile-badge" title="Global Explorer">🌍</div>
          __CSV_BUTTON__
          __KML_BUTTON__
        </div>
      </header>

      <main class="shell-body">
        <section class="workspace-main">
          <div class="workspace-head">
            <div>
              <h1>Top 100 Best Coffee Shops 2026</h1>
              <p>Interactive map of Top 100 World + South America coffee shops.</p>
            </div>
            <div class="meta-chips">
              <span class="chip">Total shops: __TOTAL_SHOPS__</span>
              <span class="chip">Top 100: __TOP_100_COUNT__</span>
              <span class="chip">South: __SOUTH_COUNT__</span>
              <span class="chip">Map skipped: __MISSING_COORDS_COUNT__</span>
            </div>
          </div>

          <div class="tabs" role="tablist" aria-label="Coffee shop views">
            <button class="tab-btn active" data-tab="overview" role="tab" aria-selected="true">Overview</button>
            <button class="tab-btn" data-tab="top100-links" role="tab" aria-selected="false">Main Top 100</button>
            <button class="tab-btn" data-tab="south-links" role="tab" aria-selected="false">South America</button>
          </div>

          <section id="overview" class="tab-panel active" role="tabpanel">
            <div class="overview-panel" id="overview-map-region">
              <div class="overview-stage">
                <div id="overview-map" aria-label="Global coffee shops map"></div>
                <div id="map-unavailable" class="map-unavailable hidden"></div>

                <aside class="detail-panel" id="shop-detail-panel">
                  <div class="hero-image">
                    <img
                      id="shop-hero-img"
                      src="https://images.unsplash.com/photo-1554118811-1e0d58224f24?q=80&w=1200&auto=format&fit=crop"
                      alt="Coffee shop interior"
                    />
                    <div class="hero-overlay"></div>
                    <div class="badge-row">
                      <span class="badge rank" id="shop-rank-badge">#1 South America</span>
                      <span class="badge type">Historic Site</span>
                    </div>
                  </div>

                  <div class="detail-content">
                    <div>
                      <h2 class="shop-title" id="shop-name">Choose a marker</h2>
                      <p class="shop-rating" id="shop-rating">Rank and category appear after selection.</p>
                      <p class="shop-address" id="shop-address">Select a coffee shop marker to inspect details.</p>
                    </div>

                    <div class="action-grid">
                      <a class="btn-primary" id="shop-directions" href="#" target="_blank" rel="noopener">Get Directions</a>
                      <a class="btn-secondary" id="shop-website" href="#" target="_blank" rel="noopener">Source Page</a>
                      <a class="btn-secondary" id="shop-map-link" href="#" target="_blank" rel="noopener">Google Maps</a>
                    </div>

                    <section class="detail-section">
                      <p class="section-title">Scraped Details</p>
                      <div class="details-grid">
                        <div class="details-card">
                          <p class="details-label">Category</p>
                          <p class="details-value" id="shop-category">-</p>
                        </div>
                        <div class="details-card">
                          <p class="details-label">City / Country</p>
                          <p class="details-value" id="shop-city-country">-</p>
                        </div>
                        <div class="details-card">
                          <p class="details-label">Coordinates</p>
                          <p class="details-value" id="shop-coordinates">-</p>
                        </div>
                        <div class="details-card">
                          <p class="details-label">Google Place ID</p>
                          <p class="details-value" id="shop-place-id">-</p>
                        </div>
                      </div>
                    </section>
                  </div>
                </aside>

                <div class="map-help">
                  Pins use national flag colors. Zoom out for country density, zoom in for individual shops.
                </div>
              </div>
            </div>

            <div class="overview-list is-hidden" id="overview-list-region">
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
                  __TABLE_ROWS__
                </tbody>
              </table>
            </div>
          </section>

          <section id="top100-links" class="tab-panel panel" role="tabpanel">
            <h2>Main Top 100</h2>
            <ol class="shop-list">
              __TOP100_LINKS__
            </ol>
          </section>

          <section id="south-links" class="tab-panel panel" role="tabpanel">
            <h2>South America</h2>
            <ol class="shop-list">
              __SOUTH_LINKS__
            </ol>
          </section>
        </section>
      </main>
    </div>

    <script>
      const mapShops = __MAP_SHOPS_JSON__;
      const sidebarShops = __SIDEBAR_SHOPS_JSON__;
      const mapCountries = __MAP_COUNTRIES_JSON__;
      const googleMapsKey = __GOOGLE_MAPS_KEY_JSON__;
      const mapMissingCoordsCount = __MISSING_COORDS_COUNT__;

      const tabButtons = document.querySelectorAll(".tab-btn");
      const tabPanels = document.querySelectorAll(".tab-panel");
      tabButtons.forEach((button) => {
        button.addEventListener("click", () => {
          const target = button.dataset.tab;
          tabButtons.forEach((item) => {
            const active = item === button;
            item.classList.toggle("active", active);
            item.setAttribute("aria-selected", String(active));
          });
          tabPanels.forEach((panel) => panel.classList.toggle("active", panel.id === target));
        });
      });

      const mapRegion = document.getElementById("overview-map-region");
      const listRegion = document.getElementById("overview-list-region");
      document.querySelectorAll(".view-btn").forEach((button) => {
        button.addEventListener("click", () => {
          const mode = button.dataset.overviewView;
          document.querySelectorAll(".view-btn").forEach((item) => item.classList.toggle("active", item === button));
          if (mode === "list") {
            mapRegion.classList.add("is-hidden");
            listRegion.classList.remove("is-hidden");
          } else {
            mapRegion.classList.remove("is-hidden");
            listRegion.classList.add("is-hidden");
          }
        });
      });

      const markerState = {
        activeCategories: new Set(["Top 100", "South"]),
        countryMarkers: [],
        shopMarkers: [],
        selectedShop: null,
        infoWindow: null,
        map: null,
      };

      function normalizeCategory(category) {
        return category === "South" ? "South" : "Top 100";
      }

      function getVisibleShops() {
        return mapShops.filter((shop) => markerState.activeCategories.has(normalizeCategory(shop.category)));
      }

      function getVisibleSidebarShops() {
        return sidebarShops.filter((shop) => markerState.activeCategories.has(normalizeCategory(shop.category)));
      }

      function showMapMessage(message) {
        const messageBox = document.getElementById("map-unavailable");
        messageBox.textContent = message;
        messageBox.classList.remove("hidden");
      }

      function hideMapMessage() {
        document.getElementById("map-unavailable").classList.add("hidden");
      }

      const FLAG_COLORS = {
        "Argentina":"#74ACDF","Australia":"#00008B","Austria":"#ED2939",
        "Belgium":"#FDDA24","Bolivia":"#007934","Brazil":"#009C3B",
        "Bulgaria":"#00966E","Canada":"#FF0000","Chile":"#D52B1E",
        "China":"#DE2910","Colombia":"#FCD116","Costa Rica":"#002B7F",
        "Czech Republic":"#D7141A","Denmark":"#C60C30",
        "Dominican Republic":"#002D62","EEUU":"#3C3B6E",
        "Ecuador":"#FFD100","Egypt":"#CE1126","El Salvador":"#0F47AF",
        "England":"#CF081F","Ethiopia":"#009A44","France":"#002395",
        "Greece":"#004C98","Guatemala":"#4997D0","Honduras":"#0073CF",
        "Ireland":"#169B62","Italy":"#008C45","Japan":"#BC002D",
        "Macedonia":"#D20000","Malaysia":"#010066","Mexico":"#006847",
        "México":"#006847","Netherlands":"#AE1C28","Nicaragua":"#0067C6",
        "Norway":"#EF2B2D","Paraguay":"#D52B1E","Peru":"#D91023",
        "Portugal":"#006600","Qatar":"#8D1B3D",
        "Republic of Korea":"#CD2E3A","Romania":"#002B7F",
        "Rwanda":"#20603D","Scotland":"#005EB8","Singapore":"#EF3340",
        "South Africa":"#007749","Spain":"#AA151B",
        "Switzerland":"#D52B1E","Taiwan":"#000095","Thailand":"#A51931",
        "The Philippines":"#0038A8","Turkey":"#E30A17","UAE":"#00732F",
        "United States":"#3C3B6E","Uruguay":"#001489","USA":"#3C3B6E",
        "Venezuela":"#FFCC00",
      };

      const PIN_PATH = "M 0,-24 C -6.6,-24 -12,-18.6 -12,-12 C -12,-4.8 0,0 0,0 C 0,0 12,-4.8 12,-12 C 12,-18.6 6.6,-24 0,-24 Z";

      function flagColorFor(country) {
        return FLAG_COLORS[country] || "#888899";
      }

      function colorForCategory(category) {
        return normalizeCategory(category) === "South" ? "#FF7600" : "#FFD030";
      }

      function shopKey(shop) {
        return `${shop.rank}|${shop.category}|${shop.name}`;
      }

      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");
      }

      function iconForShop(shop, active) {
        const color = flagColorFor(shop.country);
        return {
          path: PIN_PATH,
          fillColor: active ? "#ffffff" : color,
          fillOpacity: active ? 1 : 0.92,
          strokeColor: active ? color : "#ffffff",
          strokeWeight: active ? 2.5 : 1.5,
          scale: active ? 1.4 : 1,
          anchor: new google.maps.Point(0, 0),
          labelOrigin: new google.maps.Point(0, -14),
        };
      }

      function iconForCountry(color, scale) {
        return {
          path: PIN_PATH,
          fillColor: color,
          fillOpacity: 0.92,
          strokeColor: "#ffffff",
          strokeWeight: 2,
          scale: scale / 12,
          anchor: new google.maps.Point(0, 0),
          labelOrigin: new google.maps.Point(0, -14),
        };
      }

      function updateDetailPanel(shop) {
        if (!shop) return;
        document.getElementById("shop-name").textContent = shop.name;
        document.getElementById("shop-rank-badge").textContent = `#${shop.rank} ${shop.category}`;
        document.getElementById("shop-rating").textContent = `Rank #${shop.rank} · ${shop.category}`;
        const location = [shop.address, shop.city, shop.country].filter(Boolean).join(", ");
        document.getElementById("shop-address").textContent = location || "Address unavailable";
        document.getElementById("shop-directions").href = shop.google_maps_url;
        const website = document.getElementById("shop-website");
        website.href = shop.source_url || shop.google_maps_url;
        website.textContent = shop.source_url ? "Source Page" : "Source Unavailable";
        document.getElementById("shop-map-link").href = shop.google_maps_url;
        const cityCountry = [shop.city, shop.country].filter(Boolean).join(", ");
        document.getElementById("shop-category").textContent = shop.category || "Unknown";
        document.getElementById("shop-city-country").textContent = cityCountry || "Unknown";
        const hasCoords = Number.isFinite(shop.lat) && Number.isFinite(shop.lng);
        document.getElementById("shop-coordinates").textContent = hasCoords
          ? `${Number(shop.lat).toFixed(4)}, ${Number(shop.lng).toFixed(4)}`
          : "Unavailable";
        document.getElementById("shop-place-id").textContent = shop.place_id || "Unavailable";
      }

      function clearMarkers(markers) {
        markers.forEach((marker) => marker.setMap(null));
        markers.length = 0;
      }

      function labelColor(hexBg) {
        const r = parseInt(hexBg.slice(1, 3), 16);
        const g = parseInt(hexBg.slice(3, 5), 16);
        const b = parseInt(hexBg.slice(5, 7), 16);
        return (r * 0.299 + g * 0.587 + b * 0.114) > 140 ? "#111318" : "#ffffff";
      }

      function openShopInfo(marker, shop) {
        markerState.selectedShop = shop;
        updateDetailPanel(shop);
        const shopName = escapeHtml(shop.name);
        const cityCountry = escapeHtml(`${shop.city ? `${shop.city}, ` : ""}${shop.country || ""}`);
        const category = escapeHtml(shop.category || "");
        const flagHex = flagColorFor(shop.country);
        markerState.infoWindow.setContent(
          `<div style="min-width:200px;color:#101217;font-family:system-ui,sans-serif">` +
            `<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">` +
              `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${flagHex};border:1px solid #ccc"></span>` +
              `<strong>#${shop.rank} ${shopName}</strong>` +
            `</div>` +
            `<span>${cityCountry}</span><br/>` +
            `<span style="color:#666">${category}</span><br/>` +
            `<a href="${shop.google_maps_url}" target="_blank" rel="noopener" style="color:#1a73e8">Open in Google Maps</a>` +
          `</div>`
        );
        markerState.infoWindow.open({ map: markerState.map, anchor: marker });
      }

      function renderCountryMarkers() {
        clearMarkers(markerState.countryMarkers);
        const visibleShops = getVisibleShops();
        if (!visibleShops.length) return;

        const counts = new Map();
        visibleShops.forEach((shop) => {
          const key = shop.country || "Unknown";
          const value = counts.get(key) || { count: 0, sample: shop };
          value.count += 1;
          if (shop.rank < value.sample.rank) value.sample = shop;
          counts.set(key, value);
        });

        const maxCount = Math.max(...Array.from(counts.values()).map((row) => row.count));

        mapCountries.forEach((countryRow) => {
          const match = counts.get(countryRow.country);
          if (!match) return;

          const ratio = match.count / Math.max(1, maxCount);
          const scale = 16 + ratio * 24;
          const marker = new google.maps.Marker({
            position: { lat: countryRow.lat, lng: countryRow.lng },
            map: markerState.map,
            icon: iconForCountry(countryRow.color, scale),
            title: `${countryRow.country} - ${match.count} shops`,
            label: {
              text: String(match.count),
              color: labelColor(countryRow.color),
              fontSize: "11px",
              fontWeight: "700",
            },
          });

          marker.addListener("click", () => {
            markerState.map.setZoom(5);
            markerState.map.panTo(marker.getPosition());
            openShopInfo(marker, match.sample);
          });

          markerState.countryMarkers.push(marker);
        });
      }

      function renderShopMarkers() {
        clearMarkers(markerState.shopMarkers);
        const visibleShops = getVisibleShops();
        visibleShops.forEach((shop) => {
          const active = markerState.selectedShop && shopKey(markerState.selectedShop) === shopKey(shop);
          const color = flagColorFor(shop.country);
          const marker = new google.maps.Marker({
            position: { lat: shop.lat, lng: shop.lng },
            map: markerState.map,
            icon: iconForShop(shop, active),
            title: `${shop.rank}. ${shop.name} (${shop.country})`,
            label: {
              text: String(shop.rank),
              color: active ? labelColor("#ffffff") : labelColor(color),
              fontSize: "9px",
              fontWeight: "700",
            },
          });

          marker.addListener("click", () => {
            markerState.selectedShop = shop;
            renderShopMarkers();
            openShopInfo(marker, shop);
          });

          markerState.shopMarkers.push(marker);
        });
      }

      function refreshMapLayers() {
        if (!markerState.map) return;
        const zoom = markerState.map.getZoom() || 2;
        if (zoom < 4) {
          clearMarkers(markerState.shopMarkers);
          renderCountryMarkers();
        } else {
          clearMarkers(markerState.countryMarkers);
          renderShopMarkers();
        }
      }

      function wireCategoryChips() {
        document.querySelectorAll(".category-chip").forEach((chip) => {
          chip.addEventListener("click", () => {
            const category = chip.dataset.category;
            if (markerState.activeCategories.has(category) && markerState.activeCategories.size === 1) return;
            if (markerState.activeCategories.has(category)) {
              markerState.activeCategories.delete(category);
              chip.classList.remove("active");
            } else {
              markerState.activeCategories.add(category);
              chip.classList.add("active");
            }
            markerState.selectedShop = null;
            refreshMapLayers();
            const visible = getVisibleSidebarShops();
            if (visible.length) updateDetailPanel(visible[0]);
          });
        });
      }

      function initOverviewMap() {
        if (!window.google || !window.google.maps) {
          showMapMessage("Google Maps failed to load.");
          return;
        }
        markerState.map = new google.maps.Map(document.getElementById("overview-map"), {
          center: { lat: 10, lng: 0 },
          zoom: 2,
          mapTypeControl: false,
          streetViewControl: false,
          styles: [
            { elementType: "geometry", stylers: [{ color: "#1a1a1e" }] },
            { elementType: "labels.text.stroke", stylers: [{ color: "#15151a" }] },
            { elementType: "labels.text.fill", stylers: [{ color: "#6b6b78" }] },
            { featureType: "administrative.country", elementType: "geometry.stroke", stylers: [{ color: "#2a2a32" }, { weight: 0.8 }] },
            { featureType: "administrative.country", elementType: "labels.text.fill", stylers: [{ color: "#555566" }] },
            { featureType: "road", stylers: [{ visibility: "off" }] },
            { featureType: "poi", stylers: [{ visibility: "off" }] },
            { featureType: "transit", stylers: [{ visibility: "off" }] },
            { featureType: "water", elementType: "geometry", stylers: [{ color: "#111116" }] },
            { featureType: "landscape.natural", elementType: "geometry", stylers: [{ color: "#1e1e24" }] },
          ],
        });

        markerState.infoWindow = new google.maps.InfoWindow();
        markerState.selectedShop = getVisibleSidebarShops()[0] || sidebarShops[0] || null;
        updateDetailPanel(markerState.selectedShop);
        markerState.map.addListener("zoom_changed", refreshMapLayers);
        if (!mapShops.length) {
          showMapMessage(
            "No mapped coordinates are available yet. Run owner geocoding first: python src/main.py owner-geocode --api-key $GOOGLE_MAPS_JS_API_KEY"
          );
          document.getElementById("shop-name").textContent = "No geocoded map markers";
          document.getElementById("shop-address").textContent =
            "Map is available, but markers need lat/lng values in data/current_list.json.";
          return;
        }

        hideMapMessage();
        refreshMapLayers();

        if (mapMissingCoordsCount > 0) {
          document.querySelector(".map-help").textContent = `${mapMissingCoordsCount} shops were skipped due to missing coordinates.`;
        }
      }

      function loadGoogleMapsScript() {
        if (!googleMapsKey) {
          showMapMessage(
            "Google Maps API key is not configured in environment. Add GOOGLE_MAPS_JS_API_KEY to .env and rebuild/restart."
          );
          return;
        }
        window.initOverviewMap = initOverviewMap;
        const script = document.createElement("script");
        script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(googleMapsKey)}&callback=initOverviewMap`;
        script.async = true;
        script.defer = true;
        script.onerror = () => showMapMessage("Google Maps failed to load. Verify API key restrictions.");
        document.head.appendChild(script);
      }

      wireCategoryChips();
      loadGoogleMapsScript();
    </script>
  </body>
</html>
"""


def _style_css() -> str:
    return """
:root {
  --brand-gold: #ffd030;
  --brand-orange: #ff7600;
  --brand-dark: #0b0c10;
  --brand-surface: #18191e;
  --brand-card: #24252c;
  --brand-gray: #888899;
  --brand-white: #f8f8ff;
  --line: rgba(255, 255, 255, 0.09);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  color: var(--brand-white);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: radial-gradient(circle at 20% -10%, #2a1f1b 0%, transparent 40%),
    radial-gradient(circle at 90% 8%, #2e2118 0%, transparent 38%),
    var(--brand-dark);
}
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
}
.shell-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid var(--line);
  background: rgba(24, 25, 30, 0.88);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 10px 12px;
}
.brand-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: var(--brand-gold);
  color: var(--brand-dark);
  display: grid;
  place-items: center;
  font-size: 1rem;
  font-weight: 900;
}
.brand-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: 0.01em;
}
.brand-sub {
  margin: 0;
  color: var(--brand-gray);
  font-size: 0.66rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.collection-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.5);
  padding: 4px;
}
.category-chip {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #cbccd6;
  padding: 6px 12px;
  font-size: 0.74rem;
  font-weight: 700;
  cursor: pointer;
}
.category-chip.active {
  background: var(--brand-gold);
  color: var(--brand-dark);
}
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.view-toggle {
  display: flex;
  align-items: center;
  gap: 3px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.45);
  padding: 3px;
}
.view-btn {
  border: 0;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.72rem;
  font-weight: 700;
  color: #aeb0bc;
  background: transparent;
  cursor: pointer;
}
.view-btn.active {
  background: #f4f5fa;
  color: var(--brand-dark);
}
.profile-badge {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  border: 2px solid transparent;
  background: linear-gradient(145deg, #2b2b32, #1a1a20);
  display: grid;
  place-items: center;
  font-size: 0.82rem;
}
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  border-radius: 8px;
  border: 1px solid var(--line);
  padding: 8px;
  font-size: 0.72rem;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.04);
  color: #e8ebf7;
}
.shell-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr;
}
.workspace-main {
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(24, 25, 30, 0.78);
  backdrop-filter: blur(8px);
  padding: 10px;
  min-height: 0;
}
.workspace-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.workspace-head h1 {
  margin: 0;
  font-size: 1.15rem;
  line-height: 1.2;
}
.workspace-head p {
  margin: 4px 0 0;
  font-size: 0.82rem;
  color: #9fa3b1;
}
.meta-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.chip {
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  padding: 5px 9px;
  font-size: 0.72rem;
}
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.tab-btn {
  border: 1px solid var(--line);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.04);
  color: #c7cbd9;
  padding: 7px 11px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}
.tab-btn.active {
  border-color: rgba(255, 208, 48, 0.4);
  background: rgba(255, 208, 48, 0.16);
  color: #ffe8a2;
}
.tab-panel { display: none; }
.tab-panel.active { display: block; }
.overview-panel {
  position: relative;
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  background: rgba(5, 5, 8, 0.55);
}
.overview-stage {
  position: relative;
  min-height: clamp(520px, 70vh, 760px);
}
#overview-map {
  position: absolute;
  inset: 0;
}
.map-unavailable {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(8, 8, 12, 0.9);
  color: #f2f3fc;
  text-align: center;
  padding: 24px;
  font-size: 0.9rem;
}
.map-unavailable.hidden { display: none; }
.map-help {
  position: absolute;
  right: 14px;
  bottom: 14px;
  z-index: 5;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: rgba(24, 25, 30, 0.88);
  padding: 8px 10px;
  font-size: 0.72rem;
  color: #dbdeea;
  max-width: 260px;
}
.detail-panel {
  position: absolute;
  inset: 10px auto 10px 10px;
  width: min(350px, calc(100% - 20px));
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  background: rgba(9, 10, 14, 0.92);
  backdrop-filter: blur(12px);
  z-index: 6;
  display: flex;
  flex-direction: column;
}
.hero-image {
  position: relative;
  height: 154px;
  overflow: hidden;
}
.hero-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.75);
}
.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 30%, rgba(0, 0, 0, 0.8) 100%);
}
.badge-row {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  gap: 6px;
}
.badge {
  border-radius: 8px;
  padding: 4px 7px;
  font-size: 0.62rem;
  text-transform: uppercase;
  font-weight: 800;
  letter-spacing: 0.05em;
}
.badge.rank {
  background: var(--brand-orange);
  color: #0d0d10;
}
.badge.type {
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.15);
}
.detail-content {
  display: grid;
  gap: 10px;
  padding: 12px;
  overflow: auto;
}
.shop-title {
  margin: 0;
  line-height: 1.1;
  font-size: 1.6rem;
  font-weight: 800;
}
.shop-rating {
  margin: 3px 0 0;
  color: #ffd769;
  font-size: 0.73rem;
  font-weight: 700;
}
.shop-address {
  margin: 0;
  color: var(--brand-gray);
  font-size: 0.74rem;
}
.action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  border-radius: 8px;
  border: 1px solid rgba(255, 208, 48, 0.45);
  padding: 8px;
  font-size: 0.72rem;
  font-weight: 800;
  grid-column: 1 / -1;
  background: var(--brand-gold);
  color: #0f1116;
}
.detail-section {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 8px;
}
.section-title {
  margin: 0 0 8px;
  color: #d7b84e;
  font-size: 0.63rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 800;
}
.menu-item {
  display: grid;
  grid-template-columns: 42px 1fr auto;
  gap: 8px;
  align-items: center;
}
.menu-thumb {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  object-fit: cover;
}
.menu-name {
  margin: 0;
  font-size: 0.74rem;
  font-weight: 700;
}
.menu-desc {
  margin: 2px 0 0;
  color: var(--brand-gray);
  font-size: 0.67rem;
  line-height: 1.35;
}
.menu-price {
  color: var(--brand-orange);
  font-size: 0.72rem;
  font-weight: 700;
}
.book-btn {
  width: 100%;
  border: 0;
  border-radius: 9px;
  padding: 9px;
  background: #f4f5fa;
  color: #0b0c10;
  font-size: 0.74rem;
  font-weight: 800;
}
.overview-list {
  padding: 10px;
}
.overview-list.is-hidden {
  display: none;
}
table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(10, 10, 14, 0.75);
}
th,
td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 8px 7px;
  text-align: left;
  font-size: 0.73rem;
}
th {
  color: #f1d36a;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.66rem;
  background: rgba(255, 255, 255, 0.05);
}
.panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: rgba(9, 10, 14, 0.65);
  padding: 10px;
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
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 9px;
  background: rgba(10, 10, 14, 0.75);
}
.shop-row .rank {
  font-weight: 800;
  color: #ffdca1;
}
.shop-row .meta small {
  color: var(--brand-gray);
  display: block;
  margin-top: 2px;
}
.shop-row a {
  color: #ffdca1;
  font-weight: 600;
  text-decoration: none;
}
.shop-row a:hover,
.shop-row a:focus-visible {
  color: #ffb458;
  outline: none;
}
.shop-row.top10 {
  border-color: rgba(255, 208, 48, 0.35);
  background: rgba(255, 208, 48, 0.08);
}
.is-hidden {
  display: none !important;
}
@media (max-width: 1080px) {
  .collection-toggle {
    display: none;
  }
  .detail-panel {
    position: static;
    width: 100%;
    border-radius: 0;
    border-left: 0;
    border-right: 0;
    border-top: 1px solid var(--line);
    max-height: 360px;
  }
  .overview-stage {
    min-height: 650px;
  }
}
@media (max-width: 760px) {
  .shell-topbar {
    flex-wrap: wrap;
  }
  .topbar-actions {
    width: 100%;
    justify-content: space-between;
  }
  .workspace-head {
    flex-direction: column;
    align-items: flex-start;
  }
  .shop-row {
    grid-template-columns: 48px 1fr;
  }
  .shop-row a {
    grid-column: 2;
  }
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
