# Independent raw-source P2 handoff

This is source interpretation and planning only. I inspected both supplied image files as pixels and read text-c.md. I read the frozen common protocol/schema and GU/MS guidance. No source generator, gold/scoring key, older case/fixture, other evaluator result, SpaceClaim session, API signature, native model or export was accessed. No desktop control was used.

## Source-level geometry handoff

### A — image and embedded note

The shape is a constant right-triangular prism, not a rectangular box. The note controls dimensions, not the illustration scale: base 42 mm, perpendicular height 18 mm, extrusion depth 25 mm. A closed section can use vertices (0,0), (42,0), (0,18) mm under the declared modeling frame. No holes or edge treatment. Expected unmodified solid volume is 42 × 18 × 25 / 2 = 9450 mm^3; this is analytical expectation, not a measured result. Deliver native model only. Conceptually a closed triangular sketch and constant extrusion are sufficient; target-version construction binding and measurement acceptance remain unavailable. Illustration camera orientation is not uniquely calibrated and does not block this explicitly dimensioned geometry.

### B — drawing

Dimensions are annotations; the drawing explicitly says NOT TO SCALE. Rectangular plate blank is 90 × 45 × 6 mm. Three diameter-9 through holes have centers at (15,22.5), (45,22.5), (75,22.5) mm in the footprint. The 15 + 30 + 30 + 15 chain closes to 90 mm, and the centered row uses 45/2 = 22.5 mm. The first top-view circle corresponds to the first front-view hidden-line pair. Apply the stated equal-distance 0.5 mm chamfer to all outside perimeter edges and exclude hole edges; do not silently substitute an angle parameter or general all-edge selection. Final deliverable must contain one body named PLATE and a native file. No STEP is requested for B.

A conceptual blank-creation / hole-removal / exterior-chamfer plan is geometrically plausible, but not a tested recipe. Actual external-edge membership, measurable selection properties, tolerances and runtime method bindings must be established before execution. The stored MS-07 record marks the planned chamfer boundary and invalidation scope, not actual invalidated runtime handles.

### C — text

Three coaxial successive cylindrical regions have nominal lengths 12 mm, 0.03 m (=30 mm), and 22 mm, and end/middle/end diameters 28/20/28 mm. These successive lengths sum exactly to 64 mm, while the user requires 65 mm overall and explicitly rules out toleranced rounding. Do not stretch, average, or quietly change any segment. Ask: should total length be 64 mm, or which segment length should change to make it 65 mm?

The left-entry axial blind hole has diameter 7 mm and no decided depth. Ask for that depth with units; do not substitute through-all or a zero/default depth. Keep sharp edges. Both the inconsistent length chain and missing depth block a completed solid and acceptable native/STEP export. Capture native and STEP requirements independently, each in the current run directory. Do not claim that acknowledging the requirements means they have been fulfilled.

## Declared planning inputs

These declarations are evaluator-selected modeling conventions or source-derived conceptual operation inputs, not observations or tested API records.

- A frame: right-angle vertex is origin; base +X, height +Y, extrusion +Z; right-handed orthonormal axes; mm.
- B frame: footprint lower-left in top view on bottom face is origin; drawing right +X, top-view up +Y, thickness +Z; mm. TOP (+Z) denotes outward view-side normal; camera projection ray is -Z. FRONT (-Y) analogously denotes outward -Y.
- Analysis uses mm for C conversion, preserving original 0.03 m. A `base_length` is an unused explicit parameter name with fixed nominal allowed_values [42] mm. Single constraint: equals 42 mm; no broader design range is invented.
- A output declaration: role native_model, filename A.scdoc, symbolic explicit directory `<RUN_DIR>`, known output paths empty, raw inputs protected as `<RAW_INPUT_DIR>`. Policy is stop on any collision and never replace without explicit approval. Path checks are lexical only, not filesystem checks. This declaration is an evaluation convention, not a user-specified filename.
- `B.blank` (`plan.b.blank`): conceptual operation inputs are B's 90 × 45 footprint and 6 mm thickness; output is a plate solid. `B.drill` (`plan.b.drill`): conceptual single first-hole removal inputs are that plate solid plus first diameter-9 through-hole definition; output is the plate with that hole. Required artifact is plate solid to subtract from. Existing dependency edges: empty.
- `B.chamfer` (`plan.b.chamfer`): conceptual action is the stated exterior equal-distance 0.5 mm chamfer; topology effect is replacement of affected edges and creation/change of adjacent faces; operation boundary is after that action and before later selection. `B.external_edges` (`plan.b.edges`) is the conceptual pre-chamfer edge selection scope on PLATE, not an actual handle or selected runtime set. Scope is all stated outside perimeter edges, excluding hole edges. After the action, re-enumerate affected body edges/faces and reacquire semantic references.
- Proposed selection handling is fail-closed: zero matches stops; one candidate still must satisfy all supplied criteria; multiple matches need distinguishing properties, never an arbitrary index. No numerical selection tolerance is invented.
- No exact host/release/API/runtime, measured edge-property input, traceable volume-measurement method, numeric acceptance tolerance or source-backed API signature was provided. These missing MS inputs must remain actionable unresolved records. Ordinary sketch/extrude and material-removal concepts are not claimed as version-tested primitives.

