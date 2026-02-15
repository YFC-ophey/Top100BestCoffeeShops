# Phase 2: Geocoding, KML Generation & Static Site

**Context**: We have `data/raw_coffee_shops.json` from Phase 1. We need to geocode (owner-only), generate KML files, and build a static site for GitHub Pages.

## Part A: Geocoder (`src/geocoder.py`) — Owner-Only

> **Important**: This step is run ONLY by the project owner using their personal Google API key. End users never need an API key. Pre-geocoded data is committed to the repo.

1.  **Dependencies**: Use `requests`.
2.  **Input**: The list of dicts from Phase 1.
3.  **Google Places API**:
    -   Use `https://maps.googleapis.com/maps/api/place/textsearch/json`.
    -   Query: `"{shop_name} {address} {country}"`.
    -   API key loaded from `.env` file (never committed).
4.  **Logic**:
    -   Iterate through the raw list.
    -   If `lat/lng` is missing, call the API.
    -   **Validation**: Check `types` in response. Warn if it's not `food`, `cafe`, `bakery`, etc.
    -   Extract: `name`, `formatted_address`, `place_id`, `geometry.location.lat`, `geometry.location.lng`.
    -   **Cost Control**:
        -   Cap at 250 calls per run (safety).
        -   Check if shop is already geocoded in `data/current_list.json` to avoid re-fetching.
        -   Expected cost: ~$3.40 for ~200 shops (covered by Google's $200/month free tier).
5.  **Output**: Enriched dicts saved to `data/current_list.json` (committed to repo).

## Part B: KML Generator (`src/generator.py`)

1.  **Dependencies**: Use `simplekml` (add to `requirements.txt`).
2.  **Logic**:
    -   Create two KML files: one for Main Top 100, one for South America Top 100.
    -   Add a Point for each shop with:
        -   Name: `#{rank} {name}`
        -   Description: `Address: {address}\nCity: {city}\nCountry: {country}`
        -   ExtendedData: `place_id`.
    -   **Pin styling**: Rank 1-10 get a star icon, others get a dot.
3.  **Output**: `output/coffee_shops_main.kml`, `output/coffee_shops_south.kml`.

## Part C: Static Site Builder (`src/site_builder.py`) — NEW

1.  **Dependencies**: Use Python's built-in `string.Template` or Jinja2 (add to `requirements.txt` if using Jinja2).
2.  **Logic**:
    -   Generate a polished one-page HTML site with two sections: Main Top 100 + South America Top 100.
    -   **Each section includes**:
        -   Embedded Google My Maps iframe (owner creates the My Maps layer once per year, URL hardcoded in config).
        -   Ranked list of shops with:
            -   Rank, name, city, country.
            -   "Open in Google Maps" link using `https://www.google.com/maps/search/?api=1&query={name}+{address}` (no API key needed).
        -   KML download button linking to the repo's KML files.
    -   **Design**:
        -   Editorial feel — highlight the Madrid ceremony and award prestige.
        -   Clean, responsive layout. Not just a data dump.
        -   Mobile-friendly.
3.  **Output**: `site/index.html` + `site/assets/` (CSS, images if any).

## Part D: Orchestrator (`src/main.py`)

1.  Wire it all together with different modes:
    -   `scrape-only`: Just run the scraper.
    -   `geocode`: Run geocoder on raw data (owner-only, requires API key).
    -   `build-site`: Generate KML + static site from pre-geocoded data.
    -   `full`: All steps in sequence.
2.  Steps for `full` mode:
    -   Scrape -> `raw_data`.
    -   Load `data/current_list.json` (previous geocoded state, used as cache).
    -   Geocode new/changed shops only.
    -   Save to `data/current_list.json`.
    -   Generate KML files.
    -   Build static site.
    -   Print summary: "Scraped 100, Geocoded 10 new, Generated KML, Built site."

**Action**: Implement `src/geocoder.py`, `src/generator.py`, `src/site_builder.py`, and `src/main.py`. Update `requirements.txt` with `simplekml` and optionally `jinja2`.
