# Installed runtime and first-run check

Use after installation, controller/version changes or a missing-dependency error.
This is setup, not another mandatory modeling stage or a per-click audit.

## Fixed dependency boundary

The complete path is: vision-capable agent with local file/terminal access;
Computer Use plugin with its Skill and control service; Windows SpaceClaim
2022 R1 / scripting API V21 / IronPython 2.7; CPython 3.12.x plus this package's
requirements.txt in a host virtual environment. Read the repository README for
installation commands. Use the installed `.venv/Scripts/python.exe` for host
tools and `.scscript` in SpaceClaim. Do not run host Python inside SpaceClaim.

No additional modeling Skill, CAD MCP, renderer, document converter, image
generation service or private development directory is a runtime prerequisite.
For reference drawings supplied as images, inspect the image directly. If a
source format cannot be read by the declared environment, ask for an accessible
image/text representation rather than silently relying on another converter.
Raw demonstration recording and future source extensions are not implemented
by declaring a reserved extension slot.

The package contains its 139 operation implementations/guidance, schemas and
modeling references. Repository tests and the official Skill validator are
maintainer-only. Their absence in a standalone install is not a failure of
modeling and not a new successful test. Historical evidence remains scoped to
the exact recorded bytes, environment, and operation variant.

## First-run procedure

1. Run `scripts/check_installation.py` with the selected host interpreter. Fix
   dependency/resource failures first. The JSON report never certifies live CAD.
2. Confirm the agent can inspect the user's actual reference image (or a public
   package image) and describe a visible feature. A filename/transcript alone
   does not pass image access. Text-only preparation can skip this explicitly.
3. Load the installed Computer Use Skill and initialize its documented runtime.
   On the reference Windows plugin this is `node_repl` importing `@oai/sky`.
   Use only the plugin-provided interface. Do not search for/spawn its helper,
   replace it with a custom input injector, or enable unrelated desktop MCPs.
4. Explain the intended live setup observations and obtain run-scoped desktop
   authorization. Enumerate/identify the actual SpaceClaim window, confirm the
   application and scripting version and absence of license/blocking dialogs.
   Preserve existing designs; keep SpaceClaim maximized during active control.
5. Capture and inspect the target window. Confirm target focus, screenshot
   identity and supported input API. Test one reversible navigation control on
   a safe visible model, or defer navigation until a run-owned model exists.
6. Apply `controller-compatibility.md` to actions needed by the task. A host
   package pass and an available click function do not prove every GUI path.
   If a required variant lacks a direct or verified equivalent route, stop that
   action and report the exact gap. Do not borrow undeclared tools or relabel an
   unrelated outcome as equivalent.
7. Record host interpreter, package/version, application/API identity, controller
   identity, image/screenshot access and calibrated routes with actual evidence.
   Leave unobserved fields `not_tested`. Reuse this setup while unchanged; refresh
   target/focus observations as required by the controller during execution.

## Stopping control

Windows Computer Use occupies foreground input. Stop the task/control session
before operating the same desktop. Honor the controller's stop/end signal; do
not immediately retry or switch to a different input mechanism. A colored border
is controller UI, not an authorization token or proof that inputs are released.
An ineffective stop control is a controller failure to report, not permission to
continue. Do not attempt to remove overlays or change security settings.
