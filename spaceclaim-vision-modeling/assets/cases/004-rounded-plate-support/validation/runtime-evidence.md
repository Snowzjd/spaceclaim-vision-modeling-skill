# SpaceClaim V21 runtime evidence

## Controlled environment and run separation

- Host application: SpaceClaim 2022 R1.
- Scripting API: V21, IronPython 2.7.
- Forward start state: a new unsaved blank design.
- Forward construction: one formal `.scscript` run using transient prismatic and circular solids, Boolean unite/subtract, semantic R10 corner rounds, and one attached final design body.
- Native reopen: the saved native model was closed and reopened, then an independent read-only audit `.scscript` was run once. The audit does not modify or save the model.
- Forward status: passed; native save occurred after geometry assertions passed.
- Native-reopen status: passed; the forward/reopen report comparison passed.

## Forward-run evidence

- One body named `ROUNDED_PLATE_SUPPORT_01`.
- Measured bounding box: `[0,0,0]..[120,80,60] mm` (report values are within floating-point roundoff of these limits).
- V21 kernel volume: `128474.05661865692 mm3`.
- Face count: `16`.
- One 120 x 80 x 10 mm plate with four R10 plan-view corner rounds.
- One centered diameter-30 support with visible height 50 mm above the plate top.
- Four diameter-8 through-holes at 15 mm offsets from their adjacent plate edges.
- The structured forward report passed the case contract.

## Native-reopen evidence

- The independent read-only audit reproduced one body with the same name, bounding box, volume, face count, and feature measurements.
- Reopened V21 kernel volume: `128474.05661865692 mm3`.
- Reopened feature checks passed for the four R10 corner cylinder faces, the central support cylinder, and the four mounting-hole cylinder faces.
- Forward/reopen comparison passed for the persisted body geometry and declared feature measurements.

## Visual review evidence

- Review date: 2026-08-31.
- Active model: the reopened `004-rounded-plate-support` native model in a maximized SpaceClaim 2022 R1 window; review actions were viewport-only, with no geometry edit, script run, or save during visual calibration.
- The three screenshot artifacts are archived outside the public case bundle. The repository records their paths and SHA-256 values but cannot independently inspect their pixels or verify visual agreement from hashes alone.
- Verified interaction path: left-click face selection, blank-space selection clearing, stationary right-click context menu with `Esc` dismissal, wheel zoom, `H` Home view, SpaceClaim Spin/Pan/Zoom controls with ordinary left-button drags, the visible Zoom Extents command, and orientation-indicator snaps used to obtain the recorded face-normal views.
- `Alt+Z` was intercepted by the installed NVIDIA overlay, so it was not used as the Zoom Extents path for this run.
- No case-contract feature remained visually unresolved. Dimensions and exact radii remain supported by the structured forward/reopen measurements rather than by screenshots alone.

| Model/run | View | Selection state | Expected visible features | Observed agreement or discrepancy | Occluded/unresolved | External capture path / SHA-256 |
|---|---|---|---|---|---|---|
| `004-reopened-native / visual-2026-08-31` | Home overview | Cleared | Rounded rectangular plate, four corner mounting holes, centered cylindrical support, and one body | The rounded plate, four holes, centered support, and absence of selection highlighting were visible; no unintended second body appeared | None observed | `visual-home.png` / `BC0415BA3A056A79D7FFC22CA69B7F518ADA44F032D7F1D72A43D2A377E56E86` |
| `004-reopened-native / visual-2026-08-31` | Face-normal front (Z) | Cleared | 120 x 80 rounded-rectangle silhouette, four symmetric through-holes, and centered support placement | The silhouette, hole symmetry, and centered support agreed with the contract | None observed | `visual-front-z.png` / `54A297AA0885BC851F812E059175E9964FF5FFD5DD8E1A613C82729F8AF41858` |
| `004-reopened-native / visual-2026-08-31` | Orthogonal side (X) | Cleared | Plate thickness, support protrusion direction and relative height, and no asymmetric second body | Thickness, protrusion direction, and relative height were visually consistent; no unexpected second body or asymmetric feature was visible | None observed | `visual-side-x.png` / `D3FCF5E3A0E2867B6A6575B86F4BA431E96479746DA1EB571575EBF74ABBADAA` |

## Evidence artifacts and hashes

- Public parameterized build package: `../output/spaceclaim-v21-build.scscript`, SHA-256 `820C56F538899D311C106F400FE0A5DD09443F99056D8C4B7E7FB75E6E13CA3C`.
- Exact forward run package after run-owned output-path injection: SHA-256 `53E86FF158A27FF3AEF5B9ACB943E0E31CA4655447347C9AEF0448335C575C0B`.
- Public parameterized reopen package: `../output/spaceclaim-v21-reopen-audit.scscript`, SHA-256 `50D619760F21B9253D350401048014AE7311EF1C1D30D00CCBAD97C10B56DF4F`.
- Exact native-reopen run package after run-owned output-path injection: SHA-256 `0084229E8810BFEC04085C22695A5654D831D36786F92BE7D67C6E0404C9C059`.
- Native model created by the controlled forward run: SHA-256 `A8B77EE37CB3EC57DCD3DC54CC8BAC0F0A3349EB3E8768C7F6F30170CE840B0D`; the native file is not bundled in this public case.
- Original controlled-run forward report: SHA-256 `AFEA8A6AB8D84ECC9DFFB402ACE2A365859EC05053B56193B8B3A1ADD2799D7C`.
- Original controlled-run native-reopen report: SHA-256 `E9434F66C6F7A1B1932DD50C45C0E60A33750F0CE256FB097F944C489320059E`.
- Public sanitized forward report: `forward-runtime-report.json`, SHA-256 `E03110D5F7FEC9B0E02148FB6363A99E9B4429D8C11CF077A48FEB5AB30C4643`.
- Public sanitized native-reopen report: `reopen-runtime-report.json`, SHA-256 `0B0A3FE36D33C0C7446236855EF1B7B7581E2904EAA865A684464924E3282BEC`.

The public packages retain unset output paths for redistribution and add stricter preflight/evidence-state guards. Their geometry construction, assertions, native-save call, and read-only audit logic are unchanged, but the current packages have not been rerun after those guard changes and are not byte-identical to the executed packages. The public reports preserve controlled measurements while replacing run-owned absolute output paths with relative paths.

## Evidence boundary

This evidence supports one controlled SpaceClaim 2022 R1 / API V21 construction, one independent native close/reopen audit, and the recorded visual-review conclusion for this synthetic case. The current public packages differ from the executed packages as disclosed above. Host-side checks and static audits establish source, package, and report-contract properties only; external screenshot hashes do not expose pixels for independent review. The evidence does not establish cross-version compatibility.
