# SpaceClaim V21 runtime evidence

## Controlled run

- Host application: SpaceClaim 2022 R1.
- Scripting API: V21, IronPython 2.7.
- Start state: new unsaved blank design.
- Construction: one formal `.scscript` run; transient circular-profile extrusions, unite/subtract, one attached design body, semantic rounds and chamfers.
- Final status: passed; native model saved, closed, reopened, and audited with a separate read-only `.scscript`.

## Confirmed geometry

- One body named `FLANGED_PIPE_01`.
- Bounding box: `[0,-24,-24]..[80,24,24] mm`.
- V21 kernel volume: `44370.439806937313 mm3`.
- Face count: `22`.
- One `16 mm` bore spanning `80 mm`.
- Eight `6.5 mm` bolt holes, four per flange, on PCD `36 mm`.
- Four outside-edge chamfers measuring `1 mm` at `45 deg`.
- Two shoulder rounds measuring `R1.5 mm`.
- The independent native-reopen report reproduced the same body, bounds, volume, face count, and feature measurements.

## Visual review evidence

- Review date: 2026-08-31.
- Active model: the reopened native model in a maximized SpaceClaim 2022 R1 window; review actions were viewport-only, with no geometry edit, script run, or save.
- The three screenshot artifacts are archived outside the public bundle. The repository records their paths and SHA-256 values but cannot independently inspect their pixels or verify visual agreement from hashes alone.

| Model/run | View | Selection state | Expected visible features | Observed agreement or discrepancy | Occluded/unresolved | External capture path / SHA-256 |
|---|---|---|---|---|---|---|
| `002-reopened-native / visual-2026-08-31` | Home overview | Cleared | Two end flanges, intermediate tube, central through-bore, repeated bolt-hole pattern, shoulder rounds, and outer-edge chamfers; one body | The overall flange-and-tube arrangement, bore, repeated holes, rounds, and chamfers were visible; no unexpected second body or asymmetry | None observed | `visual-home.png` / `C978A83F89B06A649947CD3AA940D46C0EA9202C2BAA23197D0D4C6910EB2057` |
| `002-reopened-native / visual-2026-08-31` | Axial end (X) | Cleared | Circular flange end profile, central through-bore, and the four-hole pattern on the visible flange | The visible flange profile, bore, and four-hole pattern agreed with the contract | None observed | `visual-end-x.png` / `CB01111CD3FBE1CEE57F04E8FEAB656946FDAC8D0757C323CB42A92C777FEBC2` |
| `002-reopened-native / visual-2026-08-31` | Orthogonal side (Y) | Cleared | Two flange stations, intermediate tube, coaxial bore, shoulder transitions, and specified outer-edge chamfers | Flange spacing, tube, coaxial bore direction, rounds, and chamfers were visually consistent; no unexpected second body | None observed | `visual-side-y.png` / `03A10B4F92D3CA4099EF3090778CB617736B9CABC598B09F99E1B913BB53C44C` |

- Exact diameters, PCD, radii, chamfer measurements, and body volume remain supported by the structured reports rather than by screenshots alone.

## Evidence artifacts

- Public parameterized build package: `../output/spaceclaim-v21-build.scscript`, SHA-256 `544F7043D056F0153A4EAB32FFE7981A261664A7ACDDAF769F1FBFCC876026F8`.
- Exact run package after output-path injection: SHA-256 `C86814E0585BA8D8D5C119F6820FF5F8DBFADA6DFED0D879A19CEC33259F0917`.
- Public parameterized reopen package: `../output/spaceclaim-v21-reopen-audit.scscript`, SHA-256 `CA43B24094D1E6A26D6D6046FAE96C5063DB646FD0F236EB668454CDABDB517E`.
- Native model created by the controlled run: SHA-256 `57FF6F4C7620F3CFA54D575B7AE3DE1B911AD850A5F6C1D0B396A9F16D340556`; the native file is not bundled in this case.
- Sanitized forward report: `forward-runtime-report.json`, SHA-256 `BB3D70157AF892E8D8A9D863B3C550F08E403CD6D7520B2E26B44B5C1B580309`.
- Sanitized reopen report: `reopen-runtime-report.json`, SHA-256 `8749BAE337288DBFA559021514AB3EF2D16004CD3CF7D3FCB2C4C54E1D5DE7EB`.

The public packages retain unset output paths for redistribution. The historical forward-run source permitted its run-owned model path to exist, while the current public build package rejects existing model and report paths and adds stricter preflight/evidence-state guards. Geometry construction, assertions, and the native-save call are unchanged. The current public build/reopen packages have not been rerun after those guard changes and are not byte-identical to the executed packages.

## Evidence boundary

This evidence supports one controlled SpaceClaim 2022 R1 / API V21 construction, one independent native close/reopen audit, and the recorded visual-review conclusion for this synthetic case. The current public packages differ from the executed packages as disclosed above, and the external screenshot pixels are not independently reviewable from this repository. It does not establish compatibility with other SpaceClaim releases or arbitrary flange geometry.
