# Python Script, API Version = V21
# Bounded P3 forward harness.  ACTION_DIR and REPORT are supplied by the host.
# This file only evaluates the packaged atomic archives; it does not save a model.
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import *
from SpaceClaim.Api.V21.Modeler import Body as ModelerBody
import hashlib
import json
import math
import os
import traceback
import zipfile


ACTION_DIR = globals().get("ACTION_DIR")
REPORT = globals().get("REPORT")
events = []
tests = []
report = {
    "schema_version": 1,
    "suite_id": "p3-actions-forward",
    "status": "failed",
    "tests": tests,
    "events": events,
}


def _finite(value, label):
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise AssertionError(label + " must be finite")
    return value


def _close(actual, expected, tolerance, label):
    actual = _finite(actual, label + " actual")
    expected = _finite(expected, label + " expected")
    tolerance = _finite(tolerance, label + " tolerance")
    if tolerance < 0 or abs(actual - expected) > tolerance:
        raise AssertionError(label + " mismatch: " + str((actual, expected, tolerance)))


def _vector(item):
    return [float(item.X), float(item.Y), float(item.Z)]


def _origin_mm(item):
    vector = _vector(item)
    return [value * 1000.0 for value in vector]


def _assert_vector(actual, expected, label, tolerance=0.000001):
    if len(actual) != len(expected):
        raise AssertionError(label + " has the wrong dimension")
    for index in range(len(expected)):
        _close(actual[index], expected[index], tolerance, label + "[" + str(index) + "]")


def _shape(item):
    return item.Shape if hasattr(item, "Shape") else item


def _bounds(item):
    box = _shape(item).GetBoundingBox(Matrix.Identity)
    return [
        float(box.MinCorner.X) * 1000.0,
        float(box.MinCorner.Y) * 1000.0,
        float(box.MinCorner.Z) * 1000.0,
        float(box.MaxCorner.X) * 1000.0,
        float(box.MaxCorner.Y) * 1000.0,
        float(box.MaxCorner.Z) * 1000.0,
    ]


def _volume(item):
    return float(_shape(item).Volume) * 1e9


def _area(item):
    return float(_shape(item).Area) * 1e6


def _bbox_matches(actual, expected, tolerance=0.001):
    if len(actual) != 6 or len(expected) != 6:
        return False
    for index in range(6):
        try:
            _close(actual[index], expected[index], tolerance, "bbox")
        except AssertionError:
            return False
    return True


def _assert_bounds(item, expected, label):
    actual = _bounds(item)
    if not _bbox_matches(actual, expected):
        raise AssertionError(label + " mismatch: " + str((actual, expected)))
    return actual


def _assert_solid(item, label):
    shape = _shape(item)
    if not shape.IsClosed or int(shape.PieceCount) < 1:
        raise AssertionError(label + " is not a nonempty closed solid")
    volume = _finite(_volume(item), label + " volume")
    if volume <= 0:
        raise AssertionError(label + " has nonpositive volume")
    return volume


def _measure(item, label):
    volume = _assert_solid(item, label)
    return {"bbox_mm": _bounds(item), "volume_mm3": volume}


def _assert_measure(item, volume, expected_bounds, label):
    measurement = _measure(item, label)
    _close(measurement["volume_mm3"], volume, 0.001, label + " volume_mm3")
    _assert_bounds(item, expected_bounds, label + " bbox_mm")
    return measurement


def _one(values, label):
    values = list(values)
    if len(values) != 1:
        raise AssertionError("Expected one " + label + ", found " + str(len(values)))
    return values[0]


def _body_by_bounds(bodies, expected, label):
    return _one(
        [body for body in list(bodies) if _bbox_matches(_bounds(body), expected)],
        label,
    )


def _snapshot(bodies):
    return sorted([tuple(_bounds(body)) for body in list(bodies)])


def _assert_snapshot(before, after, label):
    before = list(before)
    after = list(after)
    if len(before) != len(after):
        raise AssertionError(label + " body count changed")
    before = sorted(before)
    after = sorted(after)
    for first, second in zip(before, after):
        if not _bbox_matches(list(first), list(second)):
            raise AssertionError(label + " body position changed")


