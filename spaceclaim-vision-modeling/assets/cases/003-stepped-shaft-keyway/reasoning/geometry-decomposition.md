# Geometry decomposition

## Observed construction

The drawing resolves into three coaxial cylindrical envelopes joined in series, one coaxial cylindrical void, and one open rectangular keyway cut into the largest-diameter segment.

| Region | X interval (mm) | Outside radius (mm) |
|---|---:|---:|
| Left step | 0 to 25 | 10 |
| Middle step | 25 to 65 | 19 |
| Right step | 65 to 100 | 14 |

The through-hole has radius 5 mm and spans the complete shaft. The keyway is an 8 mm by 8 mm floor in plan view. Its floor lies at Z=16 mm because the middle radius is 19 mm and the specified depth is 3 mm.

## Feature relations

- All three outer cylinders and the through-hole are coaxial with X.
- The keyway is symmetric about Y=0 and opens through the positive-Z cylindrical surface.
- The two shaft shoulders occur at X=25 mm and X=65 mm.
- The R1 shoulder transitions are topology-changing features and must be selected again after the keyway and bore Boolean operations.
- End and bore-mouth chamfers are selected by axial position and circular-edge radius, not by recorded edge numbers.

## Known, inferred, and unresolved values

- Drawing facts: all lengths, diameters, keyway width/depth/length, R1 note, 1 x 45 degree chamfer note, unit, and material note.
- Inferred relation: the keyway is radial and centered across Y because both the section and detail show a centered slot.
- Explicit assumption: the keyway is centered axially in the middle segment, X=41 to 49 mm.
- Explicit assumption: the generic chamfer note is applied to the two outer end edges and two bore mouths, not to keyway edges.
- Retained source ambiguity: the drawing does not establish whether keyway-edge deburring was intended, so those edges remain sharp in the controlled model.
