# Known issues and retained assumptions

- The source image labels itself as case 3; the repository uses case 004 to preserve the current test sequence.
- The 50 mm support height is interpreted as starting at the plate top, giving 60 mm total height.
- The support is united with the plate as one body.
- The four mounting holes pass through the plate only.
- No support-junction fillet, chamfer, or other unspecified edge treatment is added.
- Controlled SpaceClaim 2022 R1 / API V21 forward and native-reopen runs passed; this does not establish compatibility with other SpaceClaim releases.
- The V21 kernel measured volume is `128474.05661865692 mm3` in both reports. The analytic preflight value `128473.8907081775 mm3` differs by `0.1659104794 mm3`, within the `5 mm3` contract tolerance.
- A final multi-view visual-agreement review passed on SpaceClaim 2022 R1 for this controlled run; the result is case-specific and does not establish cross-version visual behavior.
- `Alt+Z` was intercepted by the installed NVIDIA overlay during calibration. The visible SpaceClaim Zoom Extents command was used instead.
