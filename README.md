# ROAST. ☕
### World's 100 Best Coffee Shops ☕️ Interactive Map Explorer 🗺️

## The Story

Earlier this year I visited **[Bouche](https://theworlds100bestcoffeeshops.com/)** in Brussels, Belgium and it completely changed what I thought a coffee shop could be. The beans were a house blend, but the quality was on another level. The interior, the merch, the whole vibe: "I was hooked".

That trip sent me down a rabbit hole. I discovered **[The World's 100 Best Coffee Shops](https://theworlds100bestcoffeeshops.com/)**, an annual ranking published every February at a global coffee festival. They release two lists: a **Top 100 Global** and a **Top 100 South America** edition. Bouche made it at #75.

I built ROAST. to make that data actually explorable. 
Whether you're on a work trip, traveling, on vacation, or just visiting someone;  
Whenever the coffee vibes hit, you can open ROAST. and instantly see if one of the world's best coffee shops is near you! Why not?!

---

## Live Preview

[![ROAST. Live Preview](https://raw.githubusercontent.com/YFC-ophey/Top-100-Best-CoffeeShops/main/docs/live-preview-image.png)]

> **[→ Visit ROAST. Live](https://yfc-ophey.github.io/Top-100-Best-CoffeeShops/)**

The site features:
- Interactive world map with country-level shop density bubbles
- Drill-down to individual shop details (address, city, country, rank)
- Filterable list view by collection, country, and rank band
- Public Google Maps links — no API key required for visitors

---

## What This Project Does

A zero-cost, open-source pipeline that:

1. **Scrapes** the annual Top 100 + South America rankings from [theworlds100bestcoffeeshops.com](https://theworlds100bestcoffeeshops.com/)
2. **Enriches** each shop entry with city, address, and geocoordinates
3. **Generates** `JSON`, `CSV`, and `KML` artifacts
4. **Builds** a static site and auto-deploys via GitHub Pages
5. **Runs automatically** on a CI/CD schedule via GitHub Actions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Preview UI | FastAPI + Jinja2 |
| Site Builder | Static HTML/CSS generator |
| Maps | Public Google Maps links (zero API cost) |
| Testing | pytest (21 tests passing) |
| CI/CD | GitHub Actions → GitHub Pages |

---

## Project Structure

```
Top-100-Best-CoffeeShops/
├── src/                  # Scraper, enricher, site builder
├── data/                 # current_list.json (source of truth)
├── output/               # coffee_shops.csv, coffee_shops.kml
├── site/                 # Generated static site (index.html + assets)
├── templates/            # Jinja2 HTML templates
├── tests/                # pytest test suite
├── claude_prompts/       # AI prompts used during development
├── docs/                 # Release timeline and notes
└── .github/workflows/    # CI/CD automation
```

---

## Zero-Cost Boundary

This project runs entirely for free:

- **Visitors** never need a Google API key — all map links are plain Google Maps URLs
- **CI** handles scraping, building, and deploying automatically
- **Optional**: Owner-only geocoding refresh via CLI (uses Google Places API once annually)

---

## Running Locally

```bash
# Install dependencies
pip install -e .

# Run full pipeline (scrape → enrich → build)
python main.py

# Preview UI
uvicorn src.app:app --reload

# Run tests
pytest
```

---

## CI/CD Workflow

On every push to `main`, GitHub Actions will:

1. Run the test suite
2. Execute the scrape + build pipeline
3. Commit generated artifacts back to the repo
4. Deploy to GitHub Pages
5. Open a reminder issue if an owner geocode refresh is needed

---

## Known Limitations

- Source site uses Elementor — selectors may shift when the site redesigns
- Detail-page scraping is intentionally throttled (respectful crawl speed)
- Place ID completeness depends on annual owner geocode refresh

---

## Data Source

All coffee shop data sourced from **[theworlds100bestcoffeeshops.com](https://theworlds100bestcoffeeshops.com/)** — an independent annual ranking published each February.

---

*Built by [@YFC-ophey](https://github.com/YFC-ophey) · [Buy Me a Coffee](https://buymeacoffee.com/opheliachen)*
