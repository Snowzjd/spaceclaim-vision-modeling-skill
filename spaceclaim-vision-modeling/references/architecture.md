# v0.3 architecture

## Contents

- [Purpose](#purpose)
- [Architectural invariants](#architectural-invariants)
- [Stage contracts](#stage-contracts)
- [Routing and conditional loading](#routing-and-conditional-loading)
- [Compatibility baseline](#compatibility-baseline)
- [v0.2 capability migration inventory](#v02-capability-migration-inventory)
- [Evidence taxonomy compatibility](#evidence-taxonomy-compatibility)
- [v0.3 evidence and regression gates](#v03-evidence-and-regression-gates)
- [Extension-stage protocol](#extension-stage-protocol)
- [Extension point for v0.4](#extension-point-for-v04)

## Purpose

Use this architecture to preserve one complete SpaceClaim modeling workflow while allowing independently maintainable atomic operations. Keep `SKILL.md` as the orchestrator and default entry point. Treat operation templates as conditional support, not as the only way to complete a task.

The stable workflow has four stages:

1. Geometry understanding
2. Modeling strategy and scripting
3. Execution and recovery
4. Validation and visual review

Do not bypass a stage merely because a template exists. A supplied, current, and validated upstream contract may satisfy a stage input, but the receiving stage must still check its entry gate.

## Architectural invariants

The approved action inventory is recorded in [operation-catalog.json](operation-catalog.json).
See [operation-catalog-guide.md](operation-catalog-guide.md) for its lifecycle,
registry mapping, overlap boundaries, and case decomposition acceptance. Its 139
entries define planned actions; only linked registry templates carry executable
scope and evidence. Keep construction order and supplied values in compositions.

- Preserve the end-to-end v0.2 workflow as the compatibility baseline.
- Keep generic reasoning and script generation available when no operation template matches.
- Load only the operation templates required by the current task and stage.
- Keep each template action-neutral and case-neutral: one template performs one modeling, state, or inspection action. Put operation order, dimensions, names, part semantics, and uncommon construction logic in the consuming composition case.
- Treat the formal executable SpaceClaim artifact as `.scscript`. Treat a matching `.py` file only as editable or packaging source.
- Match the target SpaceClaim API and Python runtime before execution.
- Re-enumerate geometry after topology-changing operations and classify results semantically rather than by recorded object number or returned order.
- Keep evidence layers independent. Do not upgrade host checks, runtime reports, screenshots, native files, or exports into evidence for a layer that was not performed.
- Keep operation evidence attached to the exact template version and artifact that was checked.

## Stage contracts

Each stage consumes a structured contract, applies an entry gate, and emits a structured handoff. Preserve unknown or untested values explicitly instead of filling them with assumptions.

### Common contract envelope

Every stage handoff must include:

```text
contract_kind
contract_version
stage
handoff_status
upstream_contract_refs
artifact_refs
assumptions
unresolved_items
evidence_refs
```

Use `draft`, `requires_clarification`, `ready`, `passed`, `failed`, or `not_tested` for `handoff_status`. This is distinct from an operation template's lifecycle `status`. A receiving stage may accept only `ready` or `passed` upstream work. Use `requires_clarification` when an unresolved item would change geometry, construction order, or acceptance. Keep artifact references repository-relative or run-owned, and include hashes when evidence is bound to exact file content.

### 1. Geometry understanding

**Inputs**

- source manifest: images, drawings, screenshots, photos, text, existing models, scripts, or logs;
- user intent and requested deliverables;
- supplied dimensions, constraints, tolerances, and target version when known.

**Required output: geometry contract**

```text
source_manifest
observed_geometry
bodies_and_features
spatial_relations
coordinate_system
dimensions_with_provenance
symmetry_and_repetition
assumptions
unresolved_items
confidence
validation_intent
```

**Exit gate**

- Separate observed facts, user-supplied values, inferred relations, and unresolved items.
- Define a usable coordinate system or mark it unresolved.
- Do not encode missing dimensions as silent numeric defaults.
- Describe geometry independently of an industry-specific object name.

### 2. Modeling strategy and scripting

**Inputs**

- accepted geometry contract;
- target SpaceClaim release, API version, and Python runtime;
- entry-state policy and requested output contract;
- applicable operation templates and their evidence levels.

**Required output: build contract**

```text
geometry_contract_ref
parameter_table
construction_strategy
ordered_operation_plan
topology_dependencies
semantic_selection_plan
failure_checkpoints
validation_plan
target_environment
entry_state_policy
output_policy
scscript_artifact
source_artifact_optional
host_preflight_result
unresolved_risks
```

**Exit gate**

- Centralize parameters and make units explicit.
- Choose one primary stable construction strategy.
- Define semantic re-selection after every topology-changing step.
- Bind version-sensitive calls to the target environment.
- Produce a formal `.scscript` artifact and a validation plan before requesting execution.
- Keep critical assertions before save.

### 3. Execution and recovery

**Inputs**

- accepted build contract and exact `.scscript` artifact;
- run-scoped desktop authorization;
- verified entry-state and run-owned paths;
- failure and safe-stop rules.

**Required output: execution contract**

```text
build_contract_ref
entry_state_observed
executed_artifact_identity
stage_events
runtime_report
model_artifact
failure_state
recovery_actions
save_state
unresolved_runtime_risks
```

**Exit gate**

- Use a new unsaved design when no baseline is supplied.
- Use only a hash-recorded copy when a baseline is supplied.
- Record the exact executed artifact, result, and earliest incorrect state.
- Stop without saving when a critical assertion fails.
- Apply the smallest repair, then rerun from a clean entry state.
- Do not treat a declared runtime report as independent observation by itself.

### 4. Validation and visual review

**Inputs**

- geometry, build, and execution contracts;
- requested acceptance criteria;
- runtime measurements, native artifact, and available visual evidence.

**Required output: acceptance contract**

```text
artifact_identity
geometry_acceptance
body_feature_and_name_checks
dimension_bbox_and_volume_checks
native_save_result
native_reopen_result
visual_review_views
visual_agreement
requested_export_result
evidence_map
unresolved_risks
overall_status
```

**Exit gate**

- Check the requested geometry properties in proportion to risk.
- Keep geometry measurements, visual agreement, native save, native reopen, and requested export as separate results.
- Use enough views to expose every contract-relevant feature and record occluded or unresolved features.
- Mark every unperformed layer `not_tested`.
- Bind acceptance to the exact model and evidence artifacts reviewed.

## Routing and conditional loading

Apply this routing order:

1. Start from `SKILL.md` and identify the current stage from the available contracts and the user's requested outcome.
2. Validate the receiving stage's entry contract. Return to the earliest incomplete stage when required fields or provenance are missing.
3. Read `operation-registry.json` only when a reusable atomic operation may reduce ambiguity or execution risk.
4. Filter registry entries by `stage`, `trigger`, target compatibility, preconditions, dependencies, and evidence level.
5. Load the smallest matching set of operation templates. Do not load an entire stage library for one operation.
6. Apply the template through its declared inputs, outputs, failure modes, recovery, and validation checks.
7. Fall back to the generic v0.2 workflow when no template matches, a precondition is unmet, the target version differs, or a template conflicts with the geometry contract.
8. Record which template versions were used in the downstream contract.

Template selection is advisory until all preconditions are checked. Never force an approximate template onto a different topology.

## First composition-case record

The rectangular-prism bundle at the legacy path
`assets/atomic-cases/001-rectangular-prism/` proves one complete four-stage
case. It is not an atomic-operation chain and none of its part-shaped steps is
registered as an atom. Its controlled V21 execution, native save/reopen,
independent measurement, and multi-view review remain valid only for the exact
case artifacts and parameters recorded there.

The original action-level modeling pilot candidates were:

1. `modeling_strategy_scripting.extrude-planar-profile`
2. `modeling_strategy_scripting.translate-body`

Each has its own parameterized V21 `.scscript`, preconditions, postconditions,
failure boundary, and exact-version evidence. Neither depends on the other. A later
composition case may order them as `extrude -> translate`, but that order is a
recipe owned by the case, not a dependency or a third atomic operation.

The three earlier geometry-understanding drafts remain as unregistered
migration material. P0 removes them from the registry because they span
multiple actions. Their schemas and fixtures may inform later action-level
templates, but they are not a granularity model or selectable capability.

## Compatibility baseline

Use these gates throughout v0.3 development:

- Existing input types must still enter the complete workflow without a registry match.
- Existing prompts and reference routes must remain usable.
- Existing `.scscript` audit, packaging, runtime-report validation, and report-comparison tools must keep their v0.2 behavior unless a versioned migration is intentional.
- Existing execution entry-state, clean-copy, safe-save, semantic-selection, topology-refresh, and evidence-boundary rules must remain in force.
- Representative v0.2 cases must still pass their host-side checks without being rewritten around the registry.
- An atomic template may advertise only the evidence level actually attached to its exact version and artifact.

## v0.2 capability migration inventory

Migrate behavior, not whole case scripts. Keep each candidate out of the registry until it has a contract-valid template file and its declared evidence is attached to that exact version.

### Direct host-tool template extraction

These deterministic tools have host-side test coverage and form the initial `active` atomic-template set. Their evidence remains `host_checked`; none of these entries proves SpaceClaim execution:

| Stage | Candidate operation | Existing artifact | Migration boundary |
|---|---|---|---|
| Modeling strategy and scripting | Package a deterministic `.scscript` with caller-supplied numeric API metadata (default 21) | `scripts/package_scscript.py` | Packaging structure and metadata preservation only; target-runtime compatibility and SpaceClaim execution remain untested |
| Modeling strategy and scripting | Audit a `.scscript` archive | `scripts/audit_scscript.py` | Static archive and policy checks only |
| Validation and visual review | Validate one structured runtime report's schema and internal invariants | `scripts/validate_runtime_report.py` without `--contract` | Validates declared structure only on the host |
| Validation and visual review | Compare one structurally valid runtime report with one contract | `scripts/validate_runtime_report.py --contract` | Compares declared measurements and boundaries on the host |
| Validation and visual review | Compare forward and native-reopen reports | `scripts/compare_runtime_reports.py` | Compares recorded persistence fields; does not independently observe the run |

### Candidate template extraction (historical migration inventory)

The table below records the original extraction plan, not the current count of
implemented candidates. P1–P5 now map all 139 catalog actions to contracts:
5 original host-active operations and 134 candidates. See the registry and each
template's exact-version evidence for current maturity. Controlled runtime or
navigation evidence covers only the variants recorded; it does not activate a
candidate or validate every possible input. The four-stage handoff and fallback
rules are operationalized in [workflow-integration.md](workflow-integration.md).

Create contract-valid, case-neutral artifacts before registration. Reset stronger evidence to `not_tested` whenever extraction changes the exact artifact that previously ran.

| Stage | Candidate operation family | Existing source | Required promotion work |
|---|---|---|---|
| Geometry understanding | Split the broad observation draft into source, view, primitive, profile, feature, relation, symmetry, and repetition actions | Unregistered migration draft `geometry_understanding.extract-geometry-observations` | Preserve its schema and fixtures only as migration inputs; build and evaluate separate action-level operations before registration |
| Geometry understanding | Split the broad dimension draft into extraction, normalization, derivation, and relationship checks | Unregistered migration draft `geometry_understanding.reconcile-dimensions` | Preserve its fixtures only as migration inputs; evaluate each replacement independently before registration |
| Geometry understanding | Split frame definition from source-view mapping | Unregistered migration draft `geometry_understanding.define-coordinate-frame` | Preserve its fixtures only as migration inputs; evaluate each replacement independently before registration |
| Modeling strategy and scripting | Centralize parameters, choose a construction order, and bind target versions | `prompts/modeling_strategy_planner.md`, `prompts/spaceclaim_script_writer.md`, and `references/spaceclaim-scripting-rules.md` | Split broad planning guidance into operations with observable postconditions |
| Modeling strategy and scripting | Select and name geometry semantically | `assets/templates/spaceclaim-v21-semantic-helpers.py` | Package a formal reusable artifact and obtain exact-version evidence for each claimed API path |
| Modeling strategy and scripting | Extrude one planar profile | Registered candidate `modeling_strategy_scripting.extrude-planar-profile` | Host packaging and action-isolation checks pass; run and independently measure the exact template before activation |
| Modeling strategy and scripting | Translate one semantic body | Registered candidate `modeling_strategy_scripting.translate-body` | Host packaging, semantic-refresh, and action-isolation checks pass; run and independently measure the exact template before activation |
| Modeling strategy and scripting | Apply other topology-safe construction and finishing actions | Public case implementations and `references/modeling-patterns.md` | Extract one action per template without case dimensions or names, isolate version-sensitive calls, and rerun exact templates |
| Execution and recovery | Split the clean-design execution transaction into authorization, session, entry-state, loading, single-run, wait, and terminal-state actions | Unregistered migration draft `execution_recovery.execute-script-in-clean-design` and `references/execution-workflow.md` | Define independent observable inputs and outputs before registering any execution action |
| Execution and recovery | Classify the earliest failure and apply a minimal repair | `prompts/script_debugger.md` and `references/failure-recovery.md` | Define failure identifiers, safe states, and clean-rerun rules per reusable operation |
| Validation and visual review | Emit a read-only geometry report | `assets/templates/spaceclaim-v21-geometry-audit.py` | Current host checks prove syntax and package policy only; obtain exact runtime evidence before stronger claims |
| Validation and visual review | Perform multi-view visual acceptance | `references/visual-interaction.md` and `prompts/validation_reviewer.md` | Define view coverage and per-image evidence while retaining interactive calibration and unresolved occlusion |

### Preserve as generic fallback

Keep a capability in the generic planner, writer, debugger, or reviewer when it lacks a case-neutral artifact, has target-dependent preconditions that are not yet encoded, or has only conditional evidence. This includes broad strategy choice, uncommon construction sequences, topology-dependent Boolean classification, interactive viewport behavior, and any operation whose exact extracted template has not been checked.

### Keep in case bundles

Keep example dimensions, object and group names, numeric tolerances, one-off feature order, and rare topology repairs in their public case bundles. A case run may motivate a candidate template, but its runtime result does not automatically validate a generalized template with different bytes or scope.

## Evidence taxonomy compatibility

Keep the v0.2 runtime-report schema unchanged during v0.3 migration. Map fields only when their meaning is exact:

| v0.3 operation-template layer | v0.2 runtime-report field | Compatibility rule |
|---|---|---|
| `design_only` | none | Keep in the template contract; never emit it as runtime evidence |
| `host_checked` | `static_archive` only for a static archive check | Other host checks, such as report validation or comparison, have no direct v0.2 field and must retain their own host-only result |
| `spaceclaim_execution` | `spaceclaim_execution` | Direct mapping only for the exact executed `.scscript` |
| `geometry_measurements` | `geometry_measurements` | Direct mapping only for measurements emitted or independently observed for the exact model |
| `native_save` | `native_save` | Direct mapping |
| `native_reopen` | `native_reopen` | Direct mapping |
| `visual_review` | none | Keep in the acceptance contract and per-view evidence record |
| `requested_export` | `neutral_export` when the requested export is neutral format | Do not map an unperformed or differently scoped export |

Do not automatically translate a generic `host_checked` result into `static_archive`, or a screenshot into `visual_review`. Preserve `failed`, `not_tested`, and `not_applicable` explicitly in the operation template even when the older report has no corresponding field.

## v0.3 evidence and regression gates

Apply all gates before a v0.3 release:

1. Validate every registered template, registry, and host-check evidence record against their schemas, then run `scripts/validate_operation_registry.py` for cross-entry and exact-evidence checks.
2. Reject duplicate operation identifiers, missing dependencies, dependency cycles, stage mismatches, absolute artifact paths, and missing linked artifacts.
3. Run all existing v0.2 host-side tests unchanged, then run v0.3 architecture and registry tests.
4. Run the official Skill validator after structural changes.
5. Confirm representative full-chain requests still work with the registry unavailable or with no matching operation.
6. Track `design_only`, `host_checked`, SpaceClaim execution, geometry measurement, native save, native reopen, visual review, and requested export evidence separately.
7. Bind each registry entry to the exact template bytes with `template_sha256`, and bind evidence to the exact template version and artifact hashes. Reset invalidated layers after any material edit.
8. Require controlled SpaceClaim reruns only for templates that claim runtime-dependent layers; do not infer them from host checks or earlier case scripts.

## Extension-stage protocol

Keep the four core stages stable while allowing optional stages before, between, or after them. Record extension hooks separately from `stages` in `operation-registry.json`; do not add an extension name to an atomic operation's four-stage `stage` enum.

Every extension stage must declare:

```text
extension_id
status
purpose
entry_from
input_contract
output_contract
reentry_stage
bypass_core_stages
contract_path
```

Apply these rules:

- Require `bypass_core_stages` to remain `false`.
- Normalize extension output into the declared core-stage input contract before normal routing resumes.
- Keep a reserved extension inactive until a versioned contract and implementation exist.
- Treat learned procedures as `candidate` operation templates. Promote them only through the normal schema, host-check, exact-artifact, runtime, persistence, and visual-evidence gates.
- Extract semantic geometry intent, SpaceClaim operations, parameters, and failure conditions. Do not generalize raw mouse coordinates, recorded `FaceN` or `BodyN` aliases, timing artifacts, or unexplained UI sequences.
- Use only authorized source material. Do not publish a raw video, screen recording, embedded model, visible path, or user data without redistribution rights and a privacy review.

Each core stage also retains an internal optimization slot without changing its handoff contract:

| Core stage | Examples of future extensions | Required normalized output |
|---|---|---|
| Geometry understanding | Video, screen-recording, multi-view, depth, or new drawing parsers | Geometry contract |
| Modeling strategy and scripting | New atomic construction patterns, version adapters, or demonstrated-operation synthesis | Build contract and formal `.scscript` |
| Execution and recovery | New controller adapters, trace alignment, state observers, or recovery instrumentation | Execution contract |
| Validation and visual review | Temporal comparison, new view planning, feature detectors, or evidence adapters | Acceptance contract |

An internal extension may enrich a stage, but it must preserve that stage's required output and exit gate.

The v0.3 registry reserves these extension points without claiming that either capability is implemented:

| Extension hook | Position | Intended future output | Core re-entry |
|---|---|---|---|
| `source.video-temporal-observation` | Before the core workflow | A temporal observation contract derived from video or screen recording, with visible before/after geometry, viewpoint changes, action/script correlations, and unresolved causality | Geometry understanding |
| `learning.demonstrated-modeling-candidate` | After a validated demonstration | A case-neutral candidate operation template or a case-specific retained procedure, with provenance and evidence boundaries | Geometry understanding |

For video or screen-recording learning, do not infer that a visible click caused a geometry change unless the action, application state, script or command, and before/after model state can be aligned. If the demonstration exposes only a special structure and not a reusable operation boundary, retain it as source-specific evidence rather than promoting it into the atomic library.

## Extension point for v0.4

Do not add composite recipes to the v0.3 atomic registry. v0.4 may compose atomic operations only after it can propagate parameters, verify preconditions and postconditions, order topology dependencies, detect conflicts, and retain the generic fallback path.
