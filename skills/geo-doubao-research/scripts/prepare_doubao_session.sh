#!/usr/bin/env bash
set -euo pipefail
URL="https://www.doubao.com"
PROFILE_DIR=".local/doubao-profile"
BROWSER="chromium"
resolve_playwright() {
  if [[ -n "${PLAYWRIGHT_BIN:-}" ]]; then
    [[ -x "$PLAYWRIGHT_BIN" ]] || { echo "PLAYWRIGHT_BIN is not executable." >&2; exit 1; }
    BIN="$PLAYWRIGHT_BIN"
  else
    BIN="$(command -v playwright || true)"
    [[ -n "$BIN" ]] || { echo "Install Playwright first; set PLAYWRIGHT_BIN. See docs/browser.md." >&2; exit 1; }
  fi
}
value_required() {
  [[ $# -ge 2 && -n "$2" ]] || { echo "Missing value for $1" >&2; exit 1; }
}
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) echo "Usage: $0 [--url URL] [--profile-dir DIR] [--browser chromium|firefox|webkit]"; exit 0 ;;
    --url) value_required "$@"; URL="$2"; shift 2 ;;
    --profile-dir) value_required "$@"; PROFILE_DIR="$2"; shift 2 ;;
    --browser) value_required "$@"; BROWSER="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
resolve_playwright
printf '%s
' "Opening a visible research session. Complete login manually; keep profile data private."
exec "$BIN" codegen --browser "$BROWSER" --user-data-dir "$PROFILE_DIR" "$URL"
