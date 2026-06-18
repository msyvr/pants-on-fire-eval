#!/usr/bin/env bash
# Render the report to styled HTML and a PDF — Chrome-free.
#   HTML : pandoc + report-style.html  (serif; open in any browser, or print to PDF)
#   PDF  : pandoc -> typst              (no browser)
# Operates in this script's own directory so the figures/ paths resolve.
# Usage:  ./render.sh [report.md]       (default: decomposition-pilot.md)
#
# Requires: pandoc, typst.  (Both Chrome-free.)
set -euo pipefail
cd "$(dirname "$0")"
SRC="${1:-decomposition-pilot.md}"
BASE="${SRC%.md}"
PDF_FONT="Palatino"   # serif font for the typst PDF (to match the HTML styling)

# --- styled HTML -----------------------------------------------------------
# <sup> citations and figures render natively in HTML; report-style.html adds
# the serif styling into <head>.
pandoc -f gfm "$SRC" --standalone --include-in-header=report-style.html -o "$BASE.html"
echo "wrote $BASE.html"

# --- PDF via typst ---------------------------------------------------------
# pandoc's typst writer drops raw <sup> HTML, so rewrite the citation
# superscripts to raw typst (#super[...]) on a temp copy. The source file keeps
# <sup> (which GitHub needs). --standalone emits a compilable typst document.
tmp="$(mktemp)"
perl -pe 's~<sup>(.*?)</sup>~`#super[$1]`{=typst}~g' "$SRC" > "$tmp"
pandoc -f gfm+raw_attribute "$tmp" -t typst --standalone -V mainfont="$PDF_FONT" -o "$BASE.typ"
rm -f "$tmp"
typst compile "$BASE.typ" "$BASE.pdf"
echo "wrote $BASE.pdf"
