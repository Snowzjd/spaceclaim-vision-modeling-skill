# Composition case 001: rectangular prism

This is a retained v0.3 four-stage composition case. The directory name is a
legacy development path and does not define atomic granularity. The case contains one
axis-aligned rectangular solid and no holes, rounds, chamfers, patterns, named
face groups, or additional bodies.

The source dimensions and body name belong only to this case. The reusable
operation templates consume parameters and do not contain these values.

## Case stage record

1. Interpret the case source into its accepted geometry contract.
2. Produce the case-specific formal build `.scscript`.
3. Run that exact artifact once in a new unsaved design and record the earliest failure or success state.
4. Apply the case-specific read-only audit and multi-view acceptance contract.

Host checks cover schema invariants, source binding, generated source, package
structure, and static audit. A controlled SpaceClaim 2022 R1 / API V21 run of
the exact generated artifacts has also passed for this case: the build script
ran once from a new unsaved design, saved a native model, the native model was
closed and reopened, a separate read-only validation script reproduced the
expected measurements, and overview/top/front/right visual review agreed with
the case contract.

The case-shaped interpretation, full-part script generation, and full-part
validation records are not atomic templates and are not registered. This case
proves the exact four-stage path for one parameter set; it does not by itself
establish cross-version or reusable action behavior. See
`stages/04-validation-visual-review/evidence/runtime-evidence.md` for the exact
artifact identities and evidence boundary.

## Reproduce in a new location

The retained output `.py`/`.scscript` pairs are exact historical run artifacts,
including their standard Windows Public Documents destinations. Do not run
those fixed-destination specimens as a new job. Preserve their hashes as evidence.

Generate fresh build and validation packages from this case's geometry contract
using `scripts/generate_rectangular_prism_scscript.py` in the installed package.
Supply `--mode build` or `--mode validate`, `--source-output`,
`--scscript-output`, and an explicit new `--run-directory` for this machine.
The generator derives the native/report destinations from that run directory
and refuses output overwrite by default. Generated packages must be preflighted
and executed in the new run before claiming new runtime evidence; historical
hashes do not validate their changed configuration.
