# Python Script, API Version = V21
"""Atomic SpaceClaim V21 template: translate one semantically resolved body.

Fill the configuration block before packaging or composing this template.  It
does not create, copy, rotate, pattern, rename, save, or otherwise modify the
target body beyond one translation.
"""

from SpaceClaim.Api.V21 import *


TARGET_BODY_NAME = None  # optional when the before-bounds uniquely identify a body
EXPECTED_BEFORE_BBOX_MM = None  # [xmin, ymin, zmin, xmax, ymax, zmax]
TRANSLATION_AXIS = None  # "X", "Y", or "Z"
TRANSLATION_DISTANCE_MM = None  # signed distance
BBOX_TOLERANCE_MM = 0.001
VOLUME_TOLERANCE_MM3 = 0.001

MM_PER_M = 1000.0
MM3_PER_M3 = 1.0e9


def point_mm(point):
    return [
        float(point.X) * MM_PER_M,
        float(point.Y) * MM_PER_M,
        float(point.Z) * MM_PER_M,
    ]


def body_bbox_mm(body):
    box = body.Shape.GetBoundingBox(Matrix.Identity)
    return point_mm(box.MinCorner) + point_mm(box.MaxCorner)


def body_volume_mm3(body):
    return float(body.Shape.Volume) * MM3_PER_M3


def near(left, right, tolerance):
    return abs(float(left) - float(right)) <= float(tolerance)


def bbox_matches(actual, expected):
    return all(
        near(actual[index], expected[index], BBOX_TOLERANCE_MM)
        for index in range(6)
    )


def validate_configuration():
    if EXPECTED_BEFORE_BBOX_MM is None or len(EXPECTED_BEFORE_BBOX_MM) != 6:
        raise ValueError("EXPECTED_BEFORE_BBOX_MM must contain six coordinates.")
    if TRANSLATION_AXIS not in ("X", "Y", "Z"):
        raise ValueError("TRANSLATION_AXIS must be X, Y, or Z.")
    if TRANSLATION_DISTANCE_MM is None:
        raise ValueError("TRANSLATION_DISTANCE_MM must be set.")
    if TARGET_BODY_NAME is not None and not isinstance(TARGET_BODY_NAME, basestring):
        raise ValueError("TARGET_BODY_NAME must be text or None.")


def expected_after_bbox():
    shift = [0.0, 0.0, 0.0]
    shift[{"X": 0, "Y": 1, "Z": 2}[TRANSLATION_AXIS]] = float(
        TRANSLATION_DISTANCE_MM
    )
    return [
        EXPECTED_BEFORE_BBOX_MM[index] + shift[index % 3]
        for index in range(6)
    ]


def resolve_unique_body(expected_bbox):
    matches = []
    for body in list(GetRootPart().GetAllBodies()):
        if TARGET_BODY_NAME is not None and body.Name != TARGET_BODY_NAME:
            continue
        if bbox_matches(body_bbox_mm(body), expected_bbox):
            matches.append(body)
    if len(matches) != 1:
        raise RuntimeError("Semantic body selection expected one match, found %d." % len(matches))
    return matches[0]


def run_atomic_translation():
    validate_configuration()
    target = resolve_unique_body(EXPECTED_BEFORE_BBOX_MM)
    volume_before = body_volume_mm3(target)
    direction = {
        "X": Direction.DirX,
        "Y": Direction.DirY,
        "Z": Direction.DirZ,
    }[TRANSLATION_AXIS]
    Move.Translate(
        BodySelection.Create(target),
        direction,
        MM(TRANSLATION_DISTANCE_MM),
        MoveOptions(),
    )

    # Re-enumerate after the state-changing operation; do not reuse the handle.
    moved = resolve_unique_body(expected_after_bbox())
    if not near(body_volume_mm3(moved), volume_before, VOLUME_TOLERANCE_MM3):
        raise RuntimeError("Translation changed the target body volume.")
    return moved


ATOMIC_RESULT = run_atomic_translation()
