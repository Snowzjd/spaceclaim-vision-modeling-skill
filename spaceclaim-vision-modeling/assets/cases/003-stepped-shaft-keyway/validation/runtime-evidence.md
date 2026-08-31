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
- Active model: the reopened native model in a maximized SpaceClaim 2022 R1 window; review actions were viewport-only, with no geometry edit, script run, or save.
- The three screenshot artifacts are archived outside the public bundle. The repository records their paths and SHA-256 values but cannot independently inspect their pixels or verify visual agreement from hashes alone.

| Model/run | View | Selection state | Expected visible features | Observed agreement or discrepancy | Occluded/unresolved | External capture path / SHA-256 |
|---|---|---|---|---|---|---|
| `003-reopened-native / visual-2026-08-31` | Home overview | Cleared | Three coaxial outside steps, central through-bore, and one body without an unexpected second solid | The stepped silhouette, coaxial bore, and single-body presentation were visible as expected | None observed | `visual-home.png` / `10E621806B5B3045AD51319DDBC33087DA2A1A1E56DE2ABA792D0FAEB85D8945` |
| `003-reopened-native / visual-2026-08-31` | Axial end (X) | Cleared | Circular end profile and central through-bore at the selected shaft end | The end profile and bore opening agreed with the contract | None observed | `visual-end-x.png` / `96857C8EFD3357B6D61854A2EEC5804D73BF6ADEA1F10B0386393A7D5BD163DB` |
| `003-reopened-native / visual-2026-08-31` | Keyway-facing side (Z) | Cleared | Three coaxial steps, keyway opening, two rounded shoulders, and end/bore-mouth chamfers | The keyway-facing view showed the step transitions, keyway opening, shoulder rounds, and specified chamfers; no unexpected second body was visible | None observed | `visual-side-z-keyway.png` / `5A9423B9F20365875995FFE57ED56483698BB8299B580B336E4EFBBA96A31830` |

- Exact lengths, diameters, keyway dimensions, radii, chamfer measurements, and body volume remain supported by the structured reports rather than by screenshots alone.

## Evidence artifacts

- Public parameterized build package: `../output/spaceclaim-v21-build.scscript`, SHA-256 `A27D5E7EA644C912B1E204EA68FA98AC9990BD997D31A09A385057F13181821C`.
- Exact run package after output-path injection: SHA-256 `D460BEF10FDCD91055920327A238CC588B7294F552E19E34DA8C500CA30B1246`.
- Public parameterized reopen package: `../output/spaceclaim-v21-reopen-audit.scscript`, SHA-256 `E8A11BBC63FC49BFF22530084FE1C9603650D23ED5255F66F7D4F6CA9DCB088F`.
- Exact run reopen package after path injection: SHA-256 `0F9BBC6F6FD50EA3F6FE58467C68D0A345E8DE2A8AC39E57D6CF8899AE5F8D22`.
- Native model created by the controlled run: SHA-256 `804B6A32C5B6FC0B03F7696FB1F73F8F190C4E44A36A8EC236D0FE9B7117A260`; the native file is not bundled in this case.
- Sanitized forward report: `forward-runtime-report.json`, SHA-256 `6F9E737AFB7D15BFEFAD00D457E65433429F713FDC25A68045F82DAD42389240`.
- Sanitized reopen report: `reopen-runtime-report.json`, SHA-256 `56DCF91A864EF60333EE35FD887C741F08CBA6FD2ECF6F6E838BB50B80DAC6A9`.

The public packages retain unset output paths for redistribution and add stricter preflight/evidence-state guards. Their geometry construction, assertions, and native-save/read-only audit logic are unchanged, but the current packages have not been rerun after those guard changes and are not byte-identical to the executed packages.

## Evidence boundary

This evidence supports one controlled SpaceClaim 2022 R1 / API V21 construction, one independent native close/reopen audit, and the recorded visual-review conclusion for this synthetic engineering-drawing case. The current public packages differ from the executed packages as disclosed above, and the external screenshot pixels are not independently reviewable from this repository. The unspecified keyway position and ambiguous chamfer scope remain explicit assumptions. It does not establish compatibility with other SpaceClaim releases or arbitrary stepped-shaft geometry.
