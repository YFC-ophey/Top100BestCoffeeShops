# Phase 2: Geocoding & KML Generation

**Context**: We have a `data/raw_coffee_shops.json` file from Phase 1.
**Goal**: Create `src/geocoder.py` and `src/generator.py` to turn raw names into a Google My Maps KML file.

## Part A: Geocoder (`src/geocoder.py`)
1.  **Dependencies**: Use `requests`.
2.  **Input**: The list of dicts from Phase 1.
3.  **Google Places API**:
    -   Use `https://maps.googleapis.com/maps/api/place/textsearch/json`.
    -   Query: `"{shop_name} {address} {country}"`.
    -   Why Text Search? It returns `place_id` and is robust against slight name variations.
4.  **Logic**:
    -   Iterate through the raw list.
    -   If `lat/lng` is missing, call the API.
    -   **Validation**: Check `types` in response. Warn if it's not `food`, `cafe`, `bakery`, etc.
    -   Extract: `name`, `formatted_address`, `place_id`, `geometry.location.lat`, `geometry.location.lng`.
    -   **Cost Control**:
        -   Limit to 150 calls per run (safety cap).
        -   Check if the shop is already geocoded in `data/current_list.json` (load this first if it exists) to avoid re-fetching unchanged shops.
5.  **Output**: A list of enriched dicts.

## Part B: KML Generator (`src/generator.py`)
1.  **Dependencies**: Use `xml.etree.ElementTree` or `simplekml` (add to requirements if needed, but `xml` is built-in and fine for simple stuff. Let's stick to built-in to save dependencies, or `simplekml` if you prefer cleaner code. **Decision**: Use `fastkml` or `simplekml` if possible, otherwise raw XML strings are fine for zero-dep).
    -   *Correction*: Let's use `simplekml` for ease. Add it to `requirements.txt`.
2.  **Logic**:
    -   Create a KML object.
    -   Create two Folders: "Top 100" and "South America".
    -   Loop through the geocoded data.
    -   Add a Point for each shop.
    -   **Metadata**:
        -   Name: `#{rank} {name}`
        -   Description: `Address: {address}\nCountry: {country}`
        -   ExtendedData: `place_id` (so My Maps might auto-link it).
3.  **Output**: Save to `coffee_shops.kml`.

## Part C: Main Orchestrator (`src/main.py`)
1.  Wire it all together.
2.  `steps`:
    -   Scrape -> `raw_data`.
    -   Load `data/current_list.json` (previous state).
    -   Geocode (using previous state as cache).
    -   Save new state to `data/current_list.json`.
    -   Generate KML.
    -   Print summary: "Scraped 100, Geocoded 10 new, Generated KML."

**Action**: Implement `src/geocoder.py`, `src/generator.py`, and `src/main.py`. Update `requirements.txt` with `simplekml` if using.
