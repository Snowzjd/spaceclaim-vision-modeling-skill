---
name: spaceclaim-vision-modeling
description: Convert images, sketches, engineering drawings, CAD screenshots, product photos, patent diagrams, text descriptions, existing SpaceClaim scripts, and error logs into geometry decomposition, parametric SpaceClaim scripts, validation checks, and minimal repairs. Use when planning, generating, debugging, or validating domain-independent 3D CAD models in Ansys SpaceClaim.
---

# SpaceClaim Vision Modeling

Turn visual or textual design intent into a reviewable SpaceClaim modeling plan, executable script, and evidence-bounded validation result.

The v0.3 four-stage architecture preserves the complete modeling workflow as the generic fallback. Its scope runs from visual or textual geometry intent through SpaceClaim-native construction and final model validation. Select atomic operations according to their lifecycle, preconditions and recorded evidence.

## Core rules

1. Reduce the input to geometry primitives, dimensions, coordinate systems, constraints, spatial relations, and modeling operations before naming an industry-specific object.
2. Separate observed facts, user-provided dimensions, inferred relations, and unresolved dimensions. Never hide invented dimensions inside the script.
3. Choose the simplest stable construction strategy: sketch and extrude, revolve, sweep, loft, pattern, mirror, Boolean operations, direct domain construction, or controlled import.
4. Centralize parameters and avoid unexplained numeric literals.
5. Match the target SpaceClaim/API version. Do not copy code across API versions without checking availability and runtime behavior.
6. Select bodies, faces, and edges semantically by direction, position, normal, area, bounding box, volume, topology, and adjacency. Do not generalize recorded `FaceN` or `BodyN` aliases.
7. With no baseline, start in a new unsaved design; with a baseline, run only on a hash-recorded copy. Save validated output to a new run-owned path and stop without saving when a critical assertion fails.
8. Treat plain `.py` as editable or packaging source only; load and deliver the matching SpaceClaim `.scscript` artifact.
9. Distinguish input interpretation, static package checks, SpaceClaim runtime success, visual agreement, geometry-kernel measurements, save/reopen evidence, and requested export evidence.
10. Before controlling the user's desktop, explain why control is needed and obtain authorization for that run. Treat that authorization as run-scoped: do not ask again for familiar setup steps unless the scope changes or the controller requires it.
11. Keep the SpaceClaim window maximized or full-screen throughout authorized control by default; allow a temporary smaller layout only for a blocking dialog, required comparison, or explicit user request.
12. Repair the smallest failing step. Preserve user-confirmed geometry, parameters, names, and output boundaries.
13. Stay within the requested SpaceClaim modeling scope. Do not infer that one successful validation layer proves unperformed modeling checks.

Read [references/integration-boundary.md](references/integration-boundary.md) when defining inputs, outputs, execution authorization, or handoff requirements for a modeling task.

## Resource routing

Load only the resources needed for the current stage:

- After installation or an environment change, use [references/installation-and-runtime.md](references/installation-and-runtime.md) and [scripts/check_installation.py](scripts/check_installation.py) with this package's host virtual environment. Use only the declared vision/file tools, Computer Use runtime and SpaceClaim; do not silently rely on other installed Skills/MCPs. A host-ready result is not live operation acceptance.
- Read [references/v261-runtime-notes.md](references/v261-runtime-notes.md) when the target is a release other than the evidenced 2022 R1 / API V21 baseline: it records the 2026 R1 (V261) unit convention, the working native-save and STEP-export routes, and the paths that block in an in-process host.
- Read [references/architecture.md](references/architecture.md) when checking stage boundaries, handoff contracts, template routing, compatibility, or future composition.
- Read [references/workflow-integration.md](references/workflow-integration.md) when resuming, handing work between stages, resolving installed template paths, or using the generic fallback without an eligible template. Use [scripts/validate_workflow_handoff.py](scripts/validate_workflow_handoff.py) for host-only contract/artifact integrity and [scripts/resolve_operation_artifact.py](scripts/resolve_operation_artifact.py) for installation-aware paths; neither establishes CAD acceptance.
- Read [references/operation-catalog-guide.md](references/operation-catalog-guide.md) and the relevant entries in [references/operation-catalog.json](references/operation-catalog.json) when decomposing a request into atomic actions or identifying implementation gaps. Catalog coverage alone does not establish an executable capability.
- Read [references/operation-template-contract.md](references/operation-template-contract.md) and [references/operation-registry.json](references/operation-registry.json) before creating, promoting, or applying an atomic operation template. Validate new entries against [references/operation-template.schema.json](references/operation-template.schema.json), [references/operation-registry.schema.json](references/operation-registry.schema.json), and the host-check record contract in [references/operation-evidence.schema.json](references/operation-evidence.schema.json). Load only matching active templates; keep this full workflow as the fallback.
- Read only the current stage library when selecting an atomic operation: [references/geometry-understanding-operations.md](references/geometry-understanding-operations.md), [references/modeling-strategy-scripting-operations.md](references/modeling-strategy-scripting-operations.md), [references/execution-recovery-operations.md](references/execution-recovery-operations.md), or [references/validation-visual-review-operations.md](references/validation-visual-review-operations.md).
- For a GU or MS reasoning atom, follow [references/atomic-reasoning-protocol.md](references/atomic-reasoning-protocol.md) and only its selected guidance entry; keep the case's ordered handoff outside the atom.
- Treat the legacy-path bundle `assets/atomic-cases/001-rectangular-prism/` as a v0.3 composition-case record, not an atomic operation, default model, or source of fixed dimensions. Its exact run evidence belongs only to that complete case.
- Use [scripts/validate_operation_registry.py](scripts/validate_operation_registry.py) after registry or template changes to reject cross-entry mismatches, missing dependencies, path escapes, missing artifacts, template-byte or evidence-version drift, and SHA-256 mismatches on the host.
- Use [references/geometry-understanding-output.schema.json](references/geometry-understanding-output.schema.json) and [scripts/validate_geometry_understanding_outputs.py](scripts/validate_geometry_understanding_outputs.py) for schema-bound Geometry-understanding outputs. Treat successful fixture checks as host-only contract evidence, not proof that unseen source material was interpreted correctly.
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
- Use the focused files in `prompts/` when a parser, planner, writer, debugger, or validation-review contract is needed.

