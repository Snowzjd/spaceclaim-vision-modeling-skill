# P4 independent guidance delta: ER-04, ER-05, ER-08

This delta recomputes only ER-04, ER-05, and ER-08 against the unchanged
synthetic input snapshot (`raw-inputs.json`, SHA-256
`aabef50fb9f00315ad2bf3eee4bbb482f9be24552e26b944db850b135fa6ce9d`). The
original `results.json` and `evaluation.md` are intentionally preserved. The
three current guide hashes are recorded in `delta-results.json`.

No GUI, SpaceClaim, host filesystem, save, deletion, or script execution was
performed. `plan_ready` means only that a bounded static fragment/plan is
available; it is not a runtime result.

| ID | Updated outcome | Revised behavior |
|---|---|---|
| ER-04 | `plan_ready` | The selector now indexes the supplied dictionary records (`c['parent_body']`, `c['geometry_type']`, `c['bbox_mm']`) and asserts one match. It does not pretend those fixture keys are SpaceClaim object properties. |
| ER-05 | `needs_manual_review` | Only `faces = list(body.Faces)` is emitted immediately after `body.Subtract([tool])`. The consumer binding remains unresolved because the input supplies no usable selector/helper/tolerance; no `one`, `bbox_matches`, `tolerance`, or ordinal fallback is introduced. |
| ER-08 | `needs_manual_review` | The target scope is `body-02`, while the suffix rule edits non-target `body-01`. The conflict is preserved; no final name or rename plan is silently chosen. |

The delta therefore has one bounded dictionary-fixture selector plan and two
explicit manual-review stops. It does not claim downstream geometry, naming,
or host effects.
