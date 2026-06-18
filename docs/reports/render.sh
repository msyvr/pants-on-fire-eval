#!/usr/bin/env bash
# Render the report to styled HTML and a PDF — Chrome-free.
#   HTML : pandoc + report-style.html  (serif; open in any browser, or print to PDF)
#   PDF  : pandoc -> typst, arXiv (arkheion) style  (no browser, no LaTeX)
# Operates in this script's own directory so the figures/ paths resolve.
# Usage:  ./render.sh [report.md]       (default: decomposition-pilot.md)
#
# arXiv styling: if a sibling "<base>.meta.yaml" exists, the PDF is built in the
# arkheion arXiv style via arxiv.typ — the title/author/abstract/keywords/date
# come from that metadata, and the PDF body starts at the "<!-- pdf:body -->"
# sentinel in the .md (so the title + abstract aren't duplicated). The abstract
# itself is extracted from the .md (single source). With no meta.yaml, the PDF
# falls back to pandoc's default typst template + a serif main font.
#
# Requires: pandoc, typst.  (Both Chrome-free.)
set -euo pipefail
cd "$(dirname "$0")"
SRC="${1:-decomposition-pilot.md}"
BASE="${SRC%.md}"
META="$BASE.meta.yaml"
PDF_FONT="Palatino"   # fallback serif font when there is no meta.yaml

# rewrite <sup>..</sup> -> raw typst #super[..]; pandoc's typst writer drops the
# raw HTML otherwise. The .md keeps <sup> (which GitHub renders).
sup_to_typst() { perl -pe 's~<sup>(.*?)</sup>~`#super[$1]`{=typst}~g'; }

# --- styled HTML -----------------------------------------------------------
# <sup> citations and figures render natively in HTML; report-style.html adds
# the serif styling into <head>.
pandoc -f gfm "$SRC" --standalone --include-in-header=report-style.html -o "$BASE.html"
echo "wrote $BASE.html"

# --- PDF via typst ---------------------------------------------------------
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

if [[ -f "$META" ]]; then
  # arXiv (arkheion) style. Assemble: meta.yaml (with the .md's abstract spliced
  # in) + the .md body from the "<!-- pdf:body -->" sentinel onward.
  # lines between '## Abstract' and the next '---'; sed strips leading blanks,
  # and $(...) strips trailing newlines.
  abstract="$(awk '/^## Abstract$/{f=1;next} f&&/^---$/{exit} f{print}' "$SRC" \
              | sed -e '/./,$!d')"
  if [[ -z "$abstract" ]]; then
    echo "error: no abstract found between '## Abstract' and the next '---' in $SRC" >&2
    exit 1
  fi
  if ! grep -q '<!-- pdf:body -->' "$SRC"; then
    echo "error: '<!-- pdf:body -->' sentinel not found in $SRC" >&2
    exit 1
  fi
  {
    # Fresh YAML metadata block: the meta.yaml fields (between its '---' fences,
    # dropping the leading comments) + the .md's abstract as a block scalar, then
    # the .md body from the sentinel onward.
    printf -- '---\n'
    awk '/^---$/{n++; next} n==1{print}' "$META"
    printf 'abstract: |\n'
    printf '%s\n' "$abstract" | sed 's/^/  /'
    printf -- '---\n\n'
    awk 'found{print} /<!-- pdf:body -->/{found=1}' "$SRC"
  } | sup_to_typst > "$tmp"
  pandoc -f gfm+raw_attribute "$tmp" -t typst --standalone --wrap=none \
    --template=arxiv.typ -o "$BASE.typ"
else
  # Fallback: pandoc's default typst template + a serif main font.
  sup_to_typst < "$SRC" > "$tmp"
  pandoc -f gfm+raw_attribute "$tmp" -t typst --standalone --wrap=none \
    -V mainfont="$PDF_FONT" -o "$BASE.typ"
fi

typst compile "$BASE.typ" "$BASE.pdf"
echo "wrote $BASE.pdf"
