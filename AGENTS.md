# Development scope

Develop `spaceclaim-vision-modeling` as a standalone, domain-independent SpaceClaim modeling skill.

## Product boundary

- Cover visual or textual geometry interpretation, modeling-strategy selection, version-aware SpaceClaim scripting, runtime diagnostics, and geometry-level validation.
- Produce explicit geometry contracts, parameters, scripts, native-model evidence, requested geometry exports, and unresolved-risk handoffs at the validation level actually reached.
- Keep meshing, Workbench orchestration, solver setup and execution, simulation data processing, and simulation reporting outside this skill.
- Treat script checks, SpaceClaim execution, geometry measurements, native save/reopen, neutral export, meshing, and solver readiness as separate evidence layers.

## Development priorities

1. Geometry decomposition from visual and textual inputs.
2. Modeling-strategy selection.
3. Version-aware, parameterized SpaceClaim script generation.
4. Semantic object selection and topology-safe operations.
5. Runtime diagnostics, validation, and minimal repair.
6. Reusable public templates and cases.

## Repository rules

- Keep `SKILL.md` concise and route detailed rules to `references/`.
- Put deterministic tools in `scripts/` and copyable templates or public case assets in `assets/`.
- Use only redistributable public examples. Do not copy private models, recordings, vendor binaries, licensed documentation, credentials, or user-specific paths.
- Keep repository development self-contained; do not require unpublished repositories, run directories, or evidence that cannot be redistributed or reproduced.
- Preserve explicit evidence boundaries. A script, screenshot, or native model alone does not prove export, mesh, or solver readiness.
- Run the official skill validator after structural changes.
