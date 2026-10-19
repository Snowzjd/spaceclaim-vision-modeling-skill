# P5 independent guidance evaluation

Recorded: 2026-09-08

This is a synthetic-only application of the frozen 44 raw inputs to the matching atomic guidance files. No GUI, SpaceClaim process, native file, geometry measurement, save/reopen, export, or real-file operation was performed. A `plan_only` record is a bounded one-action plan plus output-field shape, not a runtime result. A `refuse` record stops until the stated input ambiguity, omission, or conflict is resolved.

Summary: 44 cases; 10 bounded plans; 34 refusals. Input-state coverage: normal=11, ambiguous=11, missing=11, contradictory=11.

VI-22 uses the current guidance hash 704ea3221a7a8534c98f944141404c40bde158920e302bea7d68c691baf232b7; its preparation boundary is preserved: maximization and selection clearing belong to EX-03/VI-08, while VI-22 only captures an already-ready viewport.

| Catalog | Input state | Disposition | Bounded decision |
|---|---|---|---|
| VA-04 | normal | plan_only | Bind the current synthetic document/root scope and enumerate its current bodies once without ordinal selection. |
| VA-05 | ambiguous | refuse | The body reference must be made unique before any face enumeration. |
| VA-06 | missing | refuse | No edge enumeration is permitted without a current body snapshot. |
| VA-07 | contradictory | plan_only | Count the supplied collection once and compare the declared count under the stated solid-body scope. |
| VA-08 | normal | plan_only | Resolve body-08 in global-mm and read its six kernel bounds once. |
| VA-09 | ambiguous | refuse | The body reference resolves to two candidate bodies, so a volume cannot be bound to one object. |
| VA-10 | missing | refuse | The body surface-area measurement is absent; no value may be substituted from volume or a face. |
| VA-11 | contradictory | refuse | The request combines area, normal, and center, and the supplied normal samples disagree; the guide permits one property/record only. |
| VA-12 | normal | plan_only | Read the underlying geometry type of face-12 once and compare it with the analytic-type criterion. |
| VA-13 | ambiguous | refuse | Two cylinder-axis candidates are supplied for one face, so radius/axis/span cannot be bound uniquely. |
| VA-14 | missing | refuse | The conical angle convention is absent; half-angle versus full-angle cannot be inferred. |
| VA-15 | contradictory | refuse | The torus association is unresolved and the supplied major/minor radii are physically inconsistent for the requested fillet radius. |
| VA-16 | normal | plan_only | Compare the three supplied feature positions against the one linear 20-mm rule in the common global frame. |
| VA-17 | ambiguous | refuse | Two objects have the same observed name and no unique target identity is supplied. |
| VA-18 | missing | refuse | The expected member identity set is absent; count-only comparison is prohibited. |
| VA-19 | contradictory | refuse | The declared and observed hashes differ, and the synthetic URI is not an observed absolute regular file path. |
| VA-20 | normal | refuse | The input has a completed-looking save event but lacks the guide's explicit passed save_record/hash binding and uses a synthetic path. |
| VA-21 | ambiguous | refuse | Two open documents match the supplied title/path clues, so one close target cannot be selected safely. |
| VA-22 | missing | refuse | The target SpaceClaim session is absent, so one native file cannot be bound to one opening session. |
| VA-23 | contradictory | refuse | The raw input lacks the required single native_reopen observation and artifact hash, while the supplied property values differ. |
| VA-24 | normal | plan_only | Verify the supplied model, STEP path, and explicit options, then issue one visible export request only. |
| VA-25 | ambiguous | refuse | Two reimported objects share the source and no single measured observation/reference value/artifact hash is supplied. |
| VI-01 | missing | refuse | Maximized/unobstructed window state and review-object visibility are missing. |
| VI-02 | contradictory | refuse | The controlled mapping contains both orbit/pan results for the same middle-drag gesture and two profiles. |
| VI-03 | normal | plan_only | Set the body filter, use the supplied pre-highlighted point, and issue one ordinary left click. |
| VI-04 | ambiguous | refuse | The target semantic object has two occurrences, so a Ctrl-toggle cannot be bound to one visible target. |
| VI-05 | missing | refuse | The double-click mapping/calibration is absent, so the loop gesture is not safe to issue. |
| VI-06 | contradictory | refuse | The active filter says face while the gesture binding says complete body; one body-selection mode must be resolved first. |
| VI-07 | normal | refuse | Two candidates overlap at the cursor, but the input does not identify the currently preselected candidate/order. |
| VI-08 | ambiguous | refuse | The clear control is calibrated, but the supplied selection set is not bound to an observed active session state. |
| VI-09 | missing | refuse | The viewport rectangle is absent, so a box drag cannot be bounded. |
| VI-10 | contradictory | refuse | The context target is face-vi10 but the focus/menu state identifies body-vi10. |
| VI-11 | normal | plan_only | Verify the empty maximized viewport and middle-drag Spin mapping, then perform one short rotation drag. |
| VI-12 | ambiguous | refuse | Two navigation profiles map the same lateral drag to different actions. |
| VI-13 | missing | refuse | The Ctrl+middle Zoom mapping/equivalent is absent. |
| VI-14 | contradictory | refuse | The wheel mapping says positive steps zoom in while the supplied observed/recorded scale factors conflict. |
| VI-15 | normal | plan_only | Resolve the whole-model range and issue one verified Zoom Extents/fit command. |
| VI-16 | ambiguous | refuse | Two Home definitions are supplied for the target session. |
| VI-17 | missing | refuse | The model coordinate frame is absent, so a standard direction cannot be interpreted exactly. |
| VI-18 | contradictory | refuse | The declared back side and raw +normal view direction conflict with the supplied front/back convention. |
| VI-19 | normal | plan_only | Resolve fillet-vi19 and use only the permitted calibrated camera adjustments to create one focused local view. |
| VI-20 | ambiguous | refuse | The reference projection is null, so actual/reference views are not yet comparable despite matching direction. |
| VI-21 | missing | refuse | No occlusion/uncertainty reason is supplied. |
| VI-22 | contradictory | refuse | The model hashes conflict, expected_and_observed metadata is absent, and maximized/selection-ready viewport state is not established. |
