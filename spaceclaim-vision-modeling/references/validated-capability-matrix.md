# Validated capability matrix

This matrix records what v0.1 can responsibly reuse. “Controlled SpaceClaim runtime evidence” means the pattern has succeeded in a controlled SpaceClaim execution before being generalized here. It does not mean every public template has been independently executed on every SpaceClaim release.

| Capability | v0.1 support | Evidence boundary |
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
| Native save and reopen | Supported validation layer | Does not prove neutral export, meshing, or solver readiness |
| `.scscript` archive audit | Implemented and tested in v0.1 | Static package evidence only |
| Read-only geometry report | Template included | Must be run inside the matching SpaceClaim API environment |
| Shared topology | Experimental/out of v0.1 core | Requires separate transfer and mesh-connectivity evidence |
| Neutral export and reimport | Not yet validated in v0.1 | No claim |
| Meshing and solver execution | Out of scope | Belongs to separately validated downstream stages |

## Release interpretation

v0.1 is a reusable modeling and validation foundation. It does not claim universal geometry recognition, unattended GUI reliability, cross-version API compatibility, or downstream simulation readiness.