## Workflow

### 1. Geometry understanding

Identify whether the task starts from an image, sketch, engineering drawing, CAD screenshot, product photo, patent diagram, text description, existing script, model, or error log. Extract the user's intended geometry, required outputs, supplied dimensions, target version, and unresolved choices before controlling SpaceClaim.

Record:

- primary bodies and construction geometry;
- holes, slots, ribs, shells, channels, arrays, and freeform features;
- symmetry, coaxiality, parallelism, tangency, containment, penetration, and offsets;
- known dimensions, assumptions, unresolved values, and tolerances;
- required bodies, names, groups, exports, and intended use.

Read [references/workflow-contracts.md](references/workflow-contracts.md) for the parsing, planning, writing, debugging, and review schemas.

### 2. Modeling strategy and scripting

Prefer deterministic parametric construction. Use GUI interaction only for observations or operations that cannot be reproduced reliably through the available API.

Apply [references/spaceclaim-scripting-rules.md](references/spaceclaim-scripting-rules.md). Select the no-baseline or verified baseline-copy path policy explicitly; do not reuse a new-path-only script for an existing copy. Keep version-sensitive calls isolated, use semantic selectors, assert critical counts and dimensions, emit a runtime report, and save only after validation passes. Complete relevant host-side checks before starting desktop control; do not repeat unchanged repository or script audits between routine GUI actions.

When the input is a recorded `.scscript`, run the static auditor first. Numbered smart-variable aliases may be acceptable for a same-topology replay, but they are not reusable semantic selection logic.

### 3. Execution and recovery

After authorization, follow [references/execution-workflow.md](references/execution-workflow.md). Use the GUI only to establish the intended document, save or open the run-owned model, load the prepared script, and run it once. Let the script perform geometry construction and assertions. Do not insert manual geometry reviews between familiar setup actions; stop at the entry-state gate, the run-result gate, an exception, and any required save/reopen gate.

Preserve a maximized or full-screen SpaceClaim workspace throughout authorized control by default. Use a temporary smaller layout only for a blocking dialog, required comparison, or explicit user request, then restore it. Calibrate one small reversible navigation motion before relying on the default mouse mapping, because user navigation themes can remap spin, pan, zoom, and wheel behavior.

Classify failures as syntax/API, object selection, topology mutation, Boolean semantics, invalid geometry, naming, path/encoding, application state, save, reopen, or export. Patch the smallest responsible step and rerun from a clean design or verified baseline copy.

### 4. Validation and visual review

After the run completes, verify operations, body counts, names, bounding boxes, volumes, requested groups, visual agreement, and output existence in proportion to risk. Follow the deterministic viewpoint ladder and per-image screenshot contract in [references/visual-interaction.md](references/visual-interaction.md). Reopen native output when save persistence matters. When screenshots are archived outside the repository, record their path and SHA-256 and state that the repository cannot independently review their pixels.

Do not claim an unperformed validation layer without corresponding evidence.

## Required handoff

Return:

- geometry decomposition and assumptions;
- parameter table and coordinate-system definition;
- selected modeling strategy;
- generated or revised SpaceClaim script;
- validation evidence and its boundary;
- output paths and hashes when files were created;
- unresolved risks and the next safe test.
