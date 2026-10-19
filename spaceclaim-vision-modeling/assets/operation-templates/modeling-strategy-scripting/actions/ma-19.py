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
    # This is a transient, non-associative array.  The source is never
    # transformed; even the zero-angle member is a fresh body copy.
    source = require_transient(p["body"])
    count_value = p["count"]
    if isinstance(count_value, bool):
        raise ValueError("count must be a finite integer >= 2, not boolean")
    count_number = finite(count_value, "count")
    if count_number != int(count_number):
        raise ValueError("count must be an integer >= 2")
    count = int(count_number)
    if count < 2:
        raise ValueError("count must be at least 2")

    step_angle = finite(p["step_angle_degrees"], "step_angle_degrees")
    axis_origin = point_mm(p["axis_origin_mm"])
    axis_direction = direction(p["axis_direction"])
    axis = Line.Create(axis_origin, axis_direction)
    volume_tolerance = tolerance(p["volume_tolerance_mm3"])
    source_volume = volume_mm3(source)

    # Compare angular positions modulo one full turn before creating any
    # copies.  This catches duplicates at 360 degrees and after any number of
    # wrapped turns, including negative steps.
    angles = []
    normalized_angles = []
    for index in range(count):
        angle = step_angle * index
        normalized = math.fmod(angle, 360.0)
        if normalized < 0:
            normalized += 360.0
        for previous in normalized_angles:
            separation = abs(normalized - previous)
            if separation <= 1e-10 or abs(separation - 360.0) <= 1e-10:
                raise ValueError("Circular array contains periodic duplicate angles")
        angles.append(angle)
        normalized_angles.append(normalized)

    instances = []
    for index in range(count):
        instance = source.Copy()
        if instance is source or instance == source:
            raise RuntimeError("Body.Copy did not create an independent instance")
        if index:
            instance.Transform(Matrix.CreateRotation(axis, angles[index] * math.pi / 180.0))
        instance = require_transient(instance)
        if not near(volume_mm3(instance), source_volume, volume_tolerance):
            raise RuntimeError("Circular array instance changed volume")
        instances.append(assert_closed(instance))

    return {
        "instances": instances,
        "angles_degrees": angles,
        "source_policy": "preserved",
        "association": "independent",
    }

if "ATOMIC_INPUT" not in globals() or not isinstance(ATOMIC_INPUT, dict):
    raise ValueError("Supply this action contract input dictionary before execution")
ATOMIC_OUTPUT = operation(ATOMIC_INPUT)
