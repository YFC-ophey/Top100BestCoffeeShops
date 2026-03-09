# Development Framework

This is the standard delivery framework for bug fixes, UI changes, and feature updates.

## 1. Intake and Scope Lock

- Confirm exact user-visible problem and expected behavior.
- Define desktop vs mobile behavior explicitly.
- Define generated-artifact scope (`site/`, build outputs) before coding.

Exit criteria:
- One-sentence success definition.
- One-sentence non-goals definition.

## 2. Branching

- Start from current `origin/main`.
- Create a fresh branch with `codex/` prefix.

```bash
git fetch origin
git checkout -b codex/<task-name> origin/main
```

Exit criteria:
- Branch points to latest `origin/main`.
- No unrelated staged changes.

## 3. Debug and Root Cause

- Reproduce first with current code.
- Capture failing path and exact conditions (device class, route, data shape).
- Identify root cause before implementing.

Exit criteria:
- Repro steps documented.
- Root cause mapped to concrete file/line region.

## 4. Fix + Regression Coverage

- Implement smallest coherent fix.
- Add/update tests to prove behavior.
- Keep desktop behavior unchanged unless explicitly required.

Exit criteria:
- Tests fail before fix (or fail-equivalent assertion updated for changed contract).
- Tests pass after fix.

## 5. Generated Artifact Sync

- Rebuild static site/output when repo expects committed generated files.

```bash
uv run python src/main.py build-site
```

Exit criteria:
- `site/index.html` reflects the same logic as template/runtime source.

## 6. Verification Gate

Run before every push:

```bash
uv run pytest -q tests/test_web_app.py
uv run pytest -q tests/test_site_builder.py
uv run pytest -q
```

Playwright gate (generated local site, not only template):

- Desktop viewport check.
- Mobile viewport check.
- Verify mobile `Get Directions` resolves to expected URL shape.
- Capture screenshots for list view and detail panel.

Exit criteria:
- All tests green.
- Playwright checks green.
- Screenshots captured.

## 7. Code Review Gate

Review final diff with focus on:

- stale generated output risk
- desktop regression risk
- mobile readability regressions
- duplicated/divergent logic between template and generated site

Exit criteria:
- No blocking findings.
- Any residual risk is explicit.

## 8. Push, Merge, Workflow

- Push branch.
- Merge to `main`.
- Trigger workflow dispatch.
- Watch run until terminal state.

```bash
git push -u origin codex/<task-name>
gh workflow run update_map.yml --ref main
gh run list --workflow update_map.yml --limit 5
gh run watch <run_id>
```

Exit criteria:
- `main` contains intended commit.
- Workflow run completes successfully.

## 9. Real-Device Smoke (Phone)

- Open deployed page on iPhone.
- Perform target interaction (`Get Directions`).
- Confirm expected app/deep-link behavior.

Exit criteria:
- User confirms phone behavior is correct.

## 10. Closeout Format

Every delivery summary should include:

- commit SHA
- changed files (high-signal only)
- test commands and outcomes
- Playwright evidence paths
- workflow run URL and status
- explicit ask for phone smoke confirmation when mobile behavior changed

