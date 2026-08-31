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
intended use and acceptance thresholds
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

## Scope limit

Keep every accepted claim within visual or textual geometry interpretation, SpaceClaim construction, model properties, naming, persistence, or a requested SpaceClaim export. Do not claim universal compatibility across untested SpaceClaim or API versions.

## Handoff rules

- Require explicit input and output paths rather than relying on an application's current directory.
- Use the naming scheme supplied by the current geometry contract; do not invent names silently.
- Record the Skill version, target SpaceClaim/API version, output paths, and hashes when artifacts are created.
- Preserve clean inputs, independent outputs, failure-without-save behavior, and save/reopen checks when persistence matters.
- Treat breaking changes to inputs, outputs, naming, evidence levels, or failure behavior as interface changes.

## Evidence boundary

Successful script execution does not by itself prove intended geometry, naming, measurements, visual agreement, native persistence, or requested export behavior. Validate each claimed SpaceClaim modeling layer directly.

Bind runtime claims to the exact executed artifact. When a redistributed package differs from the executed package, disclose the difference and do not describe the revised bytes as runtime-tested until they are run again.
