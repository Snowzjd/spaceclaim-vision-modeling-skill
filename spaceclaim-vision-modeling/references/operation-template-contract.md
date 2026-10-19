# Atomic operation template contract

## Contents

- [Purpose](#purpose)
- [Required fields](#required-fields)
- [Identity and lifecycle](#identity-and-lifecycle)
- [Purpose and trigger](#purpose-and-trigger)
- [Inputs and outputs](#inputs-and-outputs)
- [Implementation](#implementation)
- [Semantic selection](#semantic-selection)
- [Failure and recovery](#failure-and-recovery)
- [Dependencies](#dependencies)
- [Validation and evidence](#validation-and-evidence)
- [Granularity test](#granularity-test)
- [Promotion gate](#promotion-gate)

## Purpose

Use this contract for one reusable operation inside exactly one of the four workflow stages. An atomic operation is one modeling action or one bounded state/inspection action, not a primitive, part, feature bundle, or complete case. For example, `extrude-planar-profile` and `translate-body` are two operations even when one model uses them consecutively. The case owns their order and parameter values.

Keep an operation small enough to have one primary action, one independently observable effect, explicit preconditions, independently replaceable parameters, and a bounded recovery path. A template must not create a whole named part merely because that part is simple.

The machine-readable companion is [operation-template.schema.json](operation-template.schema.json). Register accepted templates in [operation-registry.json](operation-registry.json), whose structure is defined by [operation-registry.schema.json](operation-registry.schema.json). Validate host-check records against [operation-evidence.schema.json](operation-evidence.schema.json). Bind each registry entry to the exact template bytes with `template_sha256`; a material template edit must update the template version, evidence state, and registry hash as applicable. Run `scripts/validate_operation_registry.py` from the repository root after any registry, template, dependency, artifact, or evidence change. The validator uses Python `jsonschema` Draft 2020-12 support and fails closed when that dependency or any required schema is unavailable.

## Required fields

Every atomic operation template must declare:

```text
operation_id
template_version
contract_version
status
stage
purpose
trigger
inputs
preconditions
outputs
postconditions
implementation
semantic_selection
failure_modes
recovery
validation
dependencies
evidence_level
artifact_links
```

### Identity and lifecycle

- `operation_id`: Stable, case-neutral identifier using `<stage>.<operation>` form. Never include a case number, part name, dimension, or recorded `FaceN`/`BodyN` alias.
- `template_version`: Semantic version of this template. Increment it when behavior, inputs, outputs, or validation change.
- `contract_version`: Version of this field contract. v0.3 starts at `1`.
- `status`: `candidate`, `active`, or `deprecated`. Only `active` templates may be selected automatically.
- `stage`: One of `geometry_understanding`, `modeling_strategy_scripting`, `execution_recovery`, or `validation_visual_review`.

### Purpose and trigger

- `purpose`: State one outcome, not a broad workflow.
- `trigger`: State observable conditions that make the operation relevant. Do not use an industry label as the only trigger.

### Inputs and outputs

Declare each field with `name`, `type`, `required`, and `description`. Use `provenance_required` on inputs when a value must distinguish observation, user input, inference, or measurement.

- `inputs`: Values or artifacts consumed by the operation.
- `outputs`: Values or artifacts produced by the operation.
- `preconditions`: Conditions that must be true before execution. Include target-version and geometry-state constraints where relevant.
- `postconditions`: Observable conditions that must be true after success.

Do not hide an input in implementation prose. Do not declare a postcondition that the operation does not check.

Parameter values belong to the consuming case or build contract. A reusable template may declare required configuration placeholders and tolerances, but it must not embed a demonstration case's dimensions, body names, feature count, or part semantics.

- `output_schema`: Optionally bind a machine-readable output contract by repository-relative path and SHA-256. Use it when free-form field descriptions are insufficient to validate the handoff.
- `host_checker`: Optionally bind a deterministic host-side evaluator by repository-relative path and SHA-256. For a reasoning-guidance operation with no primary implementation artifact, use this field to check emitted contract structure and invariants without claiming that the reasoning itself or its source interpretation is correct.

### Implementation

- `implementation`: Declare how the operation is performed and which environment and artifact it requires.

Declare:

```text
mode
primary_artifact
target_environment
topology_effect
determinism
```

- `mode`: `reasoning_guidance`, `spaceclaim_scscript`, `host_tool`, `computer_use`, or `hybrid`.
- `primary_artifact`: Repository-relative path when a reusable artifact exists; otherwise `null` with a reason in `notes`.
- `target_environment`: Supported SpaceClaim/API/Python constraints, or `not_applicable`.
- `topology_effect`: `none`, `creates`, `modifies`, `deletes`, or `unknown`.
- `determinism`: `deterministic`, `bounded_heuristic`, or `interactive`.

When `mode` produces or runs SpaceClaim code, the formal executable artifact must be `.scscript`. A `.py` companion may be linked only as editable or packaging source.

### Semantic selection

- `semantic_selection`: Declare how geometry objects are resolved and refreshed, or state explicitly that selection is not required.

Declare whether geometry selection is required. When it is required, list the semantic criteria, ambiguity checks, and topology-refresh rule. Use direction, position, normal, area, bounding box, volume, geometry type, topology, or adjacency as appropriate. Never promote recorded numbered aliases or Boolean return order into reusable selection logic.

After `topology_effect` is `modifies` or `deletes`, require re-enumeration before the next selection unless the template proves a stable created-object reference for the exact API operation.

### Failure and recovery

- `failure_modes`: Give each expected failure a stable identifier, detection condition, and safe state.
- `recovery`: Map a failure identifier to the smallest repair or safe stop. State whether a clean rerun is required.

Do not prescribe repeated GUI attempts as recovery when the failing state can be diagnosed from the script, runtime report, or geometry contract.

### Dependencies

- `dependencies`: List only operation identifiers whose declared outputs are required as inputs. Keep the list empty when the operation is independent. Do not use dependencies to create a hidden composite recipe.

### Validation and evidence

- `validation`: List the check, method, expected result, and evidence layer for each claimed postcondition.
- `evidence_level`: Repeat the exact top-level `template_version` and record every independently separable layer as `passed`, `failed`, `not_tested`, or `not_applicable`. Required layers are `design_only`, `host_checked`, `spaceclaim_execution`, `geometry_measurements`, `native_save`, `native_reopen`, `visual_review`, and `requested_export`. A `passed` or `failed` layer must attach at least one repository-relative evidence path and SHA-256; an untested or inapplicable layer must not attach evidence. A host-check record under `assets/operation-templates/evidence/` must identify the same operation and template version, reproduce the same layer states, and hash-bind its tool and test artifacts.
- `artifact_links`: Link repository-relative templates, scripts, references, tests, or public evidence. Give each link a role.

When `host_checker` is present, link it with role `evaluation`. When `output_schema` is present, link it with role `reference`. Bind fixture manifests and tests as hashed test artifacts when they support `host_checked` evidence.

Evidence is monotonic only for the exact artifact checked. Editing a runtime-observed template creates a new version whose affected evidence layers return to `not_tested` until their checks are rerun.

## Granularity test

Keep the operation atomic only when all answers are yes:

1. Does it perform exactly one main modeling, state, or inspection action?
2. Does success produce exactly one independently observable geometry or state effect?
3. Can its inputs and postconditions be stated without naming a case, primitive, part, or fixed dimension?
4. Can the operation be parameterized, replaced, tested, and recovered independently of the surrounding recipe?
5. Can another operation consume its outputs through the declared contract?
6. Can its evidence level be assessed independently?

If an item fails, split the operation or keep the logic in a composition case until a reusable action boundary is understood. A case such as a rectangular prism, flange, shaft, or support is never itself evidence that the same-named reusable atomic operation exists.

### Composition boundary

- The atomic registry contains actions, not recipes.
- A composition case contains source interpretation, parameter values, an ordered list of atomic operation identifiers, the assembled runnable `.scscript`, and case evidence.
- A composition may call `create-profile -> extrude-planar-profile -> translate-body`; it must not register that chain as one new atom.
- Running a composition validates that exact sequence and parameter set. It does not automatically promote any generalized atomic template.

## Promotion gate

Promote a candidate to `active` only when:

- its schema validates;
- its trigger and preconditions are case-neutral;
- its implementation and validation artifacts are present;
- host checks pass when applicable;
- any claimed SpaceClaim runtime, persistence, or visual layer is bound to the exact template version;
- the generic v0.2 fallback still succeeds when the template is unavailable.

Deprecation must name a replacement or state that callers should use the generic workflow.
