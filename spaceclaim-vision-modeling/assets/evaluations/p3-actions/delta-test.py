# Python Script, API Version = V21
# Bounded P3 delta harness. ACTION_DIR and REPORT are supplied by the host.
# Fixtures are synthetic and transient/live only; this script never saves a model.
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import *
from SpaceClaim.Api.V21.Modeler import Body as ModelerBody
from System import Array
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
    "suite_id": "p3-actions-delta",
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


def _assert_measure(item, expected_volume, expected_bounds, label):
    measurement = _measure(item, label)
    _close(measurement["volume_mm3"], expected_volume, 0.001, label + " volume_mm3")
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
    before = sorted(list(before))
    after = sorted(list(after))
    if len(before) != len(after):
        raise AssertionError(label + " body count changed")
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
            event["reason"] = traceback.format_exc()
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


def _refresh():
    return _call("MA-31", {})


def _block(minimum, maximum, bbox_tolerance=0.001):
    return _call(
        "MA-05",
        {
            "min_mm": minimum,
            "max_mm": maximum,
            "bbox_tolerance_mm": bbox_tolerance,
        },
    )


def _copy(body):
    return _call("MA-13", {"body": body, "volume_tolerance_mm3": 0.001})


def _face(body, bounds, normal, area):
    return _call(
        "MA-29",
        {
            "body": body,
            "criteria": {"bbox_mm": bounds, "normal": normal, "area_mm2": area},
            "bbox_tolerance_mm": 0.001,
            "area_tolerance_mm2": 0.001,
            "normal_tolerance": 0.000001,
        },
    )


def _sheet(name, x0_mm, y0_mm, z_mm, side_mm):
    x1_mm = x0_mm + side_mm
    y1_mm = y0_mm + side_mm
    points = [
        Point.Create(x0_mm / 1000.0, y0_mm / 1000.0, z_mm / 1000.0),
        Point.Create(x1_mm / 1000.0, y0_mm / 1000.0, z_mm / 1000.0),
        Point.Create(x1_mm / 1000.0, y1_mm / 1000.0, z_mm / 1000.0),
        Point.Create(x0_mm / 1000.0, y1_mm / 1000.0, z_mm / 1000.0),
    ]
    curves = Array[ITrimmedCurve]([CurveSegment.Create(points[i], points[(i + 1) % 4]) for i in range(4)])
    plane = Plane.Create(
        Frame.Create(
            Point.Create((x0_mm + side_mm / 2.0) / 1000.0, (y0_mm + side_mm / 2.0) / 1000.0, z_mm / 1000.0),
            Direction.DirX,
            Direction.DirY,
        )
    )
    modeler = ModelerBody.CreatePlanarBody(plane, curves)
    body = DesignBody.Create(GetRootPart(), name, modeler)
    return body, _one(list(body.Faces), name + " face")


def _off_axis_source(name, attached_x_mm):
    # Keep the live fixture away from the other groups, then use a transient
    # copy at the local [8,0,0,10,2,3] contract coordinates.
    attached = _block([attached_x_mm, 0, 0], [attached_x_mm + 2, 2, 3])
    source = _copy(attached)
    source.Transform(Matrix.CreateTranslation(Vector.Create((8 - attached_x_mm) / 1000.0, 0, 0)))
    _assert_bounds(source, [8, 0, 0, 10, 2, 3], name + " source")
    return source


def _square_loop(z_mm, x0_mm, y0_mm, side_mm):
    points = [
        Point.Create(x0_mm / 1000.0, y0_mm / 1000.0, z_mm / 1000.0),
        Point.Create((x0_mm + side_mm) / 1000.0, y0_mm / 1000.0, z_mm / 1000.0),
        Point.Create((x0_mm + side_mm) / 1000.0, (y0_mm + side_mm) / 1000.0, z_mm / 1000.0),
        Point.Create(x0_mm / 1000.0, (y0_mm + side_mm) / 1000.0, z_mm / 1000.0),
    ]
    return [CurveSegment.Create(points[i], points[(i + 1) % 4]) for i in range(4)]


def _test_blank_design():
    state = _refresh()
    if list(state["bodies"]):
        raise AssertionError("Delta suite requires a blank design")
    return {"body_count": 0}


