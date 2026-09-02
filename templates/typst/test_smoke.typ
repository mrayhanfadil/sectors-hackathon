// test_smoke.typ — minimal typst test
#import "common/theme.typ": *

#set-page-defaults[
  #page-wrap(
    "RESEARCH — Equity Report",
    "27 Agt 2026",
    "MTEL",
    1,
    DEFAULT_PALETTE,
    {
      section-header(1, "Test Section", DEFAULT_PALETTE)
      "Hello typst body. Body content goes here."
    },
  )
]