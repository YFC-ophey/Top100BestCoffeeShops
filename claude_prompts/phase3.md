# Phase 3: Verification & Tests

**Context**: logic is implemented. Now we need to ensure it doesn't break and doesn't cost us money unnecessarily.

**Goal**: Create `tests/test_core.py` using `unittest` (standard lib) or `pytest`.

## Requirements

1.  **Test Scraper (`test_scraper`)**:
    -   **Mock**: `requests.get`.
    -   **Scenario**: Return a sample HTML string containing 2 shops.
    -   **Assert**: The parser correctly extracts 2 items with correct names and detail URLs.

2.  **Test Geocoder (`test_geocoder`)**:
    -   **Mock**: `requests.get` (for Google API).
    -   **Scenario**:
        -   Input: `[{"name": "Test Cafe", "address": "123 St"}]`
        -   Mock Response: `{"results": [{"place_id": "ChIJ...", "geometry": {"location": {"lat": 1.0, "lng": 1.0}}, "types": ["cafe"]}]}`
    -   **Assert**: The function returns the enriched dict with `place_id`.
    -   **Edge Case**: Mock an empty result (ZERO_RESULTS). Assert it handles it gracefully (maybe leaves lat/lng None).

3.  **Test Generator (`test_generator`)**:
    -   **Scenario**: Pass a list of 1 shop.
    -   **Assert**: The output KML string contains `<name>Test Cafe</name>` and correct coordinates.

**Action**: Create `tests/test_core.py` and run it to verify the codebase structure.
