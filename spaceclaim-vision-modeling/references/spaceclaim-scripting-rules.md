# SpaceClaim scripting rules

## Version and runtime

- Record the SpaceClaim release, scripting API version, and Python runtime used by the target application.
- Treat official documentation and runtime introspection for the installed version as authoritative.
- Isolate version-sensitive calls behind small helper functions.
- Keep embedded Windows paths safe for the target Python parser; prefer forward slashes when backslash escapes are ambiguous.
- Treat plain IronPython source as a development or packaging input. Package, load, test, and deliver the executable artifact as a SpaceClaim `.scscript` matched to the target API version.
- For V21 packages, preserve the native minimal members `_script`, `_apiVersion`, `_smartVariableVersion`, and `[Content_Types].xml`; use `scripts/package_scscript.py` instead of renaming a `.py` file.
- Import required geometry types from their actual versioned subnamespace. A root wildcard import does not guarantee that types such as `CircleProfile` or `PointUV` are defined.
- For V21 reusable code, enumerate with `root.GetDescendants[DesignBody]()` and apply the declared root/occurrence scope. Editor-injected extension methods such as `GetAllBodies()` may not exist inside separately compiled script scopes.

## Coordinate systems and parameters

- Define the origin, primary axes, handedness, model units, and expected extents before constructing geometry.
- Keep user dimensions, derived dimensions, tolerances, counts, and file paths in a parameter block.
- For engineering drawings, record which view or note supplies each parameter, close dimension chains, and label every unresolved placement or feature-scope decision as an assumption.
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
- For subtractive features, independently verify the resulting cylindrical, planar, conical, or toroidal faces and their spatial spans; do not treat a successful Boolean return as proof that the intended feature was cut.

## Naming

- Use a declared naming contract with expected object type and member count.
- Prefer the object returned by a create operation when assigning its final name.
- Detect collisions and automatic unique-name suffixes.
- Recheck final names and memberships after saving and reopening when persistence matters.

## Failure and save behavior

- Choose one explicit path policy. In no-baseline mode, start from an unsaved design and require a nonexistent run-owned model path. In baseline-copy mode, verify the active hash-recorded copy and its exact run-owned path before permitting that existing model path. Never weaken a no-baseline guard merely to make it run on a baseline copy.
- Keep the original baseline unchanged and write only to the verified run-owned output or copy.
- Emit stage markers and measured assertions to a runtime report.
- Stop before save on critical failure.
- Treat “script reached the final line,” “output file exists,” and “native model reopens with expected structure” as separate checks.
- In the observed V21 `DocumentSave.Execute(path)` path, do not require a non-null result or `.Success` property. Check the saved file and active document path separately, then obtain reopen evidence when required. Do not transfer this return convention to unrelated APIs.
- Never rerun a script on a partially modified model unless the script explicitly supports idempotent recovery.

## Evidence boundary

A script package or static audit does not prove geometry correctness. A displayed model does not by itself prove measurements, naming, native persistence, or requested export behavior. Require evidence from each claimed SpaceClaim modeling stage.
