# Validation checklist

## Before desktop control

- [x] Record the drawing dimensions and source hash without redistributing the drawing.
- [x] Separate drawing facts from the keyway-location and chamfer-scope assumptions.
- [x] Parse both IronPython sources with the host Python AST.
- [x] Package both formal V21 `.scscript` archives.
- [x] Audit archive members, API version, operations, aliases, and embedded paths.
- [x] Run the complete repository host-side test suite and official Skill validator.

## Forward run

- [x] Start from a new unsaved design.
- [x] Run the prepared build `.scscript` once.
- [x] Confirm one body named `STEPPED_SHAFT_KEYWAY_01`.
- [x] Confirm bounding box `[0, -19, -19]` to `[100, 19, 19]` mm.
- [x] Confirm outside diameters 20, 38, and 28 mm over lengths 25, 40, and 35 mm.
- [x] Confirm the diameter-10 through-hole.
- [x] Confirm keyway length 8 mm, width 8 mm, and depth 3 mm at the assumed X position.
- [x] Confirm two R1 shoulder fillets.
- [x] Confirm four 1 mm x 45 degree end and bore-mouth chamfers.
- [x] Confirm the structured report passes the case contract.
- [x] Confirm the native model was saved only after geometry validation.

## Native reopen

- [x] Close and reopen the saved native model.
- [x] Run the independent read-only audit once.
- [x] Validate the reopen report and compare it with the forward report.
- [x] Perform final visual agreement review against the supplied drawing.