def _read_action(ident):
    if not isinstance(ACTION_DIR, basestring) or not ACTION_DIR.strip():
        raise ValueError("ACTION_DIR must be supplied by the host")
    path = os.path.join(ACTION_DIR, ident.lower() + ".scscript")
    stream = open(path, "rb")
    try:
        archive_bytes = stream.read()
    finally:
        stream.close()
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    archive = zipfile.ZipFile(path, "r")
    try:
        source = archive.read("_script")
    finally:
        archive.close()
    return source, archive_hash


def _call(ident, params, expect_rejection=False):
    source, archive_hash = _read_action(ident)
    event = {
        "id": ident,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "archive_sha256": archive_hash,
        "status": "failed",
    }
    events.append(event)
    scope = dict(globals())
    scope["ATOMIC_INPUT"] = params
    try:
        code = compile(source, ident + "::_script", "exec")
        exec(code, scope, scope)
        if "ATOMIC_OUTPUT" not in scope:
            raise RuntimeError("Atomic script did not publish ATOMIC_OUTPUT")
    except ValueError:
        if expect_rejection:
            event["status"] = "rejected"
            event["reason"] = str(traceback.format_exc())
            return None
        event["status"] = "failed"
        event["reason"] = traceback.format_exc()
        raise
    except:
        event["status"] = "failed"
        event["reason"] = traceback.format_exc()
        raise
    if expect_rejection:
        event["status"] = "failed"
        event["reason"] = "Expected the atomic action to reject its input"
        raise AssertionError("Expected rejection: " + ident)
    event["status"] = "executed"
    return scope["ATOMIC_OUTPUT"]


def _group(group_id, action_ids, function):
    result = {"id": group_id, "actions": list(action_ids), "status": "failed"}
    tests.append(result)
    try:
        checks = function()
        if checks is None:
            checks = {}
        if not isinstance(checks, dict):
            checks = {"result": checks}
        result["status"] = "passed"
        result["checks"] = checks
    except:
        result["error"] = traceback.format_exc()
    return result


def _block(minimum, maximum, tolerance=0.001):
    return _call(
        "MA-05",
        {
            "min_mm": minimum,
            "max_mm": maximum,
            "bbox_tolerance_mm": tolerance,
        },
    )


def _copy(body):
    return _call("MA-13", {"body": body, "volume_tolerance_mm3": 0.001})


def _refresh():
    return _call("MA-31", {})


def _square_loop(z_m, half_m):
    points = [
        Point.Create(-half_m, -half_m, z_m),
        Point.Create(half_m, -half_m, z_m),
        Point.Create(half_m, half_m, z_m),
        Point.Create(-half_m, half_m, z_m),
    ]
    return [CurveSegment.Create(points[index], points[(index + 1) % 4]) for index in range(4)]


def _test_blank_design():
    state = _refresh()
    bodies = list(state["bodies"])
    if bodies:
        raise AssertionError("P3 forward suite requires a blank design")
    return {"body_count": 0}


