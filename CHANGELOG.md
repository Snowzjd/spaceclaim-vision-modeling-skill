# Changelog

## v0.2.0 - 2026-08-31

- Clarify the project boundary around the Skill's SpaceClaim modeling capabilities, handoff contracts, exclusions, and validation layers.
- Complete controlled SpaceClaim 2022 R1 / API V21 forward runs, structured runtime reports, native save, independent close/reopen audits, and case-specific visual reviews for public cases 001–004.
- Complete public case 002 from image-plus-text intent through a formal V21 `.scscript`, transient circular-profile construction, holes, rounds, chamfers, native save, visual review, and feature-level close/reopen audit.
- Complete public case 003 from a multi-view engineering drawing through dimension reconciliation, explicit assumption tracking, a formal V21 `.scscript`, coaxial stepped construction, through-bore and keyway cuts, rounds, chamfers, native save, visual review, and feature-level close/reopen audit.
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
