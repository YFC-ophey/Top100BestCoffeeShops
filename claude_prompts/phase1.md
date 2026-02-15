# Phase 1: Scraper Implementation

**Context**: We are building a tool to scrape the "Top 100 Coffee Shops" list. The site is static HTML (WordPress + Elementor), no pagination — all 100 shops on one page per list. City data may only exist on individual detail pages.

**Goal**: Create `src/scraper.py` to extract shop data including **full addresses** from detail pages.

**Pre-requisite**: Run the discovery prompt first to validate DOM selectors and confirm city data availability on detail pages before building the full scraper.

**Requirements**:
1.  **Dependencies**: Use `requests` and `beautifulsoup4`.
2.  **URLs**:
    -   Main: `https://theworlds100bestcoffeeshops.com/top-100-coffee-shops/`
    -   South: `https://theworlds100bestcoffeeshops.com/top-100-coffee-shops-south/`
3.  **Logic**:
    -   Fetch the main/south list page.
    -   Parse the list items. Each item has a Name, Country, Rank, and a **Link** to a detail page.
    -   **DOM selectors** (to be confirmed by discovery prompt):
        -   List items contain rank, name, country.
        -   Detail URL is a link on each list item.
    -   **Loop through each item**:
        -   Fetch the detail page.
        -   Extract the **City** and **Full Address** from the detail page.
        -   **Rate limiting**: `time.sleep(1)` between requests to be polite.
    -   Handle connectivity errors gracefully (retry with backoff, or log and continue).
4.  **Output**:
    -   A function `scrape_all()` that returns a list of dictionaries:
        ```python
        {
          "name": "Toby's Estate",
          "city": "Sydney",
          "country": "Australia",
          "rank": 1,
          "category": "Main", # or "South"
          "detail_url": "...",
          "address": "32-36 City Rd, Chippendale NSW 2008..."
        }
        ```
    -   A `if __name__ == "__main__":` block that runs the scrape and saves to `data/raw_coffee_shops.json`.

**Note**: The detail pages might use relative links. Ensure you construct the full URL. The scraper output feeds into the geocoder (Phase 2), which is run by the project owner only — users never need to scrape or geocode.
