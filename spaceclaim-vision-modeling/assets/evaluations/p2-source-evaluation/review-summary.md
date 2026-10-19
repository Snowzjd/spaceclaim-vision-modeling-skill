# P2 independent source evaluation

## Result and boundary

The independent interpreter emitted 38 records covering GU-01–20 and MS-01–09
from raw image A, drawing B and text C. Main review against the actual source
pixels/text confirmed the triangular section, drawing dimensions and feature
scope, and the two blocking text requirements. A subsequent four-record
planning-input test exercised positive MS-03/05/06/08 declarations. All 42
records pass the corrected host result checker. These are observations for this
small synthetic set, not a general image benchmark or a SpaceClaim runtime test.

The interpreter received no intended answers, source-generation program or old
case outputs. Preserve its first findings in `independent/review.md` and the
bounded follow-up in `independent/delta-review.md`. The first manifest encoding
correction and `pass`/`passed` failure are recorded there rather than erased.
The updated checker accepts both supported locator forms and equivalent verdict
spellings, while preserving the numeric comparison. View direction now has an
explicit model-to-observer meaning; the original B vectors already conform.

Additional contract review preserved explicit geometry-neutral coordinate
conventions, independent optional camera requirements and unknown propagation.
Guidance has been relocated into per-action files without changing the tested
procedures, apart from the documented convention/sign clarifications. Indexes
and registry contracts bind each action separately.

## Raw material and preserved source identifiers

All source files required to inspect the claims are included under `raw/`.
The original evaluator files are preserved verbatim. Their source locator
prefix `runs/p2-evaluation/raw/` maps to this bundle's `raw/` directory. Their
operation references point to records in the same `independent/` bundle.
The transcribed API facts in planning D are bounded supplied input facts, not
redistributed vendor documentation or an independent runtime observation.

| Source | Main review against original source |
| --- | --- |
| image-a.png | Right-triangular constant section; 42 × 18 mm base/height, depth 25 mm; analytical volume 9450 mm³; native only |
| drawing-b.png | 90 × 45 × 6 mm; three Ø9 through holes at x=15/45/75 mm, centered across width; exterior equal-distance 0.5 mm chamfer excludes hole edges |
| text-c.md | 12 + 30 + 22 = 64 mm contradicts nominal 65 mm; blind-hole depth unknown; both block a completed solid |
| planning-d.md | Version-specific single-call binding, separate predicate and volume assertion use supplied inputs; no actual geometry observed |

MS-10/11 retain their existing separate host evidence. No new GU/MS template
is promoted to active by this evaluation alone. The complete generic workflow
remains available, and runtime, selection, measurements and persistence remain
separate later gates.
