# SpaceClaim Vision Modeling

Version: **v0.3.0**

Release date: **2026-10-19**.

v0.3 establishes four-stage contracts, independently scoped operation libraries,
version-bound evidence and fallback integration. The registry covers 139 operations:
5 established host tools are active and 134 operations remain candidates with their
own recorded scope. The complete modeling workflow remains available when no
eligible atomic template matches. See the [architecture](spaceclaim-vision-modeling/references/architecture.md)
and [integration rules](spaceclaim-vision-modeling/references/workflow-integration.md).

`spaceclaim-vision-modeling` is a vision-guided, script-first Codex Skill for building and validating three-dimensional models in Ansys SpaceClaim. It converts reference images, sketches, engineering drawings, CAD screenshots, product views, text descriptions, existing SpaceClaim scripts, and error logs into explicit geometry contracts, version-matched `.scscript` packages, controlled desktop execution, and evidence-bounded model review.

The Skill reasons from geometry rather than assuming a particular product or application domain:

```text
reference material and user intent
  -> geometry decomposition and dimension reconciliation
  -> explicit geometry contract and assumptions
  -> deterministic SpaceClaim modeling strategy
  -> version-matched .scscript package
  -> controlled SpaceClaim execution
  -> geometry, persistence, and multi-view visual review
```

## Required external capabilities

Installing or copying this repository does **not** install or provide the following capabilities. All three are required for the complete vision-to-model workflow.

1. **A vision-capable agent with local file and terminal tools**
   - Use Codex in the Windows desktop app with a model that can actually read reference images and returned screenshots, reason over them, and read/write local files and run host Python commands. A separate product named "Vision Skill" is not required when the agent already provides these capabilities.
   - Reads reference images, drawings, screenshots, and product views, then compares the completed model with those references. File/terminal permission and desktop-control permission are separate.
   - Without it, the package can still process text, structured parameters, and existing scripts, but it cannot claim visual recognition or final visual-agreement acceptance.

