# Top100BestCoffeeShops

**Goal:** Maintain a zero-cost, open-source pipeline that scrapes the 2026 coffee-shop rankings, generates map artifacts, and publishes a static site with public Google Maps links.

**Architecture:** The project uses a Python scrape/enrich/generate pipeline. It ingests list pages and detail pages, stores normalized output in `data/current_list.json`, produces `CSV/KML`, and builds a static site in `site/`. CI executes tests, runs scrape/build commands, commits generated artifacts, deploys via GitHub Pages, and opens a reminder issue when owner-only geocoding refresh is needed.

**Tech Stack:** Python 3.11+, FastAPI/Jinja (preview UI), static site builder, pytest, GitHub Actions, GitHub Pages.

---

## Current Project Summary

### What Is Implemented
- End-to-end scraper for Top 100 + South source pages, including fallback parsing for live Elementor layouts.
- Detail-page enrichment for `city` and `address` with graceful fallback behavior.
- Artifact generation: `data/current_list.json`, `output/coffee_shops.csv`, `output/coffee_shops.kml`.
- FastAPI+Jinja preview app with tabs and public Google Maps links.
- Static site builder producing `site/index.html` and `site/assets/style.css`.
- CI/CD workflow (`.github/workflows/update_map.yml`) that tests, scrapes, builds, commits artifacts, deploys to GitHub Pages, and creates owner geocode reminder issues when needed.

### Zero-Cost Boundary
- User-facing flow does not require Google Places API credentials.
- Optional owner-only geocoding is available via CLI for annual enrichment.

### Verification Status
- Test suite currently passing (`21 passed`).
- Static site build command verified.
- Branch delivered and pushed: `codex/oph-20-24-delivery`.

## Remaining Risks / Gaps
- Source-site HTML can still change; selectors should be periodically validated.
- Live scraping can be slow due to respectful detail-page throttling.
- Place ID completeness depends on owner-only geocode refresh cadence.

## Task Breakdown for Ongoing Maintenance

### Task 1: Weekly source integrity check

**Files:**
- Modify: `/Users/opheliachen/.codex/projects/Top100BestCoffeeShops_build/.worktrees/oph-20-24-delivery/src/scraper.py`
- Test: `/Users/opheliachen/.codex/projects/Top100BestCoffeeShops_build/.worktrees/oph-20-24-delivery/tests/test_scraper.py`

**Step 1: Write a failing test for unexpected rank gaps**

```python
def test_detect_rank_gap_in_top100():
    assert missing_ranks([1, 2, 4], 4) == [3]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scraper.py::test_detect_rank_gap_in_top100 -v`
Expected: FAIL due to missing helper

**Step 3: Write minimal implementation**

```python
def missing_ranks(ranks: list[int], expected_max: int) -> list[int]:
    return [n for n in range(1, expected_max + 1) if n not in set(ranks)]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_scraper.py::test_detect_rank_gap_in_top100 -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/scraper.py tests/test_scraper.py
git commit -m "test: add rank-gap detection utility"
```

### Task 2: Improve owner geocode observability

**Files:**
- Modify: `/Users/opheliachen/.codex/projects/Top100BestCoffeeShops_build/.worktrees/oph-20-24-delivery/src/main.py`
- Test: `/Users/opheliachen/.codex/projects/Top100BestCoffeeShops_build/.worktrees/oph-20-24-delivery/tests/test_main_orchestration.py`

**Step 1: Write failing test for geocode summary output**

```python
def test_owner_geocode_reports_enriched_count(capsys):
    owner_geocode("fake")
    assert "enriched" in capsys.readouterr().out
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main_orchestration.py::test_owner_geocode_reports_enriched_count -v`
Expected: FAIL (message absent)

**Step 3: Write minimal implementation**

```python
print(f"Owner geocode refresh complete: enriched={enriched_count}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main_orchestration.py::test_owner_geocode_reports_enriched_count -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/main.py tests/test_main_orchestration.py
git commit -m "feat: report owner geocode enrichment counts"
```

### Task 3: Add release checklist to docs

**Files:**
- Modify: `/Users/opheliachen/.codex/projects/Top100BestCoffeeShops_build/.worktrees/oph-20-24-delivery/README.md`
- Modify: `/Users/opheliachen/.codex/projects/Top100BestCoffeeShops_build/.worktrees/oph-20-24-delivery/docs/release-timeline-2026.md`

**Step 1: Add checklist items for pre-release gates**

```markdown
- [ ] Tests passing
- [ ] Scrape-only run completed
- [ ] Site built and visually checked
- [ ] Pages deploy successful
```

**Step 2: Verify docs render correctly**

Run: `rg "\[ \]" README.md docs/release-timeline-2026.md`
Expected: checklist lines present

**Step 3: Commit**

```bash
git add README.md docs/release-timeline-2026.md
git commit -m "docs: add release readiness checklist"
```
