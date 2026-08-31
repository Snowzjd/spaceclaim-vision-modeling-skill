# Case 004 requirement

Input type: text description supplied as an image.

Source image SHA-256: `FFFE8EE338B25ACECCB080E9477AE4E1D4DBEA8447DC736AB725E09427564119`.

- Create one rectangular base plate, 120 mm long, 80 mm wide, and 10 mm thick.
- Round the four plan-view corners to R10.
- Extend one central cylindrical support from the plate center, 50 mm high and 30 mm in diameter.
- Create four diameter-8 mounting holes near the plate corners.
- Place every hole center 15 mm from each of its two adjacent plate edges.
- Build a complete three-dimensional model directly from the text.

Interpretation used for the controlled candidate:

- Origin: lower-left corner of the plate bottom.
- X: plate length; Y: plate width; Z: upward through the thickness.
- The 50 mm support height starts at the plate top, so total model height is 60 mm.
- The support and plate form one solid body.
- The four mounting holes pass through the plate thickness only.
- No unspecified chamfers or support-to-plate fillets are added.

The source image labels itself as case 3, but this repository records it as case 004 according to the test sequence.
