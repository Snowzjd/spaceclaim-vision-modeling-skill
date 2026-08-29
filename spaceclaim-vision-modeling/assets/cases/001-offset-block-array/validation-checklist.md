# Validation checklist

- [x] Host-side V21 candidate build script prepared.
- [x] Versioned JSON report schema and case validation contract prepared.
- [x] Host report validator covered by unit tests.
- [x] Target SpaceClaim/API version recorded.
- [ ] Script package passes `audit_scscript.py`.
- [ ] Script runs once on a clean model.
- [ ] Runtime report reaches its final validated stage.
- [ ] Body count is three.
- [ ] Each body bounding box and volume matches the geometry contract within declared tolerance.
- [ ] Final body names are unique and correct.
- [ ] `INLET` and `OUTLET` each contain exactly one face.
- [ ] Native output is saved to a new path.
- [ ] Native output is reopened and the body/group contract persists.
- [ ] Export, shared topology, mesh, and solver evidence are reported as not tested.

The candidate script and structured-report tooling are host-prepared only. SpaceClaim execution, native save, and reopen persistence remain `runtime_pending` until an explicitly authorized V21 forward test succeeds.
