# Validation checklist

- [x] Image observations separated from text dimensions.
- [x] Fillet-radius and chamfer-scope assumptions recorded explicitly.
- [x] Geometry decomposition and modeling strategy prepared.
- [x] SpaceClaim 2022 R1 / API V21 script prepared.
- [x] Structured report contract prepared.
- [x] Formal V21 `.scscript` package passes `audit_scscript.py`.
- [x] Script runs once from a new unsaved clean design.
- [x] Exactly one body named `FLANGED_PIPE_01` remains.
- [x] Overall bounding box is `[0,-24,-24]..[80,24,24] mm`.
- [x] Finished V21 kernel volume is `44370.4398069 mm3` within tolerance.
- [x] One diameter `16 mm` bore spans the complete length.
- [x] Eight diameter `6.5 mm` holes lie on PCD `36 mm`, four per flange.
- [x] Four `1 x 45 deg` flange outside-diameter chamfers are present.
- [x] Two `R1.5 mm` external shoulder fillets are present.
- [x] Native model save succeeds.
- [x] Native close/reopen preserves the body, measurements, and feature report.
- [x] Final visual review agrees with the supplied reference at the evidence level visible from the image.

The controlled evidence is bounded to SpaceClaim 2022 R1 / API V21 and the documented case inputs.
