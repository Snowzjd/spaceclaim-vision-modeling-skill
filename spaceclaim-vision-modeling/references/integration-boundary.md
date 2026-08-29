# Skill scope and handoff boundary

## Modeling responsibility

This skill covers the SpaceClaim modeling stage:

- interpret visual and textual geometry intent;
- establish geometry contracts, parameters, coordinate systems, constraints, and modeling strategy;
- generate, audit, debug, or minimally repair version-aware SpaceClaim scripts;
- run or guide geometry construction when authorized;
- validate bodies, features, dimensions, topology, names, runtime reports, native saves, reopen persistence, and requested geometry exports at the evidence level actually reached;
- return scripts, outputs, reports, assumptions, and unresolved risks.

## Request contract

A modeling request should provide:

```text
visual or textual geometry intent
target SpaceClaim/API version
known dimensions and units
required bodies, names, groups, and exports
downstream purpose and acceptance thresholds
input model path or clean-copy rule when applicable
authorized execution level
```

## Result contract

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

## Outside scope

The skill does not perform or claim:

- Workbench project orchestration;
- mesh generation, mesh-quality acceptance, or mesh-connectivity validation;
- Fluent or other solver setup, execution, convergence, conservation, or result validation;
- simulation data processing, plotting, or reporting;
- universal compatibility across untested SpaceClaim or API versions.

Shared-topology operations and neutral exports are outside the v0.1 validated core. If requested, treat them as separate experimental validation targets and claim success only after the corresponding operation and persistence or transfer checks pass. Neither establishes downstream mesh or solver readiness.

## Handoff rules

- Require explicit input and output paths rather than relying on an application's current directory.
- Use the naming scheme supplied by the current geometry contract; do not invent downstream names silently.
- Record the Skill version, target SpaceClaim/API version, output paths, and hashes when artifacts are created.
- Preserve clean inputs, independent outputs, failure-without-save behavior, and save/reopen checks when persistence matters.
- Treat breaking changes to inputs, outputs, naming, evidence levels, or failure behavior as interface changes.

## Evidence boundary

Successful modeling does not imply successful meshing or simulation. Topology transfer, mesh connectivity, mesh quality, solver execution, convergence, conservation, and performance conclusions each require their own downstream evidence.