2. **The complete Computer Use plugin: Skill plus working control service**
   - Controls the SpaceClaim window, mouse, keyboard, script loading and execution, view changes, object selection, and screenshot capture.
   - Install and enable the plugin and both its server and Skill in the desktop app; grant access to SpaceClaim when prompted. Copying only its `SKILL.md` is insufficient. Follow the [official Computer Use setup](https://developers.openai.com/codex/computer-use).
   - The Windows reference controller uses the plugin's `node_repl` / `@oai/sky` runtime. Do not install a guessed npm substitute or add another desktop MCP to bypass a missing capability. The controller and its tools come from the plugin, not this repository.
   - The reference plugin is one implementation of the [host capability contract](spaceclaim-vision-modeling/references/controller-compatibility.md#host-capability-contract), not the contract itself. A substitute backend — a CLI command or a local MCP server — is admissible only when it satisfies that contract (window identity, capture, focus, input, stop, health) and is declared before the run; declared is still not tested.
   - Without it, the package can still generate, package, and statically audit scripts, but it cannot operate SpaceClaim or collect desktop-based execution evidence. See the [controller compatibility rules](spaceclaim-vision-modeling/references/controller-compatibility.md) for direct actions, equivalent paths and outstanding live checks.

3. **Local SpaceClaim and host Python**
   - SpaceClaim must be installed, launchable, and properly licensed. The `.scscript` API version must match the target SpaceClaim environment.
   - The currently evidenced desktop baseline is **Windows, SpaceClaim 2022 R1 with scripting API V21 and embedded IronPython 2.7**. A product release number and scripting API number are different. Other releases require explicit compatibility checks; merely editing the API marker is insufficient.
   - Install **CPython 3.12.x** for host tools and the package's [requirements.txt](spaceclaim-vision-modeling/requirements.txt) in a dedicated virtual environment as below. Host Python is separate from SpaceClaim's embedded IronPython; do not install these packages inside SpaceClaim.
   - Without a usable installation, license, or matching API, the package is limited to host-side preparation and static checks; it cannot produce SpaceClaim runtime evidence.

These requirements are intentionally separate from the repository. Before using a redistributed copy, confirm that the agent environment supplies the first two capabilities and that the local machine supplies the third.

## What the Skill contains

### Geometry understanding

- Parse visual and textual inputs into bodies, primitives, features, dimensions, coordinate systems, constraints, and spatial relations.
- Separate observed facts, user-supplied dimensions, inferred relations, assumptions, and unresolved dimensions.
- Reconcile multi-view drawings without silently inventing missing geometry.

### Modeling strategy and scripting

- Select stable constructions such as extrusion, revolve, sweep, loft, pattern, mirror, Boolean operations, and controlled import.
- Generate parameterized, version-aware SpaceClaim IronPython scripts and deliver formal `.scscript` packages.
- Use semantic selection based on geometry and topology instead of generalizing recorded `FaceN` or `BodyN` identifiers.
- Re-enumerate and reclassify geometry after topology-changing operations.
- Assert critical geometry before saving and stop without saving when a critical assertion fails.

### Execution and recovery

- Prepare and audit once before desktop control, then run familiar document and script setup as a short transaction.
- Start from a new unsaved design when no baseline is supplied, or from an identified copy when a baseline model is supplied.
- Keep SpaceClaim maximized throughout authorized control by default and reserve detailed review for meaningful gates.
- Classify failures, repair the smallest responsible stage, and restart from a clean run state.

### Validation and visual review

- Validate structured runtime reports against case contracts.
- Compare forward-run and independent native-reopen reports.
- Inspect standard and focused views using selection, fit, zoom, pan, spin, orientation controls, and clean screenshot capture.
- Keep interpretation, static checks, SpaceClaim execution, geometry measurements, visual agreement, native save/reopen, and requested exports as separate evidence layers.

See the [validated capability matrix](spaceclaim-vision-modeling/references/validated-capability-matrix.md) for operation-level support and its exact evidence boundary.

## Quick start

Download the intended release/source archive and extract it, or obtain a checkout.
Use all files from the **same version**. This README describes the v0.3.0 package.
Do not mix it with an older downloaded package that lacks its commands.

Install or link the nested [`spaceclaim-vision-modeling/`](spaceclaim-vision-modeling/) directory as a Codex Skill. The repository root contains development tests and release files; the nested directory is the installable package. Personal standalone skills can be placed under `%USERPROFILE%\.agents\skills`; see [official Skill installation locations](https://developers.openai.com/codex/skills).

In PowerShell, start in the extracted repository root and run:

```powershell
$Source = (Resolve-Path '.\spaceclaim-vision-modeling').Path
$Skill = Join-Path $env:USERPROFILE '.agents\skills\spaceclaim-vision-modeling'
if (Test-Path -LiteralPath $Skill) { throw 'An installation already exists; preserve it and choose an explicit update plan first.' }
New-Item -ItemType Directory -Path (Split-Path -Parent $Skill) -Force | Out-Null
Copy-Item -LiteralPath $Source -Destination $Skill -Recurse
py -3.12 -m venv (Join-Path $Skill '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Host Python environment creation failed.' }
$HostPython = Join-Path $Skill '.venv\Scripts\python.exe'
& $HostPython -m pip install -r (Join-Path $Skill 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed; do not continue.' }
& $HostPython (Join-Path $Skill 'scripts\check_installation.py')
if ($LASTEXITCODE -ne 0) { throw 'Installed-package check failed.' }
```

If `py -3.12` is unavailable, install CPython 3.12 with its Windows launcher, or
replace it with the absolute path to that Python interpreter. No virtual-environment
activation or PowerShell execution-policy change is necessary. In subsequent
commands use `$HostPython`, not an unrelated `python` found on PATH. For an
existing linked checkout, set `$Skill` to the actual nested package directory
and run the environment/dependency steps there without copying over it.

`check_installation.py --details` inventories every registered operation and its
installed resources. `host_ready` means package/dependency checks passed; it does
not observe a live controller, a license, image interpretation or successful CAD.
`--spaceclaim-exe <absolute-path>` can check the executable exists but does not
launch it or infer licensing/API support. Repeat this check after installation
or relevant updates, not between routine mouse actions.

Restart/refresh the agent session if the Skill is not discovered, then ask:

```text
Use $spaceclaim-vision-modeling. Use its .venv host Python. Perform the first-run
setup check from references/installation-and-runtime.md. Use only this package,
your built-in vision/file tools, the declared Computer Use plugin and SpaceClaim.
Report missing capabilities; do not silently add other skills or MCPs.
```

That first-run check verifies visual access, the live controller and application
identity, and a reversible navigation path in an authorized maximized SpaceClaim
window. It is a short setup check, not a request to test every library operation.
Then use the normal modeling workflow, selecting only the controls needed by the
task. Installation cannot remove geometric preconditions or turn unverified
candidate variants into generally proven operations.

Installed template paths resolve relative to that Skill directory using the
[installation path rule](spaceclaim-vision-modeling/references/workflow-integration.md#installed-paths-versus-maintainer-evidence).
Running the maintainer's complete tests and registry-evidence audit requires the
full repository checkout; those test sources are not modeling runtime components.

Then invoke it with a reference and a concrete modeling request, for example:

```text
Use $spaceclaim-vision-modeling to interpret this engineering drawing, list unresolved dimensions, create a SpaceClaim modeling strategy, generate the matching .scscript, run it after authorization, and validate the completed model.
```

For a text-only preparation task:

```text
Use $spaceclaim-vision-modeling to convert these dimensions into a geometry contract and a SpaceClaim V21 .scscript. Do not control SpaceClaim.
```

Desktop control is run-scoped. The agent must explain why control is needed and obtain authorization before controlling SpaceClaim. Once authorized, routine setup should proceed continuously unless the scope changes, a blocking state appears, or the active controller requires another confirmation.

## End-to-end workflow

1. **Understand the request** — identify the input type, target SpaceClaim/API version, units, outputs, supplied dimensions, and unresolved choices.
2. **Create the geometry contract** — record bodies, features, dimensions, relations, assumptions, names, and acceptance checks.
3. **Choose the modeling strategy** — prefer deterministic scripted construction and define semantic selectors for all important objects.
4. **Generate and preflight the script** — centralize parameters, add assertions and reporting, package the formal `.scscript`, and run relevant host-side checks once.
5. **Execute after authorization** — create a new unsaved design or open a clean baseline copy, load the prepared `.scscript`, and run it once.
6. **Validate the result** — check geometry, names, structured reports, required outputs, and native persistence at the levels required by the task.
7. **Perform visual acceptance** — keep the viewport maximized, inspect deterministic standard and focused views, compare against the geometry contract, and capture clean evidence views.
8. **Repair or hand off** — patch the earliest failing stage and restart cleanly, or return the artifacts, evidence boundary, unresolved risks, and next safe test.

Detailed procedures are in the [fast execution workflow](spaceclaim-vision-modeling/references/execution-workflow.md) and [visual interaction guide](spaceclaim-vision-modeling/references/visual-interaction.md).

## Host-side tools

The commands in this section run outside SpaceClaim. They inspect packages or declared reports; they do not create runtime evidence by themselves. After installation, use the configured `$Skill` and `$HostPython` above; paths to your own inputs/outputs below are relative to your current run directory.

### Package a script

```powershell
& $HostPython (Join-Path $Skill 'scripts\package_scscript.py') .\model-source.py .\model.scscript --api 21
```

The `.py` file is editable IronPython source used as packaging input. The artifact loaded, executed, and delivered to SpaceClaim is `model.scscript`.

### Audit a `.scscript` package

```powershell
& $HostPython (Join-Path $Skill 'scripts\audit_scscript.py') .\model.scscript --require-api 21 --forbid-numbered-aliases --report .\audit.json
```

Recorded numbered aliases may be acceptable for an explicitly same-topology replay, but they are not reusable semantic selection logic.

### Validate a structured runtime report

```powershell
& $HostPython (Join-Path $Skill 'scripts\validate_runtime_report.py') .\runtime-report.json --contract .\contract.json
```

This checks report structure and declared measurements. It does not independently prove that SpaceClaim ran or that the report has authentic runtime provenance.

### Compare forward and reopen reports

```powershell
& $HostPython (Join-Path $Skill 'scripts\compare_runtime_reports.py') .\runtime-report.json .\reopen-report.json
```

This checks declared persistence measurements and memberships. It does not replace the actual native close/reopen procedure.

### Run repository tests

```powershell
& $HostPython -m unittest discover -s tests -v
```

Run that command from the full checkout only when a repository regression is needed. These Python tests exercise repository utilities, schemas, public case contracts, templates, and documented workflow invariants. They do not launch or execute SpaceClaim and are not required for each modeling task. The official `skill-creator` validator is a maintainer tool, not an additional end-user modeling dependency.

For repository maintainers only, validate the installable Skill structure with the official `skill-creator` validator available in the Codex development environment:

```powershell
python <path-to-skill-creator>\scripts\quick_validate.py .\spaceclaim-vision-modeling
```

## Public assets and evidence

Public asset bundles contain redistributable requirement descriptions, geometry reasoning, `.scscript` packages, contracts, structured reports, and bounded evidence records. Source images or drawings are included only when redistribution is confirmed; otherwise their observations, assumptions, and hashes are recorded without packaging the source. Native models, controller screenshots, and machine-specific run artifacts may remain outside the repository; an external artifact is identified by its recorded path and SHA-256 only, and the repository cannot independently inspect its pixels or runtime provenance. Example-specific evidence remains scoped to its own validation record and must not be promoted to a universal capability claim.

## Evidence boundary

The project reports only the validation level actually reached:

| Evidence layer | What it can establish |
|---|---|
| Input interpretation | What was observed, supplied, inferred, assumed, or left unresolved |
| Host-side package checks | Archive structure, API declaration, token rules, resource limits, and selected static invariants |
| SpaceClaim execution | That a particular script reached its recorded runtime stages in the stated environment |
| Geometry measurements | Kernel-reported bodies, bounds, volumes, faces, features, names, and groups that were explicitly measured |
| Visual review | Visible agreement from the recorded views, including silhouette, placement, repetition, and visible topology |
| Native save/reopen | Persistence checks performed on a saved model after an independent reopen |
| Requested export | Only the export format and artifact that were actually produced and checked |

A script file, passing static audit, screenshot, runtime report, or native model does not automatically prove the other layers. Cross-version compatibility must be verified in the target SpaceClaim/API environment.

Runtime evidence is bound to the exact executed artifact. If a public package is revised afterward, its case record must disclose the difference; unchanged geometry logic or passing host checks do not make the revised package byte-for-byte runtime-tested.

## Repository layout

```text
spaceclaim-vision-modeling/
├── README.md
├── CHANGELOG.md
├── VERSION
├── tests/
└── spaceclaim-vision-modeling/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── prompts/
    ├── references/
    ├── scripts/
    └── assets/
        ├── templates/
        └── cases/
```

- `SKILL.md` contains the core agent workflow and routes detailed rules only when needed.
- `prompts/` contains focused contracts for parsing, planning, scripting, debugging, and review.
- `references/` contains modeling, scripting, execution, recovery, visual-interaction, and validation guidance.
- `scripts/` contains deterministic host-side packaging, auditing, report-validation, and comparison tools.
- `assets/templates/` contains reusable SpaceClaim V21 templates.
- `assets/cases/` contains public, redistributable case inputs, reasoning, scripts, contracts, and bounded evidence records.

## Repository constraints

- Use only public and redistributable examples.
- Do not package vendor binaries, proprietary API documentation, licenses, credentials, private models, recordings, unpublished data, or user-specific paths.
- Do not claim universal geometry recognition, unattended desktop reliability, or cross-version API compatibility without corresponding evidence.

This project is independent and is not affiliated with or endorsed by Ansys, Inc.

## License

Licensed under the [Apache License 2.0](LICENSE).