def _test_ma10_native_loft():
    first, first_face = _sheet("P3_DELTA_LOFT_FIRST", 50, 40, 50, 8)
    second, second_face = _sheet("P3_DELTA_LOFT_SECOND", 52, 42, 62, 4)
    before = list(_refresh()["bodies"])
    loft = _call(
        "MA-10",
        {"section_faces": [first_face, second_face], "ruled": True, "section_policy": "consume"},
    )
    measurement = _assert_measure(loft, 448, [50, 40, 50, 58, 48, 62], "native loft")
    after = list(_refresh()["bodies"])
    if first in after or second in after:
        raise AssertionError("Native loft did not consume both section bodies")
    if loft not in after:
        raise AssertionError("Native loft body is not a current root body")
    return {"measurement": measurement, "section_policy": "consume", "sections_consumed": 2, "before_count": len(before), "after_count": len(after)}


def _ma15_fixture(y_mm, prefix):
    source = _block([0, y_mm, 0], [4, y_mm + 6, 8])
    target = _block([10, y_mm, 0], [14, y_mm + 6, 8])
    reference = _face(source, [4, y_mm, 0, 4, y_mm + 6, 8], [1, 0, 0], 48)
    target_face = _face(target, [10, y_mm, 0, 10, y_mm + 6, 8], [-1, 0, 0], 48)
    return source, target, reference, target_face


def _test_ma15_point_to_face():
    source, target, reference, target_face = _ma15_fixture(0, "P3_DELTA_MA15")
    before = _snapshot(_refresh()["bodies"])
    result = _call(
        "MA-15",
        {
            "body": source,
            "reference_face": reference,
            "target_face": target_face,
            "reference_point_mm": [4, 3, 4],
            "direction": [1, 0, 0],
            "position_tolerance_mm": 0.001,
            "volume_tolerance_mm3": 0.001,
        },
    )
    moved = result["body"]
    measurement = _assert_measure(moved, 192, [6, 0, 0, 10, 6, 8], "MA15 moved body")
    _assert_vector(result["delta_mm"], [6, 0, 0], "MA15 delta_mm")
    _assert_vector(result["reference_endpoint_mm"], [10, 3, 4], "MA15 endpoint_mm")
    _assert_bounds(target, [10, 0, 0, 14, 6, 8], "MA15 target body")
    after = _snapshot(_refresh()["bodies"])
    if len(before) != len(after):
        raise AssertionError("MA15 changed the body count")
    return {"measurement": measurement, "delta_mm": result["delta_mm"], "reference_endpoint_mm": result["reference_endpoint_mm"]}


def _test_ma18_linear_array():
    attached = _block([80, 0, 0], [82, 3, 4])
    source = _copy(attached)
    source_measurement = _assert_measure(source, 24, [80, 0, 0, 82, 3, 4], "MA18 source")
    result = _call(
        "MA-18",
        {
            "body": source,
            "direction": [1, 2, 0],
            "count": 3,
            "spacing_mm": 5,
            "volume_tolerance_mm3": 0.001,
        },
    )
    if result["source_policy"] != "preserved" or result["association"] != "independent":
        raise AssertionError("MA18 returned the wrong source/association policy")
    instances = list(result["instances"])
    offsets = list(result["offsets_mm"])
    if len(instances) != 3 or len(offsets) != 3:
        raise AssertionError("MA18 expected three instances and offsets")
    root5 = math.sqrt(5.0)
    expected_offsets = [[0, 0, 0], [root5, 2 * root5, 0], [2 * root5, 4 * root5, 0]]
    instance_checks = []
    for index in range(3):
        _assert_vector(offsets[index], expected_offsets[index], "MA18 offset " + str(index), 0.000001)
        expected_bounds = [
            80 + expected_offsets[index][0],
            expected_offsets[index][1],
            0,
            82 + expected_offsets[index][0],
            3 + expected_offsets[index][1],
            4,
        ]
        instance = _body_by_bounds(instances, expected_bounds, "MA18 instance " + str(index))
        instance_checks.append(_assert_measure(instance, 24, expected_bounds, "MA18 instance " + str(index)))
    _assert_measure(source, 24, [80, 0, 0, 82, 3, 4], "MA18 preserved source")
    return {"source": source_measurement, "offsets_mm": offsets, "instances": instance_checks}


