# Phase 4: CI/CD + GitHub Pages Deployment

**Context**: The script works locally. Now we need it to run automatically on GitHub and deploy the static site to GitHub Pages.

**Goal**: Create `.github/workflows/update_map.yml` for automation and GitHub Pages deployment.

## Requirements

1.  **Trigger**:
    -   `schedule`:
        -   `cron: '0 9 * 2 *'` (Daily at 9am UTC in February).
        -   `cron: '0 9 * * 1'` (Every Monday at 9am UTC rest of year — keep it alive).
    -   `workflow_dispatch`: Allow manual trigger button.

2.  **Jobs**:

    ### Job 1: Scrape & Build
    -   OS: `ubuntu-latest`.
    -   Steps:
        -   Checkout code (fetch-depth: 0 for git history).
        -   Set up Python 3.11.
        -   Install dependencies (`pip install -r requirements.txt`).
        -   Run scraper: `python src/main.py scrape-only`.
        -   Build site from pre-geocoded data: `python src/main.py build-site`.
        -   **Check for changes**: Did `data/raw_coffee_shops.json` change?
        -   If yes:
            -   Config git user (actions-user).
            -   `git add data/ output/ site/`
            -   `git commit -m "Auto-update: new coffee shop data detected"`
            -   `git push`
            -   Create a GitHub Issue notifying owner that new data was found and geocoding may be needed.

    ### Job 2: Deploy to GitHub Pages
    -   Triggered after Job 1 completes (or on any push to main that changes `site/`).
    -   Uses `actions/deploy-pages` or `peaceiris/actions-gh-pages`.
    -   Deploys `site/` directory to GitHub Pages.

3.  **Important Notes**:
    -   **Geocoding is NOT automated in CI.** The owner runs `python src/main.py geocode` locally with their API key when new data appears.
    -   The `GOOGLE_API_KEY` secret is **not required** for the CI workflow. It's only used locally by the owner.
    -   The workflow builds the static site from whatever pre-geocoded data exists in `data/current_list.json`.

4.  **GitHub Pages Setup**:
    -   Enable GitHub Pages in repo settings, pointing to the `site/` directory on `main` branch (or use `gh-pages` branch).
    -   Custom domain optional (can be configured later).

**Action**: Create the workflow file and configure GitHub Pages deployment.
