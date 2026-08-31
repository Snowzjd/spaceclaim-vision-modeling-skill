# Validated capability matrix

This matrix records what the v0.2 release candidate can responsibly reuse. “Controlled SpaceClaim runtime evidence” means the pattern has succeeded in a controlled SpaceClaim execution before being generalized here. It does not mean every public template has been independently executed on every SpaceClaim release.

| Capability | v0.2 support | Evidence boundary |
|---|---|---|
| Copy and translate bodies | Supported pattern | Controlled SpaceClaim runtime evidence; case-specific topology still requires validation |
| Translate to a face and rotate about an axis | Supported pattern | Controlled SpaceClaim runtime evidence |
| Fixed-distance and up-to-face extrusion | Supported pattern | Controlled SpaceClaim runtime evidence; face selection must be semantic |
| Merge multiple bodies | Supported pattern | Controlled SpaceClaim runtime evidence |
| Split a body with a plane | Supported pattern | Controlled SpaceClaim runtime evidence |
| Split faces parametrically | Supported pattern | Controlled SpaceClaim runtime evidence |
| Boolean intersection | Supported with result re-identification | Returned bodies must be classified by geometry, never by return order |
| Direct construction of solid and fluid domains | Supported strategy | Prefer when cap-and-extract topology is unstable |
| Volume extraction | Conditional strategy | Requires closed-domain, seed, count, and failure-injection checks for each geometry family |
| Body and named-face-group naming | Supported pattern | Validate actual final names and member counts after save/reopen |
| Native save and reopen | Supported validation layer | Save and reopen must be checked separately |
| `.scscript` archive audit | Implemented and tested | Static package evidence only |
| Deterministic V21 `.scscript` packaging | Implemented and tested | Reproduces the native four-member package structure; packaging does not prove runtime |
| Forward/reopen report comparison | Implemented and tested | Host-side comparison of declared persistence measurements only |
| Read-only geometry report | Template included | Must be run inside the matching SpaceClaim API environment |
| Public case 001 V21 construction | Forward-tested; visual review passed | One controlled SpaceClaim 2022 R1 / API V21 run plus independent native close/reopen audit and one four-view visual review; case-specific only |
| Circular-profile transient extrusion and Boolean construction | Supported V21 pattern | One controlled case with one attached final body; other geometry families require validation |
| Circular hole pattern, constant rounds, and equal-distance chamfers | Supported V21 pattern | Analytic cylinder, torus, and cone measurements passed forward and after native reopen in case 002 |
| Prismatic vertical corner rounds | Supported V21 pattern | One controlled case checked cylindrical corner faces by radius, vertical span, and plan-view placement through native reopen; other kernels require validation |
| SpaceClaim viewport selection and navigation | Controlled calibration completed | One maximized SpaceClaim 2022 R1 session verified left-click selection, blank-space clearing, stationary right click, wheel zoom, Home, visible Spin/Pan/Zoom tools with left drag, Zoom Extents, and orientation-indicator snaps; this is current-controller evidence, not universal GUI reliability |
| Multi-view visual agreement review and screenshot contract | Controlled acceptance completed | Cases 001–004 used clean maximized overviews plus case-appropriate orthogonal or feature-facing views, cleared selections, and archived screenshot hashes; other models still require their own visual review |
| Public case 002 V21 construction | Forward-tested; visual review passed | One controlled SpaceClaim 2022 R1 / API V21 run plus independent feature-level native close/reopen audit and one three-view visual review; case-specific only |
| Engineering-drawing dimension reconciliation | Supported pattern | One controlled multi-view case; unresolved placements and annotation scope must remain explicit assumptions |
| Coaxial stepped solids, through-bores, and prismatic cutters | Supported V21 pattern | Segment spans, diameters, cut dimensions, analytic faces, and native persistence passed in case 003 |
| Public case 003 V21 construction | Forward-tested; visual review passed | One controlled SpaceClaim 2022 R1 / API V21 run plus independent feature-level native close/reopen audit and one three-view visual review; case-specific only |
| Public case 004 V21 construction | Forward-tested; visual review passed | One controlled SpaceClaim 2022 R1 / API V21 run plus independent feature-level native close/reopen audit and one three-view visual review; case-specific only |

## Release interpretation

The v0.2 release candidate adds four public forward-tested cases, a faster run workflow, a controlled SpaceClaim visual-interaction calibration, and completed case-specific visual reviews for cases 001–004. It does not claim universal geometry recognition, unattended GUI reliability, cross-version API compatibility, untested persistence behavior, or visual acceptance for models that were not reviewed.
