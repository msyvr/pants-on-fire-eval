// Pandoc typst *template* that renders the body in the arXiv (arkheion) style.
// Used by render.sh:  pandoc ... -t typst --template=arxiv.typ
//
// Based on `pandoc -D typst` (keeps the show-rules pandoc's typst writer
// depends on: terms, tables, figure captions, syntax highlighting), but swaps
// pandoc's default `conf(...)` document wrapper for arkheion's arXiv layout.
//   arkheion: https://typst.app/universe/package/arkheion  (New Computer Modern,
//   the classic LaTeX serif — bundled with typst, no install).
//
// Title / authors / abstract / keywords / date come from document metadata
// (see decomposition-pilot.meta.yaml); the .md body supplies only the sections
// after the abstract. One source, two outputs — the .md stays GitHub-friendly.

// --- pandoc-writer show rules (do not remove: the typst output relies on these)
#let horizontalrule = line(start: (25%,0%), end: (75%,0%))

#show terms: it => {
  it.children
    .map(child => [
      #strong[#child.term]
      #block(inset: (left: 1.5em, top: -0.4em))[#child.description]
      ])
    .join()
}

#set table(
  inset: 6pt,
  stroke: none
)

#show figure.where(
  kind: table
): set figure.caption(position: $if(table-caption-position)$$table-caption-position$$else$top$endif$)

#show figure.where(
  kind: image
): set figure.caption(position: $if(figure-caption-position)$$figure-caption-position$$else$bottom$endif$)

$if(highlighting-definitions)$
// syntax highlighting functions from skylighting:
$highlighting-definitions$

$endif$
$if(smart)$
$else$
#set smartquote(enabled: false)

$endif$
$for(header-includes)$
$header-includes$

$endfor$
// --- arXiv layout ----------------------------------------------------------
#import "@preview/arkheion:0.1.2": arkheion, arkheion-appendices

// Typographic density — tighter than arkheion's defaults, closer to an arXiv preprint.
#set text(size: 10.5pt)
#set par(leading: 0.55em)

// NB arkheion does `set document(author: ..a.name, title: title)` and
// `keywords.map(str)`, so title / author.name / keywords must be STRINGS, not
// content. email/affiliation/date/abstract are rendered as content (markup ok).
#show: arkheion.with(
  title: "$title$",
$if(author)$
  authors: (
$for(author)$
$if(author.name)$
    (name: "$author.name$", email: [$author.email$], affiliation: [$author.affiliation$]),
$else$
    (name: "$author$", email: [], affiliation: []),
$endif$
$endfor$
  ),
$endif$
$if(keywords)$
  keywords: ($for(keywords)$"$it$"$sep$, $endfor$),
$endif$
$if(date)$
  date: [$date$],
$endif$
$if(abstract)$
  abstract: [$abstract$],
$endif$
)

// Use the section numbers written into the .md headings ("## 1. Introduction"),
// not arkheion's auto "1.1" numbering (which would double them).
#set heading(numbering: none)
#show link: underline

$if(funding)$
#align(center)[#emph[$funding$]]
#v(0.8em)

$endif$
$for(include-before)$
$include-before$

$endfor$
$body$
