# Modeling-strategy-and-scripting operation library

`stage: modeling_strategy_scripting` · `architecture: v0.3` · `template contract: 1`

## Stage contract

**Purpose** — Turn an accepted geometry contract into one version-bound build contract and a formal executable `.scscript` artifact. This stage plans and audits construction; it does not authorize or perform the SpaceClaim run.

**Inputs**

- A current `ready` or `passed` geometry contract.
- Target SpaceClaim release, scripting API version, and Python runtime.
- Entry-state policy, requested output contract, applicable templates, and their evidence levels.

**Outputs**

- A build contract containing `geometry_contract_ref`, `parameter_table`, `construction_strategy`, `ordered_operation_plan`, `topology_dependencies`, `semantic_selection_plan`, `failure_checkpoints`, `validation_plan`, `target_environment`, `entry_state_policy`, `output_policy`, `scscript_artifact`, optional `source_artifact`, `host_preflight_result`, and `unresolved_risks`.
- A formal `.scscript`; an editable or packaging `.py` companion is optional.

**Exit gate**

- Parameters and units are centralized and valid; one primary stable construction strategy is selected.
- Semantic re-selection is specified after every topology-changing operation.
- Version-sensitive calls are bound to the target environment.
- The `.scscript` and validation plan exist before execution is requested.
- Critical assertions occur before save, and unresolved risks remain explicit.

## Active operations

These are the only active entries in this stage. Both are host tools; neither claims SpaceClaim execution or geometry correctness.

| Operation | Host tool and bounded outcome | Evidence boundary |
| --- | --- | --- |
| `modeling_strategy_scripting.package-scscript` (`active`, `0.1.1`) | `scripts/package_scscript.py` packages UTF-8 source with caller-supplied numeric API metadata into a deterministic `.scscript` archive and protects existing output unless replacement is explicit. | `design_only` and `host_checked` for package structure/metadata; no application runtime, geometry, save/reopen, visual, or export evidence. |
| `modeling_strategy_scripting.audit-scscript` (`active`, `0.1.1`) | `scripts/audit_scscript.py` performs static archive, API-marker, unsafe-path, and recorded-alias policy checks while preventing its JSON report from overwriting the input archive. | `design_only` and `host_checked` for the static audit only; an audit cannot prove script execution or model validity. |

## Registered action candidates

MS-01 through MS-09 have individual `0.3.1` reasoning contracts under
`assets/operation-templates/modeling-strategy-scripting/atoms/`. Their explicit
inputs, result fields, procedures and rejection rules are in
[strategy-atomic-guidance.json](strategy-atomic-guidance.json); use
[atomic-reasoning-protocol.md](atomic-reasoning-protocol.md) for their outputs.
They declare one parameter, constraint, method, dependency, version binding,
selector, refresh point, assertion or output path per invocation. They do not
execute application actions. MS-10 and MS-11 remain the existing host tools.

MA-01 through MA-35 use independent V21 `.scscript` artifacts under
`assets/operation-templates/modeling-strategy-scripting/actions/`. Resolve each
contract through the registry; do not infer its interface from its catalog label.
Each invocation consumes `ATOMIC_INPUT` and returns `ATOMIC_OUTPUT`. The caller
owns operation order, configuration, document entry, and final acceptance.

The current implementations have exact-artifact runtime checks for their bounded
variants. Inspect each contract's evidence rather than assuming that a passing
group covers all parameter ranges or that all groups in an older suite passed.
Native persistence, complete visual agreement, and export are not established by
these action tests. Runtime-tested candidates are not automatically active.

Important interface boundaries:

- MA-01/02/03 produce in-memory reference geometry, not persistent datum objects.
- MA-06 extrudes a supplied profile to a transient kernel body; MA-12 attaches a
  supplied transient body to the design. Profile creation remains separate.
- MA-14 translates a current root design body. MA-16 rotates a supplied transient
  kernel body in place; it does not attach that body or edit component occurrences.
- MA-18/19 return independent transient copies, not associative native patterns.
- MA-25 extracts an already enclosed region and returns a component body
  occurrence. It does not cap or repair an open boundary.
- MA-27 is equal-distance chamfering; the resulting angle depends on adjacent
  face geometry and is not universally 45 degrees.
- MA-35 imports a hash-verified native, non-nested component and returns component
  occurrences. It does not implement foreign-format options or unit overrides.

For a component occurrence, measure its world-space `Shape`; inspect kernel
topology through its concrete `Master.Shape`. A concrete root `DesignBody` does
not expose the same public `Master` accessor. Do not pass an occurrence into a
root-only mutation action. Re-resolve the required geometry explicitly or use the
generic workflow when the available variant does not fit.

## Candidate families (further v0.2 extraction directions)

- **Parameter centralization, construction order, and target-version binding** — Extract bounded planning operations from `prompts/modeling_strategy_planner.md`, `prompts/spaceclaim_script_writer.md`, and `references/spaceclaim-scripting-rules.md`; require observable postconditions rather than a broad recipe.
- **Semantic geometry selection and topology refresh** — Package reusable selectors based on position, direction, normal, area, bounding box, volume, topology, or adjacency from `assets/templates/spaceclaim-v21-semantic-helpers.py`; reject zero or multiple matches and reacquire objects after topology mutation.
- **Topology-safe construction and finishing actions** — Extract one operation at a time from stable primitive, transform, pattern, Boolean, split, and analytic-feature implementations; keep version-sensitive calls isolated and uncommon sequences case-specific.

Candidate families are not automatically selectable and carry no runtime claim until an exact, case-neutral artifact is checked.

## Fallback rules

- Route to the generic v0.2 planner/writer through `SKILL.md` when no active operation matches, a precondition or target version is unsupported, or the template conflicts with the geometry contract.
- Keep the `.py` source as packaging input only; the executable deliverable remains a version-matched `.scscript`.
- Do not compose candidate operations into a hidden recipe, reuse stale object handles, rely on recorded numbered aliases, or continue after an unmet assertion.
- Preserve the stage contract and return `requires_clarification` when parameters, topology dependencies, or output policy are incomplete.

## Promotion and evidence boundary

- Promote a candidate only after schema validation, case-neutral triggers/preconditions, present artifacts, applicable host checks, and a working generic fallback.
- Host package or audit evidence is static and must not be upgraded to SpaceClaim execution, geometry measurement, native persistence, visual review, or export evidence.
- Any runtime or persistence claim must be rerun and hash-bound to the exact template version and `.scscript`; edits reset affected evidence layers to `not_tested`.

## Extension slot

Reserve a per-stage slot for new atomic construction patterns, version adapters, or demonstrated-operation synthesis. An extension must emit a complete build contract and formal `.scscript`, preserve `bypass_core_stages=false`, and rejoin normal execution and validation gates. No learned or controller-generated operation is active here.