def _test_frame_profile_translate():
    frame = _call(
        "MA-01",
        {"origin_mm": [0, 0, 0], "x_axis": [2, 0, 0], "y_axis": [0, 3, 0]},
    )
    _assert_vector(_origin_mm(frame.Origin), [0, 0, 0], "frame origin")
    _assert_vector(_vector(frame.DirX), [1, 0, 0], "frame x_axis")
    _assert_vector(_vector(frame.DirY), [0, 1, 0], "frame y_axis")
    _assert_vector(_vector(frame.DirZ), [0, 0, 1], "frame z_axis")
    plane = _call("MA-02", {"frame": frame})
    _assert_vector(_origin_mm(plane.Frame.Origin), [0, 0, 0], "plane origin")
    _assert_vector(_vector(plane.Frame.DirX), [1, 0, 0], "plane x_axis")
    _assert_vector(_vector(plane.Frame.DirY), [0, 1, 0], "plane y_axis")
    _assert_vector(_vector(plane.Frame.DirZ), [0, 0, 1], "plane z_axis")
    axis = _call(
        "MA-03",
        {"origin_mm": [4, 5, 6], "direction": [0, 0, -2]},
    )
    _assert_vector(_origin_mm(axis.Origin), [4, 5, 6], "line origin")
    _assert_vector(_vector(axis.Direction), [0, 0, -1], "line direction")
    profile = _call(
        "MA-04",
        {
            "plane": plane,
            "kind": "polygon",
            "vertices_mm": [[0, 0, 0], [17, 0, 0], [0, 11, 0]],
        },
    )
    transient = _call("MA-06", {"profile": profile, "distance_mm": 8})
    transient_measurement = _assert_measure(
        transient,
        748,
        [0, 0, 0, 17, 11, 8],
        "triangle extrusion",
    )
    reverse_transient = _call("MA-06", {"profile": profile, "distance_mm": -8})
    reverse_measurement = _assert_measure(
        reverse_transient,
        748,
        [0, 0, -8, 17, 11, 0],
        "reverse triangle extrusion",
    )
    body = _call("MA-12", {"body": transient, "name": "P3_TRIANGLE_BODY"})
    _assert_measure(body, 748, [0, 0, 0, 17, 11, 8], "attached triangle")
    selected = _call(
        "MA-28",
        {
            "criteria": {"bbox_mm": [0, 0, 0, 17, 11, 8], "volume_mm3": 748},
            "bbox_tolerance_mm": 0.001,
            "volume_tolerance_mm3": 0.001,
        },
    )
    _assert_bounds(selected, [0, 0, 0, 17, 11, 8], "semantic triangle selection")
    moved = _call(
        "MA-14",
        {
            "body": selected,
            "delta_mm": [3, -2, 5],
            "bbox_tolerance_mm": 0.001,
            "volume_tolerance_mm3": 0.001,
        },
    )
    moved_measurement = _assert_measure(
        moved,
        748,
        [3, -2, 5, 20, 9, 13],
        "translated triangle",
    )
    state = _refresh()
    if len(list(state["bodies"])) != 1:
        raise AssertionError("Triangle test expected one attached body")
    return {
        "frame": {"origin_mm": _origin_mm(frame.Origin), "x_axis": _vector(frame.DirX), "y_axis": _vector(frame.DirY), "z_axis": _vector(frame.DirZ)},
        "plane": {"origin_mm": _origin_mm(plane.Frame.Origin), "x_axis": _vector(plane.Frame.DirX), "y_axis": _vector(plane.Frame.DirY), "z_axis": _vector(plane.Frame.DirZ)},
        "line": {"origin_mm": _origin_mm(axis.Origin), "direction": _vector(axis.Direction)},
        "extrusion": transient_measurement,
        "reverse_extrusion": reverse_measurement,
        "translation": moved_measurement,
        "body_count": 1,
    }


