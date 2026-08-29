# Case 001: offset block array

## Purpose

Exercise the v0.1 workflow on a synthetic, non-proprietary geometry before applying it to a real model.

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
- Neutral export is outside this case.
- Shared topology, meshing, and solver readiness are outside this case.
