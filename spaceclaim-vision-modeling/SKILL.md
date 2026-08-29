---
name: spaceclaim-vision-modeling
description: Convert images, sketches, engineering drawings, CAD screenshots, product photos, patent diagrams, text descriptions, existing SpaceClaim scripts, and error logs into geometry decomposition, parametric SpaceClaim scripts, validation checks, and minimal repairs. Use when planning, generating, debugging, or validating domain-independent 3D CAD models in Ansys SpaceClaim.
---

# SpaceClaim Vision Modeling

Turn visual or textual design intent into a reviewable SpaceClaim modeling plan, executable script, and evidence-bounded validation result.

This is the v0.1 SpaceClaim modeling skill. Its scope runs from geometry intent through SpaceClaim-native construction and geometry validation; meshing and simulation require separate downstream evidence.

## Core rules

1. Reduce the input to geometry primitives, dimensions, coordinate systems, constraints, spatial relations, and modeling operations before naming an industry-specific object.
2. Separate observed facts, user-provided dimensions, inferred relations, and unresolved dimensions. Never hide invented dimensions inside the script.
3. Choose the simplest stable construction strategy: sketch and extrude, revolve, sweep, loft, pattern, mirror, Boolean operations, direct domain construction, or controlled import.
4. Centralize parameters and avoid unexplained numeric literals.
5. Match the target SpaceClaim/API version. Do not copy code across API versions without checking availability and runtime behavior.
6. Select bodies, faces, and edges semantically by direction, position, normal, area, bounding box, volume, topology, and adjacency. Do not generalize recorded `FaceN` or `BodyN` aliases.
7. Work from a copy, save to a new path, and stop without saving when a critical assertion fails.
8. Distinguish static package checks, SpaceClaim runtime success, visual agreement, geometry-kernel measurements, save/reopen evidence, export evidence, and downstream mesh or solver evidence.
9. Before controlling the user's desktop, explain why control is needed and obtain authorization for that run.
10. Repair the smallest failing step. Preserve user-confirmed geometry, parameters, names, and output boundaries.
11. Stay within the requested SpaceClaim modeling scope. Do not infer that geometry success proves shared topology, mesh connectivity, solver readiness, or simulation results.

Read [references/integration-boundary.md](references/integration-boundary.md) when defining inputs, outputs, execution authorization, or handoff requirements for a modeling task.

## Resource routing

Load only the resources needed for the current stage:

- Read [references/validated-capability-matrix.md](references/validated-capability-matrix.md) before claiming that an operation or validation layer is supported.
- Read [references/modeling-patterns.md](references/modeling-patterns.md) when choosing semantic selectors, Boolean strategy, direct-domain construction, or naming logic.
- Read [references/failure-recovery.md](references/failure-recovery.md) when a replay or model diverges.
- Use [scripts/audit_scscript.py](scripts/audit_scscript.py) for deterministic host-side `.scscript` package checks.
- Copy [assets/templates/spaceclaim-v21-geometry-audit.py](assets/templates/spaceclaim-v21-geometry-audit.py) for a read-only SpaceClaim geometry report.
- Copy [assets/templates/spaceclaim-v21-semantic-helpers.py](assets/templates/spaceclaim-v21-semantic-helpers.py) when building V21 semantic selectors and naming assertions.
- Use [assets/cases/001-offset-block-array/requirement.md](assets/cases/001-offset-block-array/requirement.md) as the public synthetic acceptance-case format.
- Use the focused files in `prompts/` when a parser, planner, writer, debugger, or validation-review contract is needed.

## Workflow

### 1. Classify the input

Identify whether the task starts from an image, sketch, engineering drawing, CAD screenshot, product photo, patent diagram, text description, existing script, model, or error log.

### 2. Build the geometry contract

Record:

- primary bodies and construction geometry;
- holes, slots, ribs, shells, channels, arrays, and freeform features;
- symmetry, coaxiality, parallelism, tangency, containment, penetration, and offsets;
- known dimensions, assumptions, unresolved values, and tolerances;
- required bodies, names, groups, exports, and downstream use.

Read [references/workflow-contracts.md](references/workflow-contracts.md) for the parsing, planning, writing, debugging, and review schemas.

### 3. Select the modeling strategy

Prefer deterministic parametric construction. Use GUI interaction only for observations or operations that cannot be reproduced reliably through the available API.

### 4. Generate or revise the script

Apply [references/spaceclaim-scripting-rules.md](references/spaceclaim-scripting-rules.md). Keep version-sensitive calls isolated, use semantic selectors, assert critical counts and dimensions, emit a runtime report, and save only after validation passes.

When the input is a recorded `.scscript`, run the static auditor first. Numbered smart-variable aliases may be acceptable for a same-topology replay, but they are not reusable semantic selection logic.

### 5. Validate in layers

Check the script package and parameters before runtime. During runtime, verify operations, body counts, names, bounding boxes, volumes, face groups, and output existence in proportion to risk. Reopen native output when save persistence matters.

Do not claim export, mesh connectivity, or solver readiness without the corresponding downstream evidence.

### 6. Diagnose and repair

Classify failures as syntax/API, object selection, topology mutation, Boolean semantics, invalid geometry, naming, path/encoding, application state, save/export, or downstream transfer. Patch the smallest responsible stage and rerun from a clean copy.

### 7. Extract reusable knowledge

After a successful case, separate reusable geometry logic from case-specific dimensions and names. Store deterministic utilities in `scripts/`, detailed guidance in `references/`, and copyable templates or public case assets in `assets/`.

Read [references/case-library-contract.md](references/case-library-contract.md) before adding templates, examples, or training cases.

## Required handoff

Return:

- geometry decomposition and assumptions;
- parameter table and coordinate-system definition;
- selected modeling strategy;
- generated or revised SpaceClaim script;
- validation evidence and its boundary;
- output paths and hashes when files were created;
- unresolved risks and the next safe test.
