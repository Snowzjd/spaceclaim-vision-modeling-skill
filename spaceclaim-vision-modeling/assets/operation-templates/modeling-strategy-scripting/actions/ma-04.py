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
    plane, kind = p["plane"], p["kind"]
    if kind in ("rectangle", "circle"):
        center = p["center_uv_mm"]
        if len(center) != 2:
            raise ValueError("Expected two in-plane center coordinates")
        uv = PointUV.Create(finite(center[0], "u")/1000.0, finite(center[1], "v")/1000.0)
        angle = finite(p["angle_deg"], "angle") * math.pi / 180.0
        if kind == "rectangle":
            return RectangleProfile(plane, positive(p["width_mm"], "width")/1000.0, positive(p["height_mm"], "height")/1000.0, uv, angle)
        return CircleProfile(plane, positive(p["radius_mm"], "radius")/1000.0, uv, angle)
    if kind != "polygon":
        raise ValueError("Supported profile variants: rectangle, circle, simple polygon")
    vertices = [vector3(v, "vertex") for v in p["vertices_mm"]]
    if len(vertices) < 3:
        raise ValueError("Polygon needs at least three distinct vertices")
    frame = plane.Frame
    origin = [float(v)*1000 for v in (frame.Origin.X, frame.Origin.Y, frame.Origin.Z)]
    axes = [[float(v) for v in (axis.X, axis.Y, axis.Z)] for axis in (frame.DirX, frame.DirY, frame.DirZ)]
    uv = []
    for vertex in vertices:
        delta = [vertex[i]-origin[i] for i in range(3)]
        if abs(sum(delta[i]*axes[2][i] for i in range(3))) > 1e-6:
            raise ValueError("Polygon vertex does not lie in supplied plane")
        uv.append([sum(delta[i]*axes[j][i] for i in range(3)) for j in (0, 1)])
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    count = len(uv)
    if abs(sum(uv[i][0]*uv[(i+1)%count][1]-uv[(i+1)%count][0]*uv[i][1] for i in range(count))) <= 1e-9:
        raise ValueError("Polygon is degenerate")
    for i in range(count):
        a, b = uv[i], uv[(i+1)%count]
        if sum((a[j]-b[j])**2 for j in (0, 1)) <= 1e-18:
            raise ValueError("Repeated adjacent polygon vertex")
        for k in range(i+1, count):
            if k in (i, (i+1)%count) or (k+1)%count == i:
                continue
            c, d = uv[k], uv[(k+1)%count]
            if cross(a,b,c)*cross(a,b,d) <= 0 and cross(c,d,a)*cross(c,d,b) <= 0 and max(min(a[0],b[0]),min(c[0],d[0])) <= min(max(a[0],b[0]),max(c[0],d[0])) and max(min(a[1],b[1]),min(c[1],d[1])) <= min(max(a[1],b[1]),max(c[1],d[1])):
                raise ValueError("Polygon self-intersection or nonadjacent touching")
    curves = [CurveSegment.Create(point_mm(vertices[i]), point_mm(vertices[(i+1)%count])) for i in range(count)]
    return Profile(plane, Array[ITrimmedCurve](curves))

if "ATOMIC_INPUT" not in globals() or not isinstance(ATOMIC_INPUT, dict):
    raise ValueError("Supply this action contract input dictionary before execution")
ATOMIC_OUTPUT = operation(ATOMIC_INPUT)
