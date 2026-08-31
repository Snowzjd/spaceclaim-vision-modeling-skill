# Validation checklist

## Before desktop control

- [x] Record the source image hash without redistributing it.
- [x] Record the support-height interpretation and omitted-feature assumptions.
- [x] Parse the IronPython source with the host Python AST.
- [x] Package the formal V21 `.scscript` archive.
- [x] Audit archive members, API version, operations, aliases, and embedded paths.
- [x] Run the repository host-side checks and official Skill validator.

## Forward run

- [x] Start from a new unsaved design and run the build `.scscript` once.
- [x] Confirm one body named `ROUNDED_PLATE_SUPPORT_01`.
- [x] Confirm bounding box `[0,0,0]` to `[120,80,60]` mm.
- [x] Confirm a 120 x 80 x 10 mm plate with four R10 plan-view corners.
- [x] Confirm a centered diameter-30 support with visible height 50 mm.
- [x] Confirm four diameter-8 through-holes at 15 mm edge offsets.
- [x] Confirm the structured report passes the case contract.
- [x] Confirm the native model was saved only after validation.

## Native reopen

- [x] Close and reopen the saved native model.
- [x] Run the independent read-only audit once.
- [x] Validate and compare the forward and reopen reports.
- [x] Restore a maximized SpaceClaim window and clear unintended selections.
- [x] Fit the complete model and review the Home overview, face-normal front view, and orthogonal side view.
- [x] Capture clean evidence views and record any visually unresolved feature.
- [x] Perform final visual agreement review against the text description.
