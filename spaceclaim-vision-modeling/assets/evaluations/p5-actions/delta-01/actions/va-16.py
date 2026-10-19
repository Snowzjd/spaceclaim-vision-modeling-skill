# Python Script, API Version = V21
# Shared read-only helpers for VA-04 through VA-18.
#
# This file is copied into every generated action.  Generated scripts therefore
# do not import a repository module at SpaceClaim runtime.  The helpers avoid
# all document, topology, save, and GUI-mutating calls; they only resolve the
# active root document and read current geometry or group properties.
from __future__ import print_function

from SpaceClaim.Api.V21 import *
import math


try:
    _STRING_TYPES = (basestring,)
except NameError:
    _STRING_TYPES = (str,)


MM_PER_M = 1000.0
PI = math.pi


def text(value):
    """Return text without forcing IronPython unicode through ASCII ``str``."""
    try:
        return unicode(value)
    except NameError:
        return str(value)


def finite(value, label):
    if isinstance(value, bool):
        raise ValueError(label + " must be numeric, not boolean")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(label + " must be numeric")
    if math.isnan(number) or math.isinf(number):
        raise ValueError(label + " must be finite")
    return number


def nonnegative(value, label):
    number = finite(value, label)
    if number < 0.0:
        raise ValueError(label + " must be non-negative")
    return number


def positive(value, label):
    number = finite(value, label)
    if number <= 0.0:
        raise ValueError(label + " must be positive")
    return number


