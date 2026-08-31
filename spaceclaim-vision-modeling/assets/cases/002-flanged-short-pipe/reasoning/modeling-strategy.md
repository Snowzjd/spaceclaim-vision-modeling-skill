# Modeling strategy

## Primary strategy

Use deterministic axial cylinders and script-driven feature operations:

1. Create the pipe, flange, bore, and bolt-hole cylinders as transient V21 B-rep bodies by extruding circular profiles.
2. Unite the pipe and flange bodies in the transient modeler and verify one closed piece.
3. Subtract the through-bore and eight bolt-hole cutters in the transient modeler and verify one closed piece.
4. Attach only the final transient result to the document as `FLANGED_PIPE_01`.
5. Select the two shoulder edges semantically by X position and radial extent, apply `R1.5 mm` rounds, and re-enumerate the body.
6. Select the four flange outside-diameter edges semantically, apply `1 mm` equal-distance chamfers, and re-enumerate again.
7. Measure analytic faces, bounds, and kernel volume, then save only after every assertion passes.

## Semantic selectors

- Edge selection matches current topology by bounding-box signatures at the required X positions and radii.
- Cylindrical faces are classified by analytic radius and bounding-box span.
- Bolt-hole pitch-circle radius is verified from the YZ center of each cylindrical face bounding box.
- Fillets are verified as two toroidal faces with minor radius `1.5 mm`.
- Chamfers are verified as four conical faces with `45 deg` half-angle and `1 mm` axial span.

## Runtime findings

- `CircleProfile` must be imported from `SpaceClaim.Api.V21.Geometry` and constructed with a plane, radius, `PointUV`, and angle before `ModelerBody.ExtrudeProfile`.
- Transient unite/subtract avoids document-body target ambiguity and leaves exactly one attached result.
- The two rounds remain toroidal faces and the four chamfers remain conical faces after native save and reopen.
- The V21 kernel volume for the validated result is `44370.4398069 mm3`.
