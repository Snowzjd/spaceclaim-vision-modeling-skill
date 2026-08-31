# Development scope

Develop `spaceclaim-vision-modeling` as a standalone, domain-independent SpaceClaim modeling skill.

## Product boundary

- Cover visual or textual geometry interpretation, modeling-strategy selection, version-aware SpaceClaim scripting, runtime diagnostics, and geometry-level validation.
- Produce explicit geometry contracts, parameters, scripts, native-model evidence, requested geometry exports, and unresolved-risk handoffs at the validation level actually reached.
- Treat input interpretation, geometry contracts, script checks, SpaceClaim execution, geometry measurements, visual review, native save/reopen, and requested exports as separate evidence layers.

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
- Keep the installable Skill and executable public cases self-contained. External artifacts may be referenced only as bounded provenance: they must not be required to reproduce a public capability claim, and the repository must state when their contents cannot be independently inspected.
- Preserve explicit evidence boundaries. A script, screenshot, or native model alone does not prove every requested SpaceClaim modeling claim.
- Run the official skill validator after structural changes.