def _test_boolean_copy_rotation_split():
    first = _block([0, 0, 0], [12, 8, 6])
    second = _block([6, 0, 0], [18, 8, 6])
    _assert_measure(first, 576, [0, 0, 0, 12, 8, 6], "first boolean block")
    copied = _copy(first)
    copy_measurement = _assert_measure(copied, 576, [0, 0, 0, 12, 8, 6], "geometry copy")
    union = _call(
        "MA-20",
        {"target": _copy(first), "tools": [_copy(second)], "tool_policy": "consume"},
    )
    union_measurement = _assert_measure(union["body"], 864, [0, 0, 0, 18, 8, 6], "boolean union")
    if int(union["piece_count"]) != 1:
        raise AssertionError("Union should produce one piece")
    subtract = _call(
        "MA-21",
        {"target": _copy(first), "tools": [_copy(second)], "tool_policy": "consume"},
    )
    subtract_measurement = _assert_measure(subtract["body"], 288, [0, 0, 0, 6, 8, 6], "boolean subtraction")
    if int(subtract["piece_count"]) != 1:
        raise AssertionError("Subtraction should produce one piece")
    intersect = _call(
        "MA-22",
        {"target": _copy(first), "tools": [_copy(second)], "tool_policy": "consume"},
    )
    intersect_measurement = _assert_measure(intersect["body"], 288, [6, 0, 0, 12, 8, 6], "boolean intersection")
    if int(intersect["piece_count"]) != 1:
        raise AssertionError("Intersection should produce one piece")
    rotated = _call(
        "MA-16",
        {
            "body": _copy(first),
            "axis_origin_mm": [0, 0, 0],
            "axis_direction": [0, 0, 1],
            "angle_degrees": 90,
            "volume_tolerance_mm3": 0.001,
        },
    )
    rotation_measurement = _assert_measure(rotated, 576, [-8, 0, 0, 0, 12, 6], "right-hand rotation")
    reverse_rotated = _call(
        "MA-16",
        {
            "body": _copy(first),
            "axis_origin_mm": [0, 0, 0],
            "axis_direction": [0, 0, 1],
            "angle_degrees": -90,
            "volume_tolerance_mm3": 0.001,
        },
    )
    reverse_rotation_measurement = _assert_measure(
        reverse_rotated,
        576,
        [0, -12, 0, 8, 0, 6],
        "reverse rotation",
    )
    split_plane = Plane.Create(
        Frame.Create(Point.Create(0.006, 0, 0), Direction.DirY, Direction.DirZ)
    )
    split = _call(
        "MA-23",
        {"body": _copy(first), "plane": split_plane, "volume_tolerance_mm3": 0.001},
    )
    split_measurement = _assert_measure(split["body"], 576, [0, 0, 0, 12, 8, 6], "split body")
    if int(split["piece_count"]) != 2:
        raise AssertionError("Split should produce two pieces")
    return {
        "copy": copy_measurement,
        "union": dict(measurement=union_measurement, piece_count=int(union["piece_count"])),
        "subtract": dict(measurement=subtract_measurement, piece_count=int(subtract["piece_count"])),
        "intersect": dict(measurement=intersect_measurement, piece_count=int(intersect["piece_count"])),
        "rotation": rotation_measurement,
        "reverse_rotation": reverse_rotation_measurement,
        "split": dict(measurement=split_measurement, piece_count=int(split["piece_count"])),
    }


