# Geometry-understanding operation library

`stage: geometry_understanding` · `architecture: v0.3` · `template contract: 1`

## Stage contract

**Purpose** — Convert visual or textual source material into a provenance-aware, case-neutral geometry contract. This stage describes geometry; it does not choose a construction sequence or run SpaceClaim.

**Inputs**

- A source manifest (drawings, images, text, existing models, scripts, or logs).
- User intent, requested deliverables, supplied constraints, tolerances, and target release when known.
- An optional temporal-observation handoff, normalized before use.

**Outputs**

- A geometry contract containing `source_manifest`, `observed_geometry`, `bodies_and_features`, `spatial_relations`, `coordinate_system`, `dimensions_with_provenance`, `symmetry_and_repetition`, `assumptions`, `unresolved_items`, `confidence`, and `validation_intent`.
- A handoff with `handoff_status` set to `ready`, `passed`, `requires_clarification`, or `not_tested`; unknown values remain explicit.

**Exit gate**

- Observed facts, user-supplied values, inferences, and unresolved items are separated.
- A usable coordinate system is defined, or its absence is recorded as unresolved.
- Missing dimensions are not replaced by silent numeric defaults.
- Geometry is described independently of an industry-specific object label.
- The next stage receives only a current `ready` or `passed` contract.

## Active operations

No operation is active for automatic selection in this stage. Geometry interpretation remains on the generic v0.2 workflow until a candidate passes its promotion gates.

## Unregistered migration drafts

The following stage-level drafts are retained for migration analysis only.
P0 removes them from the atomic registry because each spans several
interpretation actions. They are never selected automatically and must be
split into action-level operations before any later registration:

| Operation | Composition outcome | Current evidence and promotion boundary |
|---|---|---|
| `geometry_understanding.extract-geometry-observations` (`unregistered draft`, `0.2.0`) | Produce provenance-tagged primitives, features, relations, symmetry/repetition cues, confidence, and unresolved interpretations without choosing a construction strategy. | Existing schemas and fixtures remain migration evidence only; the draft must be split before registration. |
| `geometry_understanding.reconcile-dimensions` (`unregistered draft`, `0.2.0`) | Reconcile dimension statements into accepted, derived, conflicting, and unresolved values with units, scope, and source provenance. | Existing fixtures remain migration evidence only; extraction, normalization, derivation, and conflict checks require separate operations. |
| `geometry_understanding.define-coordinate-frame` (`unregistered draft`, `0.2.0`) | Define origin, axes, handedness, units, and source-view mapping while retaining unsupported choices as unresolved. | Existing fixtures remain migration evidence only; frame definition and view mapping require separate operations. |

These exact legacy draft versions remain unregistered. P2 introduces the
separate action contracts below; it does not inherit their old fixture evidence.
Case-specific dimensions, labels, and uncommon topology decisions stay in cases.

## Registered action candidates

GU-01 through GU-20 now have individual `0.3.1` contracts under
`assets/operation-templates/geometry-understanding/atoms/`. Select the matching
catalog entry for its registry ID. Read the selected action in
[geometry-understanding-atomic-guidance.json](geometry-understanding-atomic-guidance.json)
and follow [atomic-reasoning-protocol.md](atomic-reasoning-protocol.md).
Each invocation yields one typed action result with field-level provenance,
not a complete geometry contract. Source interpretation is evaluated separately
from structural and numeric output checks.

GU-15 deliberately reuses the `define-coordinate-frame` identity at version
`0.3.1` and the new `atoms/` path. Its scope is one coherent coordinate frame;
GU-16 alone maps a view to that frame. The old `0.2.0` draft file remains a
migration artifact and supplies no promotion evidence to the replacement.

P2's bounded independent evaluation is preserved in
`assets/evaluations/p2-source-evaluation/`. Host checks pass, including 42 actual
emitted records after documented interface repairs. All new reasoning contracts
remain candidates: this small source set is not a universal interpretation claim.

## Further extraction directions

- Split source, view, primitive, profile, feature, relation, symmetry,
  repetition, dimension, frame, assumption, expected-measurement, and
  deliverable actions according to the approved operation-level plan.
- Register each replacement only after its own input, output, and evaluation
  boundary exists.

## Fallback rules

- Use the generic planner routed by `SKILL.md` when no active operation matches, a precondition is unmet, or the source is ambiguous.
- Return `requires_clarification` when an unresolved item could change geometry, coordinate orientation, construction order, or acceptance.
- Do not apply an unregistered draft or registered candidate automatically, and do not bypass this stage because a downstream script or template exists.
- Normalize video or screen-recording observations into a geometry contract before normal routing resumes.

## Promotion and evidence boundary

- Promote a candidate only after its case-neutral, single-action contract, schema-valid artifact, trigger, preconditions, postconditions, and acceptance checks are present; retain the generic v0.2 fallback.
- Use [geometry-understanding-output.schema.json](geometry-understanding-output.schema.json) and `scripts/validate_geometry_understanding_outputs.py` for the migration candidates. These checkers enforce structure and deterministic invariants only; they do not score source interpretation.
- Evidence at this stage proves interpretation and provenance only. Host checks, runtime reports, screenshots, native files, measurements, or exports do not by themselves prove that the interpreted geometry is physically correct.
- Bind any claimed evidence to the exact template version and artifact. Material edits reset affected evidence layers to `not_tested`.

## Extension slot

Reserve an internal slot for multi-view, depth, new drawing parsers, or other observation adapters. The reserved `source.video-temporal-observation` hook may enter before this stage, must set `bypass_core_stages=false`, and must re-enter here with a normalized geometry contract. No such implementation is claimed by this index.
