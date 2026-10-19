# Python Script, API Version = V21
"""Atomic SpaceClaim V21 template: extrude one parameterized planar profile.

Fill the configuration block before packaging or composing this template.  The
only persistent geometry action is extrusion of the supplied profile into one
new design body.  Translation, rotation, Boolean work, finishing, saving, and
visual navigation are deliberately outside this operation.
"""

from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import CircleProfile, Plane, PointUV, RectangleProfile
from SpaceClaim.Api.V21.Modeler import Body as ModelerBody


PROFILE_KIND = None  # "rectangle" or "circle"
PLANE_NORMAL_AXIS = None  # "X", "Y", or "Z"
PLANE_ORIGIN_MM = None  # [x, y, z]
PROFILE_SIZE_MM = None  # rectangle: [width, height]; circle: [diameter]
EXTRUSION_DISTANCE_MM = None  # signed distance
OUTPUT_BODY_NAME = None
EXPECTED_BBOX_MM = None  # optional [xmin, ymin, zmin, xmax, ymax, zmax]
BBOX_TOLERANCE_MM = 0.001

MM_PER_M = 1000.0


def mm(value):
    return float(value) / MM_PER_M


def point_m(values_mm):
    return Point.Create(mm(values_mm[0]), mm(values_mm[1]), mm(values_mm[2]))


def point_mm(point):
    return [
        float(point.X) * MM_PER_M,
        float(point.Y) * MM_PER_M,
        float(point.Z) * MM_PER_M,
    ]


def body_bbox_mm(body):
    box = body.Shape.GetBoundingBox(Matrix.Identity)
    return point_mm(box.MinCorner) + point_mm(box.MaxCorner)


def near(left, right, tolerance):
    return abs(float(left) - float(right)) <= float(tolerance)


def validate_configuration():
    if PROFILE_KIND not in ("rectangle", "circle"):
        raise ValueError("PROFILE_KIND must be rectangle or circle.")
    if PLANE_NORMAL_AXIS not in ("X", "Y", "Z"):
        raise ValueError("PLANE_NORMAL_AXIS must be X, Y, or Z.")
    if not isinstance(PLANE_ORIGIN_MM, (list, tuple)) or len(PLANE_ORIGIN_MM) != 3:
        raise ValueError("PLANE_ORIGIN_MM must contain three coordinates.")
    if PROFILE_KIND == "rectangle":
        if not isinstance(PROFILE_SIZE_MM, (list, tuple)) or len(PROFILE_SIZE_MM) != 2:
            raise ValueError("Rectangle PROFILE_SIZE_MM must contain width and height.")
    elif not isinstance(PROFILE_SIZE_MM, (list, tuple)) or len(PROFILE_SIZE_MM) != 1:
        raise ValueError("Circle PROFILE_SIZE_MM must contain one diameter.")
    if min([float(value) for value in PROFILE_SIZE_MM]) <= 0.0:
        raise ValueError("Profile dimensions must be positive.")
    if EXTRUSION_DISTANCE_MM is None or abs(float(EXTRUSION_DISTANCE_MM)) <= 0.0:
        raise ValueError("EXTRUSION_DISTANCE_MM must be nonzero.")
    if not OUTPUT_BODY_NAME or not isinstance(OUTPUT_BODY_NAME, basestring):
        raise ValueError("OUTPUT_BODY_NAME must be set.")
    if EXPECTED_BBOX_MM is not None and len(EXPECTED_BBOX_MM) != 6:
        raise ValueError("EXPECTED_BBOX_MM must contain six coordinates.")


def profile_plane():
    axes = {
        "X": (Direction.DirY, Direction.DirZ),
        "Y": (Direction.DirZ, Direction.DirX),
        "Z": (Direction.DirX, Direction.DirY),
    }
    x_axis, y_axis = axes[PLANE_NORMAL_AXIS]
    return Plane.Create(Frame.Create(point_m(PLANE_ORIGIN_MM), x_axis, y_axis))


def configured_profile():
    plane = profile_plane()
    center = PointUV.Create(0.0, 0.0)
    if PROFILE_KIND == "rectangle":
        return RectangleProfile(
            plane,
            mm(PROFILE_SIZE_MM[0]),
            mm(PROFILE_SIZE_MM[1]),
            center,
            0.0,
        )
    return CircleProfile(plane, mm(PROFILE_SIZE_MM[0]) / 2.0, center, 0.0)


def run_atomic_extrusion():
    validate_configuration()
    before = list(GetRootPart().GetAllBodies())
    transient = ModelerBody.ExtrudeProfile(
        configured_profile(), mm(EXTRUSION_DISTANCE_MM)
    )
    if transient is None or not transient.IsClosed:
        raise RuntimeError("Profile extrusion did not produce one closed transient body.")

    DesignBody.Create(GetRootPart(), OUTPUT_BODY_NAME, transient)
    after = list(GetRootPart().GetAllBodies())
    created = [body for body in after if body not in before]
    if len(created) != 1:
        raise RuntimeError("Expected exactly one new body after extrusion.")
    body = created[0]
    if body.Name != OUTPUT_BODY_NAME:
        raise RuntimeError("The extruded body name does not match the operation contract.")
    if EXPECTED_BBOX_MM is not None:
        actual = body_bbox_mm(body)
        if not all(
            near(actual[index], EXPECTED_BBOX_MM[index], BBOX_TOLERANCE_MM)
            for index in range(6)
        ):
            raise RuntimeError("The extruded body bounding box does not match the contract.")
    return body


ATOMIC_RESULT = run_atomic_extrusion()
