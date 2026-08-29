# Validation checklist

- [ ] Target SpaceClaim/API version recorded.
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

The case documents an acceptance contract; v0.1 does not bundle a claimed SpaceClaim runtime output.
