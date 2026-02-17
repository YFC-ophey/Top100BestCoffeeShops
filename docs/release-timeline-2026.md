# 2026 Release Timeline (OPH-24)

- **February 16, 2026:** Confirmed source update availability and validated selectors against live pages.
- **February 16-17, 2026:** Scrape real 2026 data (`scrape-only`) and detail-page city/address extraction.
- **February 17-18, 2026:** Optional owner geocode refresh and artifact generation (`CSV`, `KML`).
- **February 19-20, 2026:** Full test suite, static site polish, manual verification.
- **Target release:** **Around February 21, 2026** via GitHub Pages deployment workflow.

## Readiness Gates

1. Scraper integrity checks pass.
2. Site generation succeeds from `data/current_list.json` without API key.
3. CI workflow passes test + scrape + build + deploy.
4. Owner geocode reminder issue is generated when `place_id` coverage is incomplete.
