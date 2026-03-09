#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
  cat <<'EOF'
Usage:
  scripts/dev-framework.sh verify [test_paths...]
  scripts/dev-framework.sh build-site
  scripts/dev-framework.sh review
  scripts/dev-framework.sh prepush [test_paths...]
  scripts/dev-framework.sh workflow [workflow_file] [ref]

Examples:
  scripts/dev-framework.sh verify tests/test_web_app.py tests/test_site_builder.py
  scripts/dev-framework.sh prepush
  scripts/dev-framework.sh workflow update_map.yml main
EOF
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

run_verify() {
  require_cmd uv

  local tests=("$@")
  if [[ "${#tests[@]}" -eq 0 ]]; then
    tests=(tests/test_web_app.py tests/test_site_builder.py)
  fi

  echo "==> Targeted tests: ${tests[*]}"
  uv run pytest -q "${tests[@]}"

  echo "==> Full test suite"
  uv run pytest -q
}

run_build_site() {
  require_cmd uv
  echo "==> Build static site"
  uv run python src/main.py build-site
}

run_review() {
  echo "==> Git status"
  git status --short --branch
  echo
  echo "==> Diff stat"
  git diff --stat
  echo
  echo "==> Whitespace/conflict check"
  git diff --check
}

run_workflow() {
  require_cmd gh
  local workflow="${1:-update_map.yml}"
  local ref="${2:-main}"

  echo "==> Trigger workflow: $workflow (ref=$ref)"
  gh workflow run "$workflow" --ref "$ref"
  sleep 2
  echo "==> Recent runs"
  gh run list --workflow "$workflow" --limit 5
}

main() {
  local command="${1:-help}"
  shift || true

  case "$command" in
    verify)
      run_verify "$@"
      ;;
    build-site)
      run_build_site
      ;;
    review)
      run_review
      ;;
    prepush)
      run_verify "$@"
      run_build_site
      run_review
      ;;
    workflow)
      run_workflow "${1:-}" "${2:-}"
      ;;
    help|-h|--help)
      usage
      ;;
    *)
      echo "Unknown command: $command" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