def _test_topology_round_chamfer_group():
    chamfer_base = _block([0, 20, 0], [12, 28, 6])
    chamfer_edge = _call(
        "MA-30",
        {
            "body": chamfer_base,
            "criteria": {"bbox_mm": [0, 20, 0, 0, 20, 6], "curve_type": "Line"},
            "bbox_tolerance_mm": 0.001,
        },
    )
    chamfer_result = _call(
        "MA-27",
        {"body": chamfer_base, "edges": [chamfer_edge], "distance_mm": 1},
    )
    chamfered = _body_by_bounds(chamfer_result["bodies"], [0, 20, 0, 12, 28, 6], "chamfered body")
    chamfer_measurement = _assert_measure(chamfered, 573, [0, 20, 0, 12, 28, 6], "chamfered body")
    chamfer_faces = [
        face
        for face in list(chamfered.Faces)
        if _bbox_matches(_bounds(face), [0, 20, 0, 1, 21, 6])
    ]
    chamfer_face = _one(chamfer_faces, "chamfer face")
    if chamfer_face.Shape.Geometry.GetType().Name != "Plane":
        raise AssertionError("Chamfer face must be planar")
    _close(_area(chamfer_face), 6 * math.sqrt(2), 0.001, "chamfer face area_mm2")

    round_base = _block([20, 20, 0], [32, 28, 6])
    round_edge = _call(
        "MA-30",
        {
            "body": round_base,
            "criteria": {"bbox_mm": [20, 20, 0, 20, 20, 6], "curve_type": "Line"},
            "bbox_tolerance_mm": 0.001,
        },
    )
    round_result = _call("MA-26", {"body": round_base, "edges": [round_edge], "radius_mm": 1})
    rounded = _body_by_bounds(round_result["bodies"], [20, 20, 0, 32, 28, 6], "rounded body")
    round_measurement = _assert_measure(
        rounded,
        576 - 6 * (1 - math.pi / 4),
        [20, 20, 0, 32, 28, 6],
        "rounded body",
    )
    round_faces = [
        face
        for face in list(rounded.Faces)
        if _bbox_matches(_bounds(face), [20, 20, 0, 21, 21, 6])
        and face.Shape.Geometry.GetType().Name == "Cylinder"
    ]
    round_face = _one(round_faces, "round face")
    _close(_area(round_face), 3 * math.pi, 0.005, "round face area_mm2")

    group_body = _block([40, 20, 0], [52, 28, 6])
    group_body = _call("MA-32", {"body": group_body, "name": "P3_FACE_BODY"})
    face = _call(
        "MA-29",
        {
            "body": group_body,
            "criteria": {"bbox_mm": [40, 20, 0, 40, 28, 6], "normal": [-1, 0, 0], "area_mm2": 48},
            "bbox_tolerance_mm": 0.001,
            "area_tolerance_mm2": 0.001,
            "normal_tolerance": 0.000001,
        },
    )
    _close(_area(face), 48, 0.001, "group face area_mm2")
    group = _call("MA-33", {"faces": [face]})
    members = list(group.Members)
    member = _one(members, "group member")
    if member != face:
        raise AssertionError("Group member is not the selected face")
    renamed = _call("MA-34", {"group": group, "name": "P3_FACE_GROUP"})
    if renamed.Name != "P3_FACE_GROUP":
        raise AssertionError("Face group name was not applied")
    renamed_members = list(renamed.Members)
    renamed_member = _one(renamed_members, "renamed group member")
    if renamed_member != face:
        raise AssertionError("Face group rename changed membership")
    _refresh()
    return {
        "chamfer": dict(measurement=chamfer_measurement, bbox_mm=_bounds(chamfer_face), area_mm2=_area(chamfer_face)),
        "round": dict(measurement=round_measurement, bbox_mm=_bounds(round_face), area_mm2=_area(round_face)),
        "group": {"name": renamed.Name, "member_count": len(renamed_members), "member_bbox_mm": _bounds(face), "member_area_mm2": _area(face)},
    }


def _test_sweep():
    profile = _call(
        "MA-04",
        {
            "plane": Plane.PlaneXY,
            "kind": "rectangle",
            "center_uv_mm": [0, 0],
            "width_mm": 6,
            "height_mm": 4,
            "angle_deg": 0,
        },
    )
    path = [CurveSegment.Create(Point.Origin, Point.Create(0, 0, 0.015))]
    sweep = _call("MA-09", {"profile": profile, "path": path})
    rectangle_measurement = _assert_measure(sweep, 360, [-3, -2, 0, 3, 2, 15], "rectangle sweep")
    circle = _call(
        "MA-04",
        {
            "plane": Plane.PlaneXY,
            "kind": "circle",
            "center_uv_mm": [0, 0],
            "radius_mm": 2,
            "angle_deg": 0,
        },
    )
    circle_sweep = _call("MA-09", {"profile": circle, "path": path})
    circle_measurement = _assert_measure(
        circle_sweep,
        math.pi * 4 * 15,
        [-2, -2, 0, 2, 2, 15],
        "circle sweep",
    )
    return {"rectangle": rectangle_measurement, "circle": circle_measurement}


def _test_loft():
    planes = [
        Plane.PlaneXY,
        Plane.Create(Frame.Create(Point.Create(0, 0, 0.012), Direction.DirX, Direction.DirY)),
    ]
    profiles = [_square_loop(0, 0.004), _square_loop(0.012, 0.002)]
    loft = _call(
        "MA-10",
        {"profiles": profiles, "periodic": False, "ruled": True, "end_planes": planes},
    )
    return {"loft": _assert_measure(loft, 448, [-4, -4, 0, 4, 4, 12], "loft")}


