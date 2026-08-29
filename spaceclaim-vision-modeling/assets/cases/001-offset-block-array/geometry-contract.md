# Geometry contract

## Coordinate system

- Units: millimetres.
- X: array direction.
- Y: alternating lateral offset.
- Z: block height.
- Origin: minimum corner of the first block.

## Expected bodies

| Name | Bounding box in mm |
|---|---|
| `BLOCK_01` | `(0, 0, 0)` to `(20, 8, 4)` |
| `BLOCK_02` | `(30, 3, 0)` to `(50, 11, 4)` |
| `BLOCK_03` | `(60, 0, 0)` to `(80, 8, 4)` |

Each body volume is `640 mm3`. The expected total body count is three.

## Selection rules

- Resolve bodies by bounding box and volume, not tree order.
- Resolve `INLET` as the planar face at global `X = 0 mm` with outward X normal.
- Resolve `OUTLET` as the planar face at global `X = 80 mm` with outward X normal.
- Require exactly one matching face for each group.
