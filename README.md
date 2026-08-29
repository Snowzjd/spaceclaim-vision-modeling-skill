# SpaceClaim Vision Modeling

Version **v0.1**

A vision-guided SpaceClaim automation skill that turns images, sketches, engineering drawings, CAD screenshots, text descriptions, recorded scripts, and error logs into geometry contracts, parameterized modeling strategies, SpaceClaim scripts, and evidence-bounded validation results.

The project reasons from geometry rather than relying on industry-specific object names:

```text
visual or textual intent
  -> primitives, dimensions, and spatial relations
  -> deterministic modeling strategy
  -> version-matched SpaceClaim script
  -> static and runtime validation
  -> minimal repair
  -> reusable modeling pattern
```

## What v0.1 includes

- An installable Codex Skill with parser, planner, script-writer, debugger, and validation-review contracts.
- Semantic selection rules based on position, direction, normal, area, bounding box, volume, and topology.
- Reusable guidance for copy/move, rotation, extrusion, arrays, merge, split, Boolean operations, direct domain construction, naming, and native save/reopen.
- A tested host-side auditor for SpaceClaim `.scscript` archives.
- SpaceClaim API V21 templates for read-only geometry reporting and semantic selection helpers.
- A public synthetic case contract for repeatable runtime acceptance testing.
- Explicit evidence boundaries between static checks, SpaceClaim execution, native persistence, export, meshing, and solver readiness.

See the [validated capability matrix](spaceclaim-vision-modeling/references/validated-capability-matrix.md) for the exact support and evidence boundary.

## Quick start

Install or link the nested `spaceclaim-vision-modeling/` folder as a Codex Skill, then invoke:

```text
Use $spaceclaim-vision-modeling to decompose this design and produce a validated SpaceClaim script.
```

Audit an existing script package without launching SpaceClaim:

```powershell
python .\spaceclaim-vision-modeling\scripts\audit_scscript.py .\model.scscript --require-api 21 --report .\audit.json
```

Validate a structured runtime report against the public case contract on the host:

```powershell
python .\spaceclaim-vision-modeling\scripts\validate_runtime_report.py .\runtime-report.json --contract .\spaceclaim-vision-modeling\assets\cases\001-offset-block-array\validation-contract.json
```

This command checks report structure and declared measurements only. It does not prove that SpaceClaim executed or that a model was saved or reopened.

For parameterized reusable scripts, add `--forbid-numbered-aliases`. Recorded aliases may still be audited for closure when performing an explicitly same-topology replay.

Run the public unit tests:

```powershell
python -m unittest discover -s tests -v
```

Real model execution requires a separately licensed Ansys SpaceClaim installation and a script matched to its API version.

The case 001 V21 build script is prepared for an authorized forward test but remains `runtime_pending`; no public runtime success is claimed yet.

## Repository layout

```text
spaceclaim-vision-modeling/
├─ README.md
├─ CHANGELOG.md
├─ VERSION
├─ tests/
└─ spaceclaim-vision-modeling/
   ├─ SKILL.md
   ├─ agents/openai.yaml
   ├─ prompts/
   ├─ references/
   ├─ scripts/
   └─ assets/
      ├─ templates/
      └─ cases/
```

The nested folder is the installable Skill package. Repository-level tests and release files are not loaded into the Skill runtime context.

## Project boundary

This project covers the SpaceClaim modeling stage:

- interpret visual and textual geometry intent;
- define geometry contracts, parameters, coordinate systems, and modeling strategies;
- generate, audit, debug, and minimally repair version-aware SpaceClaim scripts;
- validate body and face identities, dimensions, topology, names, runtime reports, native saves, reopen persistence, and requested geometry exports at the evidence level actually tested.

Outside the project boundary:

- Ansys binaries or proprietary API documentation.
- Guaranteed cross-version compatibility.
- Workbench project orchestration.
- Meshing, mesh-quality acceptance, or mesh-connectivity validation.
- Fluent or other solver setup, execution, convergence, conservation, and result validation.
- Simulation data processing, plotting, and reporting.

Static script checks, visual inspection, SpaceClaim runtime execution, geometry-kernel measurements, native save/reopen, export, meshing, and solver readiness remain separate validation levels.

Repository examples and fixtures must be public and redistributable; private models, recordings, credentials, unpublished research data, and user-specific paths are not accepted as package content.

This project is independent and is not affiliated with or endorsed by Ansys, Inc.

## License

Licensed under the [Apache License 2.0](LICENSE).
