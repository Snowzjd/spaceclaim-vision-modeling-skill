# Geometry decomposition

## Coordinate system

- Origin: center of the left outer flange face.
- X: common pipe/flange axis, positive from left to right.
- Y and Z: flange radial plane.
- Units: millimetres.

## Primitive decomposition

1. One radius `12 mm`, length `80 mm` axial cylinder provides the continuous outer pipe core.
2. Two radius `24 mm`, thickness `10 mm` cylinders provide the end flanges.
3. Two external concave rounds of radius `1.5 mm` blend the pipe radius into the inner flange faces.
4. Four equal-distance chamfers remove `1 mm` from the four flange outside-diameter edges.
5. One radius `8 mm` cylinder cuts the central bore through the complete `80 mm` length.
6. Eight radius `3.25 mm` cylinders cut the bolt holes. Their centers lie at radius `18 mm` in the YZ plane, at angular positions `0, 90, 180, 270 deg`; four cuts span each flange.

## Sharp volume and V21 kernel result

Before fillets and chamfers, the expected volume is:

```text
2*pi*(24^2 - 8^2)*10
+ pi*(12^2 - 8^2)*60
- 8*pi*(3.25^2)*10
= 44594.9077177071 mm3
```

An initial cross-section estimate for idealized rounds and chamfers gave `44372.3493034248 mm3`. The controlled SpaceClaim V21 construction measured `44370.439806937313 mm3` while independently confirming two `R1.5 mm` toroidal faces and four `1 mm` / `45 deg` conical faces. Use the measured V21 value as the case regression target; retain the sharp value only as a broad construction sanity check.

## Expected final bounds

- Minimum: `[0, -24, -24] mm`.
- Maximum: `[80, 24, 24] mm`.
- Final body count: one.
