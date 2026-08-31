# Modeling strategy

## Primary strategy

1. Assert that the active document contains no bodies.
2. Build the left, middle, and right cylindrical envelopes as transient V21 modeler bodies.
3. Use small contained axial overlaps for the smaller cylinders so transient union is robust without moving either visible shoulder.
4. Unite the three outer envelopes and verify one closed piece.
5. Subtract an over-extended cylindrical bore cutter and an 8 mm-long rectangular-profile keyway cutter.
6. Attach only the final transient result to the document as `STEPPED_SHAFT_KEYWAY_01`.
7. Re-enumerate the current body, select the two shoulder edges by X position and radius, and apply R1 constant rounds.
8. Re-enumerate again, select the two outside end edges and two bore-mouth edges by X position and radius, and apply 1 mm chamfers.
9. Validate body count, name, bounding box, volume, analytic cylinders, keyway floor, toroidal fillets, and conical chamfers before the only native save.

## V21-sensitive calls

- Import `CircleProfile`, `RectangleProfile`, `Plane`, and `PointUV` from `SpaceClaim.Api.V21.Geometry`.
- Construct both circular and rectangular profiles on a plane whose normal is X, then call `ModelerBody.ExtrudeProfile`.
- Use transient `Body.Unite` and `Body.Subtract` before `DesignBody.Create`.
- Use `ConstantRound.Execute` and `Chamfer.Execute` only after semantic circular-edge selection.

## Failure checkpoints

- Fail before construction if paths, dimensions, assumptions, or the clean-document assertion are invalid.
- Fail if a transient operation does not leave exactly one closed piece.
- Fail on zero or multiple semantic edge or face matches.
- Fail before save if feature measurements or the volume sanity contract do not pass.
- Do not rerun on a partially modified document; start a new unsaved design after correcting the first failing stage.

## Evidence boundary

The public source and packaged `.scscript` passed host preflight checks. A controlled SpaceClaim 2022 R1 / API V21 forward run, structured geometry measurements, native save, independent close/reopen audit, and case-specific visual review also passed. Each evidence layer remains bounded to the recorded case and environment.
