# SpaceClaim visual interaction and review

Use this reference after desktop control is authorized. Keep the SpaceClaim window maximized or full-screen throughout the authorized control transaction by default. Treat viewport interaction as a read-only observation method unless the task explicitly requires selecting geometry for an operation.

## 1. Preserve a usable viewport

- Keep the SpaceClaim window maximized or full-screen by default. Do not window it merely to make control easier.
- Temporarily use a smaller window only for a blocking dialog, a required side-by-side comparison, or a user-requested layout. Restore the maximized state before model inspection or screenshot capture.
- Confirm that the 3D viewport, Structure tree, status bar, orientation indicator, and required tool controls are visible enough for the current task.
- Dismiss or move nonessential panels only when they materially obscure the model; do not permanently rearrange the user's workspace without permission.

## 2. Calibrate navigation before relying on shortcuts

Use [controller-compatibility.md](controller-compatibility.md) for the declared
controller's input limits and ordinary-control alternatives. This does not add
another controller dependency or require testing every gesture before modeling.

SpaceClaim navigation themes and custom options can remap spin, pan, zoom, and wheel behavior. At the first visual-control gate of a run:

1. capture the active maximized window;
2. place the cursor over empty viewport space;
3. try one small reversible navigation motion;
4. verify the observed result;
5. use the verified mapping for the rest of the run.

Before testing a gesture, confirm that the active desktop controller can express it. Controllers commonly differ in whether they support a modifier held during a mouse action or a middle/right-button drag. If the required combined input is unavailable:

- activate SpaceClaim's Spin, Pan, or Zoom control and use an ordinary left-button drag;
- use the View menu, orientation indicator, Home, Zoom Extents, Plan, or Snap View instead of freehand navigation;
- use the Select modes and selection filters instead of an unsupported modifier-assisted selection when possible;
- request a short user demonstration on a safe model when no deterministic alternative exists.

Do not claim direct automation of `Ctrl`/`Shift` plus mouse input, middle-button drag, or right-button drag until the current controller has exposed and verified that exact operation.

For the default SpaceClaim theme, start with these documented mappings:

| Intent | Default interaction | Verification |
|---|---|---|
| Select | Left click a pre-highlighted object | Status bar and highlight identify the intended object type |
| Add or remove one selection | Hold `Ctrl` and left click | Selection set changes by exactly one intended object |
| Select an edge loop | Double left click an edge; repeat to cycle | The highlighted loop matches the intended topology |
| Select a body | Triple left click the solid | One complete body is highlighted |
| Query coincident or hidden candidates | Hold `Ctrl` and turn the wheel without moving the cursor | Pre-highlight cycles while the cursor location stays fixed |
| Clear selection | Click empty viewport space or press `Esc` when appropriate | No object remains highlighted |
| Open a context menu | Right click without dragging | The context menu opens at the intended object or viewport point |
| Spin | Drag with the middle mouse button | Silhouette and orientation indicator rotate while model geometry stays unchanged |
| Pan | Hold `Shift` and drag with the middle mouse button | Orientation stays fixed while the model moves laterally in the viewport |
| Zoom | Hold `Ctrl` and drag the middle mouse button vertically | Apparent scale changes without changing orientation |
| Wheel zoom | Turn the wheel over the viewport | Apparent scale changes; behavior may depend on navigation options |
| Zoom extents | Press `Alt+Z` | The design or current selection fits the viewport |
| Home view | Press `H` | The saved Home orientation and scale are restored |
| Plan view | Select a plane or planar face and press `V` | The selected plane is viewed head-on |

When direct middle-button dragging is unavailable, the Spin, Pan, and Zoom tools provide the preferred automation path: activate one tool, use a left-button drag in empty viewport space, verify the result, and press `Esc` or select the next required control.

If `Alt+Z` opens an operating-system or GPU overlay instead of fitting the design, close the overlay once and stop using that shortcut for the run. Open SpaceClaim's Zoom menu and choose Zoom Extents, or use another visible fit control that can be verified directly. Do not repeatedly retry a shortcut that another application has intercepted.

Use short drag distances during calibration. If a mapping does not produce the expected result, stop using it and choose the corresponding Orient control, orientation indicator, or verified custom mapping. Do not repeatedly test uncertain gestures on selected geometry.

## 3. Selection and framing

- Observe pre-highlight and status-bar object type before clicking. Do not infer that the frontmost pixel is the intended face, edge, or body.
- Use the selection filter when dense geometry makes object type ambiguous.
- For box selection, drag left-to-right to select objects fully enclosed by the box and right-to-left to select objects touched by the box.
- Hold `Shift` while box-selecting to add; hold `Ctrl` while box-selecting to toggle.
- Use `Ctrl+A` only after selecting the intended object type because it selects similar objects, not every object indiscriminately.
- Use standard or Snap views to reduce overlap before attempting difficult selections.
- Clear diagnostic selections before clean acceptance screenshots. Preserve selection highlighting only when the screenshot is intended to prove which object was inspected.

