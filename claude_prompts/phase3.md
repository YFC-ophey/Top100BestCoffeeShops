# Phase 3: Verification & Tests

**Context**: Core logic is implemented (scraper, geocoder, KML generator, site builder). Now we need to ensure it doesn't break and doesn't cost money unnecessarily.

**Goal**: Create `tests/test_core.py` using `pytest`.

## Requirements

1.  **Test Scraper (`test_scraper`)**:
    -   **Mock**: `requests.get`.
    -   **Scenario**: Return sample HTML strings matching the WordPress + Elementor DOM structure (list page + detail page).
    -   **Assert**: Parser correctly extracts items with correct names, ranks, countries, detail URLs, cities, and addresses.
    -   **Edge Case**: Missing city on detail page — verify graceful handling.

2.  **Test Geocoder (`test_geocoder`)**:
    -   **Mock**: `requests.get` (for Google Places API).
    -   **Scenario**:
        -   Input: `[{"name": "Test Cafe", "address": "123 St", "country": "Spain"}]`
        -   Mock Response: `{"results": [{"place_id": "ChIJ...", "geometry": {"location": {"lat": 40.4, "lng": -3.7}}, "types": ["cafe"]}]}`
    -   **Assert**: Function returns enriched dict with `place_id`, `lat`, `lng`.
    -   **Edge Case**: ZERO_RESULTS — verify it handles gracefully (leaves lat/lng as None, logs warning).
    -   **Cache Test**: Verify already-geocoded shops are skipped (no API call made).

3.  **Test KML Generator (`test_generator`)**:
    -   **Scenario**: Pass a list of 2 shops (one Main, one South).
    -   **Assert**: Output KML is valid XML, contains correct names and coordinates.
    -   **Assert**: Two separate KML files are generated.

4.  **Test Site Builder (`test_site_builder`)**:
    -   **Scenario**: Pass pre-geocoded data for a few shops.
    -   **Assert**: Generated HTML contains:
        -   Ranked list entries with shop names.
        -   "Open in Google Maps" links using `google.com/maps/search/` URLs (no API key in URLs).
        -   KML download buttons.
        -   Two sections (Main + South America).
    -   **Assert**: HTML is valid and responsive meta tags are present.

**Action**: Create `tests/test_core.py` and run it to verify the codebase structure. Use `pytest` (add to `requirements.txt` as dev dependency).
