# Execution-and-recovery operation library

`stage: execution_recovery` · `architecture: v0.3` · `template contract: 1`

## Stage contract

**Purpose** — Execute an accepted, exact `.scscript` in an authorized SpaceClaim session and recover from the earliest diagnosed failure without contaminating the baseline. This stage is the runtime boundary; host preparation alone is not execution evidence.

**Inputs**

- An accepted build contract and its hash-identified `.scscript` artifact.
- Run-scoped desktop authorization, verified entry state, and run-owned output paths.
- Failure classification, safe-stop, and recovery rules.

**Outputs**

- An execution contract containing `build_contract_ref`, `entry_state_observed`, `executed_artifact_identity`, `stage_events`, `runtime_report`, `model_artifact`, `failure_state`, `recovery_actions`, `save_state`, and `unresolved_runtime_risks`.

**Exit gate**

- A no-baseline run starts in a new unsaved design; a supplied baseline is used only through a hash-recorded copy.
- The exact executed artifact, result, and earliest incorrect state are recorded.
- A critical assertion stops the run before save; the smallest repair is applied and rerun from a clean entry state.
- A declared runtime report is not treated as independent observation by itself.

## Active operations

No active operations are registered for this stage. Runtime control and recovery remain the generic, authorization-gated v0.2 workflow.

## P4 action candidates

EX-01–14 and ER-01–12 have separate action guidance and contracts. Resolve a
selected operation through the catalog and registry; load only its
`references/atomic-guidance/ex-XX.json` or `er-XX.json` resource (lowercase file
names). A guidance artifact is an instruction to an available controller or
reasoning agent, not an autonomous controller and not proof of desktop success.

Host-side file and event actions use `scripts/execution_host_actions.py`. They
validate supplied identities and evidence; they cannot authorize a run or infer
an actual desktop event from a JSON declaration. GUI actions must still observe
the intended session and obey the controller's observation/confirmation rules.

EX-14 also provides a V21 `.scscript` implementation of one native-save action.
Its new-output variant consumes the asserted current root, completed critical
checks, a run-owned directory and a new `.scdoc` path. It rejects wrong models,
failed or incomplete checks, existing files and reparse-point ancestors before
saving. It does not support overwriting a baseline copy or reopening the output.
Its exact save and failed-check guards have separate test evidence; this does
not validate all other EX/ER controller procedures.

Recovery operates on one diagnosed failure. A generated patch or selected
repair is not a successfully repaired model until the corresponding execution
and measurement checks pass. Preserve confirmed dimensions and identities;
reject unknown causes and unresolved semantic ambiguity. For unsupported local
repairs use the generic debugger or request a targeted demonstration.

## Unregistered transaction draft

`execution_recovery.execute-script-in-clean-design` (`unregistered draft`, `0.1.0`)
records the earlier transaction design: confirm a maximized matching SpaceClaim session,
a new unsaved design with no bodies, no blocking dialog, exact script identity,
run-owned outputs, and current authorization; then load and run the exact
`.scscript` once and record the earliest terminal state. P0 removes this draft
from the atomic registry because authorization, session confirmation, entry
state, script loading, one execution event, waiting, and terminal-state capture
are independently observable actions. Its retained file is migration material,
not an automatically selectable operation or runtime claim.

## Candidate families (mature v0.2 extraction directions)

- **Safe entry-state preparation and gated script run** — Separate observable entry, run, completion, and save states from `references/execution-workflow.md`; define clean-design or baseline-copy policy, run-once behavior, and run-owned paths without encoding UI coordinates.
- **Earliest-failure classification and minimal repair** — Extract stable failure identifiers, detection conditions, safe states, smallest repairs, and clean-rerun requirements from `prompts/script_debugger.md` and `references/failure-recovery.md`; do not turn repeated GUI attempts into recovery logic.

Candidate families are directions for extraction, not active runtime capabilities. A case run or a declared report does not by itself validate a generalized controller.

## Fallback rules

- Use the generic authorized workflow routed by `SKILL.md` when no active operation matches, the target environment or controller is unsupported, or an entry precondition is unmet.
- Confirm application, document, blocking-dialog status, intended baseline policy, and maximized/full-screen workspace at the entry gate; keep the control transaction short and deterministic.
- Run once and wait for a meaningful completion or exact error. Never press Run again while completion is uncertain or continue from a partially modified model.
- On failure, preserve the report and earliest incorrect state, patch only the responsible stage, and restart from a new design or clean baseline copy. Save only after critical assertions pass.

## Promotion and evidence boundary

- Promote a candidate only after a case-neutral artifact declares target environment, entry/exit states, failure identifiers, recovery, and validation; schema and host checks must pass and the generic fallback must remain usable.
- A controlled SpaceClaim rerun is required for `spaceclaim_execution` claims. Runtime reports, host scripts, screenshots, or GUI instructions cannot substitute for direct observation.
- Native save, native reopen, geometry measurements, visual review, and requested export remain separate evidence layers bound to the exact artifact and run; material changes reset affected layers to `not_tested`.

## Extension slot

Reserve a per-stage slot for controller adapters, trace alignment, state observers, or recovery instrumentation. Extensions must normalize to the execution contract, preserve `bypass_core_stages=false`, and return through normal validation. No extension implementation or runtime success is claimed by this index.
