# Phase 4: CI/CD Automation

**Context**: The script works locally. Now we need it to run automatically on GitHub.

**Goal**: Create `.github/workflows/update_map.yml`.

## Requirements

1.  **Trigger**:
    -   `schedule`:
        -   `cron: '0 9 * 2 *'` (Daily at 9am UTC in February).
        -   `cron: '0 9 * * 1'` (Every Monday at 9am UTC rest of year - keep it alive).
    -   `workflow_dispatch`: Allow manual trigger button.

2.  **Jobs**:
    -   **Run Update**:
        -   OS: `ubuntu-latest`.
        -   Steps:
            -   Checkout code (fetch-depth: 0 for git history).
            -   Set up Python 3.10.
            -   Install dependencies (`pip install -r requirements.txt`).
            -   Run Script: `python src/main.py`.
                -   **Env Var**: `GOOGLE_API_KEY` (Secrets).
            -   **Commit & Push**:
                -   Check if `data/current_list.json` or `coffee_shops.kml` changed.
                -   If yes:
                    -   Config git user (actions-user).
                    -   `git add .`
                    -   `git commit -m "Auto-update: Found new coffee shops"`
                    -   `git push`

**Critical**: Ensure the `GOOGLE_API_KEY` is referenced from `${{ secrets.GOOGLE_API_KEY }}`.

**Action**: Create the workflow file.
