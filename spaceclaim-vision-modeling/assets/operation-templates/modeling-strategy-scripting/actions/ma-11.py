# Python Script, API Version = V21
# Shared non-mutating helpers. Copied into each formal atomic .scscript.
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import *
from SpaceClaim.Api.V21.Modeler import Body as ModelerBody
from System import Array
import math


def finite(value, label):
    if isinstance(value, bool):
        raise ValueError(label + " must be numeric, not boolean")
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise ValueError(label + " must be finite")
    return value


def vector3(values, label):
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        raise ValueError(label + " requires three coordinates")
    return [finite(v, label) for v in values]


def point_mm(values):
    values = vector3(values, "point_mm")
    return Point.Create(*[v / 1000.0 for v in values])


def direction(values):
    values = vector3(values, "direction")
    length = math.sqrt(sum(v*v for v in values))
    if length <= 1e-12:
        raise ValueError("Direction must be nonzero")
    return Direction.Create(*[v / length for v in values])


def positive(value, label):
    value = finite(value, label)
    if value <= 0:
        raise ValueError(label + " must be positive")
    return value


def tolerance(value):
    value = finite(value, "tolerance")
    if value < 0:
        raise ValueError("Tolerance cannot be negative")
    return value


def near(a, b, tol):
    return abs(float(a) - float(b)) <= tolerance(tol)


def shape_of(body):
    return body.Shape if isinstance(body, DesignBody) else body


def bounds_mm(item):
    shape = item.Shape if hasattr(item, "Shape") else item
    box = shape.GetBoundingBox(Matrix.Identity)
    return [float(v) * 1000.0 for v in (box.MinCorner.X, box.MinCorner.Y, box.MinCorner.Z, box.MaxCorner.X, box.MaxCorner.Y, box.MaxCorner.Z)]


def volume_mm3(body):
    return float(shape_of(body).Volume) * 1e9


def one(items, label):
    values = list(items)
    if len(values) != 1:
        raise ValueError("Expected one " + label + ", found " + str(len(values)))
    return values[0]


def assert_closed(body):
    shape = shape_of(body)
    if not shape.IsClosed or int(shape.PieceCount) < 1 or volume_mm3(body) <= 0:
        raise RuntimeError("Expected a nonempty closed solid")
    return body


def require_transient(body):
    if isinstance(body, DesignBody) or DesignBody.GetDesignBody(body) is not None:
        raise ValueError("This operation variant requires a transient Modeler Body")
    return assert_closed(body)


def require_live_body(body):
    if not isinstance(body, DesignBody) or body not in current_bodies():
        raise ValueError("Expected a current DesignBody from this document")
    return assert_closed(body)


def current_bodies():
    # Explicit V21 method: editor-injected extension methods are not inherited
    # by independently compiled action scopes. Occurrence editing is excluded.
    root = GetRootPart()
    if Window.ActiveWindow.ActiveContext.ActivePart != root:
        raise ValueError("This action variant requires the root part to be active")
    return [body for body in root.GetDescendants[DesignBody]() if body.Parent == root]


def bbox_matches(actual, expected, tol):
    if not isinstance(expected, (list, tuple)) or len(expected) != 6:
        raise ValueError("Expected six bounding coordinates")
    return all(near(actual[i], finite(expected[i], "bbox"), tol) for i in range(6))


def result_ok(result, label):
    if result is not None and hasattr(result, "Success") and not result.Success:
        raise RuntimeError(label + " reported failure")


def require_name(name):
    if not isinstance(name, basestring) or not name.strip():
        raise ValueError("A nonempty object name is required")
    return name


def face_normal(face):
    shape = face.Shape
    geometry = shape.Geometry
    if geometry.GetType().Name != "Plane":
        raise ValueError("This normal variant supports planar faces only")
    normal = geometry.Frame.DirZ
    sign = -1.0 if shape.IsReversed else 1.0
    return [sign * float(v) for v in (normal.X, normal.Y, normal.Z)]


def operation(p):
    # Native root-part shell.  A signed offset expresses both thickness and
    # direction; removing faces and shelling the whole body are separate API
    # branches selected before the kernel call.
    body = require_live_body(p["body"])
    offset_mm = finite(p["offset_mm"], "offset_mm")
    if abs(offset_mm) <= 1e-12:
        raise ValueError("offset_mm must be finite and nonzero")

    raw_faces = p.get("remove_faces", [])
    if raw_faces is None:
        raw_faces = []
    faces = list(raw_faces)
    if len(faces) != len(set(faces)):
        raise ValueError("remove_faces must contain distinct current faces")
    body_faces = list(body.Faces)
    if any(face not in body_faces for face in faces):
        raise ValueError("Every remove face must belong to the current body")

    before = current_bodies()
    if faces:
        result = Shell.RemoveFaces(
            FaceSelection.Create(*faces),
            offset_mm / 1000.0,
            None,
        )
        mode = "remove-faces"
    else:
        result = Shell.ShellBodies(
            BodySelection.Create(body),
            offset_mm / 1000.0,
            None,
        )
        mode = "whole-body"
    result_ok(result, "shell")

    after = current_bodies()
    surviving = [candidate for candidate in after if candidate == body and volume_mm3(candidate) > 0]
    replacements = [
        candidate
        for candidate in after
        if candidate not in before and volume_mm3(candidate) > 0
    ]
    if len(surviving) == 1 and not replacements:
        result_body = surviving[0]
    elif not surviving and len(replacements) == 1:
        result_body = replacements[0]
    else:
        raise RuntimeError("Shell did not yield one identifiable positive-volume root body")

    return {
        "body": result_body,
        "mode": mode,
        "offset_mm": offset_mm,
        "remove_face_count": len(faces),
        "is_closed": bool(result_body.Shape.IsClosed),
        "volume_mm3": volume_mm3(result_body),
    }

if "ATOMIC_INPUT" not in globals() or not isinstance(ATOMIC_INPUT, dict):
    raise ValueError("Supply this action contract input dictionary before execution")
ATOMIC_OUTPUT = operation(ATOMIC_INPUT)
