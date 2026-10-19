# Validated capability matrix

This matrix records the capabilities supported in v0.2 and the evidence available for each one. “Controlled SpaceClaim runtime evidence” means that the stated pattern succeeded in a controlled SpaceClaim execution. It does not mean every public template has been independently executed on every SpaceClaim release or that post-run guard changes were rerun; exact package differences remain disclosed in the corresponding case record.

| Capability | v0.2 support | Evidence boundary |
|---|---|---|
| Copy and translate bodies | Supported pattern | Controlled SpaceClaim runtime evidence; case-specific topology still requires validation |
| Translate to a face and rotate about an axis | Supported pattern | Controlled SpaceClaim runtime evidence |
| Fixed-distance and up-to-face extrusion | Supported pattern | Controlled SpaceClaim runtime evidence; face selection must be semantic |
| Merge multiple bodies | Supported pattern | Controlled SpaceClaim runtime evidence |
| Split a body with a plane | Supported pattern | Controlled SpaceClaim runtime evidence |
| Split faces parametrically | Supported pattern | Controlled SpaceClaim runtime evidence |
| Boolean intersection | Supported with result re-identification | Returned bodies must be classified by geometry, never by return order |
| Direct construction of solid and void domains | Supported strategy | Prefer when cap-and-extract topology is unstable |
| Volume extraction | Conditional strategy | Requires closed-domain, seed, count, and failure-injection checks for each geometry family |
| Body and named-face-group naming | Supported pattern | Validate actual final names and member counts after save/reopen |
| Native save and reopen | Supported validation layer | Save and reopen must be checked separately |
| `.scscript` archive audit | Implemented and tested | Static package evidence only |
| Deterministic V21 `.scscript` packaging | Implemented and tested | Reproduces the native four-member package structure; packaging does not prove runtime |
| Forward/reopen report comparison | Implemented and tested | Host-side comparison of declared persistence measurements only |
| Read-only geometry report | Template included | Must be run inside the matching SpaceClaim API environment |
| Circular-profile transient extrusion and Boolean construction | Supported V21 pattern | One controlled case with one attached final body; other geometry families require validation |
| Circular hole patterns, constant rounds, and equal-distance chamfers | Supported V21 pattern | Analytic face measurements and native persistence must be checked for each geometry |
| Prismatic corner rounds | Supported V21 pattern | Check cylindrical faces by radius, span, and placement; other kernels require validation |
| SpaceClaim viewport selection and navigation | Controlled calibration workflow | Calibrate the active controller in a maximized window; this is not universal GUI reliability |
| Multi-view visual agreement and screenshot contract | Supported validation workflow | Review every contract-relevant view; external screenshots require per-image metadata and path/hash records, while pixel review remains outside this repository |
| Engineering-drawing dimension reconciliation | Supported pattern | Keep unresolved placements and annotation scope explicit as assumptions |
| Coaxial stepped solids, through-bores, and prismatic cutters | Supported V21 pattern | Check segment spans, diameters, cut dimensions, analytic faces, and native persistence for each model |

## Release interpretation

### v0.3 operation evidence

The registry maps 139 action contracts: 5 preserved host-active
operations and 134 candidates. It is not a claim of 139 fully verified runtime
capabilities. Candidate modeling, execution, measurement and navigation evidence
is bound to exact artifacts and variants in the registry and
`assets/evaluations/p2-source-evaluation`, `p3-actions`, `p4-actions` and
`p5-actions`. General input coverage, unobserved controller gestures and
cross-version behavior remain unclaimed. The complete v0.2 workflow remains the
fallback when no eligible active template matches.

### v0.2 stable release

The v0.2 release adds deterministic `.scscript` packaging, structured report validation and comparison, a faster authorized-run workflow, and a calibrated visual-review contract. It does not claim universal geometry recognition, unattended GUI reliability, cross-version API compatibility, untested persistence behavior, or visual acceptance without a completed per-model review.
