# Top100BestCoffeeShops

Zero-cost automation for scraping the yearly Top 100 coffee shop list, generating map artifacts, and publishing a static site to GitHub Pages.

## User Workflow (No API Key Required)

Open-source users do **not** need Google Places credentials.

1. `python src/main.py scrape-only`
2. `python src/main.py build-site`
3. Open `site/index.html` or deploy via GitHub Pages workflow.

Map links are generated as public Google Maps search URLs (`google.com/maps/search/`).

## Owner-Only Geocode Refresh (Optional)

If you maintain a private API key, you can enrich `place_id` values once per year:

```bash
python src/main.py owner-geocode --api-key "$GOOGLE_MAPS_API_KEY"
```

This is optional and not required for public usage or static site generation.

## Commands

```bash
# Scrape live list + detail pages (city/address), update data/current_list.json + artifacts
python src/main.py scrape-only

# Build static site
python src/main.py build-site

# Optional owner geocode refresh
python src/main.py owner-geocode --api-key "$GOOGLE_MAPS_API_KEY"
```

## CI/CD

Workflow: `.github/workflows/update_map.yml`

- Runs tests
- Runs scrape-only pipeline (no API key)
- Builds static site
- Commits generated data/site updates
- Deploys `site/` to GitHub Pages
- Opens reminder issue if rows are missing `place_id` values
