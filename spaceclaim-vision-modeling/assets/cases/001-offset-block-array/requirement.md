# Case 001: offset block array

## Purpose

Exercise the v0.2 workflow on a synthetic, non-proprietary geometry and preserve a reproducible forward-run evidence record.

## Input contract

- Create three independent rectangular blocks.
- Each block has dimensions `20 x 8 x 4 mm`.
- Their centers are separated by `30 mm` along X.
- Alternate blocks are offset by `3 mm` along Y.
- Body names are `BLOCK_01`, `BLOCK_02`, and `BLOCK_03`.
- Create named face groups `INLET` and `OUTLET` from the global X-min and X-max end faces.
- Save to a new native model path only after validation passes.

## Deliberately unresolved

- Fillet radius is not specified and must not be invented.
- Only the requested SpaceClaim geometry, names, native save, and validation report belong to this case.
