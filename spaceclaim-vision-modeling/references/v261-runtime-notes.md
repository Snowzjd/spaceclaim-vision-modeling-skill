# Runtime notes: SpaceClaim 2026 R1 (scripting API V261)

This file records what was observed while running this package's construction
methods against a 2026 R1 installation. It is **not** a compatibility claim: the
evidenced baseline remains Windows SpaceClaim 2022 R1 with scripting API V21.
Everything below was executed through the in-process `SpaceClaim.Api.V261` API
from a host program, in both headless and visible modes, with and without a
Windows message loop.

Status words follow the repository convention:
`tested` / `partially_testable` / `blocked` / `not_tested`.

## 1. Units are metres, not millimetres

`Body.Shape.Volume` returns cubic metres and `GetBoundingBox` returns metres,
even when the document reports its active length unit as millimetres.

- Convert on the way in: pass `value / 1000.0` to `Point.Create`, profile radii and
  extrusion heights.
- Convert on the way out: `volume_mm3 = Shape.Volume * 1e9`,
  `bbox_mm = bbox * 1000`.
- Consequence: a script that passes millimetre numbers straight into the API and
  compares the raw volume against a millimetre-cubed expectation can "pass" while
  building a part 1000x too large. Check the bounding box, not only the volume.

Status: `tested`.

## 2. `Document.SaveAs` blocks under an in-process host

`Document.SaveAs(path)` did not return in any configuration tested:

| Configuration | Result |
| --- | --- |
| Called inside a script run by `Application.RunScript` | hangs, killed after 90-130 s |
| Called on the host thread inside `WriteBlock.ExecuteTask` | hangs |
| Posted with `Application.ExecuteOnMainThread` | the posted task never runs |
| Same, with the host pumping `Application.DoEvents` | posted task still never runs |
| Visible application window (`ShowApplication = true`) | still hangs |
| Host that owns a real message loop, script on a worker thread | still hangs |

A direct host call outside a write block fails fast with
`Write calls are only allowed inside a write block.`, which shows the call reaches
the API and is rejected by its transaction guard rather than by argument parsing.

Status: `blocked` for `Document.SaveAs` in an in-process host.

## 3. Saving does work: the `DocumentSave` command

The scripting command writes a native document without blocking:

```python
result = DocumentSave.Execute(path)
if not result.Success:
    raise RuntimeError("native save failed")
```

Observed behaviour:

- `DocumentSave` is importable from the `SpaceClaim.Api.V261` namespace used by
  scripts (it is also reachable through `SpaceClaim.Api.V261.Scripting.Commands`).
- The product rewrites the extension to its current container format: a `.scdoc`
  path produces a `.scdocx` file. Callers must record the path actually written,
  not the path they asked for.
- `Document.SaveAsSnapshot(path)` also writes `.scdocx` and does not block; it does
  not bind `Document.Path`, so it is not a substitute for a save that must reopen
  by path.

Status: `tested` for `.scdocx`; `blocked` for a `.scdoc` file on this release.

## 4. STEP export

`Window.ExportPart`/`WindowExportFormat` do not include STEP. The entry point is:

```python
doc.MainPart.Export(PartExportFormat.Step, path, False, None)
```

- Produces an `ISO-10303-21` file written by HOOPS Exchange; the extension is
  rewritten from `.step` to `.stp`.
- `PartExportFormat` also covers Iges, Vda, Parasolid text/binary, Acis, JtOpen,
  Rhino, PdfGeometry/PdfFacets, SketchUp, FMD, Stride and MCNP.

Status: `tested` (export only).

## 5. STEP import does not complete in-process

`Document.Open(stepPath, options)` returns a document, reports metric units and
`IsModified = true`, but the body count stays 0. Tested with:

- `options = None` and `options = ImportOptions.Create()` (including
  `StitchSurfaces = true`);
- polling for 60 s from inside the script;
- a two-phase run: open in one script, idle 10-15 s, measure in a second script;
- the same two-phase run under a host that owns a message loop;
- headless and visible application modes;
- `Document.GetDocument(path)` and an enumeration of every `Window` in the session
  (one window, empty document).

The translation appears to need an interactive session that an in-process host
cannot provide. Import a neutral format through the product UI, or supply the
native document, until a licensed interactive-session route is measured.

Status: `blocked`.

## 6. Fillets and chamfers: present, in a different assembly

An earlier reading of this build concluded that the fillet/chamfer commands were
missing. That was wrong: it looked only in `SpaceClaim.Api.V261.dll`. The commands
live in **`SpaceClaim.Api.V261.Scripting.dll`**, and the selections in
`SpaceClaim.Api.V261.Scripting.Selection`.

```python
import clr
clr.AddReference("SpaceClaim.Api.V261.Scripting")
from SpaceClaim.Api.V261.Scripting.Commands import ConstantRound, Chamfer
from SpaceClaim.Api.V261.Scripting.Selection import EdgeSelection

# edge selection by geometry: radius and z of a circular edge, or bbox of a line edge
sel = EdgeSelection.Create(edges)
result = ConstantRound.Execute(sel, radius_m, None)   # ICommandInfo may be null
result = Chamfer.Execute(sel, distance_m, None)
```

Signature summary:

- `ConstantRound.Execute(ISelection selection, Double radius, ICommandInfo info)`
- `Chamfer.Execute(ISelection selection, Double distance, ICommandInfo info)`
  (plus two-distance and `copy` overloads)
- `FullRound.Execute(ISelection faceSelection, ICommandInfo info)`
- `EdgeSelection.Create(IDesignEdge)` / `Create(IEnumerable<IDesignEdge>)`,
  `FaceSelection.Create(...)` with the same shapes.

Measured effect on a part with the public cases' feature set (180x140x18 plate,
phi96 body, phi132 flange, stepped bore, 4 phi14 holes, 4 phi6.8 holes, 4 ribs):

| stage | volume (mm3) |
| --- | --- |
| prismatic solid | 850,128.476680 |
| after R18 rounds on the 4 plate corners | 845,122.245036 |
| after C1.5 flange rim chamfer | 844,659.252818 |
| after C2 bore-bottom chamfer | 844,324.149602 |
| after C1.5 bore-top chamfer | 844,161.572182 |
| contract volume | 844,020.4 |

That is +0.017% against the contract value, with the four R18 fillets present as
real cylindrical faces (radius 18, four of them) in the reopened document.

Two limits remain:

- The modeler-only route (`Modeler.Body` + profiles) still has no revolve primitive,
  so an axisymmetric feature has to be built as document commands or as
  extrude/boolean compositions.
- `EdgeSelection` is geometry-based; a script must find its edges by radius, bbox or
  position. Recorded `EdgeN` identifiers are not reusable.

Status: `tested`.
## 7. What a caller should check before claiming a run

1. The written path and its extension (`.scdocx` on this release).
2. `Body.Shape.Volume * 1e9` against the contract volume, **and** the bounding box.
3. The body count and per-feature cylindrical radii (a face-radius histogram
   catches missing holes, which a volume comparison can hide).
4. A reopen from a new process, not a second read of the in-memory document.

## Evidence boundary

These notes describe one 2026 R1 installation exercised through the in-process
API. A licensed interactive session, a different build number, or a GUI-driven
translation may behave differently. Nothing here upgrades the package's
compatibility statement, and none of these runs included a licensed user session
with the product's own scripting console.
