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
    # Native root-part target-face extrusion.  The source is a current one-face
    # planar sheet; profile construction and semantic face discovery remain
    # caller-owned actions.
    section_policy = p.get("section_policy", "kernel-managed")
    if section_policy not in ("kernel-managed", "preserve", "consume"):
        raise ValueError("Unsupported section policy")

    profile_face = p["profile_face"]
    target_face = p["target_face"]
    travel = direction(p["direction"])
    seed_point = point_mm(p["seed_point_mm"])
    before = current_bodies()

    profile_owners = [body for body in before if profile_face in list(body.Faces)]
    source = one(profile_owners, "profile sheet owner")
    if len(list(source.Faces)) != 1 or source.Shape.IsClosed:
        raise ValueError("Profile face must be the only face of an open sheet body")
    if profile_face.Shape.Geometry.GetType().Name != "Plane":
        raise ValueError("Profile face must be planar")

    target_owners = [body for body in before if target_face in list(body.Faces)]
    one(target_owners, "target face owner")
    if target_face == profile_face:
        raise ValueError("Profile and target faces must be distinct")

    options = ExtrudeFaceOptions()
    options.ExtrudeType = ExtrudeType.ForceIndependent
    result = ExtrudeFaces.UpTo(
        FaceSelection.Create(profile_face),
        travel,
        FaceSelection.Create(target_face),
        seed_point,
        options,
        None,
    )
    result_ok(result, "extrusion to face")

    after = current_bodies()
    source_count_before = len(profile_owners)
    source_count_after = len([body for body in after if profile_face in list(body.Faces)])
    if section_policy == "preserve" and source_count_after != source_count_before:
        raise RuntimeError("Extrusion did not preserve the profile section")
    if section_policy == "consume" and source_count_after != 0:
        raise RuntimeError("Extrusion did not consume the profile section")

    # Do not dereference consumed pre-operation sheet bodies.
    created = [body for body in after if body not in before]
    solids = [body for body in created if body.Shape.IsClosed and volume_mm3(body) > 0]
    result_body = one(solids, "new solid extrusion")
    return {
        "body": assert_closed(result_body),
        "section_policy": section_policy,
        "source_count_before": source_count_before,
        "source_count_after": source_count_after,
    }

if "ATOMIC_INPUT" not in globals() or not isinstance(ATOMIC_INPUT, dict):
    raise ValueError("Supply this action contract input dictionary before execution")
ATOMIC_OUTPUT = operation(ATOMIC_INPUT)
