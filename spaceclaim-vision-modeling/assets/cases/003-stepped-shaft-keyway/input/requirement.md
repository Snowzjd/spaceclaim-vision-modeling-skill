# Case 003 requirement

Reconstruct the stepped hollow shaft shown in a user-supplied engineering drawing.
The drawing itself is not redistributed in this public case bundle.

## Drawing provenance

- Input type: dimensioned engineering drawing with orthographic, section, detail, and isometric views.
- Source-image SHA-256: `c99ebbe52f00e79a7845fdc4d7864a47438c253a6073f70538031430b7489bfb`.
- Source-image size: 1448 x 1086 pixels.
- Drawing units: mm.
- Drawing title: three-step shaft with keyway.
- Drawing material note: 45 steel. Material assignment is outside this geometry case and is not claimed.

## Required geometry

- One coaxial stepped shaft, total length 100 mm.
- Left segment: length 25 mm, outside diameter 20 mm.
- Middle segment: length 40 mm, outside diameter 38 mm.
- Right segment: length 35 mm, outside diameter 28 mm.
- One axial through-hole, diameter 10 mm.
- One open keyway in the middle segment: axial length 8 mm, transverse width 8 mm, radial depth 3 mm.
- Sharp-edge chamfer note: 1 mm x 45 degrees.
- Unspecified fillets: R1.

## Explicit interpretation assumptions

The drawing does not dimension the keyway's axial location. Place it at the axial center of the 40 mm middle segment, from X=41 mm to X=49 mm, until the user supplies a different location.

Apply R1 to the two re-entrant shoulder transitions at X=25 mm and X=65 mm. Apply 1 mm x 45 degree chamfers to the two outer end edges and the two through-hole mouth edges. Leave keyway edges sharp because the detail view does not explicitly define their chamfer treatment.

## Coordinate system

- Origin: center of the left end face.
- X: shaft axis, positive from left to right.
- Y: transverse direction across the keyway width.
- Z: radial direction toward the keyway opening.
- Expected final bounding box: `[0, -19, -19]` to `[100, 19, 19]` mm.

## Required output

- One native body named `STEPPED_SHAFT_KEYWAY_01`.
- One run-owned native SpaceClaim model.
- One structured forward runtime report.
- One independent read-only native-reopen report.
