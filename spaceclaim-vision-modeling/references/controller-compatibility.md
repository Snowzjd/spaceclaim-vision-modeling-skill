# Computer Use compatibility

The runtime dependency is the complete Computer Use plugin, not a separate
SpaceClaim MCP or an extra modeling Skill. Read that plugin's current instructions
and API before control. The reference used in development is the Windows plugin
26.803.81509 with `node_repl` / `@oai/sky`; later compatible versions may be used
after checking their actual exposed interface. Do not install that private npm
package separately or invoke the native helper directly.

## Use the interface that exists

The inspected reference API provides window discovery/activation/state capture,
clicks (button and count), keyboard chords, text entry, scroll and ordinary drag.
It does not expose a modifier field on click/scroll/drag, a drag-button field,
or separate key-down/key-up controls. Sending `Ctrl` once is not holding it during
a later mouse action. A keyboard chord API alone cannot express Ctrl+wheel.

| Need | Supported path or bounded alternative |
| --- | --- |
| Load/run scripts and use menus | Ordinary click, keyboard navigation and text entry; verify focus using the current controller observation |
| Single/double/triple click | `click_count` and `mouse_button` when exposed; verify the resulting selection, since CAD click meanings depend on mode |
| Rotate a view | Activate SpaceClaim Spin and use ordinary left drag; this exact path has bounded development evidence |
| Pan or drag-zoom | Activate SpaceClaim Pan or Zoom, then ordinary left drag; verify one short movement before relying on it; do not claim an untested modifier gesture |
| Fit and standard orientation | Visible Zoom Extents/View controls, Home, and orientation indicator; use known controls instead of arbitrary long drags |
| Box select | Ordinary drag with the intended filter/direction; verify the resulting selection set |
| Ctrl-assisted selection or candidate cycling | Only use an equivalent visible selection control if it actually preserves the requested outcome. In particular, VI-07 requires cycling preselection without committing selection; choosing an object in the tree is not equivalent. If unavailable, use another modeling/selection strategy for the user's task, or report that exact gesture unavailable |
| Screenshot and visual comparison | Capture through the controller and inspect through the declared visual model; bind to the current document and view |

Equivalent paths serve the user's modeling intent, not an artificial requirement
to reproduce a particular mouse gesture. If the user specifically requests that
gesture or an atomic test with a stricter output, retain its exact boundary.
Do not silently use a separate input injector or another undeclared MCP to make
it appear supported. Candidate state and operation evidence are unchanged by
this compatibility reference.

For normal modeling, use the existing generic workflow when no eligible atom or
gesture fits. Reuse calibrated controls while the application/controller setup
is unchanged. Check only the navigation operations needed for the current task;
do not ask a new user to exercise all 139 operations after installation.

## Host capability contract

The plugin above is the reference implementation, not the only admissible
backend. A host may provide the same capability through a CLI command or a local
MCP server, on condition that it satisfies the contract below and is declared
before the run. The prohibition stays: do not add an undeclared input injector or
a second desktop MCP to make a missing capability appear present.

Minimum operation set:

| Operation | Required outcome |
| --- | --- |
| `list_windows` | Enumerate top-level windows with handle, process id, executable name and title |
| `capture_window` | Image of the identified window, bound to its handle and capture time |
| `focus_window` | Foreground the identified window and report whether focus took effect |
| `click` | Pointer action at a stated point in a stated coordinate system |
| `type_text` | Literal text entry into the focused window |
| `key` | One named key or chord in the foreground window |
| `stop` | Stop accepting input and clear actions that have not run |
| `health` | Report backend identity, version, interactive session and queue state |

Every observation and action records: backend identity and version; run id;
window handle and process id; timestamp; coordinate origin; DPI or scale factor;
and, for a capture, the image size in pixels. An action without that metadata
cannot support a later measurement or a repeat of the run.

Capability states are `implemented`, `tested`, `unsupported` and `not_tested`. A
backend that merely exposes a function is `implemented` at most; only a recorded
observation or action on the identified window makes that path `tested`. Do not
promote a whole action list from a subset of tested paths.

Interaction-session rules:

- Capture and input must run in the same interactive desktop session. A locked,
  disconnected or reconnecting session is a stop condition; do not attempt to
  work around it.
- Verify the target window identity before and after each action, and stop on a
  mismatch, a covered window or a blocking dialog.
- Use one backend and one input queue per run.
- A stop request records the latency to an empty queue; the suggested threshold
  is two seconds from request to empty queue with no later action executed. An
  ineffective stop is reported, not retried on another backend.
- Report the coordinate error actually observed and its unit, rather than
  claiming pixel-exact agreement.

Record for each run id which operations were exercised, their observed results
and their failures. This evidence stays host-side: passing the contract does not
establish SpaceClaim execution, geometry or persistence.

## User control and interruption

Windows Computer Use occupies foreground input. Let the user stop the task or
use the app's takeover control before operating the same desktop. After a stop
signal, cease input and do not switch backends to continue. Do not infer control
ownership or a particular backend from a colored screen border. The border and
stop controls belong to the desktop app/plugin, not this Skill.

Official setup and foreground-use rules:
[Computer Use](https://developers.openai.com/codex/computer-use).
