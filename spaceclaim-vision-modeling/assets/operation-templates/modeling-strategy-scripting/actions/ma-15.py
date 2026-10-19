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
    # Point-to-planar-face variant: translates, never rotates or deforms.
    # The caller supplies a reference point on one current face of the body.
    body = require_live_body(p["body"])
    reference, target = p["reference_face"], p["target_face"]
    if reference not in list(body.Faces):
        raise ValueError("Reference face must belong to the current moving body")
    if not any(target in list(candidate.Faces) for candidate in current_bodies() if candidate != body):
        raise ValueError("Target face must belong to a different current root body")
    if target.Shape.Geometry.GetType().Name != "Plane":
        raise ValueError("This variant requires a planar target face")
    tol = tolerance(p["position_tolerance_mm"])
    vtol = tolerance(p["volume_tolerance_mm3"])
    reference_point = point_mm(p["reference_point_mm"])
    projected = reference.Shape.ProjectPoint(reference_point).Point
    if sum((float(getattr(projected, a))-float(getattr(reference_point, a)))**2 for a in ("X", "Y", "Z")) > (tol/1000.0)**2:
        raise ValueError("Reference point does not lie on the supplied trimmed face")
    travel = direction(p["direction"])
    plane = target.Shape.Geometry
    n = plane.Frame.DirZ
    denominator = sum(float(getattr(n, a))*float(getattr(travel, a)) for a in ("X", "Y", "Z"))
    if abs(denominator) < 1e-10:
        raise ValueError("Travel direction is parallel to the target plane")
    distance = sum((float(getattr(plane.Frame.Origin, a))-float(getattr(reference_point, a)))*float(getattr(n, a)) for a in ("X", "Y", "Z"))/denominator
    if distance < -tol/1000.0:
        raise ValueError("Target lies behind the supplied travel direction")
    distance = max(0.0, distance)
    endpoint = Point.Create(*[float(getattr(reference_point, a))+distance*float(getattr(travel, a)) for a in ("X", "Y", "Z")])
    projected = target.Shape.ProjectPoint(endpoint).Point
    if sum((float(getattr(projected, a))-float(getattr(endpoint, a)))**2 for a in ("X", "Y", "Z")) > (tol/1000.0)**2:
        raise ValueError("Reference point would miss the trimmed target face")
    before, volume = bounds_mm(body), volume_mm3(body)
    delta = [distance*float(getattr(travel, a))*1000.0 for a in ("X", "Y", "Z")]
    if distance > 0:
        result_ok(Move.Translate(BodySelection.Create(body), travel, distance, MoveOptions()), "move to planar face")
    expected = [before[i]+delta[i%3] for i in range(6)]
    moved = one([b for b in current_bodies() if bbox_matches(bounds_mm(b), expected, tol) and near(volume_mm3(b), volume, vtol)], "moved body")
    return dict(body=moved, delta_mm=delta, reference_endpoint_mm=[float(getattr(endpoint, a))*1000.0 for a in ("X", "Y", "Z")])

if "ATOMIC_INPUT" not in globals() or not isinstance(ATOMIC_INPUT, dict):
    raise ValueError("Supply this action contract input dictionary before execution")
ATOMIC_OUTPUT = operation(ATOMIC_INPUT)
