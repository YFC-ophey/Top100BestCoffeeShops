# Phase 1: Scraper Implementation

**Context**: We are building a tool to scrape the "Top 100 Coffee Shops" list.

**Goal**: Create `src/scraper.py` to extract shop data including **full addresses** from detail pages.

**Requirements**:
1.  **Dependencies**: Use `requests` and `beautifulsoup4`.
2.  **URLs**:
    -   Top 100: `https://theworlds100bestcoffeeshops.com/top-100-coffee-shops/`
    -   South America: `https://theworlds100bestcoffeeshops.com/top-100-coffee-shops-south/`
3.  **Logic**:
    -   Fetch the main/south list page.
    -   Parse the list items. Each item has a Name, Country, and a **Link** to a detail page.
    -   **Loop through each item**:
        -   Fetch the detail page (e.g., `/locales/shop-name` or `/locales-south/shop-name`).
        -   Extract the **Full Address** from the detail page (usually in the "Contact" section or `h2`/`p` tags).
        -   **Snooze**: `time.sleep(1)` between requests to be polite.
    -   Handle connectivity errors gracefully (retry or log).
4.  **Output**:
    -   A function `scrape_all()` that returns a list of dictionaries:
        ```python
        {
          "name": "Toby's Estate",
          "country": "Australia",
          "rank": 1,
          "category": "Top 100", # or "South America"
          "detail_url": "...",
          "address": "32-36 City Rd, Chippendale NSW 2008..."
        }
        ```
    -   A `if __name__ == "__main__":` block that runs the scrape and saves it to `data/raw_coffee_shops.json`.

**Note**: The detail pages might use relative links. Ensure you construct the full URL.
