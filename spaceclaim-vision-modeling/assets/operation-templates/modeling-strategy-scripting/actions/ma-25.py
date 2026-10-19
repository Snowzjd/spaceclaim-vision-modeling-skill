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
    # Already enclosed region, seeded on a current face. No caps or repairs.
    source = require_live_body(p["source_body"])
    face = p["seed_face"]
    if face not in list(source.Faces):
        raise ValueError("Seed face must belong to the current source body")
    point = point_mm(p["seed_point_mm"])
    tol = tolerance(p["position_tolerance_mm"])
    seed = face.Shape.ProjectPoint(point)
    if sum((float(getattr(seed.Point, a))-float(getattr(point, a)))**2 for a in ("X", "Y", "Z")) > (tol/1000.0)**2:
        raise ValueError("Seed point must lie on the supplied trimmed face")
    # V21 places the extracted volume under a new component.  The shared
    # current_bodies() helper is intentionally root-body-only. Locate the
    # newly created component and inspect its Content without changing it.
    root = GetRootPart()
    before_components = list(root.GetDescendants[Component]())
    options = VolumeExtractOptions()
    options.CreateShareTopology = False
    options.ImprintCappingEdges = False
    options.MergeCreatedVolume = False
    options.SeedPoint = seed
    result_ok(VolumeExtract.Create(Selection.Empty(), FaceSelection.Create(face), options), "enclosed volume extraction")
    after_bodies = list(root.GetDescendants[DesignBody]())
    after_components = list(root.GetDescendants[Component]())
    created_components = [component for component in after_components if component not in before_components]
    component = one(created_components, "new volume extraction component")
    if source not in after_bodies:
        raise RuntimeError("Volume extraction did not preserve the source body")
    content = component.Content
    if content is None:
        raise RuntimeError("New volume extraction component has no content part")
    component_bodies = list(content.Bodies)
    # Content is PartGeneral; its occurrences are DesignBodyGeneral, not
    # concrete DesignBody. Use IPart.Bodies inside the identified component.
    body = one(component_bodies, "extracted region in new component")
    if list(content.Components):
        raise RuntimeError("Nested extraction components are outside this variant")
    # Occurrence Shape is TrimmedSpace; kernel topology is on its master.
    assert_closed(body.Master)
    return body

if "ATOMIC_INPUT" not in globals() or not isinstance(ATOMIC_INPUT, dict):
    raise ValueError("Supply this action contract input dictionary before execution")
ATOMIC_OUTPUT = operation(ATOMIC_INPUT)
