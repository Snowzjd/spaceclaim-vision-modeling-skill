# Case 001 SpaceClaim V21 runtime evidence

## Controlled environment

- Date: 2026-08-29
- Application: SpaceClaim 2022 R1
- Scripting API: V21
- Runtime: IronPython 2.7
- Input state: new design saved directly to the run-owned final native-model path
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
- Active model: the reopened native model in a maximized SpaceClaim 2022 R1 window.
- Review actions were viewport-only. No geometry was edited, no script was run, and the model was not saved.
- The Home overview and plan, height, and end views confirmed three separate rectangular bodies with the expected offset pattern, relative spacing, common thickness, and no visually unexpected fourth body.
- Exact bounds, volumes, names, and face-group membership remain supported by the structured reports rather than by screenshots alone.
- Run-owned screenshots are archived outside the public bundle: `visual-home.png` SHA-256 `EC8B7BB81943A87FD59FE90D272424819AC968EDB87CAE992F616AA7A73C12AE`; `visual-plan.png` SHA-256 `8D22BA5E1A68911F80369FFC125EFBF8048C654EBA537BD99A1A59E9D8A6D98F`; `visual-height.png` SHA-256 `B6730CE59F62487CCF822DFDE135113A8DD680C579E0C49A8247D4BF9FB72069`; `visual-end.png` SHA-256 `7A2DCC6B24F6D91800343B7FFB0E02F23924084E6F3EB727BCB38A577DBFD530`.

## Artifact hashes

These hashes identify the original controlled-run artifacts without publishing machine-specific paths:

| Artifact | SHA-256 |
|---|---|
| Native `.scdoc` model | `67A2DF7544E62F2E30338D6A333419523D8ADBC7191D7E355C52A077AAD3D1FF` |
| Original controlled-run forward report | `2E0F04B3B823B95F82CBB003C4CFA19C3FF197F8C5218E53519A6FB292CF07B1` |
| Original controlled-run reopen report | `89FEB64CA386459A06A7EB1F71A778C28926DF31D3158CB1A9472C62C78D5537` |
| Public sanitized forward report | `5FBCC7DD0ECC7353938B4AD8B3D170BC2F930FBAE598E842CA9DD1643244B1E6` |
| Public sanitized reopen report | `5EEE8542A0321AAEDF0FCC95BFF86E29DF66E59962DA7A4CE05EFE264D7B0A0D` |
| Public parameterized build package | `FEB5AEA955A560F4DC973282AE34E625252FC1DBEB587B512F8F3459D264E973` |
| Executed build-script copy | `128858EFBA06E1FDB09F5A9A831DF2B288A3229C88DFEF6092092DB0D56058A9` |
| Executed reopen-audit script | `5CF30B8B4E1791C0D75A458880B23B3400022D56003F792F56A95127979A0130` |

The packaged build template intentionally leaves output paths unset. Compared with the executed copy, its executable modeling, validation, and save logic is unchanged; only machine-specific path values, descriptive comments, and formatting differ. The public reports preserve controlled measurements while replacing run-owned absolute output paths with relative paths.

## Operational learning

An earlier attempt had no active design document, so the application root object was unavailable. No geometry or native model was produced. The corrected sequence was: create a design, save it directly to the final run-owned path, load the script, and run once. A blank design does not need a separate manual body-count review because the script owns the clean-document assertion.

## Evidence boundary

This record proves one controlled run of this public synthetic case in the stated SpaceClaim/API environment, including geometry measurements, case-specific naming, native save, native close/reopen persistence, and visible agreement from the four recorded views. It does not establish universal behavior for other geometries, scripts, SpaceClaim releases, or unperformed exports.
