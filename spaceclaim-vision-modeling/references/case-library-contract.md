# Case library contract

Use public, redistributable geometry only. Do not add proprietary models, licensed API documentation, private recordings, unpublished research data, credentials, or user-specific paths.

## Case categories

Grow the library by geometry behavior rather than industry labels:

- primitives and sketch-based solids;
- revolved and axisymmetric parts;
- pipes, bends, branches, and transitions;
- shells, housings, ribs, holes, and slots;
- linear, circular, grid, and variable-spacing arrays;
- Boolean merge, subtract, intersect, and split;
- internal voids, external envelopes, and enclosed regions;
- naming, defeaturing, and export preparation;
- visually inferred or dimension-incomplete models.

## Case bundle

Use this structure only for real cases; do not create empty category folders:

```text
case-name/
├─ input/
│  ├─ requirement.md
│  └─ public visual or drawing
├─ reasoning/
│  ├─ geometry-decomposition.md
│  └─ modeling-strategy.md
├─ output/
│  ├─ script.scscript
│  ├─ script-source.py (optional packaging source; not the formal executable asset)
│  └─ public neutral-format result when redistributable
├─ validation/
│  ├─ checklist.md
│  ├─ run-log.txt
│  └─ known-issues.md
```

## Acceptance questions

Every case must answer:

1. What is the geometry decomposition?
2. Which operations construct it, and why?
3. Which parameters should be exposed?
4. Which runtime states are fragile?
5. Which validation proves success?
