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
    # This binding is deliberately limited to a native, non-nested .scdoc
    # component.  It does not open/replace the active document or apply unit
    # overrides for foreign formats.
    import hashlib
    import os

    source_path = p["source_path"]
    if not isinstance(source_path, basestring) or not source_path.strip():
        raise ValueError("source_path must be a nonempty path")
    source_path = source_path.strip()
    if not source_path.lower().endswith(".scdoc"):
        raise ValueError("Only native .scdoc sources are supported")
    if not os.path.isfile(source_path):
        raise ValueError("source_path must identify an existing file")
    if any(key in p for key in ("format", "units", "unit_override", "import_options")):
        raise ValueError("Foreign-format and unit-override options are unsupported")

    expected_hash = p["source_sha256"]
    if not isinstance(expected_hash, basestring) or len(expected_hash) != 64:
        raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
    expected_hash = expected_hash.lower()
    if any(character not in "0123456789abcdef" for character in expected_hash):
        raise ValueError("source_sha256 must be hexadecimal")

    expected_count_value = p["expected_body_count"]
    if isinstance(expected_count_value, bool):
        raise ValueError("expected_body_count must be a positive integer, not boolean")
    expected_count_number = finite(expected_count_value, "expected_body_count")
    if expected_count_number != int(expected_count_number):
        raise ValueError("expected_body_count must be an integer")
    expected_count = int(expected_count_number)
    if expected_count <= 0:
        raise ValueError("expected_body_count must be positive")

    bbox_tolerance = tolerance(p["bbox_tolerance_mm"])
    volume_tolerance = tolerance(p["volume_tolerance_mm3"])
    signatures = list(p["expected_body_signatures"])
    if len(signatures) != expected_count:
        raise ValueError("expected_body_signatures must match expected_body_count")
    normalized_signatures = []
    for signature in signatures:
        if not isinstance(signature, dict) or "bbox_mm" not in signature or "volume_mm3" not in signature:
            raise ValueError("Each body signature requires bbox_mm and volume_mm3")
        bbox = signature["bbox_mm"]
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 6:
            raise ValueError("Each body signature bbox_mm requires six coordinates")
        bbox = [finite(value, "bbox_mm") for value in bbox]
        volume = finite(signature["volume_mm3"], "volume_mm3")
        if volume <= 0:
            raise ValueError("Expected body volumes must be positive")
        normalized_signatures.append((bbox, volume))

    with open(source_path, "rb") as source_file:
        verified_hash = hashlib.sha256(source_file.read()).hexdigest().lower()
    if verified_hash != expected_hash:
        raise ValueError("source_sha256 does not match source_path")

    # The active root part is the only supported import target.  All guards
    # above run before Component.CreateFromFile can mutate the document.
    root = GetRootPart()
    if Window.ActiveWindow.ActiveContext.ActivePart != root:
        raise ValueError("This import variant requires the root part to be active")
    before_components = [component for component in root.GetDescendants[Component]() if component.Parent == root]

    options = ImportOptions.Create()
    Component.CreateFromFile(root, source_path, options)

    after_components = [component for component in root.GetDescendants[Component]() if component.Parent == root]
    imported_components = [component for component in after_components if component not in before_components]
    component = one(imported_components, "new direct-root imported component")
    if component.Parent != root:
        raise RuntimeError("Imported component is not a direct child of the active root")

    nested_components = list(component.Content.Components)
    if nested_components:
        raise RuntimeError("Nested .scdoc component sources are outside this variant")

    bodies = list(component.Content.Bodies)
    if len(bodies) != expected_count:
        raise RuntimeError("Imported body count differs from expected_body_count")

    measurements = []
    for body in bodies:
        assert_closed(body.Master)
        measurements.append({
            "body": body,
            "bbox_mm": bounds_mm(body),
            "volume_mm3": volume_mm3(body.Shape),
        })

    # Match each supplied signature uniquely by geometry, never by import
    # enumeration order or the opaque return value of CreateFromFile.
    remaining = list(range(len(measurements)))
    for expected_bbox, expected_volume in normalized_signatures:
        matches = [
            index for index in remaining
            if bbox_matches(measurements[index]["bbox_mm"], expected_bbox, bbox_tolerance)
            and near(measurements[index]["volume_mm3"], expected_volume, volume_tolerance)
        ]
        if len(matches) != 1:
            raise RuntimeError("Expected body signature did not resolve uniquely")
        remaining.remove(matches[0])
    if remaining:
        raise RuntimeError("Imported body signatures did not cover every body")

    with open(source_path, "rb") as source_file:
        unchanged_hash = hashlib.sha256(source_file.read()).hexdigest().lower()
    if unchanged_hash != verified_hash:
        raise RuntimeError("Source file changed during import")

    return {
        "component": component,
        "bodies": bodies,
        "source_sha256": verified_hash,
        "measurements": measurements,
    }

if "ATOMIC_INPUT" not in globals() or not isinstance(ATOMIC_INPUT, dict):
    raise ValueError("Supply this action contract input dictionary before execution")
ATOMIC_OUTPUT = operation(ATOMIC_INPUT)
