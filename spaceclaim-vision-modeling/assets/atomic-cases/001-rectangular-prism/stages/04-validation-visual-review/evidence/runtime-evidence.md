# Rectangular-prism composition-case runtime evidence

The retained v0.3 four-stage composition case completed one controlled run in a
maximized SpaceClaim 2022 R1 session using API V21 and IronPython 2.7.

- The build `.scscript` SHA-256 was
  `d99e7d0a5df422bba143503c74bce84ae39d0eaa7ed1a60499b8f833358c80ff`.
- It was loaded and run exactly once from a new unsaved design.
- The generated native model was saved, closed, and reopened successfully.
- The reopened model was measured by the separate read-only validation
  `.scscript` SHA-256
  `17cf13aa9b1acb9eb5ae73dacd23770e156779066a5e517368df4ef019380554`.
- The read-only result reproduced one body named `ATOMIC_PRISM`, bounding box
  `[10,-5,2]..[50,25,14] mm`, volume `14400.000000000002 mm3`, six faces, and
  twelve edges.
- Overview, Top, Front, and Right views were reviewed with no active geometry
  selection. Their silhouettes agreed with the expected `40 x 30`, `40 x 12`,
  and `30 x 12 mm` orthogonal extents, with no extra body or feature observed.

The public JSON reports are sanitized copies: only run-owned absolute paths
were replaced by repository-safe filenames. Their original SHA-256 values are
retained in `runtime-evidence.json`. The native `.scdoc` and screenshot binaries
are not bundled; the evidence record retains their filenames and SHA-256 values.

This evidence supports this exact complete case, parameter set, and environment.
It does not establish cross-version behavior and is not runtime evidence for
any generalized atomic operation template.