Right-button drag can invoke mouse gestures. Prefer a stationary right click for context menus and avoid right-button drags in the viewport unless a deliberate gesture has been calibrated.

## 4. Viewpoint ladder

Prefer deterministic viewpoints before free rotation:

1. zoom extents or fit the intended selection;
2. Home, isometric, or trimetric overview;
3. front and back;
4. left and right;
5. top and bottom;
6. Plan or Snap view normal to a critical planar face;
7. short middle-button rotations only for occluded or curved features;
8. a focused view for each unresolved feature.

SpaceClaim provides Trimetric, Isometric, Top, Bottom, Front, Back, Right, and Left views through the View control. The orientation indicator can also snap to axis-normal views and rotate the view in controlled increments. Use these controls instead of long freehand rotations when repeatability matters.

## 5. Visual debugging during modeling

Use visual inspection at meaningful gates, not after every routine click:

- after a script reports success but a required feature appears missing;
- at the first visible divergence from the geometry contract;
- when an object selector or Boolean result is ambiguous;
- after a repair, to verify that the visible failure changed as intended;
- before accepting a model whose required characteristics cannot all be measured through the available script API.

At a debugging gate:

1. capture one overview state;
2. record the view, selection state, visible symptom, and expected appearance;
3. use the smallest deterministic view or selection change needed to isolate the symptom;
4. compare the visual symptom with structured measurements and runtime stages;
5. repair the earliest responsible script stage, not the viewport appearance itself;
6. restart from the clean run entry state when geometry changed.

Do not use manual viewport manipulation to conceal, compensate for, or replace incorrect geometry.

## 6. Final visual acceptance

Final visual agreement is a required evidence layer when the input includes an image, drawing, screenshot, product view, or a text description containing visually checkable structure.

Before declaring visual agreement:

- maximize SpaceClaim and remove blocking dialogs;
- confirm the intended saved or reopened model is active;
- clear unintended selections and fit the complete model;
- inspect the overview and every contract-relevant standard view;
- inspect occluded, internal, repeated, rounded, tapered, and cut features from suitable focused views;
- compare silhouette, proportions, feature presence, placement, symmetry, repetition, and visible topology with the geometry contract;
- capture clean evidence views with adequate model scale and padding;
- record any feature that cannot be visually resolved.

For each evidence image, record:

```text
model or run identifier:
view name or orientation:
selection state:
expected visible features:
observed agreement or discrepancy:
occluded or unresolved features:
capture path and hash, when archived:
```

A screenshot proves only the visible state from that viewpoint. A path or SHA-256 for an image archived outside this repository identifies the artifact but does not expose its pixels for independent review here. A screenshot does not replace dimensional, topological, naming, save, or reopen checks. Mark visual agreement `not_tested` until the multi-view review has actually been performed.

## 7. Efficient control loop

- Prepare the geometry contract, script, and visual checklist before desktop control.
- Use standard views, fit, and calibrated shortcuts to reduce coordinate hunting and repeated screenshots.
- Capture a fresh state after an action that changes focus, layout, modality, selection, or viewpoint, as required by the active controller.
- Do not rerun repository checks or reread unchanged guidance between viewport actions.
- Stop after a few failed attempts at the same interaction. Ask the user to demonstrate the operation on a safe baseline when the mapping or object-selection behavior cannot be established reliably.

## Official documentation basis

The default mappings and view behaviors above are summarized from the public SpaceClaim help pages for [keyboard shortcuts](https://help.spaceclaim.com/v19.0/en/Content/SpaceClaim_shortcuts.htm), [selection](https://help.spaceclaim.com/v19.0/en/Content/Selecting.htm), [box selection](https://help.spaceclaim.com/v19.0/en/Content/Select_Filter.htm), [spinning](https://help.spaceclaim.com/v19.0/en/Content/Orienting_Spinning_your_design.htm), [panning](https://help.spaceclaim.com/v19.0/en/Content/Orienting_Panning_your_design.htm), [zooming](https://help.spaceclaim.com/2016.1.0/en/Content/Orienting_Zooming_into_and_out_of_your_design.htm), [standard views](https://help.spaceclaim.com/v19.0/en/Content/Orienting_Selecting_a_view.htm), and [navigation options](https://help.spaceclaim.com/v19.0/en/Content/Navigation_options.htm). Treat these as defaults to calibrate against the installed release and user navigation theme, not as proof of the current machine configuration.
