# Four-stage integration and fallback

Use this only when handing work between stages, resuming a partial run, or
checking that extracted operations preserve the complete modeling workflow.
It does not prescribe a fixed modeling recipe or add a fifth core stage.

For installed dependency setup and the one-time live environment check, use
[installation-and-runtime.md](installation-and-runtime.md). Use the installation's
host interpreter for checks, not a different Python selected incidentally by PATH.

## Installed paths versus maintainer evidence

Registry/template metadata paths are repository-relative. For a nested-only
Skill installation, resolve a leading `spaceclaim-vision-modeling/` relative to
the actual installed package root, not the current model's working directory.
`scripts/resolve_operation_artifact.py` implements this relocation rule and
rejects traversal. It accepts a renamed installation directory as well.

References under `tests/` are maintainer test/provenance sources, not modeling
runtime dependencies. They require the full checkout for inspection/replay.
An absent test source is not a successful verification; retain the recorded
evidence boundary and use the generic workflow if needed. The full
`validate_operation_registry.py` and `validate_operation_catalog.py` gates are
checkout-level maintenance checks, not mandatory repeated desktop preflights.
Never resolve an unavailable primary implementation by guessing a nearby path.

## Dispatch

1. Identify the earliest incomplete core stage from the available contracts.
2. Check source provenance, dimensions, units, artifact identity and the receiving
   stage's entry conditions before using an upstream result.
3. Consider only matching active operations by default. A development request
   may explicitly select a candidate for a controlled test; it remains a
   candidate afterward. Satisfy version/topology/input/evidence preconditions
   before using either lifecycle. Contract field names, not conceptual guide
   labels, are the callable interface.
4. If the registry is absent, invalid, unmatched, candidate-only for the needed
   action, or incompatible with the target, continue the generic workflow from
   `SKILL.md` at the same stage. Do not make a candidate active, choose a nearby
   example's dimensions, or skip a stage to force a template match.
5. Keep operation order, numeric parameters and cross-action object handoff in
   the consuming model plan. Refresh geometry handles after topology changes.

Fallback preserves the ability to reason, write a parameterized `.scscript`,
perform host preparation, execute after authorization, recover and validate.
It is not an assertion that an untested API or an unseen model must work.
Unresolved dimensions still return to Geometry understanding; an incompatible
API needs a compatible path or an explicit limitation, not a version-label edit.

## Resume boundaries

| Boundary | Reject or return upstream when |
| --- | --- |
| Understanding → strategy | Dimensions or frame remain unresolved, or source/geometry contract changed |
| Strategy → execution | Preflight failed, `.scscript` identity changed, API/entry policy is unavailable, or desktop control is not authorized |
| Execution → acceptance | Executed script/model cannot be identified, or a failed run requires recovery; diagnostic review is allowed but is not passed acceptance |
| Acceptance → handoff | A requested check lacks evidence, model hash differs, a relevant feature is occluded, or an unresolved risk changes acceptance |

## Host integrity helper

`scripts/validate_workflow_handoff.py` checks declared four-stage envelopes,
ordered stage identities, required completed-stage fields, artifact hashes and
upstream contract hashes. Its `passed` means **host handoff integrity only**;
it neither audits script contents nor verifies CAD or visual interpretation.
Use the dedicated package/report tools and actual observations for those tasks.

The input is a JSON object with `handoff_version: 1`, an ordered `contracts`
array and an explicit `required_evidence_layers` array for final acceptance.
Each contract uses the common envelope and stage fields in `architecture.md`,
plus a unique `contract_id`. Use `geometry_contract`, `build_contract`,
`execution_contract`, `acceptance_contract` for `contract_kind`. Identity fields
`geometry_contract_ref` and `build_contract_ref` name earlier contract IDs.

An `upstream_contract_refs` item is `{contract_id, sha256}`. Compute its digest
using `contract_sha256` from the helper (canonical JSON, not pretty-file bytes).
An artifact or evidence reference is `{path, sha256}`, relative to an explicitly
supplied artifact root; its digest is the actual file-byte SHA-256. Build and
execution script identities must match. Final artifact identity must match
execution output. For each evidence layer use `{status, evidence_refs}`.
Persisted model references must resolve to matching bytes. For an unsaved model,
use `{unsaved_document_id, observation_ref}` instead, with the separate
observation file hash-bound under the run root; this checks the declared link,
not the truth of its contents or continued liveness of the document.
Completed acceptance must keep all six runtime/persistence/visual/export layers
explicit, including unperformed layers. Requested layers must pass before an
overall `passed` result can be structurally valid.
Overall `passed` requires at least one requested layer. Use `passed`, `failed`,
`not_tested` or `needs_manual_review` for the acceptance `overall_status`.

Keep incomplete stages `draft`, `requires_clarification`, `failed` or
`not_tested`; do not invent their completed-stage fields. A ready/passed
downstream stage cannot bypass an incomplete upstream stage. Use `assumptions`
for explicitly accepted assumptions and `unresolved_items` for remaining
blocking questions. A preparation-only chain normally ends with execution and
acceptance `not_tested` and returns `execution_recovery` as `next_stage`.

```console
python scripts/validate_workflow_handoff.py handoff.json --artifact-root <run-directory>
```

This helper validates supplied declarations, including supplied required-layer
choices. It cannot decide whether those choices match the user's intent or
whether a referenced observation is true. The agent remains responsible for
that review. Do not register this cross-stage helper as an atomic modeling step.
