# Validation-and-visual-review operation library

`stage: validation_visual_review` · `architecture: v0.3` · `template contract: 1`

## Stage contract

**Purpose** — Check the requested geometry, measurements, naming, persistence, visual agreement, and exports while keeping each evidence layer independent.

**Inputs**

- Geometry, build, and execution contracts plus the requested acceptance criteria.
- Runtime measurements/reports, native model artifact, and available visual evidence.

**Outputs**

- An acceptance contract containing `artifact_identity`, `geometry_acceptance`, `body_feature_and_name_checks`, `dimension_bbox_and_volume_checks`, `native_save_result`, `native_reopen_result`, `visual_review_views`, `visual_agreement`, `requested_export_result`, `evidence_map`, `unresolved_risks`, and `overall_status`.

**Exit gate**

- Checks are proportional to risk and cover every requested property.
- Geometry measurements, visual agreement, native save, native reopen, and requested export are reported separately.
- Enough overview, standard, and focused views expose each contract-relevant feature; occluded or unresolved features are recorded.
- Every unperformed layer is `not_tested`, and acceptance is bound to the exact model and evidence artifacts reviewed.

## Active operations

These are the only active entries in this stage. All three are host tools; they validate declared data and do not independently observe SpaceClaim.

| Operation | Host tool and bounded outcome | Evidence boundary |
| --- | --- | --- |
| `validation_visual_review.validate-runtime-report-schema` (`active`, `0.1.0`) | `scripts/validate_runtime_report.py` without `--contract` validates one report's structure and internal invariants. | `design_only` and `host_checked` for report structure only; no direct execution, geometry observation, save/reopen, visual, or export evidence. |
| `validation_visual_review.compare-runtime-report-to-contract` (`active`, `0.1.0`) | `scripts/validate_runtime_report.py --contract` compares one structurally valid report with one expected measurement contract. | `design_only` and `host_checked` for declared contract consistency only; no direct execution, geometry observation, save/reopen, visual, or export evidence. |
| `validation_visual_review.compare-runtime-reports` (`active`, `0.1.1`) | `scripts/compare_runtime_reports.py` compares distinct forward and native-reopen report artifacts, body measurements, feature values, and named-group membership. | `design_only` and `host_checked` for the comparison only; matching declarations do not independently prove either run or native persistence. |

## Candidate families (mature v0.2 extraction directions)

### P5 action resources

Use the catalog/registry mapping to select one VA or VI action and load only its
`references/atomic-guidance/va-XX.json` or `vi-XX.json` (lowercase filename).
Keep the three existing host-active entries above. New candidates require
explicit selection during development; their existence does not activate them.

The new `scripts/validation_host_actions.py` offers four bounded checks:

| Action | Callable | Boundary |
| --- | --- | --- |
| VA-19 | `check_output_file_identity(path, expected_sha256)` | Reads one regular file and compares SHA-256; not geometry validation. |
| VA-20 | `check_native_save_result(path, expected_sha256, save_record, run_ref)` | Checks a nonempty native file and a supplied correlated save record; does not observe a save. |
| VA-23 | `check_observed_property(observation, expected_value, expected_artifact_sha256, absolute_tolerance=0, action_id='VA-23')` | Compares one declared native-reopen property; does not reopen or measure it. |
| VA-25 | Same callable with `action_id='VA-25'` | Compares one property of already reimported geometry; import belongs outside this action. |

Model-measurement `.scscript` artifacts and desktop guidance have their own
interfaces and evidence. Controller support for a gesture is not implied by
the SpaceClaim documentation: if middle-button drag or a held modifier cannot
be expressed, retain the direct gesture as untested and use a verified visible
navigation control where appropriate. Do not convert an alternative left-drag
into evidence for an unperformed middle-button gesture.

- **Enumerate bodies** — Return the current body set and semantic identities without adding measurement or persistence claims.
- **Measure one bounding box** — Resolve one body and report only its kernel bounds.
- **Measure one volume** — Resolve one body and report only its kernel volume.
- **Check one semantic name** — Compare one resolved object's current name with one expected value.
- **Save native model** and **reopen native model** — Keep these as separate state operations with separate evidence.
- **Inspect one planned view** — Establish one view and record visibility/agreement for the requested feature; multi-view acceptance remains a composition of these checks.

Candidate families are not active and must not be presented as completed runtime or visual capabilities until their exact artifacts and evidence pass promotion gates.

## Fallback rules

- Use the generic validation workflow routed by `SKILL.md` when no active operation matches, an input contract is stale, or a required evidence layer is unavailable.
- Validate each report's structure before comparing it with a contract or another report. Use forward/reopen comparison only after both reports are structurally valid and declare the required states.
- Keep the SpaceClaim window maximized or full-screen for authorized visual review, calibrate navigation, inspect overview and contract-relevant standard/focused views, and record occlusion.
- Mark unperformed geometry, persistence, visual, and export checks `not_tested`; never infer them from a plausible screenshot, file existence, or host report result.

## Promotion and evidence boundary

- Promote a candidate only after a schema-valid, case-neutral artifact exists with observable postconditions, validation method, applicable host checks, and a usable generic fallback.
- Host report validation and comparison are static evidence only. `spaceclaim_execution`, `geometry_measurements`, `native_save`, `native_reopen`, `visual_review`, and `requested_export` require their own exact-run or exact-view evidence.
- Bind every passed or failed layer to the exact template version and artifact hash; material edits reset affected evidence to `not_tested`.

## Extension slot

Reserve a per-stage slot for temporal comparison, feature detectors, new view planners, or evidence adapters. Each extension must emit the acceptance contract, preserve `bypass_core_stages=false`, and return through the normal evidence gates. No extension implementation is active here.
