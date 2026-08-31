---
name: spaceclaim-vision-modeling
description: Convert images, sketches, engineering drawings, CAD screenshots, product photos, patent diagrams, text descriptions, existing SpaceClaim scripts, and error logs into geometry decomposition, parametric SpaceClaim scripts, validation checks, and minimal repairs. Use when planning, generating, debugging, or validating domain-independent 3D CAD models in Ansys SpaceClaim.
---

# SpaceClaim Vision Modeling

Turn visual or textual design intent into a reviewable SpaceClaim modeling plan, executable script, and evidence-bounded validation result.

This is the v0.2 version of the SpaceClaim visual modeling skill. Its scope runs from visual or textual geometry intent through SpaceClaim-native construction and final model validation.

## Core rules

1. Reduce the input to geometry primitives, dimensions, coordinate systems, constraints, spatial relations, and modeling operations before naming an industry-specific object.
2. Separate observed facts, user-provided dimensions, inferred relations, and unresolved dimensions. Never hide invented dimensions inside the script.
3. Choose the simplest stable construction strategy: sketch and extrude, revolve, sweep, loft, pattern, mirror, Boolean operations, direct domain construction, or controlled import.
4. Centralize parameters and avoid unexplained numeric literals.
5. Match the target SpaceClaim/API version. Do not copy code across API versions without checking availability and runtime behavior.
6. Select bodies, faces, and edges semantically by direction, position, normal, area, bounding box, volume, topology, and adjacency. Do not generalize recorded `FaceN` or `BodyN` aliases.
7. Work from a copy, save to a new path, and stop without saving when a critical assertion fails.
8. Distinguish input interpretation, static package checks, SpaceClaim runtime success, visual agreement, geometry-kernel measurements, save/reopen evidence, and requested export evidence.
9. Before controlling the user's desktop, explain why control is needed and obtain authorization for that run. Treat that authorization as run-scoped: do not ask again for familiar setup steps unless the scope changes or the controller requires it.
10. Keep the SpaceClaim window maximized or full-screen during visual work unless a blocking dialog or required side-by-side comparison makes a temporary smaller layout necessary.
11. Repair the smallest failing step. Preserve user-confirmed geometry, parameters, names, and output boundaries.
12. Stay within the requested SpaceClaim modeling scope. Do not infer that one successful validation layer proves unperformed modeling checks.

Read [references/integration-boundary.md](references/integration-boundary.md) when defining inputs, outputs, execution authorization, or handoff requirements for a modeling task.

## Resource routing

Load only the resources needed for the current stage:

- Read [references/validated-capability-matrix.md](references/validated-capability-matrix.md) before claiming that an operation or validation layer is supported.
- Read [references/modeling-patterns.md](references/modeling-patterns.md) when choosing semantic selectors, Boolean strategy, direct-domain construction, or naming logic.
- Read [references/failure-recovery.md](references/failure-recovery.md) when a replay or model diverges.
- Read [references/execution-workflow.md](references/execution-workflow.md) before an authorized SpaceClaim run; prepare once, execute routine setup continuously, and review at defined gates.
- Read [references/visual-interaction.md](references/visual-interaction.md) before selecting geometry through the viewport, manipulating views, diagnosing visible failures, or performing final visual acceptance.
- Use [scripts/audit_scscript.py](scripts/audit_scscript.py) for deterministic host-side `.scscript` package checks.
- Use [scripts/validate_runtime_report.py](scripts/validate_runtime_report.py) with [references/spaceclaim-validation-report.schema.json](references/spaceclaim-validation-report.schema.json) to validate a structured report and case contract on the host without upgrading it to runtime evidence.
- Use [scripts/compare_runtime_reports.py](scripts/compare_runtime_reports.py) to compare forward and native-reopen body/group measurements on the host without upgrading the reports to independent runtime evidence.
- Copy [assets/templates/spaceclaim-v21-geometry-audit.py](assets/templates/spaceclaim-v21-geometry-audit.py) for a read-only SpaceClaim geometry report.
- Copy [assets/templates/spaceclaim-v21-semantic-helpers.py](assets/templates/spaceclaim-v21-semantic-helpers.py) when building V21 semantic selectors and naming assertions.
- Use [assets/cases/001-offset-block-array/requirement.md](assets/cases/001-offset-block-array/requirement.md) as the public synthetic acceptance-case format.
- Use [assets/cases/001-offset-block-array/output/spaceclaim-v21-build.scscript](assets/cases/001-offset-block-array/output/spaceclaim-v21-build.scscript) as a V21 forward-tested primitive-array example, bounded by [its runtime evidence](assets/cases/001-offset-block-array/runtime-evidence.md).
- Use [assets/cases/002-flanged-short-pipe/output/spaceclaim-v21-build.scscript](assets/cases/002-flanged-short-pipe/output/spaceclaim-v21-build.scscript) and its separate [native-reopen audit package](assets/cases/002-flanged-short-pipe/output/spaceclaim-v21-reopen-audit.scscript) as a V21 circular-profile, transient-Boolean, hole-pattern, round, and chamfer example, bounded by [its runtime evidence](assets/cases/002-flanged-short-pipe/validation/runtime-evidence.md).
- Use the focused files in `prompts/` when a parser, planner, writer, debugger, or validation-review contract is needed.