def _test_ma19_circular_array():
    source = _off_axis_source("P3_DELTA_MA19", 110)
    source_measurement = _assert_measure(source, 12, [8, 0, 0, 10, 2, 3], "MA19 source")
    result = _call(
        "MA-19",
        {
            "body": source,
            "count": 4,
            "step_angle_degrees": 90,
            "axis_origin_mm": [0, 0, 0],
            "axis_direction": [0, 0, 1],
            "volume_tolerance_mm3": 0.001,
        },
    )
    if result["source_policy"] != "preserved" or result["association"] != "independent":
        raise AssertionError("MA19 returned the wrong source/association policy")
    angles = list(result["angles_degrees"])
    if len(angles) != 4:
        raise AssertionError("MA19 expected four angles")
    _assert_vector(angles, [0, 90, 180, 270], "MA19 angles", 0.000001)
    expected_bounds = [
        [8, 0, 0, 10, 2, 3],
        [-2, 8, 0, 0, 10, 3],
        [-10, -2, 0, -8, 0, 3],
        [0, -10, 0, 2, -8, 3],
    ]
    instance_checks = []
    for index in range(4):
        instance = _body_by_bounds(result["instances"], expected_bounds[index], "MA19 instance " + str(index))
        instance_checks.append(_assert_measure(instance, 12, expected_bounds[index], "MA19 instance " + str(index)))
    _assert_measure(source, 12, [8, 0, 0, 10, 2, 3], "MA19 preserved source")
    return {"source": source_measurement, "angles_degrees": angles, "instances": instance_checks}


def _test_ma24_split_face():
    # The local contract is a 10 x 8 x 6 block; x=30 keeps this live fixture
    # separate from MA15 while retaining the requested x=4 split offset.
    base_x = 30
    body = _block([base_x, 0, 0], [base_x + 10, 8, 6])
    top = _face(body, [base_x, 0, 6, base_x + 10, 8, 6], [0, 0, 1], 80)
    curve = CurveSegment.Create(Point.Create((base_x + 4) / 1000.0, 0, 0.006), Point.Create((base_x + 4) / 1000.0, 0.008, 0.006))
    result = _call(
        "MA-24",
        {
            "body": body,
            "face": top,
            "curves": [curve],
            "volume_tolerance_mm3": 0.001,
            "bbox_tolerance_mm": 0.001,
        },
    )
    current = result["body"]
    measurement = _assert_measure(current, 480, [base_x, 0, 0, base_x + 10, 8, 6], "MA24 split body")
    faces = list(result["faces"])
    if len(faces) != 7 or int(result["added_face_count"]) != 1:
        raise AssertionError("MA24 expected seven faces and one added face")
    left_top = _one(
        [face for face in faces if _bbox_matches(_bounds(face), [base_x, 0, 6, base_x + 4, 8, 6])],
        "MA24 left top face",
    )
    right_top = _one(
        [face for face in faces if _bbox_matches(_bounds(face), [base_x + 4, 0, 6, base_x + 10, 8, 6])],
        "MA24 right top face",
    )
    _close(_area(left_top), 32, 0.001, "MA24 left top area_mm2")
    _close(_area(right_top), 48, 0.001, "MA24 right top area_mm2")
    return {"measurement": measurement, "face_count": len(faces), "top_face_areas_mm2": [_area(left_top), _area(right_top)], "added_face_count": int(result["added_face_count"])}


def _test_unicode_name_only():
    body = _block([140, 0, 0], [152, 8, 6])
    unicode_name = u"\u6d4b\u8bd5\u8fb9\u754c\u4f53"
    result = RenameObject.Execute(BodySelection.Create(body), unicode_name)
    if result is not None and hasattr(result, "Success") and not result.Success:
        raise RuntimeError("Unicode fixture rename failed")
    if unicode(body.Name) != unicode_name:
        raise AssertionError("Unicode fixture name was not applied")
    _call(
        "MA-28",
        {"criteria": {"name": unicode_name}, "bbox_tolerance_mm": 0.001, "volume_tolerance_mm3": 0.001},
        True,
    )
    return {"unicode_name_only_rejected": True}


def _test_ma10_duplicate_section():
    first, first_face = _sheet("P3_DELTA_BAD_LOFT_FIRST", 170, 40, 50, 8)
    second, second_face = _sheet("P3_DELTA_BAD_LOFT_SECOND", 172, 42, 62, 4)
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-10",
        {"section_faces": [first_face, first_face], "ruled": True, "section_policy": "consume"},
        True,
    )
    after = _snapshot(_refresh()["bodies"])
    _assert_snapshot(before, after, "MA10 duplicate section")
    if first not in list(_refresh()["bodies"]) or second not in list(_refresh()["bodies"]):
        raise AssertionError("MA10 duplicate-section rejection changed fixtures")
    return {"duplicate_section_rejected": True}


