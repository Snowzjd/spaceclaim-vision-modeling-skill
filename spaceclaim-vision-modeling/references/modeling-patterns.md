# Modeling patterns

## Primitive-first decomposition

Translate a visual object into blocks, cylinders, cones, planar profiles, sweeps, shells, holes, ribs, and repeated features. Record dimensions and relationships separately from the object’s industry name.

## Transform and array

Create one verified prototype, then copy, translate, rotate, mirror, or pattern it. Keep the spacing sequence explicit and assert its count and cumulative extent before construction.

## Boolean construction

Treat Boolean calls as topology mutations. Capture the pre-operation body set, execute the operation, reacquire all bodies, and identify each survivor or overlap by bounding box, volume, face count, and spatial role. Do not assume the API return order is the desired body order.

## Direct domain construction

When temporary caps and volume extraction are unstable, construct the intended fluid or void envelope directly and intersect it with the solid geometry. This changes the modeling strategy, so validate body counts, volumes, extents, interfaces, and leakage assumptions explicitly.

## Semantic selection

Use several independent properties together:

- extremal position and axis direction;
- face normal and planarity;
- bounding box and centroid;
- area or body volume;
- expected layer or region;
- adjacency to a known body or interface.

Require a unique match. A selector that silently chooses the first candidate is not a semantic selector.

## Topology mutation rule

After merge, split, intersect, subtract, repair, import, or shared-topology operations, discard old face and body handles. Re-enumerate the current document and rebuild selections.

## Naming contract

Define every required body or face group with its object type, semantic rule, and expected member count. Use the object returned by group creation when assigning the final name, then recheck the final name set and memberships.

## Validation-before-save

Place inexpensive assertions early and geometry assertions immediately before save. Write stage markers to a runtime report. Save only after all critical assertions pass; reopen when persistence is part of the claim.
