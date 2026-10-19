# P4 independent atomic-guidance evaluation

Evaluated on 2026-09-08 using the frozen synthetic input set in
`runs/p4-independent/raw-inputs.json` (SHA-256
`aabef50fb9f00315ad2bf3eee4bbb482f9be24552e26b944db850b135fa6ce9d`) and the
26 versioned files in `spaceclaim-vision-modeling/references/atomic-guidance/`.
Each case was evaluated against its own `procedure` and `rejection_rules`;
inputs were not repaired before evaluation.

This is an offline guidance application. No SpaceClaim session, GUI, host
filesystem, native save/reopen, deletion, or script execution was performed.
`plan_ready` therefore means “one bounded action plan can be emitted”, not
that the action happened. Hashes and before-states in the synthetic fixtures
are claims supplied to the evaluator, not independent runtime evidence.

## Outcome summary

| Scope | plan_ready | observed_in_input | blocked_or_rejected | uncertain | needs_manual_review |
|---|---:|---:|---:|---:|---:|
| EX-01..EX-14 | 1 | 1 | 4 | 1 | 7 |
| ER-01..ER-12 | 8 | 0 | 0 | 0 | 4 |
| Total | 9 | 1 | 4 | 1 | 11 |

The single `observed_in_input` result is EX-06: the supplied document ID,
type, path, and modified marker match the expected identity while the script
label is correctly ignored. It is not a host observation.

## Per-action results

| ID | Outcome | Behavior / bounded result | Refusal or uncertainty boundary |
|---|---|---|---|
| EX-01 | needs_manual_review | No authorization status is granted. | No issuer, validity, application, artifact, or action-scope record; no self-authorization. |
| EX-02 | needs_manual_review | No session is selected. | Two V21 candidates match; no focus/click by recency or title. |
| EX-03 | plan_ready | One maximize-and-reobserve plan for `window-v21-a`. | Final bounds/state are not observed; no bundled document/script action. |
| EX-04 | blocked_or_rejected | Blank-design creation is blocked. | Modified user work and non-idle session violate the safe clean-entry gate. |
| EX-05 | blocked_or_rejected | No copy is attempted. | Source is explicitly unavailable; a claimed hash is not readable-source evidence. |
| EX-06 | observed_in_input | Input-level model-document match; script label ignored. | Hash is absent and no host observation is claimed. |
| EX-07 | blocked_or_rejected | No accepted output path. | `run_output` and `evidence` collide and overwrite is forbidden. |
| EX-08 | needs_manual_review | Run gate remains closed; no load is issued. | Readability/package/hash/document-binding checks are not independently supplied. |
| EX-09 | needs_manual_review | No Run command is issued. | Session and loaded-for-document binding/idle evidence are incomplete. |
| EX-10 | uncertain | Terminal state is `unknown` after the stated timeout; no retry. | No terminal event exists; timeout is not success or failure. |
| EX-11 | needs_manual_review | No executed-artifact identity is promoted. | Only claimed hashes/report binding are supplied; actual bytes are unavailable. |
| EX-12 | needs_manual_review | No earliest failure is promoted. | Chronology exists but records have no `run_ref`; `e-01` remains only a candidate. |
| EX-13 | blocked_or_rejected | Caller save gate receives `blocked`; no saver/deleter call. | Critical body-count assertion failed while save was still pending. |
| EX-14 | needs_manual_review | No native save result or hash is emitted. | Required `expected_root` and `run_root` identities are missing. |
| ER-01 | needs_manual_review | No failure category or repair is emitted. | Category names lack versioned evidence predicates. |
| ER-02 | plan_ready | One V21 replacement: `Component.CreateFromFile(root, source_path, options)`. | Static signature correction only; execution is not claimed. |
| ER-03 | plan_ready | One Unicode path/`io.open(..., 'rb')` encoding correction, same path/hash. | Placeholder path and interpreter behavior are not executed. |
| ER-04 | plan_ready | One semantic selector using parent, geometry type, and bbox plus uniqueness assertion. | Candidate selection is not run on a model. |
| ER-05 | plan_ready | One `body.Faces` re-enumeration immediately after mutation, before `seed_face`. | Downstream topology result is not claimed. |
| ER-06 | needs_manual_review | No Boolean result is selected. | Expected relation has no tolerance; `result[0]` is forbidden. |
| ER-07 | needs_manual_review | Defect and preservation checks are recorded; no repair call guessed. | Selected mode has no known target-version repair signature. |
| ER-08 | plan_ready | Rename non-target `body-01` to `Body_Final_01`; preserve target `body-02` as `Body_Final`. | Naming plan only; no rename API/runtime effect claimed. |
| ER-09 | plan_ready | Activate `run-005-model` only and re-observe focus; keep modified scratch document. | No GUI focus change is performed. |
| ER-10 | plan_ready | Prepare one run-owned parent-directory precondition; leave save to its own atom. | No directory or save action is performed. |
| ER-11 | needs_manual_review | No deletion; cleanup plan waits for host-verified size/reparse-safe ownership. | Claimed hash exists but size/absence/host ownership are not independently observed. |
| ER-12 | plan_ready | One traceable rerun plan linked to `run-008`/`f-08`; waiting remains EX-10. | No rerun command or terminal state is claimed; no cleanup/new document/load is bundled. |

## Safety and evidence checks

- Missing authorization, ambiguous sessions, modified user work, path-role
  collisions, missing root identity, and missing artifact checks fail closed.
- EX-10 records timeout as unknown; EX-12 does not promote a timestamp-only
  first error without run association; ER-01 does not turn an API-looking
  message into an unversioned diagnosis.
- ER-02 changes one V21 member binding only and retains the surrounding import
  strategy. ER-04 rejects list-index selection. ER-05 refreshes after the
  mutation and before its first consumer. ER-06 refuses a missing tolerance.
- ER-07 refuses a guessed repair call; ER-09 restores only document focus;
  ER-10 repairs only a path precondition; ER-11 does not delete on filename or
  claimed hash alone; ER-12 contains one rerun dispatch and no wait/retry loop.
- No historical P3/P4 report, script label, synthetic hash, or planned event
  was promoted to SpaceClaim runtime, native persistence, visual, or host
  filesystem evidence.

The detailed structured decisions, snippets, action plans, rejection reasons,
uncertainties, and snapshot hashes are in `runs/p4-independent/results.json`.
