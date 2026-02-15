# Implementation Plan - Coffee Map Auto-Sync

The goal is to build a Python-based tool that scrapes the top 100 coffee shops, geocodes them (owner-only, once per year), and publishes a polished static website on GitHub Pages with embedded maps, ranked lists, and KML downloads.

## Key Architecture Decisions
> [!IMPORTANT]
> - **No user-facing API key required.** The Google Places API is used only by the project owner to geocode ~200 shops once per year (~$3.40, covered by free tier).
> - **Pre-geocoded data is committed to the repo.** Open-source users get lat/lng, place_id, and addresses out of the box.
> - **Static site on GitHub Pages.** A polished one-pager with editorial feel — two sections (Main Top 100 + South America Top 100), embedded Google My Maps iframes, ranked lists with "Open in Google Maps" links, and KML download buttons.
> - **No rush for Feb 16.** Wait for the list to actually update, scrape real 2026 data, build the site over 3-4 days, ship ~Feb 21.

## Repository Structure

```
Top100BestCoffeeShops/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Scrapes list + detail pages
│   ├── geocoder.py         # Google Places API (owner-only)
│   ├── generator.py        # KML file generation
│   ├── site_builder.py     # Static HTML site generation
│   ├── templates.py        # Jinja2 HTML/CSS template strings
│   └── main.py             # Orchestrator
├── data/
│   ├── raw_coffee_shops.json    # Raw scraped data
│   └── current_list.json        # Pre-geocoded data (committed)
├── site/
│   ├── index.html               # Generated static site
│   └── assets/
│       └── style.css            # Generated CSS
├── output/
│   ├── coffee_shops_main.kml    # KML for Main Top 100
│   └── coffee_shops_south.kml   # KML for South America Top 100
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures + mock HTML
│   ├── test_scraper.py          # Scraper unit tests
│   ├── test_scraper_integration.py  # Scraper integration tests
│   ├── test_geocoder.py         # Geocoder tests
│   ├── test_generator.py        # KML generator tests
│   └── test_site_builder.py     # Site builder tests
├── .github/
│   └── workflows/
│       └── update_map.yml       # CI/CD + GitHub Pages deploy
├── requirements.txt
└── main.py                      # Entry point (thin wrapper)
```

## Dependencies (`requirements.txt`)

```
requests==2.31.0
beautifulsoup4==4.12.3
lxml==5.1.0
python-dotenv==1.0.1
simplekml==1.3.6
jinja2==3.1.3
pytest==8.0.2
```

---

## Phase 1: Scraper (`src/scraper.py`) — COMPLETE

**Status**: Done. 295 lines, 45 tests passing.

- Fetches Main + South America list pages.
- Parses HTML using BeautifulSoup — groups `<a>` tags by URL to extract rank (h3), name (h2), country (p) per shop.
- Visits each detail page to extract city and full address from Contact/Contacto sections.
- Rate limiting: `time.sleep(1)` between detail page requests.
- Retry with exponential backoff (3 attempts, 2s base).
- Output: `data/raw_coffee_shops.json`.

**Scraper output format:**
```python
{
    "name": str,        # Shop name
    "rank": int,        # Rank 1-100
    "country": str,     # Country (default "Unknown")
    "city": str | None, # City from detail page
    "address": str,     # Full address or "Address not found"
    "category": str,    # "Main" or "South"
    "detail_url": str   # Detail page URL
}
```

**Key public functions:**
- `scrape_all()` → combined list of Main + South shops
- `scrape_list(list_url, category, delay)` → list for one category
- `parse_list_page(soup, category)` → parse without network calls
- `extract_detail_info(detail_url)` → dict with city and address
- `fetch_page(url, retries)` → BeautifulSoup | None

---

## Phase 2: Geocoding + Site Generation

### Part A: Geocoder (`src/geocoder.py`) — Owner-Only (~180 lines)

- Uses Google Places API Text Search (`textsearch/json`).
- Input: raw scraped data from Phase 1.
- Query: `"{name} {address} {country}"` — omits address if "Address not found".
- Output: enriched data with `lat`, `lng`, `place_id`, `formatted_address`.
- Cost control: skip already-geocoded shops (cache match by name + category), cap at 250 calls per run.
- **API key**: loaded from `.env` via `python-dotenv`. Never committed.
- Pre-geocoded results saved to `data/current_list.json` and committed to repo.
- Validates place types — warns if result isn't cafe/food/bakery.
- Handles `ZERO_RESULTS` gracefully (lat/lng set to None, logs warning).

**Enriched output format** (extends scraper output):
```python
{
    ...scraper fields...,
    "lat": float | None,
    "lng": float | None,
    "place_id": str | None,
    "formatted_address": str | None
}
```

**Key functions:**
- `geocode_all(raw_shops, api_key, cache)` → enriched list
- `geocode_shop(shop, api_key)` → single enriched dict
- `load_cache()` / `save_cache(shops)` → read/write `data/current_list.json`
- `load_api_key()` → loads from `.env`

### Part B: KML Generator (`src/generator.py`) (~130 lines)