def _test_empty_path():
    profile = _call(
        "MA-04",
        {
            "plane": Plane.PlaneXY,
            "kind": "rectangle",
            "center_uv_mm": [0, 0],
            "width_mm": 6,
            "height_mm": 4,
            "angle_deg": 0,
        },
    )
    _call("MA-09", {"profile": profile, "path": []}, True)
    return {"empty_path_rejected": True}


def _test_insufficient_loft():
    planes = [
        Plane.PlaneXY,
        Plane.Create(Frame.Create(Point.Create(0, 0, 0.012), Direction.DirX, Direction.DirY)),
    ]
    _call(
        "MA-10",
        {"profiles": [_square_loop(0, 0.004)], "periodic": False, "ruled": True, "end_planes": planes},
        True,
    )
    return {"insufficient_sections_rejected": True}


def _test_unknown_body_predicate():
    body = _block([100, 0, 0], [112, 8, 6])
    _call(
        "MA-28",
        {
            "criteria": {"unsupported_predicate": "red", "bbox_mm": [100, 0, 0, 112, 8, 6]},
            "bbox_tolerance_mm": 0.001,
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    _assert_bounds(body, [100, 0, 0, 112, 8, 6], "unknown predicate fixture")
    return {"unknown_predicate_rejected": True}


def _test_bbox_no_match():
    _block([120, 0, 0], [132, 8, 6])
    _call(
        "MA-28",
        {
            "criteria": {"bbox_mm": [999, 999, 999, 1000, 1000, 1000]},
            "bbox_tolerance_mm": 0.001,
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    return {"bbox_no_match_rejected": True}


def _test_name_only():
    body = _block([140, 0, 0], [152, 8, 6])
    _call(
        "MA-28",
        {"criteria": {"name": unicode(body.Name)}, "bbox_tolerance_mm": 0.001, "volume_tolerance_mm3": 0.001},
        True,
    )
    return {"name_only_rejected": True}


def _test_duplicate_name():
    first = _block([160, 0, 0], [172, 8, 6])
    second = _block([180, 0, 0], [192, 8, 6])
    _call("MA-32", {"body": first, "name": "P3_DUPLICATE_NAME"})
    before = _snapshot(_refresh()["bodies"])
    _call("MA-32", {"body": second, "name": "P3_DUPLICATE_NAME"}, True)
    after = _snapshot(_refresh()["bodies"])
    _assert_snapshot(before, after, "duplicate naming")
    return {"duplicate_name_rejected": True, "body_count": len(after)}


def _test_negative_block_tolerance():
    before = _snapshot(_refresh()["bodies"])
    _call("MA-05", {"min_mm": [200, 0, 0], "max_mm": [212, 8, 6], "bbox_tolerance_mm": -0.001}, True)
    after = _snapshot(_refresh()["bodies"])
    _assert_snapshot(before, after, "negative block tolerance")
    return {"negative_block_tolerance_rejected": True, "body_count_unchanged": True}


def _test_negative_translate_tolerance():
    body = _block([220, 0, 0], [232, 8, 6])
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-14",
        {
            "body": body,
            "delta_mm": [3, 4, 5],
            "bbox_tolerance_mm": -0.001,
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    after = _snapshot(_refresh()["bodies"])
    _assert_snapshot(before, after, "negative translation tolerance")
    return {"negative_translate_tolerance_rejected": True, "body_position_unchanged": True}


def _test_nonfinite_block():
    before = _snapshot(_refresh()["bodies"])
    _call("MA-05", {"min_mm": [240, 0, 0], "max_mm": [252, 8, float("nan")], "bbox_tolerance_mm": 0.001}, True)
    after = _snapshot(_refresh()["bodies"])
    _assert_snapshot(before, after, "nonfinite block input")
    return {"nonfinite_block_rejected": True, "body_count_unchanged": True}


def _test_nonfinite_translate():
    body = _block([260, 0, 0], [272, 8, 6])
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-14",
        {
            "body": body,
            "delta_mm": [float("inf"), 0, 0],
            "bbox_tolerance_mm": 0.001,
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    after = _snapshot(_refresh()["bodies"])
    _assert_snapshot(before, after, "nonfinite translation input")
    return {"nonfinite_translate_rejected": True, "body_position_unchanged": True}


def _test_nonfinite_rotation():
    body = _block([280, 0, 0], [292, 8, 6])
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-16",
        {
            "body": _copy(body),
            "axis_origin_mm": [0, 0, 0],
            "axis_direction": [0, 0, 1],
            "angle_degrees": float("inf"),
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    after = _snapshot(_refresh()["bodies"])
    _assert_snapshot(before, after, "nonfinite rotation input")
    return {"nonfinite_rotation_rejected": True, "body_position_unchanged": True}


def _test_nonunique_face():
    body = _block([300, 0, 0], [312, 8, 6])
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-29",
        {
            "body": body,
            "criteria": {"area_mm2": 48},
            "bbox_tolerance_mm": 0.001,
            "area_tolerance_mm2": 0.001,
            "normal_tolerance": 0.000001,
        },
        True,
    )
    after = _snapshot(_refresh()["bodies"])
    _assert_snapshot(before, after, "nonunique face selection")
    return {"nonunique_area_face_rejected": True, "matching_opposite_faces": 2}


def _run_suite():
    blank = _group("blank-design", ["MA-31"], _test_blank_design)
    if blank["status"] != "passed":
        return
    _group(
        "frame-profile-translate",
        ["MA-01", "MA-02", "MA-03", "MA-04", "MA-06", "MA-12", "MA-28", "MA-14", "MA-31"],
        _test_frame_profile_translate,
    )
    _group(
        "boolean-copy-rotation-split",
        ["MA-05", "MA-13", "MA-20", "MA-21", "MA-22", "MA-16", "MA-23"],
        _test_boolean_copy_rotation_split,
    )
    _group(
        "topology-round-chamfer-group",
        ["MA-05", "MA-30", "MA-27", "MA-26", "MA-32", "MA-29", "MA-33", "MA-34", "MA-31"],
        _test_topology_round_chamfer_group,
    )
    _group("sweep", ["MA-04", "MA-09"], _test_sweep)
    _group("loft-solid", ["MA-10"], _test_loft)
    _group("negative-empty-path", ["MA-04", "MA-09"], _test_empty_path)
    _group("negative-loft-sections", ["MA-10"], _test_insufficient_loft)
    _group("negative-unknown-body-predicate", ["MA-05", "MA-28"], _test_unknown_body_predicate)
    _group("negative-bbox-no-match", ["MA-05", "MA-28"], _test_bbox_no_match)
    _group("negative-name-only", ["MA-05", "MA-28"], _test_name_only)
    _group("negative-duplicate-name", ["MA-05", "MA-32", "MA-31"], _test_duplicate_name)
    _group("negative-block-tolerance", ["MA-31", "MA-05", "MA-31"], _test_negative_block_tolerance)
    _group("negative-translate-tolerance", ["MA-05", "MA-31", "MA-14", "MA-31"], _test_negative_translate_tolerance)
    _group("negative-nonfinite-block", ["MA-31", "MA-05", "MA-31"], _test_nonfinite_block)
    _group("negative-nonfinite-translate", ["MA-05", "MA-31", "MA-14", "MA-31"], _test_nonfinite_translate)
    _group("negative-nonfinite-rotation", ["MA-05", "MA-31", "MA-13", "MA-16", "MA-31"], _test_nonfinite_rotation)
    _group("negative-nonunique-face", ["MA-05", "MA-31", "MA-29", "MA-31"], _test_nonunique_face)


try:
    if not isinstance(REPORT, basestring) or not REPORT.strip():
        raise ValueError("REPORT must be supplied by the host")
    _run_suite()
except:
    report["error"] = traceback.format_exc()
finally:
    report["status"] = "passed" if tests and not report.get("error") else "failed"
    for test in tests:
        if test.get("status") != "passed":
            report["status"] = "failed"
            break
    try:
        stream = open(REPORT, "wb")
        try:
            stream.write(json.dumps(report, indent=2).encode("utf-8"))
        finally:
            stream.close()
    except:
        report["status"] = "failed"
        report["error"] = traceback.format_exc()
    print(json.dumps(report))
