# Known issues and retained assumptions

- The keyway axial location is not dimensioned. The controlled model uses X=41 to 49 mm as an explicit centered assumption.
- The generic sharp-edge chamfer note is ambiguous. The controlled model chamfers only the two outer end edges and the two bore mouths; keyway edges remain sharp.
- The drawing's 45-steel note is retained as metadata; no material assignment is performed or claimed.
- The controlled evidence covers SpaceClaim 2022 R1 / API V21. Other API versions require a separate compatibility run.
- The V21 kernel volume is retained as a regression fingerprint for this case, not as a universal analytic value for all modeling kernels.
