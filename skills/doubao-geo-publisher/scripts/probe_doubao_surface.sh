#!/usr/bin/env bash
set -euo pipefail
URL="https://www.doubao.com"
OUTPUT_DIR=""
WAIT_MS="4000"
CHANNEL=""
FULL_PAGE="false"
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
    --help|-h) echo "Usage: $0 --output-dir DIR [--url URL] [--wait-ms N] [--channel NAME] [--full-page]"; exit 0 ;;
    --url) value_required "$@"; URL="$2"; shift 2 ;;
    --output-dir) value_required "$@"; OUTPUT_DIR="$2"; shift 2 ;;
    --wait-ms) value_required "$@"; WAIT_MS="$2"; shift 2 ;;
    --channel) value_required "$@"; CHANNEL="$2"; shift 2 ;;
    --full-page) FULL_PAGE="true"; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
[[ -n "$OUTPUT_DIR" ]] || { echo "--output-dir is required." >&2; exit 1; }
[[ "$WAIT_MS" =~ ^[0-9]+$ ]] || { echo "--wait-ms must be a nonnegative integer." >&2; exit 1; }
resolve_playwright
mkdir -p "$OUTPUT_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)-$$"
SHOT_PATH="$OUTPUT_DIR/doubao-surface-$STAMP.png"
CMD=("$BIN" screenshot --wait-for-timeout "$WAIT_MS")
[[ -z "$CHANNEL" ]] || CMD+=(--channel "$CHANNEL")
[[ "$FULL_PAGE" != "true" ]] || CMD+=(--full-page)
CMD+=("$URL" "$SHOT_PATH")
"${CMD[@]}"
printf '%s
' "Saved: $SHOT_PATH" "Inspect the image manually; this probe does not search or verify results."
