# Validation checklist

- [x] Host-side V21 build script prepared.
- [x] Versioned JSON report schema and case validation contract prepared.
- [x] Host report validator covered by unit tests.
- [x] Target SpaceClaim/API version recorded.
- [x] Script package passes `audit_scscript.py`.
- [x] Script runs once on a clean model.
- [x] Runtime report reaches its final validated stage.
- [x] Body count is three.
- [x] Each body bounding box and volume matches the geometry contract within declared tolerance.
- [x] Final body names are unique and correct.
- [x] `INLET` and `OUTLET` each contain exactly one face.
- [x] Native output is saved to the run-owned final path.
- [x] Native output is reopened and the body/group contract persists.
- [x] Home, plan, height, and end views visually agree with the three-body offset-array contract.
- [x] Clean evidence screenshots are archived by hash outside the public case bundle.
- [x] Every unperformed SpaceClaim validation item is reported as not tested.

The controlled SpaceClaim 2022 R1 / API V21 forward test and independent close/reopen audit passed on 2026-08-29. The case-specific visual review passed on 2026-08-31. See [runtime-evidence.md](runtime-evidence.md) for measurements, hashes, and the claim boundary.
