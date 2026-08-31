# Case 001 SpaceClaim V21 runtime evidence

## Controlled environment

- Date: 2026-08-29
- Application: SpaceClaim 2022 R1
- Scripting API: V21
- Runtime: IronPython 2.7
- Historical run start: a new design was saved directly to the run-owned final native-model path before the script was loaded. This records the 2026-08-29 run as performed; it is not evidence that a current no-baseline run began unsaved.
- Execution: prepared build script loaded and run once; an independent read-only script audited the model after native close/reopen

## Forward result

The build script reached `status: passed`. It created and named three independent bodies, measured their geometry, created the two case-specific face groups, and saved the native model.

| Body | Bounding-box minimum (mm) | Bounding-box maximum (mm) | Volume (mm3) |
|---|---:|---:|---:|
| `BLOCK_01` | `[0, 0, 0]` | `[20, 8, 4]` | `640.0` |
| `BLOCK_02` | `[30, 3, 0]` | `[50, 11, 4]` | `640.0` |
| `BLOCK_03` | `[60, 0, 0]` | `[80, 8, 4]` | `640.0000000000001` |

The case-specific `INLET` and `OUTLET` groups each contained one face. The host validator accepted the forward report against `validation-contract.json` with no issues.

## Native persistence result

After SpaceClaim closed the native document and reopened it from disk, an independent read-only audit returned `status: passed`. The reopened `bodies` and `named_face_groups` sections were exactly equal to the forward report. The reopen report also passed host-side structure validation with no issues.

## Visual review evidence

- Review date: 2026-08-31.
- Active model: the reopened native model in a maximized SpaceClaim 2022 R1 window; review actions were viewport-only, with no geometry edit, script run, or save.
- The four screenshot artifacts are archived outside the public bundle. The repository records their paths and SHA-256 values but cannot independently inspect their pixels or verify visual agreement from hashes alone.

| Model/run | View | Selection state | Expected visible features | Observed agreement or discrepancy | Occluded/unresolved | External capture path / SHA-256 |
|---|---|---|---|---|---|---|
| `001-reopened-native / visual-2026-08-31` | Home overview | Cleared | Three independent rectangular bodies; common thickness; offset arrangement | Three bodies and the expected arrangement were visible; no unexpected fourth body | None observed | `visual-home.png` / `EC8B7BB81943A87FD59FE90D272424819AC968EDB87CAE992F616AA7A73C12AE` |
| `001-reopened-native / visual-2026-08-31` | Plan | Cleared | Relative X spacing and alternating Y offsets | Offset pattern and relative spacing agreed with the contract | None observed | `visual-plan.png` / `8D22BA5E1A68911F80369FFC125EFBF8048C654EBA537BD99A1A59E9D8A6D98F` |
| `001-reopened-native / visual-2026-08-31` | Height | Cleared | Common 4 mm body thickness and three-body separation | Common thickness and separation were visually consistent | None observed | `visual-height.png` / `B6730CE59F62487CCF822DFDE135113A8DD680C579E0C49A8247D4BF9FB72069` |
| `001-reopened-native / visual-2026-08-31` | End | Cleared | Three end profiles and expected end-face arrangement | Three end profiles were visible with no unexpected extra body | None observed | `visual-end.png` / `7A2DCC6B24F6D91800343B7FFB0E02F23924084E6F3EB727BCB38A577DBFD530` |

- Exact bounds, volumes, names, and face-group membership remain supported by the structured reports rather than by screenshots alone.

## Artifact hashes

These hashes identify the original controlled-run artifacts without publishing machine-specific paths:

| Artifact | SHA-256 |
|---|---|
| Native `.scdoc` model | `67A2DF7544E62F2E30338D6A333419523D8ADBC7191D7E355C52A077AAD3D1FF` |
| Original controlled-run forward report | `2E0F04B3B823B95F82CBB003C4CFA19C3FF197F8C5218E53519A6FB292CF07B1` |
| Original controlled-run reopen report | `89FEB64CA386459A06A7EB1F71A778C28926DF31D3158CB1A9472C62C78D5537` |
| Public sanitized forward report | `5FBCC7DD0ECC7353938B4AD8B3D170BC2F930FBAE598E842CA9DD1643244B1E6` |
| Public sanitized reopen report | `5EEE8542A0321AAEDF0FCC95BFF86E29DF66E59962DA7A4CE05EFE264D7B0A0D` |
| Public parameterized build package | `629D1F299076C7E65A29801820DFC7EF971577BF2B717821B4AA0C6CDFBA74F8` |
| Executed build-script copy | `128858EFBA06E1FDB09F5A9A831DF2B288A3229C88DFEF6092092DB0D56058A9` |
| Executed reopen-audit script | `5CF30B8B4E1791C0D75A458880B23B3400022D56003F792F56A95127979A0130` |

The public build package intentionally leaves output paths unset and now rejects both an existing model path and an existing report path. The historical executed package injected run-owned paths and used the already-saved blank model, so its hash is not the public package hash. The current public package also adds stricter preflight/evidence-state guards; its geometry construction, assertions, and native-save call are unchanged, but this revised package has not been rerun in SpaceClaim. The public reports preserve the historical controlled measurements while replacing run-owned absolute paths with relative paths.

## Evidence boundary

This record supports one controlled run of the case geometry in the stated SpaceClaim/API environment, including geometry measurements, case-specific naming, native save, native close/reopen persistence, and the recorded visual-review conclusion. The current public package differs from the executed package as disclosed above, and the external screenshot pixels are not independently reviewable from this repository. This record does not establish universal behavior for other geometries, scripts, SpaceClaim releases, or unperformed exports.
