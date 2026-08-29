# Integration boundary

## Standalone responsibility

This skill owns only the SpaceClaim modeling module:

- interpret visual and textual geometry intent;
- establish parameters, coordinate systems, and modeling strategy;
- generate or repair SpaceClaim scripts;
- run or guide geometry construction when authorized;
- validate bodies, features, dimensions, topology, names, native saves, and requested exports at the claimed evidence level;
- return scripts, outputs, reports, and unresolved risks.

It does not own:

- mesh generation or mesh-quality acceptance;
- shared-topology acceptance in a downstream mesher unless explicitly tested as a SpaceClaim operation;
- Workbench project orchestration;
- Fluent setup, execution, convergence, or conservation;
- simulation data processing, plotting, or reporting;
- private parent-project state.

## Consumer interface

A parent workflow should provide:

```text
visual or textual geometry intent
target SpaceClaim/API version
known dimensions and units
required bodies, names, groups, and exports
downstream purpose and acceptance thresholds
input model path or clean-copy rule when applicable
authorized execution level
```

The skill should return:

```text
geometry contract and assumptions
parameter table and coordinate system
modeling strategy
version-aware script
runtime report
native or neutral output paths when created
validation results by evidence layer
failure diagnostics and next safe action
```

## Coupling rules

- Keep this repository, version history, releases, and tests independent.
- Do not import files through absolute paths from a parent repository.
- Do not require a parent's naming scheme unless supplied as an input contract for the current task.
- Do not write into a parent's workspace except through an explicitly provided output path.
- Publish a stable version before a parent workflow pins or vendors the module.
- Record the consumed skill version and output hashes in the parent workflow.
- Treat breaking changes to inputs, outputs, naming, evidence levels, or failure behavior as interface changes.

## Evidence boundary

Successful modeling does not imply successful meshing or simulation. A parent workflow must run its own topology transfer, mesh connectivity, mesh quality, solver, convergence, and conservation gates after consuming the model.
