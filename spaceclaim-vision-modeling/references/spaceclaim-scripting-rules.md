# SpaceClaim scripting rules

## Version and runtime

- Record the SpaceClaim release, scripting API version, and Python runtime used by the target application.
- Treat official documentation and runtime introspection for the installed version as authoritative.
- Isolate version-sensitive calls behind small helper functions.
- Keep embedded Windows paths safe for the target Python parser; prefer forward slashes when backslash escapes are ambiguous.

## Coordinate systems and parameters

- Define the origin, primary axes, handedness, model units, and expected extents before constructing geometry.
- Keep user dimensions, derived dimensions, tolerances, counts, and file paths in a parameter block.
- Assert valid ranges before geometry creation.

## Selection

- Prefer references returned by creation operations while topology is unchanged.
- After split, merge, intersect, subtract, repair, or import, reacquire objects from the current document.
- Select by combinations of bounding box, centroid, normal, direction, area, volume, topology type, layer, adjacency, and extremal position.
- Require a unique match when a single body or face is expected. Fail on zero or multiple matches.
- Never promote recorded `FaceN`, `BodyN`, tree indices, or screen coordinates to reusable logic.

## Boolean operations

- Inspect the actual result semantics of merge, subtract, intersect, and split for the target API.
- Compare body sets before and after the operation.
- Identify kept bodies by geometry properties, not return order.
- Remove tool or overlap remnants only after proving their identity.
- Re-enumerate bodies and faces after every topology-changing operation.

## Naming

- Use a declared naming contract with expected object type and member count.
- Prefer the object returned by a create operation when assigning its final name.
- Detect collisions and automatic unique-name suffixes.
- Recheck final names and memberships after saving and reopening when persistence matters.

## Failure and save behavior

- Run on a clean copy and write an independent output.
- Emit stage markers and measured assertions to a runtime report.
- Stop before save on critical failure.
- Treat “script reached the final line,” “output file exists,” and “native model reopens with expected structure” as separate checks.
- Never rerun a script on a partially modified model unless the script explicitly supports idempotent recovery.

## Evidence boundary

A script package or static audit does not prove geometry correctness. A native model does not prove neutral-format transfer, shared topology, mesh connectivity, or solver readiness. Require evidence from each claimed stage.