## Workflow

### 1. Understand the request and references

Identify whether the task starts from an image, sketch, engineering drawing, CAD screenshot, product photo, patent diagram, text description, existing script, model, or error log. Extract the user's intended geometry, required outputs, supplied dimensions, target version, and unresolved choices before controlling SpaceClaim.

### 2. Build the geometry contract

Record:

- primary bodies and construction geometry;
- holes, slots, ribs, shells, channels, arrays, and freeform features;
- symmetry, coaxiality, parallelism, tangency, containment, penetration, and offsets;
- known dimensions, assumptions, unresolved values, and tolerances;
- required bodies, names, groups, exports, and intended use.

Read [references/workflow-contracts.md](references/workflow-contracts.md) for the parsing, planning, writing, debugging, and review schemas.

### 3. Select the modeling strategy

Prefer deterministic parametric construction. Use GUI interaction only for observations or operations that cannot be reproduced reliably through the available API.

### 4. Generate and preflight the script

Apply [references/spaceclaim-scripting-rules.md](references/spaceclaim-scripting-rules.md). Keep version-sensitive calls isolated, use semantic selectors, assert critical counts and dimensions, emit a runtime report, and save only after validation passes. Complete relevant host-side checks before starting desktop control; do not repeat unchanged repository or script audits between routine GUI actions.

When the input is a recorded `.scscript`, run the static auditor first. Numbered smart-variable aliases may be acceptable for a same-topology replay, but they are not reusable semantic selection logic.

### 5. Execute in SpaceClaim

After authorization, follow [references/execution-workflow.md](references/execution-workflow.md). Use the GUI only to establish the intended document, save or open the run-owned model, load the prepared script, and run it once. Let the script perform geometry construction and assertions. Do not insert manual geometry reviews between familiar setup actions; stop at the entry-state gate, the run-result gate, an exception, and any required save/reopen gate.

Preserve a maximized or full-screen SpaceClaim workspace during viewport work. Calibrate one small reversible navigation motion before relying on the default mouse mapping, because user navigation themes can remap spin, pan, zoom, and wheel behavior.

### 6. Review the final model

After the run completes, verify operations, body counts, names, bounding boxes, volumes, requested groups, visual agreement, and output existence in proportion to risk. Follow the deterministic viewpoint ladder and screenshot contract in [references/visual-interaction.md](references/visual-interaction.md). Reopen native output when save persistence matters.

Do not claim an unperformed validation layer without corresponding evidence.

### 7. Diagnose and repair

Classify failures as syntax/API, object selection, topology mutation, Boolean semantics, invalid geometry, naming, path/encoding, application state, save, reopen, or export. Patch the smallest responsible stage and rerun from a clean copy.

## Required handoff

Return:

- geometry decomposition and assumptions;
- parameter table and coordinate-system definition;
- selected modeling strategy;
- generated or revised SpaceClaim script;
- validation evidence and its boundary;
- output paths and hashes when files were created;
- unresolved risks and the next safe test.
