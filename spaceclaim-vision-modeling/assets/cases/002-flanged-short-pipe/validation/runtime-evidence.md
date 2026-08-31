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
- Active model: the reopened native model in a maximized SpaceClaim 2022 R1 window.
- Review actions were viewport-only. No geometry was edited, no script was run, and the model was not saved.
- The Home overview, axial end view, and orthogonal side view showed two end flanges, the intermediate tube, the central through-bore, four bolt holes on each flange, shoulder rounds, and the specified flange outer-edge chamfers without visible asymmetry or an unexpected second body.
- Exact diameters, PCD, radii, chamfer measurements, and body volume remain supported by the structured reports rather than by screenshots alone.
- Run-owned screenshots are archived outside the public bundle: `visual-home.png` SHA-256 `C978A83F89B06A649947CD3AA940D46C0EA9202C2BAA23197D0D4C6910EB2057`; `visual-end-x.png` SHA-256 `CB01111CD3FBE1CEE57F04E8FEAB656946FDAC8D0757C323CB42A92C777FEBC2`; `visual-side-y.png` SHA-256 `03A10B4F92D3CA4099EF3090778CB617736B9CABC598B09F99E1B913BB53C44C`.

## Evidence artifacts

- Public parameterized build package: `../output/spaceclaim-v21-build.scscript`, SHA-256 `0E89E668CBFEE8B8515F14392D6F733B34CDF239C48B7661A7D216F03049898E`.
- Exact run package after output-path injection: SHA-256 `C86814E0585BA8D8D5C119F6820FF5F8DBFADA6DFED0D879A19CEC33259F0917`.
- Public parameterized reopen package: `../output/spaceclaim-v21-reopen-audit.scscript`, SHA-256 `3A520E981992BBDD6B4E73FC8810D01B220ED341EA80EDDF9892AABD3E663ED4`.
- Native model created by the controlled run: SHA-256 `57FF6F4C7620F3CFA54D575B7AE3DE1B911AD850A5F6C1D0B396A9F16D340556`; the native file is not bundled in this case.
- Sanitized forward report: `forward-runtime-report.json`, SHA-256 `BB3D70157AF892E8D8A9D863B3C550F08E403CD6D7520B2E26B44B5C1B580309`.
- Sanitized reopen report: `reopen-runtime-report.json`, SHA-256 `8749BAE337288DBFA559021514AB3EF2D16004CD3CF7D3FCB2C4C54E1D5DE7EB`.

The public packages retain unset output paths for redistribution. The exact run package differs only by injected run-owned output paths, so the public package hash is not represented as the byte-identical executed package.

## Evidence boundary

This evidence confirms one controlled SpaceClaim 2022 R1 / API V21 construction, one independent native close/reopen audit, and visible agreement from the three recorded views for this synthetic case. It does not establish compatibility with other SpaceClaim releases or arbitrary flange geometry.
