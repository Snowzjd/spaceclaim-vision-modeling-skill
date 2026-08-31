# Modeling patterns

## Primitive-first decomposition

Translate a visual object into blocks, cylinders, cones, planar profiles, sweeps, shells, holes, ribs, and repeated features. Record dimensions and relationships separately from the object's industry name.

## Engineering-drawing reconciliation

Map each view to the dimensions and hidden relationships it actually constrains. Close length and diameter chains across views before scripting. Keep source dimensions, derived values, metadata, and unresolved assumptions separate; never silently invent the position or scope of an incompletely dimensioned feature.

## Transform and array

Create one verified prototype, then copy, translate, rotate, mirror, or pattern it. Keep the spacing sequence explicit and assert its count and cumulative extent before construction.

## Boolean construction

Treat Boolean calls as topology mutations. Capture the pre-operation body set, execute the operation, reacquire all bodies, and identify each survivor or overlap by bounding box, volume, face count, and spatial role. Do not assume the API return order is the desired body order.

For coaxial stepped geometry, construct explicit axis intervals and radii, unite the segments as transient bodies, then subtract through-bores or prismatic cutters. Validate every segment by axial span and diameter, and validate every cut by its bounding box, depth, planar or cylindrical face geometry, and adjacency.

## Transient B-rep before document attachment

When several primitives and cutters form one final solid, consider constructing and Booleaning them as transient modeler bodies first. Verify one closed piece, then attach only the final result as a design body. This avoids document-body target ambiguity and leaves a smaller topology surface to name and validate.

For V21 circular-profile extrusion, import `CircleProfile`, `Plane`, and `PointUV` from `SpaceClaim.Api.V21.Geometry`; construct the profile with an explicit plane, radius, UV location, and angle; then call `ModelerBody.ExtrudeProfile`. Do not assume a wildcard import from the root namespace exposes subnamespace types.

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

## Analytic feature validation

Use analytic face geometry as an independent check when the kernel preserves it:

- cylinders for bores and circular holes, checked by radius and axial span;
- cones for equal-distance chamfers, checked by half-angle and bounding-box span;
- tori for constant rounds, checked by minor radius;
- cylindrical faces for prismatic vertical corner rounds, checked by radius, vertical span, and plan-view bounding-box placement;
- repeated cylindrical faces checked by center locations and angular or pitch-circle relations.

Run these checks again after native reopen when feature persistence is part of the acceptance contract.
