# Implementation Plan - Coffee Map Auto-Sync

The goal is to build a Python-based tool that scrapes the top 100 coffee shops and produces a format importable to Google Maps, automating this process via GitHub Actions.

## User Review Required
> [!IMPORTANT]
> **Google Maps API Access**: You will need to obtain a Google Maps API Key (Free tier) with **Places API** enabled. The script needs this to find the exact coordinates/Place IDs of the shops.
>
> **Write Access Limitation**: Google does NOT provide a public API to write directly to a user's primary "Saved Places" lists (Starred, Want to Go).
> **Solution**: We will generate a **KML/CSV file** that you can import into "Google My Maps". This is the only reliable free method. We can automate the *generation* of this file, but you may need to click "Import" once a year.

## Proposed Changes

### Repository Structure
New repository `coffee-map-sync` logic.

#### [NEW] `src/scraper.py`
- Function to fetch target URLs:
  - Main: `.../top-100-coffee-shops/`
  - South: `.../top-100-coffee-shops-south/`
- Parse HTML using `BeautifulSoup`.
- Extract List of Dicts: `{name, city, country, rank, category}` (category = "Main" or "South").

#### [NEW] `src/geocoder.py`
- Interface with Google Places API.
- Input: "Shop Name, City, Country".
- Output: `lat`, `lng`, `place_id`, `formatted_address`.
- Rate limiting handling (simple sleep).

#### [NEW] `src/generator.py`
- Convert the geocoded list into a **KML** (Keyhole Markup Language) file.
- KML is the native format for Google My Maps.
- **Features**: Organize into two folders/layers: "Top 100" and "South Edition".
- Style the pins (e.g., rank 1-10 get a star, others a dot).

#### [NEW] `main.py`
- Orchestrator script.
- Loads previous state.
- Runs scraper -> geocoder -> generator.
- Saves `coffee_shops.kml`.

#### [NEW] `.github/workflows/update.yml`
- GitHub Actions workflow.
- Schedule:
    - Weekly check.
    - Daily check Feb 10-20.
- Steps:
    - Checkout code.
    - Install Python deps.
    - Run `main.py`.
    - Any changes to `coffee_shops.kml`? -> Commit and Push.

## Verification Plan

### Automated Tests
- Mock the HTML source to verify scraper logic.
- Mock the Google API response to verify geocoder logic without spending credits.
- Verify KML output is valid XML.

### Manual Verification
- Run the script locally once.
- Take string output `coffee_shops.kml`.
- Import into `google.com/maps/d/` (My Maps).
- Verify pins appear correctly on the map.