- Uses `simplekml` library.
- Two KML files: Main Top 100, South America Top 100.
- Pin name: `#{rank} {name}`.
- Description: `Address: {address}\nCity: {city}\nCountry: {country}`.
- ExtendedData: `place_id`.
- Pin styling: rank 1-10 get star icon, others get dot.
- Skips shops with `None` coordinates (logs warning).
- Coordinate order: `(lng, lat)` for simplekml.
- Output: `output/coffee_shops_main.kml`, `output/coffee_shops_south.kml`.

**Key functions:**
- `generate_kml(shops)` → creates both files, returns `(main_path, south_path)`
- `generate_single_kml(shops, filepath, title)` → one KML file, returns shop count

### Part C: Static Site Builder (`src/site_builder.py` ~200 lines + `src/templates.py` ~280 lines)

Split into two files to stay under 300-line limit.

- Uses Jinja2 for HTML templating.
- Generates a polished one-page HTML site.
- Two sections: Main Top 100 + South America Top 100.
- Each section includes:
    - Embedded Google My Maps iframe (owner creates layer once per year, URL configurable).
    - Ranked list with "Open in Google Maps" links (`google.com/maps/search/?api=1&query=...` — no API key needed).
    - KML download button.
- Editorial design: highlight the Madrid ceremony and award prestige.
- Responsive/mobile-friendly layout.
- Top 10 shops visually highlighted.
- Output: `site/index.html` + `site/assets/style.css`.

**Key functions in site_builder.py:**
- `build_site(shops)` → writes index.html + style.css, returns index path
- `_build_maps_url(name, address)` → Google Maps search URL (no API key)
- `_prepare_shop_data(shops, category)` → filter, add maps_url, mark top 10, sort by rank
- `_render_html(main_shops, south_shops)` → Jinja2 render

**templates.py:** `HTML_TEMPLATE` (Jinja2 string) + `CSS_TEMPLATE` (CSS string).

### Part D: Orchestrator (`src/main.py` ~150 lines + root `main.py` ~10 lines)

- CLI via argparse with 4 subcommands:
    - `scrape-only`: run scraper, save to `data/raw_coffee_shops.json`
    - `geocode`: load raw data, geocode new shops, save to `data/current_list.json` (owner-only)
    - `build-site`: load cached data, generate KML + build site
    - `full`: all steps in sequence (owner-only, requires API key)
- Prints human-readable summary of actions taken.
- Root `main.py` is a thin wrapper: `from src.main import run; run()`.

---

## Phase 3: Testing

Per-module test files (following the pattern established in Phase 1):

- **`tests/test_geocoder.py`** (~150 lines): Mock Google API responses, verify enrichment with place_id/lat/lng. Edge cases: ZERO_RESULTS, cache skipping, API call cap, non-cafe type warnings.
- **`tests/test_generator.py`** (~120 lines): Verify valid KML XML output, correct coordinates and names, pin styling, skip null coords. Uses `tmp_path` fixture.
- **`tests/test_site_builder.py`** (~130 lines): Verify HTML contains ranked lists, Google Maps links (no API key in URLs), KML download buttons, responsive meta tags, two sections. Uses `tmp_path` fixture.
- **`tests/conftest.py`** (update): Add shared mock data for geocoder/generator/site builder tests.

**Total test target**: ~75 tests (existing 45 + ~30 new).

---

## Phase 4: CI/CD + GitHub Pages Deployment

**GitHub Actions workflow** (`.github/workflows/update_map.yml`, ~110 lines):

- **Triggers**:
    - `schedule`: `0 9 * 2 *` (daily at 9am UTC in February).
    - `schedule`: `0 9 * * 1` (every Monday at 9am UTC, keeps workflow alive year-round).
    - `workflow_dispatch`: manual trigger button.
- **Job 1: Scrape & Build**:
    - Checkout, Python 3.11, install deps.
    - Run `python main.py scrape-only`.
    - Run `python main.py build-site`.
    - Check for changes in `data/`, `output/`, `site/`.
    - If changes: commit, push, create GitHub issue for owner ("new data detected, geocoding may be needed").
- **Job 2: Deploy to GitHub Pages**:
    - Uses `actions/deploy-pages@v4` (official GitHub action).
    - Deploys `site/` directory.
- **Geocoding is NOT automated** — owner runs `python main.py geocode` locally when new data appears.

---

## Verification Plan

### Automated Tests
- `pytest tests/ -v` — all ~75 tests pass.
- Mock HTML source to verify scraper logic.
- Mock Google API responses to verify geocoder logic without spending credits.
- Verify KML output is valid XML with correct coordinates.
- Verify static site HTML contains expected elements (no API keys exposed).

### Manual Verification
- Run scraper against live site to validate selectors.
- Import KML into Google My Maps to verify pins.
- Preview `site/index.html` locally before deploying.
- Test "Open in Google Maps" links on mobile and desktop.
- Validate KML: `python -c "import xml.etree.ElementTree as ET; ET.parse('output/coffee_shops_main.kml')"`

---

## Timeline
- **~Feb 16**: List updates on source site.
- **Feb 16-17**: Validate scraper selectors against 2026 data, scrape real data.
- **Feb 17-18**: Owner geocodes with personal API key. Generate KML and static site.
- **Feb 19-20**: Testing, polish, and manual verification.
- **~Feb 21**: Ship to GitHub Pages.
