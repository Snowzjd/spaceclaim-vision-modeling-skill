# P3 action evidence

`snapshot-map.json` binds each selected raw report to the historical configured
source/archive hashes and a portable copy of the exact harness body. Only the
machine-specific configuration prefix was removed. The portable `.py` is build
input, not a claim that those full bytes were loaded in SpaceClaim. Package a
caller-configured copy as `.scscript` for a new run.

The action events bind exact `.scscript` and embedded-source hashes. Accept only
the action's independently passing groups. In particular, `suite-01` retains an
overall failure and later suites provide the repaired operations' evidence.
Do not reinterpret that failed suite as an overall pass.

`fixtures/native-loft.scdoc` is the synthetic native file used in the MA35 test;
its manifest supplies expected bounds, volume and hash. Use a separate run-owned
output directory. No user baseline or licensed runtime dependency is bundled.

These tests establish the listed bounded action implementations, not every
parameter range, native save/reopen persistence, complete visual agreement or
exports. The contracts remain candidates pending integration and acceptance.
