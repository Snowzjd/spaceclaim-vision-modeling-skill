# Fast SpaceClaim execution workflow

Use this workflow after the geometry contract and script are ready. Spend reasoning time before desktop control, keep the live GUI transaction short, and perform detailed review after the script finishes.

## 1. Prepare once

Before opening or controlling SpaceClaim:

- understand the request and supplied references;
- resolve the target SpaceClaim/API version, inputs, outputs, units, names, and acceptance checks;
- generate the script and runtime-report paths;
- run applicable host-side syntax, package, path, and contract checks together;
- prepare a short visual checklist from the geometry contract;
- obtain authorization for the run.

Do not reread unchanged references, rescan the repository, or rerun the same host checks between routine GUI actions.

## 2. Establish the starting document

Choose exactly one path:

- **No baseline model:** create a new unsaved design, load the prepared script, and run it once. Do not create or save an extra blank working model, and do not manually inspect the blank design for body or group counts; put clean-document assertions in the script. The script writes the validated result directly to a new run-owned native-model path.
- **Baseline model supplied:** create a hash-recorded copy at the final run-owned path, open the copy, and run against it. Never modify the baseline.

## 3. Execute routine setup as one transaction

At the entry gate, observe enough to confirm the target SpaceClaim window, absence of a blocking dialog, the intended new design or baseline copy, and a maximized or full-screen workspace suitable for visual work. Then perform familiar setup actions continuously, as the active controller permits:

```text
new unsaved design or open baseline copy -> open prepared script -> run once
```

Prefer deterministic keyboard commands, accessible controls, and script-driven modeling over repeated screen-coordinate actions. Do not perform a separate repository audit, geometry review, or evidence review after each click. Follow any observation or confirmation required by the active computer-control system, but do not duplicate it with extra domain reviews.

Never press Run again while completion is uncertain.

## 4. Use visual interaction at defined gates

Read [visual-interaction.md](visual-interaction.md) before manipulating the viewport. Preserve the maximized window, calibrate one small reversible motion against the current navigation theme, and then use standard views, fit, selection filters, and short verified drags.

Use visual interaction during modeling only when the script cannot resolve a visible divergence, selector ambiguity, or unexpected result. Reserve the complete multi-view ladder and clean screenshots for final acceptance. Do not turn every routine click into a separate geometry review.

## 5. Stop only at meaningful gates

Use these checkpoints:

1. **Entry state:** correct application and document, no blocking dialog.
2. **Run result:** final runtime-report stage or the first exact error.
3. **Persistence:** expected native file exists; close/reopen only when persistence is part of the acceptance contract.
4. **Final review:** geometry, names, measurements, requested groups, multi-view visual agreement, evidence screenshots, reports, paths, and hashes.

When a native close/reopen check is required, use `scripts/compare_runtime_reports.py` after both reports pass structural validation.

Do not add intermediate visual reviews unless the script cannot observe a required state or a high-risk irreversible operation needs a decision.

## 6. Recover from failure

Record the first failing stage and error once. Do not repeat uncertain clicks or continue from a partially modified document. Patch the smallest responsible script stage, then restart from a new design or a fresh baseline copy.

When cleanup is authorized, close and delete only a failed native model owned by the current run, then start again from a new design or clean baseline copy. Preserve reports needed to explain the failure and never touch the original baseline.

## 7. Hand off once

After final review, return the model and report paths, hashes, validated evidence layers, unresolved risks, and any next safe test. Keep the desktop-control trace secondary to the geometry and validation evidence.
