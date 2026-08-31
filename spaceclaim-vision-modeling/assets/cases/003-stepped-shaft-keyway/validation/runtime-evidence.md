# SpaceClaim V21 runtime evidence

## Controlled run

- Host application: SpaceClaim 2022 R1.
- Scripting API: V21, IronPython 2.7.
- Start state: new unsaved blank design.
- Construction: one formal `.scscript` run using transient coaxial cylinders, Boolean unite/subtract, a rectangular keyway cutter, semantic rounds and chamfers, and one attached final design body.
- Final status: passed; native model saved, closed, reopened, and audited with a separate read-only `.scscript`.

## Confirmed geometry

- One body named `STEPPED_SHAFT_KEYWAY_01`.
- Bounding box: `[0,-19,-19]..[100,19,19] mm`.
- V21 kernel volume: `66658.040821020753 mm3`.
- Face count: `19`.
- Three coaxial outside segments: diameter 20 over 25 mm, diameter 38 over 40 mm, and diameter 28 over 35 mm.
- One diameter-10 through-bore spanning 100 mm.
- One 8 x 8 x 3 mm keyway at the explicit centered assumption X=41..49 mm.
- Four 1 mm x 45 degree end and bore-mouth chamfers.
- Two R1 shoulder fillets.
- The independent native-reopen report reproduced the same body, bounds, volume, face count, and feature measurements.

## Visual review evidence

- Review date: 2026-08-31.
- Active model: the reopened native model in a maximized SpaceClaim 2022 R1 window.
- Review actions were viewport-only. No geometry was edited, no script was run, and the model was not saved.
- The Home overview, axial end view, and keyway-facing side view confirmed the three coaxial outside steps, central through-bore, keyway opening, two rounded shoulders, and the specified end and bore-mouth chamfers without a visually unexpected second body.
- Exact lengths, diameters, keyway dimensions, radii, chamfer measurements, and body volume remain supported by the structured reports rather than by screenshots alone.
- Run-owned screenshots are archived outside the public bundle: `visual-home.png` SHA-256 `10E621806B5B3045AD51319DDBC33087DA2A1A1E56DE2ABA792D0FAEB85D8945`; `visual-end-x.png` SHA-256 `96857C8EFD3357B6D61854A2EEC5804D73BF6ADEA1F10B0386393A7D5BD163DB`; `visual-side-z-keyway.png` SHA-256 `5A9423B9F20365875995FFE57ED56483698BB8299B580B336E4EFBBA96A31830`.

## Evidence artifacts

- Public parameterized build package: `../output/spaceclaim-v21-build.scscript`, SHA-256 `13CC8302B2389C5343FECF0266E4DF37E4479CAD1690067EF61AAF39AB487DD2`.
- Exact run package after output-path injection: SHA-256 `D460BEF10FDCD91055920327A238CC588B7294F552E19E34DA8C500CA30B1246`.
- Public parameterized reopen package: `../output/spaceclaim-v21-reopen-audit.scscript`, SHA-256 `118E74BDC3E9257AD3667DB0898A7ADF6C704995FCF66A193142A91BAEA92D83`.
- Exact run reopen package after path injection: SHA-256 `0F9BBC6F6FD50EA3F6FE58467C68D0A345E8DE2A8AC39E57D6CF8899AE5F8D22`.
- Native model created by the controlled run: SHA-256 `804B6A32C5B6FC0B03F7696FB1F73F8F190C4E44A36A8EC236D0FE9B7117A260`; the native file is not bundled in this case.
- Sanitized forward report: `forward-runtime-report.json`, SHA-256 `6F9E737AFB7D15BFEFAD00D457E65433429F713FDC25A68045F82DAD42389240`.
- Sanitized reopen report: `reopen-runtime-report.json`, SHA-256 `56DCF91A864EF60333EE35FD887C741F08CBA6FD2ECF6F6E838BB50B80DAC6A9`.

The public packages retain unset output paths for redistribution. The exact run packages differ only by injected run-owned paths, so the public hashes are not represented as byte-identical executed-package hashes.

## Evidence boundary

This evidence confirms one controlled SpaceClaim 2022 R1 / API V21 construction, one independent native close/reopen audit, and visible agreement from the three recorded views for this synthetic engineering-drawing case. The unspecified keyway position and ambiguous chamfer scope remain explicit assumptions. It does not establish compatibility with other SpaceClaim releases or arbitrary stepped-shaft geometry.
