# Case 002: flanged short pipe from image and text

## Input type

- One perspective reference image supplied by the user.
- One dimensioned textual description.
- The text is authoritative for dimensions; the image supplies visible structure and spatial arrangement only.

The supplied image is not copied into this public case bundle until its redistribution status is confirmed. Its SHA-256 is `3ACE4BC3E547C3C1CB2E0DE1335C279996742974F5CF77FDC5DEAECFC3B6B790`.

## Visual observations

- Two coaxial circular end flanges.
- One straight cylindrical middle section joining the flanges.
- One coaxial through bore.
- Four equally spaced bolt holes on each flange.
- Rounded external shoulders where the middle cylinder meets the inner flange faces.
- Small bevels along the flange outer-diameter edges.

The image appears to show additional edge softening at some hole entrances, but the text does not specify it, so it is not modeled.

## User dimensions

- Overall axial length: `80 mm`.
- Visible straight middle section: `60 mm`.
- Middle outside diameter: `24 mm`.
- Two flanges: each `10 mm` thick and `48 mm` outside diameter.
- Coaxial through bore: diameter `16 mm`.
- Bolt holes: four per flange, diameter `6.5 mm`.
- Bolt-hole pitch circle: diameter `36 mm`.
- Flange outer-edge chamfer: `1 mm x 45 deg`.
- External shoulder fillet: `R1 mm` to `R2 mm`.

## Explicit modeling assumptions

- Use X as the common axis. Set the left outer face to `X = 0 mm` and the right outer face to `X = 80 mm`.
- Place the left flange in `X = 0..10 mm`, the visible middle section in `X = 10..70 mm`, and the right flange in `X = 70..80 mm`.
- Use `R1.5 mm` for the first controlled run, the midpoint of the user-provided `R1..R2` range. Keep it as an exposed parameter.
- Apply the `1 x 45 deg` chamfer to the four circular flange edges at outside diameter `48 mm`. Do not add chamfers to the central bore or bolt holes.
- Create one final solid body named `FLANGED_PIPE_01` for deterministic validation. This name is case-local.

## Required output

- One native SpaceClaim model.
- One forward runtime report.
- One independent native-reopen audit report when the forward run succeeds.
- Evidence-bounded validation of overall bounds, volume, bore, bolt-hole pattern, chamfers, fillets, body name, native save, and reopen persistence.
