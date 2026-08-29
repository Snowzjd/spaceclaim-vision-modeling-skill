# Failure recovery

## Wrong object selected

Stop at the earliest incorrect state. Compare the intended location, normal, area, bounding box, and adjacency with the selector. Replace numbered aliases or tree-order assumptions with a unique semantic predicate.

## Stale handles after a topology change

Re-enumerate bodies and faces after the operation. Never reuse an object captured before merge, split, intersect, subtract, repair, or import.

## Unexpected Boolean result count

Inspect all post-operation bodies. Classify them by geometry rather than return order. Do not delete candidates until their role is proved.

## Open or incorrectly extracted volume

Audit enclosure, cap contact, seed placement, and free boundaries. If cap-and-extract remains state-sensitive, consider direct domain construction and validate the new strategy independently.

## Named group collision

Use the named-selection object returned by creation, not a localized default group name. Check for automatic suffixes and verify memberships after reopening.

## Path or encoding failure

Prefer forward slashes in embedded Windows paths. Keep generated runtime paths explicit and avoid relying on the application’s current directory.

## GUI or application-state failure

Confirm the active model and script tab before running. Run once, wait for the application’s completion indicator and runtime report, and never press the run command repeatedly on an uncertain state. Restart from a clean copy rather than continuing a partially modified model.

## Save appears incomplete

Treat geometry display, final report marker, file creation, and native reopen as separate events. Wait for the application to finish post-processing before closing or starting the next case.
