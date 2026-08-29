# Workflow contracts

Use these contracts as structured outputs. Merge roles when the task is small; do not run them as disconnected agents by default.

## Visual geometry parser

Report:

```text
input type:
viewpoint and projection:
primary bodies:
geometry primitives:
features:
spatial relations:
symmetry and repetition:
known dimensions:
unknown dimensions:
confidence and ambiguities:
```

Describe geometry, not only object identity. For example, prefer “two coaxial cylinders, one tapered transition, a circular hole pattern, and two fillets” over “a connector.”

## Modeling strategy planner

Report:

```text
coordinate system:
construction order:
operation per feature:
Boolean plan:
pattern or mirror plan:
parameter list:
version-sensitive operations:
semantic selectors:
failure checkpoints:
```

Choose one primary strategy and explain alternatives only when they materially affect reliability.

## SpaceClaim script writer

Require:

- centralized parameters and explicit units;
- target API version declaration;
- created-object references where stable;
- semantic selection after topology-changing operations;
- critical assertions before save;
- explicit output and runtime-report paths;
- no hidden overwrite of user inputs.

## Script debugger

Classify the failure before editing:

```text
syntax or runtime API mismatch
path or encoding
missing or ambiguous selection
stale object handle after topology mutation
Boolean-result misunderstanding
invalid or open geometry
application/UI state
naming collision
save or export failure
```

Identify the earliest incorrect state, patch that stage, and rerun from a clean model copy.

## Validation reviewer

Use [spaceclaim-validation-report.schema.json](spaceclaim-validation-report.schema.json) when a machine-readable runtime report is required. Validate the JSON structure and case measurements with `scripts/validate_runtime_report.py`, while preserving the distinction between a host-validated report and independently observed SpaceClaim execution.

Record each evidence layer separately:

```text
static package and parameter audit:
SpaceClaim execution:
body and feature counts:
dimensions, bounding boxes, volumes:
naming and group membership:
visual agreement:
native save and reopen:
neutral export and reimport:
mesh or solver evidence:
```

Mark unperformed layers as not tested. Do not infer downstream readiness from a visually plausible model.
