# Historical checker identity

The three unregistered stage-sized interpretation drafts retain their original
host-check records; they are not selectable atomic operations. Their records
identify the old checker at `scripts/validate_geometry_understanding_outputs.py`
with SHA-256 `1fb78b0cdc159e2ab8e9cb740b545cb60c403ac6a3cb745c311eeab5f92b6e20`.

After the installed-schema path correction, that current script has different
bytes. The exact former source is retained as
[legacy-checker-snapshot.py](legacy-checker-snapshot.py) with the original hash.
It is a historical snapshot, not the installed command to invoke. Use the current
script for new checks. Do not transfer the historical hash or test verdict to
the revised command; its relocation checks are separate maintenance evidence.
