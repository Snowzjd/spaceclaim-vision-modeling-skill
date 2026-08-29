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

For parameterized reusable scripts, add `--forbid-numbered-aliases`. Recorded aliases may still be audited for closure when performing an explicitly same-topology replay.

Run the public unit tests:

```powershell
python -m unittest discover -s tests -v
```

Real model execution requires a separately licensed Ansys SpaceClaim installation and a script matched to its API version.

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

This is an independent SpaceClaim modeling module, not a complete Ansys simulation workflow. It does not depend on private CAD models, research parameters, desktop recordings, local paths, meshing state, or solver state. A broader Ansys workflow may consume a released version through the documented integration contract.

Not included in v0.1:

- Ansys binaries or proprietary API documentation.
- Private models, scripts, recordings, or unpublished research data.
- Guaranteed cross-version compatibility.
- Shared-topology, neutral-export, mesh-connectivity, Fluent, or solver validation.

Static script checks, visual inspection, SpaceClaim runtime execution, geometry-kernel measurements, native save/reopen, export, meshing, and solver readiness remain separate validation levels.

This project is independent and is not affiliated with or endorsed by Ansys, Inc.

## License

Licensed under the [Apache License 2.0](LICENSE).