## Atomic coverage and limits

38 emitted records exercise every GU-01 through GU-20 and MS-01 through MS-09 at least once. IDs unexercised: none. Coverage is not equivalent to successful execution or confirmed generality.

- Resolved geometry interpretation includes direct extraction, dimensions, unit conversion, closed triangle interpretation, one cross-view feature correspondence, coaxial relation, one hole-set symmetry, one repetition, one derived coordinate, explicit coordinate conventions, one view mapping, equal-distance chamfer scope, volume expectation and separate delivery requirements.
- GU-03 for A retains unknown numeric camera direction. GU-14 detects a definite C conflict; independent GU-18 records preserve that conflict and the missing bore depth as blocking. GU-07 for C also propagates missing depth.
- MS-01/02 check one nominal parameter only. MS-04/07/09 produce conceptual dependency, topology refresh and output-path declarations, not executed operations.
- MS-03/05/06/08 are deliberately unresolved where required environment/signature, geometry measurement or tolerance inputs are unavailable. Their rejected or unresolved paths are exercised; positive construction selection, API binding, predicate generation and assertion binding are not demonstrated.

## Guidance observations

The typed actions keep expected geometry, operation planning and measured/runtime proof distinct, and allow useful unresolved handoffs without inventing a bore depth or API signature. The protocol's explicit convention permission allows geometry-neutral frame choices. GU-03 `view_direction` does not fix whether a vector means view-side normal or camera ray; I therefore state the convention and carry both meanings explicitly in GU-16. A more precise field semantic would reduce sign disagreement between independent interpreters.

MS-03 is stricter than an ordinary geometric strategy recommendation because it requires environment-associated supplied methods. With raw requests alone it supports an actionable missing-input result but cannot substantiate a positive version-aware choice. The handoff therefore contains conceptual geometric guidance in prose while keeping `construction_decision` null. This is an input limitation, not evidence of API incompatibility.

## Checker execution

The first programmatic run of `validate(result, manifest, specifications())` on every one of the 38 saved records returned 36 `Invalid source manifest entry` messages per record plus cascading `Unknown source reference` messages, and no distinct action-data failure. The manifest originally used structured locator objects. The protocol requires id/kind/locator but does not state the manifest locator type; GU-02's result locator is explicitly an object, whereas the checker enforces a nonempty string for every manifest locator. This is a demonstrated documentation/interface ambiguity. I inspected only that checker condition, not tests or scoring data, then mechanically encoded each existing locator object as a JSON string. IDs, paths, regions, geometry interpretation and all action results were unchanged. The original shape remains fully reconstructable by JSON-decoding the locator strings.

The handoff helper was also called per source, not across the mixed batch. It reports A's unknown camera action plus MS-03/MS-08, B's MS-06, and C's conflict/depth/API blockers. A's camera uncertainty is explicitly nonblocking for the dimensioned geometry, although the helper treats any requires_clarification action as an unresolved required action. Do not interpret this as a geometry-construction blocker when the consuming case does not require camera reproduction; retain the other actual runtime/measurement input gaps. No whole-batch readiness status is asserted.

Final recheck after the locator-only correction: 38 records evaluated, 37 passed, one failed. `a-ms02` returns `Parameter constraint verdict mismatch`. Its numerical comparison is 42 eq 42 and its verdict is `pass`, matching the guidance's prose instruction to record a "pass or fail outcome"; the checker accepts only `passed` or `failed`. The guidance result field describes verdict but does not enumerate those exact tokens. I inspected that failure condition and preserved the emitted `pass` unchanged, so the actual interface failure remains visible for review. No interpretation was adapted to an expected answer.

Structural validation alone cannot certify pixel interpretation, native save/reopen, measurement, topology, export or API compatibility. The 37/38 result is a checker result, not a 37/38 geometry success score.
