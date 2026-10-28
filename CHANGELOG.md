# Changelog

## Unreleased

- Document a backend-agnostic host capability contract for desktop control: minimum operation set, per-action metadata, `implemented`/`tested`/`unsupported`/`not_tested` states, one-backend and one-queue rules, and stop/queue-empty thresholds. The existing Computer Use plugin remains the reference implementation; no controller implementation or capability claim changed.

## v0.3.0 - 2026-10-19

- Establish Geometry understanding, Modeling strategy and scripting, Execution and recovery, and Validation and visual review as the four core stages, with explicit handoff contracts.
- Register 139 action-scoped contracts and implementations/guidance across the four libraries; retain 5 active host tools and keep 134 candidates bounded by their own evidence.
- Add independent source-interpretation and strategy evaluations, V21 modeling-action scripts, execution/recovery helpers, geometry checks and recorded visual-navigation variants.
- Preserve the complete modeling workflow as the fallback when an eligible atomic operation is unavailable.
- Bind execution and measurement claims to exact script versions and hashes; retain failure reports and reviewed corrections.
- Add host handoff integrity checks and installation-aware artifact resolution.
- Document the complete external runtime requirements and provide pinned host dependencies, installation checks and relocated-install support.
- Clarify Computer Use input limits and standard SpaceClaim navigation alternatives.
- Reserve extension interfaces for future video-source interpretation, demonstrated operations and later composition without bypassing core-stage validation.

Existing evidence covers only its recorded inputs, versions and variants; this release
does not activate all operations or establish universal recognition, gesture or
cross-version support.

## v0.2.0 - 2026-08-31

- Clarify the project boundary around the Skill's SpaceClaim modeling capabilities, handoff contracts, exclusions, and validation layers.
- Archive evidence from controlled SpaceClaim 2022 R1 / API V21 forward runs, structured reports, native save/reopen audits, and bounded multi-view reviews in the public case library.
- Expand the public case library across visual, drawing, and textual input forms while keeping each case's geometry, assumptions, names, and measurements local to its own bundle.
- Add deterministic four-member V21 `.scscript` packaging and formal packaged assets for public cases.
- Add a versioned structured runtime-report schema and dependency-free host validator.
- Harden `.scscript` token analysis, exact smart-variable closure, archive-integrity checks, and resource-safety limits.
- Harden runtime-report and case-contract validation for invalid tolerances, bounding-box order, status consistency, duplicate identifiers, and output-path collisions.
- Add a deterministic forward-versus-reopen report comparator for persistence checks.
- Expand deterministic host-side coverage for packaging, archive auditing, case contracts, runtime reports, persistence comparison, templates, and execution-workflow invariants.
- Add a fast execution workflow: prepare and audit once before control, execute familiar document/script setup continuously, and perform detailed review only at meaningful gates and after completion.
- Add a maximized-workspace visual interaction workflow covering selection, clearing, zoom, pan, spin, standard-view orientation, focused inspection, and clean screenshot evidence.
- Document the three external requirements for the complete workflow: visual understanding, desktop control, and a licensed local SpaceClaim installation with a matching scripting API.

## v0.1 - 2026-08-29

- Release the standalone `spaceclaim-vision-modeling` Skill package.
- Define the vision-to-geometry, modeling strategy, scripting, debugging, and validation contracts.
- Add semantic selection, Boolean-result recovery, topology-mutation, naming, and save/reopen rules.
- Add a tested static `.scscript` archive auditor.
- Add SpaceClaim API V21 read-only geometry-audit and semantic-helper templates.
- Add a public synthetic acceptance case and an evidence-bounded capability matrix.
- Define the Skill's SpaceClaim modeling scope, handoff contract, and evidence boundary.
- License the repository under Apache License 2.0.
