# Single-action reasoning protocol

Use one matching registered template at a time. The case chooses the sequence
and supplies operation inputs; no fixed part or end-to-end recipe is hidden in
an atom. Candidate use is explicit development/evaluation only, never automatic
selection. Keep the generic workflow available.

Read only the selected `catalog_id` entry linked by the indexes
[geometry-understanding-atomic-guidance.json](geometry-understanding-atomic-guidance.json)
or [strategy-atomic-guidance.json](strategy-atomic-guidance.json). Each points to
one independent file under `references/atomic-guidance/`; editing one action's
guidance does not invalidate other actions' guidance evidence. To retrieve
only that action, run `scripts/validate_atomic_reasoning.py --describe GU-03`
(replace the ID). Its named
inputs, typed result fields, procedure and rejection rules form the action's
implementation. A result is one record, not an entire geometry contract.

Emit [atomic-reasoning-output.schema.json](atomic-reasoning-output.schema.json):
`contract_version: 1`, the catalog/instance IDs, `status`, `data`, `provenance`
and `unresolved`. `data` has exactly the selected action's result fields. Use
`null` for unsupported fields; list their clarification need. For a truly
inapplicable field (such as a fillet's chamfer angle), use `null` plus an entry
in optional `not_applicable: [{field, reason}]`; do not use this to conceal an
unknown required dimension. Distinguish a
resolved finding of a conflict from a usable model specification: GU14 may
resolve that a relation conflicts, but the consuming case must stop the
affected geometry handoff.

Each data field has exactly one provenance owner. `source_refs` identifies raw
source regions, text clauses, or prior operation instance IDs supplied in the
case's source manifest. The checker cannot inspect source pixels or guarantee
truth of a reference. Never use a generated expected answer as source evidence.
An explicit modeling coordinate convention may be chosen when it does not
alter geometry, with `kind: convention`; it is not an observed datum. Missing
shape-changing dimensions cannot be resolved by such a convention.

Run `scripts/validate_atomic_reasoning.py result.json --sources manifest.json`.
The manifest has a `sources` array of records with unique `id`, `kind`, and
`locator`. A manifest locator is either a nonempty string or a nonempty object
of nonempty string fields, such as `{path, region}`. GU-02's action result
retains its structured locator object. Known source kinds are image, drawing, text, model, script, log,
operation and api_reference. Referenced prior operation records must actually
be supplied by the case. The check is read-only and enforces field types,
source membership, unresolved propagation and supported numeric invariants;
it does not establish correct image interpretation or API compatibility.

`handoff_blockers(results, required_instance_ids)` checks a case's explicit
required-action set. Omit that set to conservatively require all supplied
results. Keep optional camera matching outside the required geometry set when
the user does not request that camera; never exclude a dimension or feature
needed to define the requested solid. A `GU-14` conflict, `GU-18` blocking issue
or failed parameter constraint blocks its dependent build even when the finding
itself was recorded successfully. MS-02 uses canonical `passed`/`failed` verdicts;
the checker also accepts equivalent `pass`/`fail` values without changing the
recorded evidence. Neither spelling can invert the actual comparison.

Independent source evaluation must give the interpreter raw material and the
candidate guidance without the scoring key. Preserve raw inputs, emitted
results, reviewer observations and tested operation IDs. Missing visual access
is an unperformed visual test, not a successful text substitute. Promote only
the exact tested scope; do not transfer case evidence to untested actions.