def _test_ma10_policy():
    first, first_face = _sheet("P3_DELTA_POLICY_FIRST", 190, 40, 50, 8)
    second, second_face = _sheet("P3_DELTA_POLICY_SECOND", 192, 42, 62, 4)
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-10",
        {"section_faces": [first_face, second_face], "ruled": True, "section_policy": "retain"},
        True,
    )
    after = _snapshot(_refresh()["bodies"])
    _assert_snapshot(before, after, "MA10 section policy")
    return {"invalid_section_policy_rejected": True}


def _test_ma15_reference_point():
    source, target, reference, target_face = _ma15_fixture(30, "P3_DELTA_MA15_OFFPLANE")
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-15",
        {
            "body": source,
            "reference_face": reference,
            "target_face": target_face,
            "reference_point_mm": [4, 33, 9],
            "direction": [1, 0, 0],
            "position_tolerance_mm": 0.001,
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    _assert_snapshot(before, _snapshot(_refresh()["bodies"]), "MA15 off-face reference")
    return {"off_face_reference_rejected": True}


def _test_ma15_parallel_direction():
    source, target, reference, target_face = _ma15_fixture(60, "P3_DELTA_MA15_PARALLEL")
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-15",
        {
            "body": source,
            "reference_face": reference,
            "target_face": target_face,
            "reference_point_mm": [4, 63, 4],
            "direction": [0, 1, 0],
            "position_tolerance_mm": 0.001,
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    _assert_snapshot(before, _snapshot(_refresh()["bodies"]), "MA15 parallel direction")
    return {"parallel_direction_rejected": True}


def _test_ma15_negative_tolerance():
    source, target, reference, target_face = _ma15_fixture(90, "P3_DELTA_MA15_TOLERANCE")
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-15",
        {
            "body": source,
            "reference_face": reference,
            "target_face": target_face,
            "reference_point_mm": [4, 93, 4],
            "direction": [1, 0, 0],
            "position_tolerance_mm": -0.001,
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    _assert_snapshot(before, _snapshot(_refresh()["bodies"]), "MA15 negative tolerance")
    return {"negative_tolerance_rejected": True, "body_position_unchanged": True}


def _test_ma18_count():
    attached = _block([210, 0, 0], [212, 3, 4])
    source = _copy(attached)
    before = _bounds(source)
    _call(
        "MA-18",
        {"body": source, "direction": [1, 2, 0], "count": 1, "spacing_mm": 5, "volume_tolerance_mm3": 0.001},
        True,
    )
    _assert_bounds(source, before, "MA18 invalid count source")
    return {"count_below_two_rejected": True}


def _test_ma18_direction():
    attached = _block([220, 0, 0], [222, 3, 4])
    source = _copy(attached)
    before = _bounds(source)
    _call(
        "MA-18",
        {"body": source, "direction": [0, 0, 0], "count": 3, "spacing_mm": 5, "volume_tolerance_mm3": 0.001},
        True,
    )
    _assert_bounds(source, before, "MA18 zero direction source")
    return {"zero_direction_rejected": True}


def _test_ma18_nonfinite():
    attached = _block([230, 0, 0], [232, 3, 4])
    source = _copy(attached)
    before = _bounds(source)
    _call(
        "MA-18",
        {"body": source, "direction": [1, 2, 0], "count": 3, "spacing_mm": float("nan"), "volume_tolerance_mm3": 0.001},
        True,
    )
    _assert_bounds(source, before, "MA18 nonfinite spacing source")
    return {"nonfinite_spacing_rejected": True}


def _test_ma19_periodic_count():
    source = _off_axis_source("P3_DELTA_MA19_PERIODIC", 240)
    before = _bounds(source)
    _call(
        "MA-19",
        {
            "body": source,
            "count": 5,
            "step_angle_degrees": 90,
            "axis_origin_mm": [0, 0, 0],
            "axis_direction": [0, 0, 1],
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    _assert_bounds(source, before, "MA19 periodic source")
    return {"periodic_duplicate_count_rejected": True}


def _test_ma19_zero_step():
    source = _off_axis_source("P3_DELTA_MA19_ZERO", 250)
    before = _bounds(source)
    _call(
        "MA-19",
        {
            "body": source,
            "count": 2,
            "step_angle_degrees": 0,
            "axis_origin_mm": [0, 0, 0],
            "axis_direction": [0, 0, 1],
            "volume_tolerance_mm3": 0.001,
        },
        True,
    )
    _assert_bounds(source, before, "MA19 zero-step source")
    return {"duplicate_zero_step_rejected": True}


def _test_ma24_empty_curves():
    base_x = 280
    body = _block([base_x, 0, 0], [base_x + 10, 8, 6])
    top = _face(body, [base_x, 0, 6, base_x + 10, 8, 6], [0, 0, 1], 80)
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-24",
        {"body": body, "face": top, "curves": [], "volume_tolerance_mm3": 0.001, "bbox_tolerance_mm": 0.001},
        True,
    )
    _assert_snapshot(before, _snapshot(_refresh()["bodies"]), "MA24 empty curves")
    return {"empty_curves_rejected": True}


def _test_ma24_negative_tolerance():
    base_x = 300
    body = _block([base_x, 0, 0], [base_x + 10, 8, 6])
    top = _face(body, [base_x, 0, 6, base_x + 10, 8, 6], [0, 0, 1], 80)
    curve = CurveSegment.Create(Point.Create((base_x + 4) / 1000.0, 0, 0.006), Point.Create((base_x + 4) / 1000.0, 0.008, 0.006))
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-24",
        {"body": body, "face": top, "curves": [curve], "volume_tolerance_mm3": 0.001, "bbox_tolerance_mm": -0.001},
        True,
    )
    _assert_snapshot(before, _snapshot(_refresh()["bodies"]), "MA24 negative tolerance")
    return {"negative_tolerance_rejected": True, "body_position_unchanged": True}


def _test_ma24_stale_face():
    first = _block([320, 0, 0], [330, 8, 6])
    second = _block([340, 0, 0], [350, 8, 6])
    wrong_face = _face(second, [340, 0, 6, 350, 8, 6], [0, 0, 1], 80)
    curve = CurveSegment.Create(Point.Create(324 / 1000.0, 0, 0.006), Point.Create(324 / 1000.0, 0.008, 0.006))
    before = _snapshot(_refresh()["bodies"])
    _call(
        "MA-24",
        {"body": first, "face": wrong_face, "curves": [curve], "volume_tolerance_mm3": 0.001, "bbox_tolerance_mm": 0.001},
        True,
    )
    _assert_snapshot(before, _snapshot(_refresh()["bodies"]), "MA24 stale face")
    return {"foreign_face_rejected": True}


def _run_suite():
    blank = _group("blank-design", ["MA-31"], _test_blank_design)
    if blank["status"] != "passed":
        return
    _group("ma10-native-loft", ["MA-10", "MA-31"], _test_ma10_native_loft)
    _group("ma15-point-to-face", ["MA-05", "MA-29", "MA-15", "MA-31"], _test_ma15_point_to_face)
    _group("ma18-linear-array", ["MA-05", "MA-13", "MA-18"], _test_ma18_linear_array)
    _group("ma19-circular-array", ["MA-05", "MA-13", "MA-19"], _test_ma19_circular_array)
    _group("ma24-split-face", ["MA-05", "MA-29", "MA-24"], _test_ma24_split_face)
    _group("unicode-name-only", ["MA-05", "MA-28"], _test_unicode_name_only)
    _group("negative-ma10-duplicate", ["MA-10", "MA-31"], _test_ma10_duplicate_section)
    _group("negative-ma10-policy", ["MA-10", "MA-31"], _test_ma10_policy)
    _group("negative-ma15-reference", ["MA-05", "MA-29", "MA-15", "MA-31"], _test_ma15_reference_point)
    _group("negative-ma15-parallel", ["MA-05", "MA-29", "MA-15", "MA-31"], _test_ma15_parallel_direction)
    _group("negative-ma15-tolerance", ["MA-05", "MA-29", "MA-15", "MA-31"], _test_ma15_negative_tolerance)
    _group("negative-ma18-count", ["MA-05", "MA-13", "MA-18"], _test_ma18_count)
    _group("negative-ma18-direction", ["MA-05", "MA-13", "MA-18"], _test_ma18_direction)
    _group("negative-ma18-nonfinite", ["MA-05", "MA-13", "MA-18"], _test_ma18_nonfinite)
    _group("negative-ma19-periodic-count", ["MA-05", "MA-13", "MA-19"], _test_ma19_periodic_count)
    _group("negative-ma19-zero-step", ["MA-05", "MA-13", "MA-19"], _test_ma19_zero_step)
    _group("negative-ma24-empty-curves", ["MA-05", "MA-29", "MA-24", "MA-31"], _test_ma24_empty_curves)
    _group("negative-ma24-tolerance", ["MA-05", "MA-29", "MA-24", "MA-31"], _test_ma24_negative_tolerance)
    _group("negative-ma24-foreign-face", ["MA-05", "MA-29", "MA-24", "MA-31"], _test_ma24_stale_face)


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