def vector3(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(label + " requires exactly three coordinates")
    return [finite(item, label) for item in value]


def normalize(vector, label):
    values = vector3(vector, label)
    length = math.sqrt(sum(item * item for item in values))
    if length <= 1.0e-12:
        raise ValueError(label + " must be nonzero")
    return [item / length for item in values]


def require_mapping(value, label="ATOMIC_INPUT"):
    if not isinstance(value, dict):
        raise ValueError(label + " must be a dictionary")
    return value


def required(mapping, *names):
    for name in names:
        if name in mapping:
            return mapping[name]
    raise ValueError("Missing required input: " + "/".join(names))


def optional(mapping, default, *names):
    for name in names:
        if name in mapping:
            return mapping[name]
    return default


def same_object(left, right):
    if left is right:
        return True
    # SpaceClaim can expose the same native object through different Python
    # wrappers.  Equality is accepted only when it returns a real bool; this
    # does not silently accept a truthy proxy or a collection.
    try:
        value = left == right
    except Exception:
        return False
    return isinstance(value, bool) and value


def contains_object(items, target):
    for item in list(items):
        if same_object(item, target):
            return True
    return False


def _parent_is(item, root):
    try:
        return same_object(item.Parent, root)
    except Exception:
        return False


def active_root(mapping):
    """Require the explicitly supplied root to be the active root part.

    Component occurrences and an arbitrary component root are intentionally
    rejected.  This makes every action's scope explicit and prevents a valid
    object from another occurrence being treated as the current body.
    """
    mapping = require_mapping(mapping)
    supplied = required(mapping, "root", "current_root", "expected_root")
    try:
        root = GetRootPart()
    except Exception:
        raise ValueError("SpaceClaim root part is unavailable")
    if not same_object(supplied, root):
        raise ValueError("Input root is not the current document root part")
    try:
        active = Window.ActiveWindow.ActiveContext.ActivePart
    except Exception:
        raise ValueError("Active root-part context is unavailable")
    if not same_object(active, root):
        raise ValueError("Occurrence or non-root active part is unsupported")
    return root


def root_bodies(root):
    """Return current DesignBody descendants whose direct parent is root."""
    try:
        values = list(root.GetDescendants[DesignBody]())
    except Exception:
        try:
            values = list(root.GetAllBodies())
        except Exception:
            raise ValueError("Current root body enumeration is unsupported")
    result = [body for body in values if _parent_is(body, root)]
    return result


def require_body(mapping, root=None):
    if root is None:
        root = active_root(mapping)
    body = required(mapping, "body", "current_body")
    if not contains_object(root_bodies(root), body):
        raise ValueError("Body is not a current direct child of the root part")
    if not _parent_is(body, root):
        raise ValueError("Occurrence body is not supported")
    return body


def _members(owner, attribute, label):
    try:
        return list(getattr(owner, attribute))
    except Exception:
        raise ValueError("Current " + label + " collection is unavailable")


def require_face(mapping, root=None):
    if root is None:
        root = active_root(mapping)
    body = require_body(mapping, root)
    face = required(mapping, "face", "current_face")
    faces = _members(body, "Faces", "face")
    if not contains_object(faces, face):
        raise ValueError("Face is not part of the supplied current body")
    return body, face


def require_edge(mapping, root=None):
    if root is None:
        root = active_root(mapping)
    body = require_body(mapping, root)
    edge = required(mapping, "edge", "current_edge")
    edges = _members(body, "Edges", "edge")
    if not contains_object(edges, edge):
        raise ValueError("Edge is not part of the supplied current body")
    return body, edge


def unit_spec(mapping):
    value = required(mapping, "unit", "units")
    if not isinstance(value, _STRING_TYPES):
        raise ValueError("unit must be a string")
    key = value.strip().lower()
    aliases = {
        "mm": ("mm", MM_PER_M),
        "millimeter": ("mm", MM_PER_M),
        "millimeters": ("mm", MM_PER_M),
        "m": ("m", 1.0),
        "meter": ("m", 1.0),
        "meters": ("m", 1.0),
        "in": ("in", 39.37007874015748),
        "inch": ("in", 39.37007874015748),
        "inches": ("in", 39.37007874015748),
    }
    if key not in aliases:
        raise ValueError("Unsupported unit; use mm, m, or in")
    canonical, length_scale = aliases[key]
    return canonical, length_scale, length_scale * length_scale, length_scale * length_scale * length_scale


def frame_spec(mapping):
    frame = required(mapping, "frame", "coordinate_frame")
    if isinstance(frame, _STRING_TYPES):
        if frame.strip().lower() not in ("world", "global", "identity"):
            raise ValueError("Only world/global/identity frame names are supported")
        return Matrix.Identity, "world"
    return frame, "supplied"


def point_components(point, label):
    names = ("X", "Y", "Z")
    values = []
    for index, name in enumerate(names):
        try:
            values.append(finite(getattr(point, name), label))
            continue
        except Exception:
            pass
        try:
            values.append(finite(point[index], label))
            continue
        except Exception:
            raise ValueError(label + " has no X/Y/Z coordinates")
    return values


def bbox_values(shape, frame):
    try:
        box = shape.GetBoundingBox(frame)
    except Exception:
        raise ValueError("Bounding-box measurement is unsupported for this object")
    minimum = point_components(box.MinCorner, "bbox minimum")
    maximum = point_components(box.MaxCorner, "bbox maximum")
    for index in range(3):
        if minimum[index] > maximum[index]:
            raise ValueError("Bounding-box limits are not ordered")
    return minimum + maximum


def _shape_of(item):
    try:
        return item.Shape
    except Exception:
        return item


def shape_bbox_in_units(item, frame, length_scale):
    values = bbox_values(_shape_of(item), frame)
    return [value * length_scale for value in values]


def geometry_kind(face):
    try:
        name = face.Shape.Geometry.GetType().Name
    except Exception:
        raise ValueError("Analytic face type is unavailable")
    if not isinstance(name, _STRING_TYPES) or not name.strip():
        raise ValueError("Analytic face type is empty")
    return text(name)


def geometry_axis(face):
    try:
        direction = face.Shape.Geometry.Frame.DirZ
    except Exception:
        return None
    try:
        return normalize(point_components(direction, "analytic axis"), "analytic axis")
    except Exception:
        return None


def projected_bbox_span(face, axis, length_scale):
    """Return an axis projection of the current trimmed-face bounding box.

    The projection is exact for an axis-aligned trimmed span.  For a rotated
    face the result is deliberately marked approximate; callers must not
    promote that enclosure to an exact trim measurement without a manual API
    check.
    """
    raw = bbox_values(_shape_of(face), Matrix.Identity)
    minimum = raw[:3]
    maximum = raw[3:]
    corners = []
    for x in (minimum[0], maximum[0]):
        for y in (minimum[1], maximum[1]):
            for z in (minimum[2], maximum[2]):
                corners.append((x, y, z))
    projections = [sum(corner[i] * axis[i] for i in range(3)) for corner in corners]
    span = (max(projections) - min(projections)) * length_scale
    dominant = max([abs(value) for value in axis])
    aligned = dominant >= 1.0 - 1.0e-8 and all(
        abs(value) <= 1.0e-8 for value in axis if abs(value) != dominant
    )
    return finite(span, "axis span"), aligned


def read_scalar(owner, attribute, label):
    try:
        return finite(getattr(owner, attribute), label)
    except ValueError:
        raise
    except Exception:
        raise ValueError(label + " is unavailable")


def safe_name(owner, label="object name"):
    try:
        value = getattr(owner, "Name")
    except Exception:
        raise ValueError(label + " is unavailable")
    if not isinstance(value, _STRING_TYPES) or not value.strip():
        raise ValueError(label + " is empty")
    # Convert only after the native/string-type guard.  In IronPython a
    # SpaceClaim/.NET string may be ``unicode`` even when the host-side
    # harness is Python 3; returning ``str(value)`` here can raise an ASCII
    # encoding error for a non-ASCII object name.
    return text(value)


def groups_for_root(root):
    try:
        groups = list(WindowHelper.GetGroups())
    except Exception:
        raise ValueError("Named-group enumeration is unsupported")
    result = []
    for group in groups:
        try:
            parent = group.Parent
        except Exception:
            parent = None
        if parent is not None and not same_object(parent, root):
            continue
        result.append(group)
    return result


def require_group(mapping, root=None):
    if root is None:
        root = active_root(mapping)
    group = required(mapping, "group", "named_group", "selection")
    if not contains_object(groups_for_root(root), group):
        raise ValueError("Named group is not a current root-scoped group")
    try:
        parent = group.Parent
    except Exception:
        parent = None
    if parent is not None and not same_object(parent, root):
        raise ValueError("Occurrence named groups are unsupported")
    return group


def group_members(group):
    for attribute in ("Members", "Items"):
        try:
            return list(getattr(group, attribute))
        except Exception:
            pass
    raise ValueError("Named-group member enumeration is unsupported in V21")


def object_identity(mapping, root):
    """Resolve one target; a body may be owner context for one face/edge."""

    def one_alias(names, label):
        found = []
        for name in names:
            if name in mapping and mapping[name] is not None:
                found.append((name, mapping[name]))
        if len(found) > 1:
            raise ValueError("Supply exactly one " + label + " identity")
        return found[0] if found else None

    owner_entry = one_alias(("body", "current_body"), "owner body")
    target_entry = one_alias(
        ("face", "current_face", "edge", "current_edge", "group", "named_group", "selection", "object"),
        "target object",
    )

    # With no separate target, a body is itself the target.  Once a face or
    # edge is supplied, the body is only its owner context and must not count
    # as a second name target.
    if target_entry is None:
        if owner_entry is None:
            raise ValueError("Supply exactly one object identity")
        owner = owner_entry[1]
        child = dict(mapping)
        child["body"] = owner
        require_body(child, root)
        return owner, "body"

    key, target = target_entry
    if key in ("face", "current_face", "edge", "current_edge"):
        if owner_entry is None:
            raise ValueError("A face or edge target requires one owner body")
        child = dict(mapping)
        child["body"] = owner_entry[1]
        child["face" if key in ("face", "current_face") else "edge"] = target
        if key in ("face", "current_face"):
            require_face(child, root)
            return target, "face"
        require_edge(child, root)
        return target, "edge"

    if key in ("group", "named_group", "selection"):
        if owner_entry is not None:
            raise ValueError("A named group target cannot also have an owner body")
        child = dict(mapping)
        child["group"] = target
        require_group(child, root)
        return target, "group"

    if owner_entry is None:
        owner = None
    else:
        owner = owner_entry[1]
    kind = optional(mapping, None, "object_kind", "kind")
    if kind not in ("body", "face", "edge", "group"):
        raise ValueError("object_kind is required for generic object input")
    if owner is not None and kind not in ("face", "edge"):
        raise ValueError("Generic object plus owner body must designate one face or edge target")
    child = dict(mapping)
    if owner is not None:
        child["body"] = owner
    child[kind] = target
    if kind == "body":
        require_body(child, root)
    elif kind == "face":
        require_face(child, root)
    elif kind == "edge":
        require_edge(child, root)
    else:
        require_group(child, root)
    return target, kind


def _base_result(action_id, status):
    return {
        "action_id": action_id,
        "status": status,
        "geometry_modified": False,
        "gui_interaction": False,
        "runtime_claim": False,
        "validation_boundary": "Read-only current-root measurement/check; no save or runtime proof.",
    }


def passed(action_id, **values):
    result = _base_result(action_id, "passed")
    result.update(values)
    return result


def failed(action_id, reason, **values):
    result = _base_result(action_id, "failed")
    result["reason"] = text(reason)
    result.update(values)
    return result


def manual_review(action_id, reason, **values):
    result = _base_result(action_id, "needs_manual_review")
    result["needs_manual_review"] = True
    result["reason"] = text(reason)
    result.update(values)
    return result


def compare_identity_sets(actual, expected):
    """Compare collections by object identity, never by count alone."""
    actual = list(actual)
    expected = list(expected)
    if len(actual) != len(expected):
        return False
    unmatched = list(actual)
    for wanted in expected:
        match = None
        for index, candidate in enumerate(unmatched):
            if same_object(candidate, wanted):
                match = index
                break
        if match is None:
            return False
        del unmatched[match]
    return not unmatched


def degrees(radians, label):
    return finite(radians, label) * 180.0 / PI


def dot(left, right):
    return sum(left[index] * right[index] for index in range(3))


def subtract(left, right):
    return [left[index] - right[index] for index in range(3)]


def norm(value, label):
    return math.sqrt(dot(vector3(value, label), vector3(value, label)))


def angle_wrap_degrees(value):
    value = finite(value, "angle") % 360.0
    if value > 180.0:
        value -= 360.0
    return value

ACTION_ID = "VA-16"

# Circular interface (all coordinates and tolerances are millimetres):
#
#   {
#       "positions_mm": [[x, y, z], ...],
#       "tolerance_mm": 0.01,
#       "expected_rule": {
#           "mode": "circular",
#           "center_mm": [x, y, z],
#           "axis": [x, y, z],
#           "pitch_radius_mm": 10.0,
#           "angle_step_deg": 90.0,
#           "count": 4,
#       },
#   }
#
# ``angle_step_deg`` is the expected angular step, but angular discrepancies
# are converted to chord-length millimetres before comparison with the one
# ``tolerance_mm`` value.  The output retains both angular and distance errors
# so a JSON report never mixes degree and millimetre quantities.


def _cross(left, right):
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def operation(p):
    root = active_root(p)
    raw = required(p, "feature_positions_mm", "positions_mm", "positions")
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return manual_review(ACTION_ID, "At least two ordered feature positions are required for a repeated-placement check.")
    positions = [vector3(value, "feature position") for value in raw]
    tolerance_value = nonnegative(required(p, "tolerance_mm", "tolerance"), "tolerance_mm")
    rule = required(p, "expected_rule", "rule")
    if not isinstance(rule, dict):
        raise ValueError("expected_rule must be a dictionary")
    mode = optional(rule, None, "mode", "kind", "type")
    if not isinstance(mode, _STRING_TYPES):
        return manual_review(ACTION_ID, "Repeated-placement rule mode is missing or ambiguous.")
    mode = mode.strip().lower()
    expected_count = optional(rule, None, "count", "expected_count")
    if expected_count is not None:
        expected_count = finite(expected_count, "expected repeated count")
        if expected_count != int(expected_count) or expected_count < 2:
            raise ValueError("expected repeated count must be an integer >= 2")
    errors = []
    angular_errors_deg = []
    angular_errors_mm = []
    normalized_rule = {"mode": mode}
    count_matches = True
    if mode in ("linear", "translation"):
        step = optional(rule, None, "step_mm", "delta_mm", "spacing_vector_mm")
        if step is None:
            return manual_review(ACTION_ID, "Linear repeat requires an explicit three-dimensional step vector.")
        step = vector3(step, "repeat step")
        normalized_rule["step_mm"] = step
        for index in range(1, len(positions)):
            delta = subtract(positions[index], positions[index - 1])
            errors.append(norm(subtract(delta, step), "linear placement error"))
    elif mode in ("circular", "polar"):
        center = vector3(required(rule, "center_mm", "center"), "repeat center")
        axis = normalize(required(rule, "axis", "axis_direction"), "repeat axis")
        radius = positive(required(rule, "pitch_radius_mm", "radius_mm", "radius"), "pitch radius")
        angle_step = finite(required(rule, "angle_step_deg", "angular_step_deg"), "angle step")
        if abs(angle_step) <= 1.0e-12:
            raise ValueError("angle step must be nonzero")
        normalized_rule.update(
            center_mm=center,
            axis=axis,
            pitch_radius_mm=radius,
            angle_step_deg=angle_step,
        )
        first_radial = subtract(positions[0], center)
        first_axial = dot(first_radial, axis)
        first_radial = [first_radial[i] - first_axial * axis[i] for i in range(3)]
        first_length = norm(first_radial, "first radial vector")
        if first_length <= 1.0e-12:
            return manual_review(ACTION_ID, "First repeated feature lies on the repeat axis; angular placement is ambiguous.")
        for index, position in enumerate(positions):
            relative = subtract(position, center)
            axial = dot(relative, axis)
            radial = [relative[i] - axial * axis[i] for i in range(3)]
            radial_length = norm(radial, "radial placement")
            radial_error = abs(radial_length - radius)
            axial_error = abs(axial)
            cross = _cross(first_radial, radial)
            actual_angle = math.atan2(dot(axis, cross), dot(first_radial, radial)) * 180.0 / PI
            angular_error_deg = abs(angle_wrap_degrees(actual_angle - index * angle_step))
            # Convert the angular discrepancy to a chord-length error before
            # combining it with radial/axial millimetre errors.  A single
            # tolerance must never compare unlike units.
            angular_error_mm = 2.0 * radius * math.sin(angular_error_deg * PI / 360.0)
            angular_errors_deg.append(angular_error_deg)
            angular_errors_mm.append(angular_error_mm)
            errors.append(max(radial_error, axial_error, angular_error_mm))
    else:
        return manual_review(ACTION_ID, "Unsupported repeated-placement rule; use linear or circular.", mode=mode)
    if expected_count is not None:
        normalized_rule["count"] = int(expected_count)
        if len(positions) != int(expected_count):
            count_matches = False
    if not errors:
        return manual_review(ACTION_ID, "Repeated-placement rule produced no independent comparisons.")
    max_error = max(errors)
    matches = count_matches and max_error <= tolerance_value
    result = passed(
        ACTION_ID,
        root_scope="current_root",
        positions_mm=positions,
        rule=normalized_rule,
        errors=errors,
        angular_errors_deg=angular_errors_deg,
        angular_errors_mm=angular_errors_mm,
        max_error=max_error,
        tolerance=tolerance_value,
        tolerance_mm=tolerance_value,
        count_matches=count_matches,
        matches=matches,
    )
    result["status"] = "passed" if matches else "failed"
    return result
# ATOMIC_INPUT is intentionally injected by the host harness; this is
# the only execution entry point for this independent action.
if "ATOMIC_INPUT" not in globals() or not isinstance(ATOMIC_INPUT, dict):
    raise ValueError("Supply one explicit ATOMIC_INPUT dictionary before execution")
ATOMIC_OUTPUT = operation(ATOMIC_INPUT)
