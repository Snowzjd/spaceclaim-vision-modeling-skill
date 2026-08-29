# Development scope

Develop `spaceclaim-vision-modeling` as a standalone, domain-independent SpaceClaim modeling skill.

## Architectural boundary

- Do not depend on private parent repositories, local research paths, unpublished models, run directories, or unpublished evidence.
- Do not modify a consuming workflow while developing this repository.
- Treat future integration as a downstream consumer relationship through documented inputs, outputs, versions, and evidence, not shared mutable state.
- Keep meshing, solver setup, solver execution, data processing, and reporting outside this skill.

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
- Preserve explicit evidence boundaries. A script, screenshot, or native model alone does not prove export, mesh, or solver readiness.
- Run the official skill validator after structural changes.
